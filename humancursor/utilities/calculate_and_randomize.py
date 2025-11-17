import math

from selenium.webdriver import Chrome, Edge, Firefox, Safari
import pytweening
import random

from humancursor.constants import (
    VIEWPORT_MARGIN_MIN,
    VIEWPORT_MARGIN_MAX,
    OFFSET_BOUNDARY_RANGE_LOW,
    OFFSET_BOUNDARY_RANGE_MID,
    OFFSET_BOUNDARY_RANGE_HIGH,
    OFFSET_BOUNDARY_WEIGHTS,
    KNOTS_COUNT_OPTIONS,
    KNOTS_COUNT_WEIGHTS,
    DISTORTION_MEAN_MIN,
    DISTORTION_MEAN_MAX,
    DISTORTION_STDEV_MIN,
    DISTORTION_STDEV_MAX,
    DISTORTION_FREQ_MIN,
    DISTORTION_FREQ_MAX,
    TARGET_POINTS_RANGE_LOW,
    TARGET_POINTS_RANGE_MID,
    TARGET_POINTS_RANGE_HIGH,
    TARGET_POINTS_WEIGHTS,
)


def calculate_absolute_offset(element, list_of_x_and_y_offsets: list) -> list:
    """Calculates exact number of pixel offsets from relative values
    
    Args:
        element: WebElement with size property
        list_of_x_and_y_offsets: [x_percent, y_percent] as floats (0.0 to 1.0)
        
    Returns:
        [x_pixels, y_pixels] as integers
        
    Raises:
        ValueError: If offsets list doesn't have exactly 2 values
    """
    if not isinstance(list_of_x_and_y_offsets, list) or len(list_of_x_and_y_offsets) != 2:
        raise ValueError("Offsets must be a list of 2 values [x, y]")
    
    dimensions = element.size
    width, height = dimensions["width"], dimensions["height"]
    x_final = width * list_of_x_and_y_offsets[0]
    y_final = height * list_of_x_and_y_offsets[1]

    return [int(x_final), int(y_final)]


def generate_random_curve_parameters(driver, pre_origin: tuple | list, post_destination: tuple | list) -> tuple:
    """Generates random parameters for the curve, the tween, number of knots, distortion, target points and boundaries.
    
    Args:
        driver: Browser driver (Selenium) or screen size provider (pyautogui)
        pre_origin: Starting point [x, y]
        post_destination: Ending point [x, y]
        
    Returns:
        Tuple of (offset_boundary_x, offset_boundary_y, knots_count, distortion_mean,
                  distortion_st_dev, distortion_frequency, tween, target_points)
    """
    is_web_driver = isinstance(driver, (Chrome, Firefox, Edge, Safari))
    
    if is_web_driver:
        viewport_width, viewport_height = driver.get_window_size().values()
    else:
        viewport_width, viewport_height = driver.size()
    
    min_width = viewport_width * VIEWPORT_MARGIN_MIN
    max_width = viewport_width * VIEWPORT_MARGIN_MAX
    min_height = viewport_height * VIEWPORT_MARGIN_MIN
    max_height = viewport_height * VIEWPORT_MARGIN_MAX

    tween_options = [
        pytweening.easeOutExpo,
        pytweening.easeInOutQuint,
        pytweening.easeInOutSine,
        pytweening.easeInOutQuart,
        pytweening.easeInOutExpo,
        pytweening.easeInOutCubic,
        pytweening.easeInOutCirc,
        pytweening.linear,
        pytweening.easeOutSine,
        pytweening.easeOutQuart,
        pytweening.easeOutQuint,
        pytweening.easeOutCubic,
        pytweening.easeOutCirc,
    ]

    tween = random.choice(tween_options)
    
    # Select offset boundaries with weighted randomness
    offset_boundary_x = random.choice(
        random.choices(
            [OFFSET_BOUNDARY_RANGE_LOW, OFFSET_BOUNDARY_RANGE_MID, OFFSET_BOUNDARY_RANGE_HIGH],
            OFFSET_BOUNDARY_WEIGHTS
        )[0]
    )
    offset_boundary_y = random.choice(
        random.choices(
            [OFFSET_BOUNDARY_RANGE_LOW, OFFSET_BOUNDARY_RANGE_MID, OFFSET_BOUNDARY_RANGE_HIGH],
            OFFSET_BOUNDARY_WEIGHTS
        )[0]
    )
    
    knots_count = random.choices(KNOTS_COUNT_OPTIONS, KNOTS_COUNT_WEIGHTS)[0]

    distortion_mean = random.choice(range(DISTORTION_MEAN_MIN, DISTORTION_MEAN_MAX)) / 100
    distortion_st_dev = random.choice(range(DISTORTION_STDEV_MIN, DISTORTION_STDEV_MAX)) / 100
    distortion_frequency = random.choice(range(DISTORTION_FREQ_MIN, DISTORTION_FREQ_MAX)) / 100

    if is_web_driver:
        target_points = random.choice(
            random.choices(
                [TARGET_POINTS_RANGE_LOW, TARGET_POINTS_RANGE_MID, TARGET_POINTS_RANGE_HIGH],
                TARGET_POINTS_WEIGHTS
            )[0]
        )
    else:
        # For system cursor, calculate based on distance
        distance = math.sqrt(
            (pre_origin[0] - post_destination[0]) ** 2 + 
            (pre_origin[1] - post_destination[1]) ** 2
        )
        target_points = max(int(distance), 2)

    # Reduce complexity if origin or destination is near viewport edge
    if (
            min_width > pre_origin[0]
            or max_width < pre_origin[0]
            or min_height > pre_origin[1]
            or max_height < pre_origin[1]
    ):
        offset_boundary_x = 1
        offset_boundary_y = 1
        knots_count = 1
    
    if (
            min_width > post_destination[0]
            or max_width < post_destination[0]
            or min_height > post_destination[1]
            or max_height < post_destination[1]
    ):
        offset_boundary_x = 1
        offset_boundary_y = 1
        knots_count = 1

    return (
        offset_boundary_x,
        offset_boundary_y,
        knots_count,
        distortion_mean,
        distortion_st_dev,
        distortion_frequency,
        tween,
        target_points,
    )
