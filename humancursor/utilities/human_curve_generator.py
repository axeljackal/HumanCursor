import random
import math
import logging
import numpy as np
import pytweening

logger = logging.getLogger(__name__)


class HumanizeMouseTrajectory:
    def __init__(self, from_point, to_point, **kwargs):
        self.from_point = from_point
        self.to_point = to_point
        self.points = self.generate_curve(**kwargs)

    def generate_curve(self, **kwargs):
        """Generates the curve based on arguments below, default values below are automatically modified to cause randomness"""
        offset_boundary_x = kwargs.get("offset_boundary_x", 80)
        offset_boundary_y = kwargs.get("offset_boundary_y", 80)
        left_boundary = (
            kwargs.get("left_boundary", min(self.from_point[0], self.to_point[0]))
            - offset_boundary_x
        )
        right_boundary = (
            kwargs.get("right_boundary", max(self.from_point[0], self.to_point[0]))
            + offset_boundary_x
        )
        down_boundary = (
            kwargs.get("down_boundary", min(self.from_point[1], self.to_point[1]))
            - offset_boundary_y
        )
        up_boundary = (
            kwargs.get("up_boundary", max(self.from_point[1], self.to_point[1]))
            + offset_boundary_y
        )
        knots_count = kwargs.get("knots_count", 2)
        distortion_mean = kwargs.get("distortion_mean", 1)
        distortion_st_dev = kwargs.get("distortion_st_dev", 1)
        distortion_frequency = kwargs.get("distortion_frequency", 0.5)
        tween = kwargs.get("tweening", pytweening.easeOutQuad)
        target_points = kwargs.get("target_points", 100)
        target_size = kwargs.get("target_size", 20)  # Estimated target size in pixels

        internalKnots = self.generate_internal_knots(
            left_boundary, right_boundary, down_boundary, up_boundary, knots_count
        )
        points = self.generate_points(internalKnots)
        points = self.distort_points(
            points, distortion_mean, distortion_st_dev, distortion_frequency
        )
        points = self.tween_points(points, tween, target_points)
        
        # Add realistic overshoot behavior
        distance = math.sqrt(
            (self.to_point[0] - self.from_point[0])**2 + 
            (self.to_point[1] - self.from_point[1])**2
        )
        points = self.add_overshoot_correction(points, distance, target_size)
        
        # Add realistic pause patterns
        points = self.add_pause_patterns(points, distance)
        
        return points
    
    def add_overshoot_correction(self, points, distance, target_size=20):
        """Add realistic overshoot and correction pattern to curve points
        
        Args:
            points: List of curve points
            distance: Movement distance in pixels
            target_size: Estimated target size in pixels (default 20)
        
        Returns:
            Modified points list with potential overshoot
        """
        # Overshoot probability increases with:
        # - Longer distances (more momentum)
        # - Smaller targets (harder to hit precisely)
        distance_factor = min(distance / 1000, 1.0)  # Normalize to [0, 1]
        target_factor = max(0, (50 - target_size) / 50)  # Smaller target = higher factor
        
        overshoot_prob = min(0.4, (distance_factor + target_factor) / 2)
        
        if random.random() < overshoot_prob:
            # Overshoot by 3-8% of total distance
            overshoot_factor = random.uniform(1.03, 1.08)
            
            # Find injection point (80-90% through the curve)
            injection_idx = int(len(points) * random.uniform(0.80, 0.90))
            
            # Calculate overshoot direction vector
            direction_x = self.to_point[0] - self.from_point[0]
            direction_y = self.to_point[1] - self.from_point[1]
            
            # Create overshoot point beyond target
            overshoot_point = (
                self.to_point[0] + direction_x * (overshoot_factor - 1.0),
                self.to_point[1] + direction_y * (overshoot_factor - 1.0)
            )
            
            # Insert overshoot point, then correction will happen naturally
            # as curve continues to actual target
            points = list(points)  # Convert to list if tuple
            points.insert(injection_idx, overshoot_point)
        
        return points
    
    def add_pause_patterns(self, points, distance):
        """Add realistic pause patterns during movement
        
        Humans naturally pause briefly:
        - During long movements (thinking/adjusting)
        - At decision points mid-trajectory
        
        Args:
            points: List of curve points
            distance: Movement distance in pixels
        
        Returns:
            List of points with pause markers (duplicated points indicate pauses)
        """
        if distance < 300 or len(points) < 10:
            return points  # No pauses for short movements
        
        points = list(points)
        
        # Longer movements get more pauses
        if distance < 500:
            num_pauses = random.choice([0, 1])  # 0-1 pauses for medium movements
        else:
            num_pauses = random.choice([1, 2])  # 1-2 pauses for long movements
        
        if num_pauses == 0:
            return points
        
        # Select random pause points (avoid first 10% and last 20%)
        safe_start = int(len(points) * 0.10)
        safe_end = int(len(points) * 0.80)
        
        if safe_end <= safe_start:
            return points
        
        # Get random pause indices
        pause_indices = sorted(random.sample(range(safe_start, safe_end), k=num_pauses))
        
        # Duplicate points at pause locations to simulate brief hesitation
        # Each pause is 2-4 duplicate points (represents ~20-40ms at typical speeds)
        offset = 0
        for idx in pause_indices:
            pause_length = random.randint(2, 4)
            pause_point = points[idx + offset]
            # Insert duplicates to create a brief "stop"
            for _ in range(pause_length):
                points.insert(idx + offset, pause_point)
            offset += pause_length
        
        return points

    def generate_internal_knots(
        self, l_boundary, r_boundary, d_boundary, u_boundary, knots_count
    ):
        """Generates the internal knots of the curve randomly with boundary variation
        
        Args:
            l_boundary: Left boundary for knot placement
            r_boundary: Right boundary for knot placement
            d_boundary: Down boundary for knot placement
            u_boundary: Upper boundary for knot placement
            knots_count: Number of internal knots to generate
            
        Returns:
            List of (x, y) knot coordinates
        """
        if not (
            self.check_if_numeric(l_boundary)
            and self.check_if_numeric(r_boundary)
            and self.check_if_numeric(d_boundary)
            and self.check_if_numeric(u_boundary)
        ):
            raise ValueError("Boundaries must be numeric values")
        if not isinstance(knots_count, int) or knots_count < 0:
            knots_count = 0
        if l_boundary > r_boundary:
            raise ValueError(
                "left_boundary must be less than or equal to right_boundary"
            )
        if d_boundary > u_boundary:
            raise ValueError(
                "down_boundary must be less than or equal to upper_boundary"
            )
        
        # Add slight variation to boundaries (±5%) to prevent fingerprinting
        boundary_variation = 0.05
        l_boundary = int(l_boundary * (1 + random.uniform(-boundary_variation, boundary_variation)))
        r_boundary = int(r_boundary * (1 + random.uniform(-boundary_variation, boundary_variation)))
        d_boundary = int(d_boundary * (1 + random.uniform(-boundary_variation, boundary_variation)))
        u_boundary = int(u_boundary * (1 + random.uniform(-boundary_variation, boundary_variation)))
        
        # Handle equal boundaries (no range to choose from)
        if l_boundary == r_boundary:
            knotsX = np.full(knots_count, l_boundary)
        else:
            try:
                knotsX = np.random.choice(range(l_boundary, r_boundary), size=knots_count)
            except TypeError:
                # Fallback for float boundaries - convert to int
                logger.debug(f"Converting float boundaries to int: l={l_boundary}, r={r_boundary}")
                knotsX = np.random.choice(
                    range(int(l_boundary), int(r_boundary)), size=knots_count
                )
        
        if d_boundary == u_boundary:
            knotsY = np.full(knots_count, d_boundary)
        else:
            try:
                knotsY = np.random.choice(range(d_boundary, u_boundary), size=knots_count)
            except TypeError:
                # Fallback for float boundaries - convert to int
                logger.debug(f"Converting float boundaries to int: d={d_boundary}, u={u_boundary}")
                knotsY = np.random.choice(
                    range(int(d_boundary), int(u_boundary)), size=knots_count
                )
        
        knots = list(zip(knotsX, knotsY))
        return knots

    def generate_points(self, knots):
        """Generates the points from BezierCalculator"""
        if not self.check_if_list_of_points(knots):
            raise ValueError("knots must be valid list of points")

        midPtsCnt = max(
            abs(self.from_point[0] - self.to_point[0]),
            abs(self.from_point[1] - self.to_point[1]),
            2,
        )
        knots = [self.from_point] + knots + [self.to_point]
        return BezierCalculator.calculate_points_in_curve(int(midPtsCnt), knots)

    def distort_points(
        self, points, distortion_mean, distortion_st_dev, distortion_frequency
    ):
        """Distorts points with velocity-based scaling on both X and Y axes
        
        Args:
            points: List of curve points to distort
            distortion_mean: Mean for Gaussian noise (legacy parameter, now uses 0)
            distortion_st_dev: Standard deviation for Gaussian noise
            distortion_frequency: Probability of applying distortion to each point
            
        Returns:
            List of distorted points with velocity-based noise on both axes
        """
        if not (
            self.check_if_numeric(distortion_mean)
            and self.check_if_numeric(distortion_st_dev)
            and self.check_if_numeric(distortion_frequency)
        ):
            raise ValueError("Distortions must be numeric")
        if not self.check_if_list_of_points(points):
            raise ValueError("points must be valid list of points")
        if not (0 <= distortion_frequency <= 1):
            raise ValueError("distortion_frequency must be in range [0,1]")

        distorted = [points[0]]  # Keep first point exact
        
        for i in range(1, len(points) - 1):
            x, y = points[i]
            prev_x, prev_y = points[i - 1]
            
            # Calculate velocity-based scaling
            # Faster movements get more distortion (simulates reduced precision at speed)
            velocity = math.sqrt((x - prev_x)**2 + (y - prev_y)**2)
            velocity_factor = min(1.0 + velocity / 50.0, 2.5)  # Scale 1x-2.5x based on speed
            
            if random.random() < distortion_frequency:
                # Apply Gaussian noise to BOTH axes with velocity scaling
                # Mean is now 0 (centered distortion) instead of using distortion_mean
                delta_x = np.random.normal(0, distortion_st_dev * velocity_factor)
                delta_y = np.random.normal(0, distortion_st_dev * velocity_factor)
                distorted.append((x + delta_x, y + delta_y))
            else:
                distorted.append((x, y))
        
        distorted.append(points[-1])  # Keep last point exact
        return distorted

    def tween_points(self, points, tween, target_points):
        """Modifies points by tween with directional acceleration profiles
        
        Args:
            points: List of curve points
            tween: Easing function
            target_points: Number of target points to generate
            
        Returns:
            List of tweened points with directional acceleration adjustments
        """
        if not self.check_if_list_of_points(points):
            raise ValueError("List of points not valid")
        if not isinstance(target_points, int) or target_points < 2:
            raise ValueError("target_points must be an integer greater or equal to 2")

        # Calculate movement direction
        dx = self.to_point[0] - self.from_point[0]
        dy = self.to_point[1] - self.from_point[1]
        
        # Determine if movement is more horizontal or vertical
        is_horizontal = abs(dx) > abs(dy)
        
        # Apply directional easing
        # Horizontal movements: slightly different timing (humans are faster horizontally)
        # Vertical movements: slightly more careful (gravity/ergonomics)
        res = []
        for i in range(target_points):
            base_progress = float(i) / (target_points - 1)
            
            if is_horizontal:
                # Horizontal: slightly faster acceleration, quicker deceleration
                adjusted_progress = tween(base_progress ** 0.95)
            else:
                # Vertical: slightly slower, more controlled
                adjusted_progress = tween(base_progress ** 1.05)
            
            # Jerk minimization: smooth out start and end with cubic easing
            if i < 3:  # First 3 points: smooth start (reduce jerk)
                smooth_factor = (i / 3) ** 3  # Cubic smoothing
                adjusted_progress = adjusted_progress * smooth_factor
            elif i > target_points - 4:  # Last 3 points: smooth end
                remaining = (target_points - 1 - i) / 3
                smooth_factor = remaining ** 3
                adjusted_progress = 1.0 - smooth_factor * (1.0 - adjusted_progress)
            
            index = int(adjusted_progress * (len(points) - 1))
            res += (points[index],)
        
        return res

    @staticmethod
    def check_if_numeric(val):
        """Checks if value is proper numeric value"""
        return isinstance(val, (float, int)) or (
            hasattr(np, 'integer') and isinstance(val, np.integer)
        ) or (
            hasattr(np, 'floating') and isinstance(val, np.floating)
        )

    def check_if_list_of_points(self, list_of_points):
        """Checks if list of points is valid"""
        if not isinstance(list_of_points, list):
            return False
        try:
            point = lambda p: (
                (len(p) == 2)
                and self.check_if_numeric(p[0])
                and self.check_if_numeric(p[1])
            )
            return all(map(point, list_of_points))
        except (KeyError, TypeError):
            return False




