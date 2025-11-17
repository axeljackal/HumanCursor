from time import sleep
import random
import pyautogui

from humancursor.utilities.human_curve_generator import HumanizeMouseTrajectory
from humancursor.utilities.calculate_and_randomize import generate_random_curve_parameters


class SystemCursor:
    """Simulates human-like cursor movements on the system level.
    
    Warning: This class modifies global pyautogui settings (MINIMUM_DURATION, 
    MINIMUM_SLEEP, PAUSE). Multiple instances may interfere with each other.
    Creating multiple SystemCursor instances will affect the same global state.
    """
    
    def __init__(self):
        pyautogui.MINIMUM_DURATION = 0
        pyautogui.MINIMUM_SLEEP = 0
        pyautogui.PAUSE = 0

    @staticmethod
    def move_to(point: list | tuple, duration: int | float | None = None, human_curve=None, steady=False):
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
                pyautogui, from_point, point
            )
            if steady:
                offset_boundary_x, offset_boundary_y = 10, 10
                distortion_mean, distortion_st_dev, distortion_frequency = 1.2, 1.2, 1
            human_curve = HumanizeMouseTrajectory(
                from_point,
                point,
                offset_boundary_x=offset_boundary_x,
                offset_boundary_y=offset_boundary_y,
                knots_count=knots_count,
                distortion_mean=distortion_mean,
                distortion_st_dev=distortion_st_dev,
                distortion_frequency=distortion_frequency,
                tween=tween,
                target_points=target_points,
            )

        if duration is None:
            duration = random.uniform(0.5, 2.0)
        pyautogui.PAUSE = duration / len(human_curve.points)
        for pnt in human_curve.points:
            pyautogui.moveTo(pnt)
        pyautogui.moveTo(point)

    def click_on(self, point: list | tuple, clicks: int = 1, click_duration: int | float = 0, steady=False):
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
            sleep(random.uniform(0.170, 0.280))

    def drag_and_drop(self, from_point: list | tuple, to_point: list | tuple, duration: int | float | list | tuple | None = None, steady=False):
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
