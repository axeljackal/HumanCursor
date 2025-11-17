"""Constants for HumanCursor package.

This module contains all configuration constants used throughout the package
to avoid magic numbers and improve maintainability.
"""

# Duration settings (in seconds)
DEFAULT_DURATION_MIN = 0.5
DEFAULT_DURATION_MAX = 2.0

# Click timing settings (in seconds)
CLICK_PAUSE_MIN = 0.170
CLICK_PAUSE_MAX = 0.280

# GUI window settings
WINDOW_WIDTH = 340
WINDOW_HEIGHT = 320
WINDOW_BACKGROUND_COLOR = '#3e99de'
INDICATOR_BACKGROUND_COLOR = '#577b96'

# GUI indicator dimensions
INDICATOR_WIDTH = 50
INDICATOR_HEIGHT = 100
INDICATOR_RECT_X1 = 15
INDICATOR_RECT_Y1 = 10
INDICATOR_RECT_X2 = 38
INDICATOR_RECT_Y2 = 33

# GUI colors
INDICATOR_COLOR_INACTIVE = "red"
INDICATOR_COLOR_ACTIVE = "green"

# Viewport boundaries (percentages)
VIEWPORT_MARGIN_MIN = 0.15
VIEWPORT_MARGIN_MAX = 0.85

# Click offset ranges (percentages)
CLICK_OFFSET_MIN = 0.20
CLICK_OFFSET_MAX = 0.80

# Curve generation settings
OFFSET_BOUNDARY_RANGE_LOW = (20, 45)
OFFSET_BOUNDARY_RANGE_MID = (45, 75)
OFFSET_BOUNDARY_RANGE_HIGH = (75, 100)

# Weights for random choices
OFFSET_BOUNDARY_WEIGHTS = [0.2, 0.65, 0.15]

# Knots count options and weights
KNOTS_COUNT_OPTIONS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
KNOTS_COUNT_WEIGHTS = [0.15, 0.36, 0.17, 0.12, 0.08, 0.04, 0.03, 0.02, 0.015, 0.005]

# Distortion settings (percentages)
DISTORTION_MEAN_MIN = 80
DISTORTION_MEAN_MAX = 110
DISTORTION_STDEV_MIN = 85
DISTORTION_STDEV_MAX = 110
DISTORTION_FREQ_MIN = 25
DISTORTION_FREQ_MAX = 70

# Target points settings
TARGET_POINTS_RANGE_LOW = (35, 45)
TARGET_POINTS_RANGE_MID = (45, 60)
TARGET_POINTS_RANGE_HIGH = (60, 80)
TARGET_POINTS_WEIGHTS = [0.53, 0.32, 0.15]

# Steady mode settings
STEADY_OFFSET_BOUNDARY = 10
STEADY_DISTORTION_MEAN = 1.2
STEADY_DISTORTION_STDEV = 1.2
STEADY_DISTORTION_FREQ = 1

# Drag and drop settings
HOLD_TIME_THRESHOLD = 0.5

# GUI update intervals (milliseconds)
COORDINATES_UPDATE_INTERVAL = 10

# Scroll timing
SCROLL_WAIT_MIN = 0.8
SCROLL_WAIT_MAX = 1.4

# Default filename generation
DEFAULT_FILENAME_RANDOM_MIN = 1
DEFAULT_FILENAME_RANDOM_MAX = 10000
