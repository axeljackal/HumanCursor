import random
import logging
import numpy as np

from selenium.common.exceptions import MoveTargetOutOfBoundsException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver import Firefox
from selenium.webdriver.remote.webelement import WebElement

from humancursor.utilities.human_curve_generator import HumanizeMouseTrajectory
from humancursor.utilities.calculate_and_randomize import generate_random_curve_parameters, calculate_absolute_offset
from humancursor.constants import (
    CLICK_OFFSET_MIN,
    CLICK_OFFSET_MAX,
    STEADY_OFFSET_BOUNDARY,
    STEADY_DISTORTION_MEAN,
    STEADY_DISTORTION_STDEV,
    STEADY_DISTORTION_FREQ,
)

logger = logging.getLogger(__name__)


class WebAdjuster:
    """Handles human-like cursor movements for web automation.
    
    This class manages the low-level movement calculations and execution
    for web-based cursor automation using Selenium.
    """
    
    def __init__(self, driver):
        self.__driver = driver
        self.__action = ActionChains(self.__driver, duration=0 if not isinstance(driver, Firefox) else 1)
        self.origin_coordinate = [0, 0]

    def move_to(
        self,
        element_or_pos,
        origin_coordinates=None,
        absolute_offset=False,
        relative_position=None,
        human_curve=None,
        steady=False
    ):
        """Moves the cursor, trying to mimic human behaviour!
        
        Args:
            element_or_pos: WebElement or [x, y] coordinates
            origin_coordinates: Starting position (None uses last position)
            absolute_offset: If True, treat coordinates as pixel offsets
            relative_position: [x_pct, y_pct] within element
            human_curve: Pre-generated curve
            steady: If True, straighter movement
            
        Returns:
            New cursor position as [x, y]
        """
        origin = origin_coordinates if origin_coordinates is not None else self.origin_coordinate

        pre_origin = tuple(origin)
        destination_x, destination_y = self._calculate_destination(
            element_or_pos, pre_origin, absolute_offset, relative_position
        )
        
        human_curve = self._get_or_generate_curve(
            origin, destination_x, destination_y, steady, human_curve
        )
        
        total_offset = self._execute_movement(human_curve, origin, element_or_pos)
        
        self.origin_coordinate = [
            pre_origin[0] + total_offset[0],
            pre_origin[1] + total_offset[1],
        ]

        return [pre_origin[0] + total_offset[0], pre_origin[1] + total_offset[1]]
    
    def _calculate_destination(self, element_or_pos, pre_origin: tuple, absolute_offset: bool, relative_position) -> tuple:
        """Calculate the destination coordinates based on input type.
        
        Args:
            element_or_pos: WebElement or coordinates
            pre_origin: Current position
            absolute_offset: Whether to use absolute positioning
            relative_position: Position within element
            
        Returns:
            (x, y) destination coordinates
        """
        if isinstance(element_or_pos, list):
            if not absolute_offset:
                x, y = element_or_pos[0], element_or_pos[1]
            else:
                x = element_or_pos[0] + pre_origin[0]
                y = element_or_pos[1] + pre_origin[1]
        else:
            script = "return { x: Math.round(arguments[0].getBoundingClientRect().left), y: Math.round(arguments[0].getBoundingClientRect().top) };"
            destination = self.__driver.execute_script(script, element_or_pos)
            
            if relative_position is None:
                # Calculate element dimensions
                element_width = element_or_pos.size["width"]
                element_height = element_or_pos.size["height"]
                element_area = element_width * element_height
                
                # Adaptive beta distribution parameters
                # Smaller elements = tighter distribution (higher alpha/beta)
                # Larger elements = wider distribution (lower alpha/beta)
                # Range: 2-5 based on element area
                alpha = beta = 2 + min(element_area / 10000, 3)
                
                # Beta distribution centered at 0.5 (center-biased clicking)
                # This mimics human tendency to click near element centers
                x_random_offset = np.random.beta(alpha, beta)
                y_random_offset = np.random.beta(alpha, beta)

                x = destination["x"] + (element_or_pos.size["width"] * x_random_offset)
                y = destination["y"] + (element_or_pos.size["height"] * y_random_offset)
            else:
                abs_exact_offset = calculate_absolute_offset(element_or_pos, relative_position)
                x_exact_offset, y_exact_offset = abs_exact_offset[0], abs_exact_offset[1]
                x = destination["x"] + x_exact_offset
                y = destination["y"] + y_exact_offset
        
        return x, y
    
    def _get_or_generate_curve(self, origin: list, destination_x: float, destination_y: float, 
                                steady: bool, human_curve) -> HumanizeMouseTrajectory:
        """Get existing curve or generate a new one.
        
        Args:
            origin: Starting coordinates
            destination_x: Target x coordinate
            destination_y: Target y coordinate
            steady: Whether to use steady mode
            human_curve: Existing curve or None
            
        Returns:
            HumanizeMouseTrajectory object
        """
        if human_curve:
            return human_curve
        
        (
            offset_boundary_x,
            offset_boundary_y,
            knots_count,
            distortion_mean,
            distortion_st_dev,
            distortion_frequency,
            tween,
            target_points,
        ) = generate_random_curve_parameters(
            self.__driver, [origin[0], origin[1]], [destination_x, destination_y]
        )
        
        if steady:
            offset_boundary_x = STEADY_OFFSET_BOUNDARY
            offset_boundary_y = STEADY_OFFSET_BOUNDARY
            distortion_mean = STEADY_DISTORTION_MEAN
            distortion_st_dev = STEADY_DISTORTION_STDEV
            distortion_frequency = STEADY_DISTORTION_FREQ
        
        return HumanizeMouseTrajectory(
            [origin[0], origin[1]],
            [destination_x, destination_y],
            offset_boundary_x=offset_boundary_x,
            offset_boundary_y=offset_boundary_y,
            knots_count=knots_count,
            distortion_mean=distortion_mean,
            distortion_st_dev=distortion_st_dev,
            distortion_frequency=distortion_frequency,
            tween=tween,
            target_points=target_points,
        )
    
    def _execute_movement(self, human_curve: HumanizeMouseTrajectory, origin: list, element_or_pos) -> list:
        """Execute the cursor movement along the curve.
        
        Args:
            human_curve: The trajectory to follow
            origin: Starting position
            element_or_pos: The target element or position (for fallback)
            
        Returns:
            [x_offset, y_offset] total movement
        """
        fractional_accumulator = [0, 0]
        total_offset = [0, 0]
        
        for point in human_curve.points:
            x_offset, y_offset = point[0] - origin[0], point[1] - origin[1]
            fractional_accumulator[0] += x_offset - int(x_offset)
            fractional_accumulator[1] += y_offset - int(y_offset)
            
            if (abs(fractional_accumulator[0]) > 1) and (abs(fractional_accumulator[1]) > 1):
                self.__action.move_by_offset(
                    int(fractional_accumulator[0]), int(fractional_accumulator[1])
                )
                total_offset[0] += int(fractional_accumulator[0])
                total_offset[1] += int(fractional_accumulator[1])
                fractional_accumulator[0] = fractional_accumulator[0] - int(fractional_accumulator[0])
                fractional_accumulator[1] = fractional_accumulator[1] - int(fractional_accumulator[1])
            elif abs(fractional_accumulator[0]) > 1:
                self.__action.move_by_offset((int(fractional_accumulator[0])), 0)
                total_offset[0] += int(fractional_accumulator[0])
                fractional_accumulator[0] = fractional_accumulator[0] - int(fractional_accumulator[0])
            elif abs(fractional_accumulator[1]) > 1:
                self.__action.move_by_offset(0, int(fractional_accumulator[1]))
                total_offset[1] += int(fractional_accumulator[1])
                fractional_accumulator[1] = fractional_accumulator[1] - int(fractional_accumulator[1])
            
            origin[0], origin[1] = point[0], point[1]
            total_offset[0] += int(x_offset)
            total_offset[1] += int(y_offset)
            self.__action.move_by_offset(int(x_offset), int(y_offset))

        total_offset[0] += int(fractional_accumulator[0])
        total_offset[1] += int(fractional_accumulator[1])
        self.__action.move_by_offset(int(fractional_accumulator[0]), int(fractional_accumulator[1]))
        
        try:
            self.__action.perform()
        except MoveTargetOutOfBoundsException as e:
            # Fallback to direct movement if human trajectory fails
            logger.warning(
                "MoveTargetOutOfBoundsException - Attempting fallback to direct movement. Error: %s",
                str(e)
            )
            # Only use move_to_element if element_or_pos is a WebElement
            if isinstance(element_or_pos, WebElement):
                self.__action.move_to_element(element_or_pos)
                self.__action.perform()
                logger.info("Fallback successful using move_to_element")
            else:
                # For coordinate-based movements, re-raise the exception
                logger.error("Cannot fallback for coordinate-based movement")
                raise
        
        return total_offset
