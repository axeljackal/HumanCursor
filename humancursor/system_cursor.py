from time import sleep, time
import random
import math
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


class _CursorContext:
    """Internal class to track cursor usage context for realistic speed variation"""
    
    def __init__(self):
        self.start_time = time()
        self.movement_count = 0
        self.last_movement_time = time()
        self.recent_targets = []  # Track last 5 target sizes
    
    def record_movement(self, target_size: Optional[float] = None):
        """Record a movement for fatigue and pattern tracking"""
        self.movement_count += 1
        self.last_movement_time = time()
        if target_size is not None:
            self.recent_targets.append(target_size)
            if len(self.recent_targets) > 5:
                self.recent_targets.pop(0)
    
    def get_fatigue_factor(self) -> float:
        """Calculate fatigue factor based on usage duration
        
        Returns:
            Float between 1.0 (no fatigue) and 1.15 (15% slower after 30+ minutes)
        """
        elapsed_minutes = (time() - self.start_time) / 60
        # Gradual slowdown: 1% per 2 minutes, capped at 15%
        fatigue = 1.0 + min(elapsed_minutes / 2 * 0.01, 0.15)
        return fatigue
    
    def get_repetition_factor(self) -> float:
        """Calculate speed boost from repeated similar actions
        
        Returns:
            Float between 0.85 (15% faster) and 1.0 (normal speed)
        """
        if self.movement_count < 3:
            return 1.0  # No boost for first few movements
        
        # Check if recent movements are similar (target size variance)
        if len(self.recent_targets) < 3:
            return 1.0
        
        # Calculate variance in recent target sizes
        avg_size = sum(self.recent_targets) / len(self.recent_targets)
        variance = sum((s - avg_size) ** 2 for s in self.recent_targets) / len(self.recent_targets)
        
        # Low variance (repetitive tasks) = faster movements
        if variance < 100:  # Similar targets
            return 0.85  # 15% speed boost
        elif variance < 500:
            return 0.92  # 8% speed boost
        else:
            return 1.0  # No boost for varied tasks


