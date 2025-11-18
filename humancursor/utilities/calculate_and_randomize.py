import math
from typing import Union, Tuple, List

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


def calculate_edge_proximity(point: Union[Tuple, List], viewport_width: Union[int, float], viewport_height: Union[int, float]) -> float:
    """Calculate how close a point is to viewport edges
    
    Args:
        point: (x, y) coordinates as tuple or list
        viewport_width: Width of viewport (must be positive)
        viewport_height: Height of viewport (must be positive)
        
    Returns:
        Float between 0 (center) and 1 (edge) representing proximity to nearest edge
        
    Raises:
        ValueError: If viewport dimensions are not positive
        TypeError: If point is not a tuple or list with 2 elements
    """
    if not isinstance(point, (tuple, list)) or len(point) != 2:
        raise TypeError(f"Point must be a tuple or list with 2 elements, got {type(point).__name__} with {len(point) if hasattr(point, '__len__') else 'unknown'} elements")
    
    if not isinstance(viewport_width, (int, float)) or viewport_width <= 0:
        raise ValueError(f"viewport_width must be a positive number, got {viewport_width}")
    
    if not isinstance(viewport_height, (int, float)) or viewport_height <= 0:
        raise ValueError(f"viewport_height must be a positive number, got {viewport_height}")
    
    x, y = point
    
    # Distance to nearest edge (normalized to 0-1, where 1 is center, 0 is edge)
    # Safe division: viewport dimensions are validated to be positive
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
        ValueError: If offsets list doesn't have exactly 2 values or values out of range
        TypeError: If element doesn't have size property or offsets aren't numeric
    """
    if not isinstance(list_of_x_and_y_offsets, list) or len(list_of_x_and_y_offsets) != 2:
        raise ValueError(f"Offsets must be a list of 2 values [x, y], got {type(list_of_x_and_y_offsets).__name__} with {len(list_of_x_and_y_offsets) if hasattr(list_of_x_and_y_offsets, '__len__') else 'unknown'} elements")
    
    # Validate offset values are numeric and in valid range
    for i, offset in enumerate(list_of_x_and_y_offsets):
        if not isinstance(offset, (int, float)):
            raise TypeError(f"Offset {i} must be numeric, got {type(offset).__name__}")
        if not 0 <= offset <= 1:
            raise ValueError(f"Offset {i} must be between 0.0 and 1.0, got {offset}")
    
    # Validate element has size property
    try:
        dimensions = element.size
    except AttributeError:
        raise TypeError(f"Element must have 'size' property (WebElement expected), got {type(element).__name__}")
    
    # Validate dimensions are present and positive
    if not isinstance(dimensions, dict) or 'width' not in dimensions or 'height' not in dimensions:
        raise ValueError(f"Element size must be a dict with 'width' and 'height' keys, got {dimensions}")
    
    width, height = dimensions["width"], dimensions["height"]
    
    if width < 0 or height < 0:
        raise ValueError(f"Element dimensions must be non-negative, got width={width}, height={height}")
    
    x_final = width * list_of_x_and_y_offsets[0]
    y_final = height * list_of_x_and_y_offsets[1]

    return [int(x_final), int(y_final)]


def generate_random_curve_parameters(driver, pre_origin: Union[Tuple, List], post_destination: Union[Tuple, List]) -> tuple:
    """Generates random parameters for the curve, the tween, number of knots, distortion, target points and boundaries.
    
    Args:
        driver: Browser driver (Selenium) or screen size provider (pyautogui)
        pre_origin: Starting point [x, y]
        post_destination: Ending point [x, y]
        
    Returns:
        Tuple of (offset_boundary_x, offset_boundary_y, knots_count, distortion_mean,
                  distortion_st_dev, distortion_frequency, tween, target_points)
                  
    Raises:
        TypeError: If points are not tuples/lists or driver is invalid
        ValueError: If points don't have exactly 2 coordinates or coordinates are not numeric
    """
    # Validate input points
    if not isinstance(pre_origin, (tuple, list)) or len(pre_origin) != 2:
        raise TypeError(f"pre_origin must be a tuple or list with 2 elements, got {type(pre_origin).__name__}")
    
    if not isinstance(post_destination, (tuple, list)) or len(post_destination) != 2:
        raise TypeError(f"post_destination must be a tuple or list with 2 elements, got {type(post_destination).__name__}")
    
    # Validate coordinates are numeric
    for i, coord in enumerate(pre_origin):
        if not isinstance(coord, (int, float)):
            raise ValueError(f"pre_origin coordinate {i} must be numeric, got {type(coord).__name__}")
    
    for i, coord in enumerate(post_destination):
        if not isinstance(coord, (int, float)):
            raise ValueError(f"post_destination coordinate {i} must be numeric, got {type(coord).__name__}")
    
    is_web_driver = isinstance(driver, (Chrome, Firefox, Edge, Safari))
    
    try:
        if is_web_driver:
            viewport_width, viewport_height = driver.get_window_size().values()
        else:
            viewport_width, viewport_height = driver.size()
    except (AttributeError, TypeError) as e:
        raise TypeError(f"Driver must have get_window_size() method or size() method, got {type(driver).__name__}: {e}")
    
    # Validate viewport dimensions
    if not isinstance(viewport_width, (int, float)) or viewport_width <= 0:
        raise ValueError(f"Viewport width must be positive, got {viewport_width}")
    
    if not isinstance(viewport_height, (int, float)) or viewport_height <= 0:
        raise ValueError(f"Viewport height must be positive, got {viewport_height}")
    
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

    # IMPROVED: Scale distortion based on distance to reduce jerkiness on short movements
    # Short movements need less distortion to maintain smoothness
    if distance < 30:
        # Very short movements: reduce distortion significantly (60% reduction)
        distortion_st_dev *= 0.4
        distortion_frequency *= 0.5
    elif distance < 75:
        # Short movements: moderate distortion reduction (30% reduction)
        distortion_st_dev *= 0.7
        distortion_frequency *= 0.8

    # Use logarithmic scaling with distance-based tiers
    # IMPROVED: Reduced point density for very short movements to improve smoothness
    # Short movements: lower density to reduce jerkiness | Long movements: logarithmic growth
    if distance < 50:
        # Very short movements: significantly reduced points to minimize jerkiness
        target_points = max(int(distance * 0.3), 10)  # 0.3 points/pixel, min 10
    elif distance < 100:
        # Short movements: moderate point density
        target_points = max(int(distance * 0.5), 15)  # 0.5 points/pixel, min 15
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
