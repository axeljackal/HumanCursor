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


def calculate_edge_proximity(point: tuple | list, viewport_width: int, viewport_height: int) -> float:
    """Calculate how close a point is to viewport edges
    
    Args:
        point: (x, y) coordinates as tuple or list
        viewport_width: Width of viewport
        viewport_height: Height of viewport
        
    Returns:
        Float between 0 (center) and 1 (edge) representing proximity to nearest edge
    """
    x, y = point
    
    # Distance to nearest edge (normalized to 0-1, where 1 is center, 0 is edge)
    x_proximity = min(x / viewport_width, (viewport_width - x) / viewport_width) * 2
    y_proximity = min(y / viewport_height, (viewport_height - y) / viewport_height) * 2
    
    # Return inverse (1 at edge, 0 at center)
    edge_proximity = 1 - min(x_proximity, y_proximity)
    return max(0, min(edge_proximity, 1))  # Clamp to [0, 1]


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
    
    # Calculate distance once for both knots and target_points
    distance = math.sqrt(
        (pre_origin[0] - post_destination[0]) ** 2 + 
        (pre_origin[1] - post_destination[1]) ** 2
    )
    
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
    
    # Randomize thresholds to prevent fingerprinting
    threshold_1 = random.uniform(80, 120)    # ~100px nominal
    threshold_2 = random.uniform(400, 600)   # ~500px nominal
    
    # Scale knots with distance using randomized thresholds
    if distance < threshold_1:
        options = [1, 2]
        weights = [0.65, 0.35]
    elif distance < threshold_2:
        options = [2, 3, 4]
        weights = [0.45, 0.40, 0.15]
    else:
        options = [3, 4, 5, 6]
        weights = [0.35, 0.40, 0.18, 0.07]
    
    knots_count = random.choices(options, weights)[0]

    distortion_mean = random.choice(range(DISTORTION_MEAN_MIN, DISTORTION_MEAN_MAX)) / 100
    distortion_st_dev = random.choice(range(DISTORTION_STDEV_MIN, DISTORTION_STDEV_MAX)) / 100
    distortion_frequency = random.choice(range(DISTORTION_FREQ_MIN, DISTORTION_FREQ_MAX)) / 100

    # Use logarithmic scaling with distance-based tiers
    # Short movements: higher density | Long movements: logarithmic growth
    if distance < 100:
        target_points = max(int(distance * 0.6), 30)  # 0.6 points/pixel, min 30
    elif distance < 500:
        target_points = int(60 + 40 * math.log2(distance / 100))  # Logarithmic scaling
    else:
        target_points = int(100 + 50 * math.log2(distance / 500))  # Continued scaling
    
    # Cap to prevent excessive computation
    target_points = min(target_points, 250)

    # Gradually reduce complexity based on edge proximity
    origin_edge_proximity = calculate_edge_proximity(pre_origin, viewport_width, viewport_height)
    dest_edge_proximity = calculate_edge_proximity(post_destination, viewport_width, viewport_height)
    max_edge_proximity = max(origin_edge_proximity, dest_edge_proximity)
    
    # Scale boundaries instead of binary reduction
    # At edge: 70% boundary reduction, 50% knot reduction
    # At center: No reduction
    offset_boundary_x = int(offset_boundary_x * (1 - max_edge_proximity * 0.7))
    offset_boundary_y = int(offset_boundary_y * (1 - max_edge_proximity * 0.7))
    knots_count = max(1, int(knots_count * (1 - max_edge_proximity * 0.5)))

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