class SystemCursor:
    """Simulates human-like cursor movements on the system level.
    
    Warning: This class modifies global pyautogui settings (MINIMUM_DURATION, 
    MINIMUM_SLEEP, PAUSE). Multiple instances may interfere with each other.
    Creating multiple SystemCursor instances will affect the same global state.
    
    Usage:
        # Method 1: Manual cleanup
        cursor = SystemCursor()
        # ... do work ...
        cursor.cleanup()
        
        # Method 2: Context manager (recommended)
        with SystemCursor() as cursor:
            # ... do work ...
            pass  # cleanup happens automatically
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
        
        # Initialize context for speed variation
        self._context = _CursorContext()
    
    def __enter__(self):
        """Enter the context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager and cleanup."""
        self.cleanup()
        return False
    
    def cleanup(self):
        """Restore original pyautogui settings.
        
        Call this method when you're done using SystemCursor to restore
        the original global pyautogui configuration.
        """
        pyautogui.MINIMUM_DURATION = self._original_min_duration
        pyautogui.MINIMUM_SLEEP = self._original_min_sleep
        pyautogui.PAUSE = self._original_pause

    def _calculate_movement_duration(self, from_point: Tuple, to_point: Union[List, Tuple], target_size: float = 12.0) -> float:
        """Calculate realistic movement duration based on Fitts' Law with contextual variation
        
        Fitts' Law: MT = a + b * log2(D/W + 1)
        Adjusted for: target size, fatigue, and repetition patterns
        
        Args:
            from_point: Starting coordinates (x, y)
            to_point: Ending coordinates (x, y)
            target_size: Target size in pixels (smaller = slower)
            
        Returns:
            Duration in seconds for the movement
        """
        # Calculate Euclidean distance
        distance = math.sqrt(
            (to_point[0] - from_point[0])**2 + 
            (to_point[1] - from_point[1])**2
        )
        
        # Randomize Fitts' Law coefficients per movement (prevents fingerprinting)
        a = random.uniform(0.08, 0.12)     # Intercept (reaction time component)
        b = random.uniform(0.12, 0.18)     # Slope (movement time component)
        
        # Use provided target size (smaller targets = longer time)
        target_width = max(target_size, 5)  # Minimum 5px to avoid division issues
        
        # Calculate Index of Difficulty and apply Fitts' Law
        index_of_difficulty = math.log2(distance / target_width + 1)
        base_time = a + b * index_of_difficulty
        
        # Apply contextual speed variations
        fatigue_factor = self._context.get_fatigue_factor()  # 1.0 to 1.15 (slower over time)
        repetition_factor = self._context.get_repetition_factor()  # 0.85 to 1.0 (faster when repeating)
        
        # Combine factors
        base_time *= fatigue_factor * repetition_factor
        
        # Add human variability: ±25% with slight bias toward slower movements
        duration = base_time * random.uniform(0.75, 1.30)
        
        # Clamp to reasonable range (150ms minimum, 3s maximum)
        duration = max(0.15, min(duration, 3.0))
        
        # Record movement for context tracking
        self._context.record_movement(target_size)
        
        return duration

    def move_to(self, point: Union[List, Tuple], duration: Union[int, float, None] = None, human_curve=None, steady=False, target_size: float = 12.0):
        """Moves to certain coordinates of screen
        
        Args:
            point: Target coordinates as [x, y] or (x, y)
            duration: Movement duration in seconds (None for auto-calculated with Fitts' Law)
            human_curve: Pre-generated HumanizeMouseTrajectory curve
            steady: If True, uses straighter movement path
            target_size: Estimated target size in pixels (affects speed for small targets)
            
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
            human_curve = self._generate_human_curve(from_point, point, steady)

        if duration is None:
            duration = self._calculate_movement_duration(from_point, point, target_size)
        
        self._execute_curve_movement(human_curve, point, duration)
    
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

    def click_on(self, point: Union[List, Tuple], clicks: int = 1, click_duration: Union[int, float] = 0, steady=False, target_size: float = 12.0):
        """Clicks a specified number of times, on the specified coordinates
        
        Args:
            point: Target coordinates as [x, y] or (x, y)
            clicks: Number of times to click (must be positive)
            click_duration: Duration to hold mouse button down in seconds
            steady: If True, uses straighter movement path
            target_size: Estimated target size in pixels
            
        Raises:
            ValueError: If clicks is not a positive integer
            TypeError/ValueError: From move_to if point is invalid
        """
        if not isinstance(clicks, int) or clicks < 1:
            raise ValueError(f"Clicks must be a positive integer, got {clicks}")
        if not isinstance(click_duration, (int, float)) or click_duration < 0:
            raise ValueError(f"Click duration must be non-negative, got {click_duration}")
        
        self.move_to(point, steady=steady, target_size=target_size)
        
        # Add realistic pre-click pause (humans don't click instantly after arriving)
        pre_click_pause = random.uniform(0.05, 0.15)  # 50-150ms pause before clicking
        sleep(pre_click_pause)
        
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
    
    @staticmethod
    def idle_jitter(duration: float = 1.0, intensity: float = 1.0):
        """Simulate natural hand tremor while hovering/idle
        
        Humans exhibit tiny random movements when holding the mouse still,
        simulating natural hand tremor and micro-adjustments.
        
        Args:
            duration: How long to jitter in seconds (default 1.0)
            intensity: Jitter intensity multiplier (default 1.0, range 0.5-2.0)
            
        Raises:
            ValueError: If duration or intensity are invalid
        """
        if not isinstance(duration, (int, float)) or duration <= 0:
            raise ValueError(f"Duration must be positive, got {duration}")
        if not isinstance(intensity, (int, float)) or intensity <= 0:
            raise ValueError(f"Intensity must be positive, got {intensity}")
        
        intensity = max(0.5, min(intensity, 2.0))  # Clamp to reasonable range
        
        # Number of micro-movements (10 per second)
        iterations = int(duration * 10)
        interval = duration / iterations
        
        for _ in range(iterations):
            # Tiny random offset (±1-3 pixels scaled by intensity)
            max_offset = 3 * intensity
            x_offset = random.uniform(-max_offset, max_offset)
            y_offset = random.uniform(-max_offset, max_offset)
            
            current_pos = pyautogui.position()
            new_x = current_pos[0] + x_offset
            new_y = current_pos[1] + y_offset
            
            pyautogui.moveTo(new_x, new_y, duration=interval)
            sleep(interval)