class BezierCalculator:
    """Optimized Bézier curve calculator with precomputed binomial coefficients"""
    
    # Cache for binomial coefficients to avoid recalculation
    _binomial_cache = {}
    
    @staticmethod
    def binomial(n, k):
        """Returns the binomial coefficient "n choose k" with caching"""
        if k > n:
            return 0
        if k == 0 or k == n:
            return 1
        
        # Check cache
        cache_key = (n, k)
        if cache_key in BezierCalculator._binomial_cache:
            return BezierCalculator._binomial_cache[cache_key]
        
        # Calculate using Pascal's triangle (more efficient than factorial for large n)
        # Use symmetry: C(n,k) = C(n, n-k)
        k = min(k, n - k)
        
        result = 1
        for i in range(k):
            result = result * (n - i) // (i + 1)
        
        # Cache result
        BezierCalculator._binomial_cache[cache_key] = result
        return result

    @staticmethod
    def bernstein_polynomial_point(x, i, n, binomial_coeff=None):
        """Calculate the i-th component of a bernstein polynomial of degree n
        
        Args:
            x: Parameter value [0, 1]
            i: Index of the Bernstein basis polynomial
            n: Degree of the polynomial
            binomial_coeff: Precomputed binomial coefficient (optional)
        
        Returns:
            Value of the Bernstein polynomial
        """
        if binomial_coeff is None:
            binomial_coeff = BezierCalculator.binomial(n, i)
        
        # Optimize power calculations using direct multiplication for small exponents
        if i == 0:
            x_pow = 1
        elif i == 1:
            x_pow = x
        else:
            x_pow = x ** i
        
        if n - i == 0:
            one_minus_x_pow = 1
        elif n - i == 1:
            one_minus_x_pow = 1 - x
        else:
            one_minus_x_pow = (1 - x) ** (n - i)
        
        return binomial_coeff * x_pow * one_minus_x_pow

    @staticmethod
    def bernstein_polynomial(points):
        """
        Given list of control points, returns a function, which given a point [0,1] returns
        a point in the Bézier curve described by these points
        
        Optimized version with precomputed binomial coefficients
        """
        n = len(points) - 1
        
        # Precompute all binomial coefficients for this curve
        binomial_coeffs = [BezierCalculator.binomial(n, i) for i in range(n + 1)]
        
        def bernstein(t):
            x = y = 0
            for i, point in enumerate(points):
                bern = BezierCalculator.bernstein_polynomial_point(t, i, n, binomial_coeffs[i])
                x += point[0] * bern
                y += point[1] * bern
            return x, y

        return bernstein

    @staticmethod
    def calculate_points_in_curve(n, points):
        """
        Given list of control points, returns n points in the Bézier curve,
        described by these points
        
        Optimized version using vectorized operations where possible
        """
        if n < 2:
            return points[:n]
        
        curvePoints = []
        bernstein_polynomial = BezierCalculator.bernstein_polynomial(points)
        
        # Pre-calculate t values
        for i in range(n):
            t = i / (n - 1) if n > 1 else 0
            curvePoints += (bernstein_polynomial(t),)
        
        return curvePoints

