from time import sleep
import random
import pyautogui
from typing import Union, Optional, Tuple, List

from humancursor.utilities.human_curve_generator import HumanizeMouseTrajectory
from humancursor.utilities.calculate_and_randomize import generate_random_curve_parameters
from humancursor.constants import (
    DEFAULT_DURATION_MIN,
    DEFAULT_DURATION_MAX,
    CLICK_PAUSE_MIN,
    CLICK_PAUSE_MAX,
    STEADY_OFFSET_BOUNDARY,
    STEADY_DISTORTION_MEAN,
    STEADY_DISTORTION_STDEV,
    STEADY_DISTORTION_FREQ,
)


class SystemCursor:
    """Simulates human-like cursor movements on the system level.
    
    Warning: This class modifies global pyautogui settings (MINIMUM_DURATION, 
    MINIMUM_SLEEP, PAUSE). Multiple instances may interfere with each other.
    Creating multiple SystemCursor instances will affect the same global state.
    
    Call cleanup() method to restore original pyautogui settings when done.
    """
    
    def __init__(self):
        # Store original settings for cleanup
        self._original_min_duration = pyautogui.MINIMUM_DURATION
        self._original_min_sleep = pyautogui.MINIMUM_SLEEP
        self._original_pause = pyautogui.PAUSE
        
        # Set new settings
        pyautogui.MINIMUM_DURATION = 0
        pyautogui.MINIMUM_SLEEP = 0
        pyautogui.PAUSE = 0
    
    def cleanup(self):
        """Restore original pyautogui settings.
        
        Call this method when you're done using SystemCursor to restore
        the original global pyautogui configuration.
        """
        pyautogui.MINIMUM_DURATION = self._original_min_duration
        pyautogui.MINIMUM_SLEEP = self._original_min_sleep
        pyautogui.PAUSE = self._original_pause

    @staticmethod
    def move_to(point: Union[List, Tuple], duration: Union[int, float, None] = None, human_curve=None, steady=False):
        """Moves to certain coordinates of screen
        
        Args:
            point: Target coordinates as [x, y] or (x, y)
            duration: Movement duration in seconds (None for random 0.5-2.0s)
            human_curve: Pre-generated HumanizeMouseTrajectory curve
            steady: If True, uses straighter movement path
            
        Raises:
            TypeError: If point is not a list or tuple
            ValueError: If point doesn't contain exactly 2 numeric values
        """
        if not isinstance(point, (list, tuple)):
            raise TypeError(f"Point must be list or tuple, got {type(point).__name__}")
        if len(point) != 2:
            raise ValueError(f"Point must contain exactly 2 coordinates, got {len(point)}")
        if not all(isinstance(coord, (int, float)) for coord in point):
            raise ValueError("Point coordinates must be numeric (int or float)")
        
        from_point = pyautogui.position()

        if not human_curve:
            human_curve = SystemCursor._generate_human_curve(from_point, point, steady)

        if duration is None:
            duration = random.uniform(DEFAULT_DURATION_MIN, DEFAULT_DURATION_MAX)
        
        SystemCursor._execute_curve_movement(human_curve, point, duration)
    
    @staticmethod
    def _generate_human_curve(from_point: Tuple, to_point: Union[List, Tuple], steady: bool) -> HumanizeMouseTrajectory:
        """Generate a human-like movement curve between two points.
        
        Args:
            from_point: Starting coordinates
            to_point: Ending coordinates
            steady: If True, uses less curvature
            
        Returns:
            HumanizeMouseTrajectory object with the curve points
        """
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
            pyautogui, from_point, to_point
        )
        
        if steady:
            offset_boundary_x = STEADY_OFFSET_BOUNDARY
            offset_boundary_y = STEADY_OFFSET_BOUNDARY
            distortion_mean = STEADY_DISTORTION_MEAN
            distortion_st_dev = STEADY_DISTORTION_STDEV
            distortion_frequency = STEADY_DISTORTION_FREQ
        
        return HumanizeMouseTrajectory(
            from_point,
            to_point,
            offset_boundary_x=offset_boundary_x,
            offset_boundary_y=offset_boundary_y,
            knots_count=knots_count,
            distortion_mean=distortion_mean,
            distortion_st_dev=distortion_st_dev,
            distortion_frequency=distortion_frequency,
            tween=tween,
            target_points=target_points,
        )
    
    @staticmethod
    def _execute_curve_movement(human_curve: HumanizeMouseTrajectory, final_point: Union[List, Tuple], duration: float) -> None:
        """Execute the cursor movement along the generated curve.
        
        Args:
            human_curve: The curve to follow
            final_point: Final destination point
            duration: Total duration for the movement
            
        Raises:
            ValueError: If human_curve has no points
        """
        if not human_curve.points or len(human_curve.points) == 0:
            raise ValueError("Human curve has no points to follow")
        
        pyautogui.PAUSE = duration / len(human_curve.points)
        for point in human_curve.points:
            pyautogui.moveTo(point)
        pyautogui.moveTo(final_point)

    def click_on(self, point: Union[List, Tuple], clicks: int = 1, click_duration: Union[int, float] = 0, steady=False):
        """Clicks a specified number of times, on the specified coordinates
        
        Args:
            point: Target coordinates as [x, y] or (x, y)
            clicks: Number of times to click (must be positive)
            click_duration: Duration to hold mouse button down in seconds
            steady: If True, uses straighter movement path
            
        Raises:
            ValueError: If clicks is not a positive integer
            TypeError/ValueError: From move_to if point is invalid
        """
        if not isinstance(clicks, int) or clicks < 1:
            raise ValueError(f"Clicks must be a positive integer, got {clicks}")
        if not isinstance(click_duration, (int, float)) or click_duration < 0:
            raise ValueError(f"Click duration must be non-negative, got {click_duration}")
        
        self.move_to(point, steady=steady)
        for _ in range(clicks):
            pyautogui.mouseDown()
            sleep(click_duration)
            pyautogui.mouseUp()
            sleep(random.uniform(CLICK_PAUSE_MIN, CLICK_PAUSE_MAX))

    def drag_and_drop(self, from_point: Union[List, Tuple], to_point: Union[List, Tuple], duration: Union[int, float, List, Tuple, None] = None, steady=False):
        """Drags from a certain point, and releases to another
        
        Args:
            from_point: Starting coordinates as [x, y] or (x, y)
            to_point: Ending coordinates as [x, y] or (x, y)
            duration: Total duration in seconds, or [first_half, second_half] durations
            steady: If True, uses straighter movement path
            
        Raises:
            TypeError/ValueError: From move_to if points are invalid
        """
        # Validate both points (move_to will validate them)
        if not isinstance(from_point, (list, tuple)):
            raise TypeError(f"from_point must be list or tuple, got {type(from_point).__name__}")
        if not isinstance(to_point, (list, tuple)):
            raise TypeError(f"to_point must be list or tuple, got {type(to_point).__name__}")
        
        if isinstance(duration, (list, tuple)):
            first_duration, second_duration = duration
        elif isinstance(duration, (float, int)):
            first_duration = second_duration = duration / 2
        else:
            first_duration = second_duration = None

        self.move_to(from_point, duration=first_duration)
        pyautogui.mouseDown()
        self.move_to(to_point, duration=second_duration, steady=steady)
        pyautogui.mouseUp()
