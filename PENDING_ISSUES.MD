# Deep Analysis of HumanCursor

## Architecture Overview

HumanCursor simulates human-like mouse movements through three main components:

1. **SystemCursor** - Physical cursor control via pyautogui
2. **WebCursor** - Web browser cursor via Selenium
3. **HumanizeMouseTrajectory** - Core algorithm generating realistic curves

---

## Core Algorithm: Bézier Curves with Noise

### How It Works

#### 1. Bézier Curve Generation

- Uses **Bernstein polynomials** to create smooth curves between points
- Formula: `B(t) = Σ(binomial(n,i) * t^i * (1-t)^(n-i) * P_i)` where `t ∈ [0,1]`
- Generates "control points" (knots) that the curve passes through

#### 2. Randomized Control Points

- Randomly places 1-10 knots between start/end points (weighted toward 2-3 knots)
- Knots confined within boundaries that extend beyond the direct path
- Creates natural "overshoot" and "correction" patterns

#### 3. Distortion Layer

- Adds Gaussian noise to Y-coordinates of curve points
- Mean: ~0.8-1.1, StdDev: ~0.85-1.1
- Applied probabilistically (25-70% frequency)
- Simulates hand tremors and micro-adjustments

#### 4. Easing Functions

- Uses `pytweening` library for velocity profiles
- Randomly selects from 13 easing functions (easeOutQuad, easeInOutSine, etc.)
- Mimics acceleration/deceleration patterns of human movement

---

## Strengths of the Implementation

### ✅ Excellent Practices

1. **Bézier curves are appropriate** - Used in research for human movement modeling (Fitts' Law extensions)
2. **Stochastic noise** - Gaussian distortion mimics neuromuscular tremor
3. **Variable parameters** - Randomizing knots, boundaries, and easing prevents pattern detection
4. **Edge case handling** - Reduces complexity near viewport boundaries
5. **Fractional accumulation** (web_adjuster.py) - Preserves sub-pixel precision during movement
6. **Fallback mechanisms** - Graceful degradation when curves fail

### ✅ Research-Backed Elements

- **Fitts' Law consideration** - Longer distances → more target points (system_cursor.py:125)
- **Variable velocity** - Easing functions match human acceleration patterns
- **Click timing variation** - 170-280ms pauses are realistic

---

## Critical Issues & Improvements

---

### ❌ Issue 1: Overly Simplistic Distortion

**Location:** `humancursor/utilities/human_curve_generator.py` - `distort_points()` method

**Current Implementation:**

```python
delta = np.random.normal(distortion_mean, distortion_st_dev) if random.random() < distortion_frequency else 0
distorted += ((x, y + delta),)
```

**Problems:**

- Only distorts Y-axis (X-axis ignored completely)
- Distortion is independent of velocity (humans shake more during acceleration/deceleration)
- No temporal correlation (each point is independent)

**Proposed Solution:**

```python
# Apply distortion to BOTH axes
# Scale by velocity (more distortion when moving fast)
velocity = math.sqrt((x - prev_x)**2 + (y - prev_y)**2)
velocity_factor = min(velocity / 10, 2.0)  # Cap at 2x

# Use Perlin noise for temporal correlation instead of pure randomness
delta_x = perlin_noise(i * 0.1) * distortion_st_dev * velocity_factor
delta_y = perlin_noise(i * 0.1 + 100) * distortion_st_dev * velocity_factor

if random.random() < distortion_frequency:
    distorted += ((x + delta_x, y + delta_y),)
```

**Priority:** 🔴 **HIGH** - Major flaw affecting realism

---

### ❌ Issue 2: Fixed Boundary Logic

**Location:** `humancursor/utilities/human_curve_generator.py` - `generate_internal_knots()` method

**Current Implementation:**

```python
left_boundary = min(from_point[0], to_point[0]) - offset_boundary_x
right_boundary = max(from_point[0], to_point[0]) + offset_boundary_x
```

**Problems:**

- Creates rectangular boundaries (unnatural)
- Doesn't account for movement direction
- Can place knots outside valid screen space

**Proposed Solution:**

```python
# Use elliptical boundaries oriented along movement direction
angle = math.atan2(to_point[1] - from_point[1], to_point[0] - from_point[0])
# Create rotated ellipse for more natural knot placement
```

**Priority:** 🟡 **MEDIUM**

---

### ❌ Issue 3: Target Points Calculation

**Location:** `humancursor/utilities/calculate_and_randomize.py` - `generate_random_curve_parameters()`

**Current Implementation:**

```python
# For system cursor
target_points = max(int(distance), 2)

# For web cursor
target_points = random.choice([35-45, 45-60, 60-80])
```

**Problems:**

- System cursor: Can create thousands of points for large distances (inefficient)
- Web cursor: Disconnected from actual movement distance
- No consideration of movement speed

**Proposed Solution:**

```python
# Use Fitts' Law inspired formula
distance = math.sqrt((x2-x1)**2 + (y2-y1)**2)
# 0.5 points per pixel for short moves, logarithmic scaling for long
target_points = max(int(distance * 0.5), 50) if distance < 200 else int(50 + 30 * math.log10(distance/200))
target_points = min(target_points, 300)  # Cap to prevent excess
```

**Priority:** 🔴 **HIGH** - Performance and accuracy issue

---

### ❌ Issue 4: Knot Count Distribution

**Location:** `humancursor/constants.py` and `calculate_and_randomize.py`

**Current Implementation:**

```python
KNOTS_COUNT_OPTIONS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
KNOTS_COUNT_WEIGHTS = [0.15, 0.36, 0.17, 0.12, 0.08, 0.04, 0.03, 0.02, 0.015, 0.005]
```

**Problems:**

- Same distribution regardless of distance
- High knots (7-10) are rare but pointless for short movements
- Low knots (1-2) make long movements too linear

**Proposed Solution:**

```python
# Scale knots with distance
if distance < 100:
    knots_count = random.choices([1, 2], [0.7, 0.3])[0]
elif distance < 500:
    knots_count = random.choices([2, 3, 4], [0.5, 0.35, 0.15])[0]
else:
    knots_count = random.choices([3, 4, 5, 6], [0.4, 0.35, 0.15, 0.1])[0]
```

**Priority:** 🟡 **MEDIUM**

---

### ❌ Issue 5: Boundary Edge Simplification

**Location:** `humancursor/utilities/calculate_and_randomize.py` - End of `generate_random_curve_parameters()`

**Current Implementation:**

```python
if (min_width > pre_origin[0] or max_width < pre_origin[0] or ...):
    offset_boundary_x = 1
    offset_boundary_y = 1
    knots_count = 1
```

**Problems:**

- Too aggressive - reduces ALL complexity when near ANY edge
- Makes edge movements detectable (always linear)
- 15% and 85% thresholds are arbitrary

**Proposed Solution:**

```python
# Gradually reduce complexity based on proximity to edge
edge_proximity = calculate_edge_proximity(origin, viewport_size)
# Scale boundaries instead of binary reduction
offset_boundary_x *= (1 - edge_proximity * 0.7)
offset_boundary_y *= (1 - edge_proximity * 0.7)
knots_count = max(1, int(knots_count * (1 - edge_proximity * 0.5)))
```

**Priority:** 🟡 **MEDIUM** - Detection vulnerability

---

### ⚠️ Issue 6: Duration Calculation

**Location:** `humancursor/system_cursor.py` - `move_to()` method

**Current Implementation:**

```python
duration = random.uniform(DEFAULT_DURATION_MIN, DEFAULT_DURATION_MAX)  # 0.5-2.0s
pyautogui.PAUSE = duration / len(human_curve.points)
```

**Problems:**

- Same duration range (0.5-2s) for 10px and 1000px movements
- Violates Fitts' Law: `Time = a + b * log2(Distance/Width + 1)`
- Easily fingerprinted by consistent timing patterns

**Proposed Solution:**

```python
# Fitts' Law based timing
distance = math.sqrt((x2-x1)**2 + (y2-y1)**2)
target_width = 10  # Assume 10px target
base_time = 0.1 + 0.15 * math.log2(distance / target_width + 1)
# Add human variability (±20%)
duration = base_time * random.uniform(0.8, 1.2)
```

**Priority:** 🔴 **HIGH** - Fitts' Law violation

---

### ⚠️ Issue 7: Missing Overshoot Behavior

**Location:** New feature needed in `human_curve_generator.py`

**Problem:**

Humans often overshoot targets then correct back (especially for small/fast targets). The current implementation doesn't model this.

**Proposed Solution:**

Add overshoot probability based on movement characteristics:

```python
if distance > 200 and target_size < 50:
    if random.random() < 0.3:  # 30% chance of overshoot
        overshoot_distance = random.uniform(5, 15)
        # Add overshoot point beyond target, then correct back
```

**Priority:** 🟡 **MEDIUM** - Realism enhancement

---

### ⚠️ Issue 8: Click Position Randomization

**Location:** `humancursor/utilities/web_adjuster.py` - `_calculate_destination()` method

**Current Implementation:**

```python
x_random_offset = random.choice(range(20, 80)) / 100  # 0.20-0.80
y_random_offset = random.choice(range(20, 80)) / 100
```

**Problems:**

- Uniform distribution (unnatural - humans prefer center)
- Uses `random.choice(range())` which is inefficient
- Same randomization for all element sizes

**Proposed Solution:**

```python
# Use beta distribution (peaks in center, allows edges)
x_offset = np.random.beta(2, 2)  # Bell curve centered at 0.5
y_offset = np.random.beta(2, 2)
# Scale based on element size (smaller elements = less variance)
scale_factor = min(element_width / 100, 1.0)
```

**Priority:** 🟢 **LOW** - Minor optimization

---

## Missing Features for Advanced Detection Evasion

### 1. Pause Patterns

**Description:** Humans pause briefly before clicking, during complex movements, and when "thinking".

**Proposed Implementation:**

```python
if distance > 300:
    # Add 1-2 brief pauses during long movements
    pause_points = random.sample(range(len(points)), k=random.randint(1, 2))
```

**Priority:** 🟡 **MEDIUM**

---

### 2. Mouse Jitter on Idle

**Description:** When "hovering", add tiny random movements to simulate natural hand tremor.

**Proposed Implementation:**

```python
def simulate_idle_jitter(duration):
    for _ in range(int(duration * 10)):
        offset = random.uniform(-2, 2)
        move_by_offset(offset, offset)
        sleep(0.1)
```

**Priority:** 🟢 **LOW**

---

### 3. Contextual Speed Variation

**Description:** Movement speed should vary based on:

- Task urgency (faster when repeating actions)
- Target size (slower for small targets)
- Fatigue (slight slow-down over time)

**Priority:** 🟢 **LOW**

---

### 4. Acceleration Profiles

**Description:** Current easing is good, but could add:

- Different profiles for horizontal vs vertical movement
- Jerk minimization (3rd derivative) for smoother start/stop

**Priority:** 🟢 **LOW**

---

## Performance Concerns

### Issue: Bezier Calculation Inefficiency

**Location:** `humancursor/utilities/human_curve_generator.py` - `BezierCalculator` class

**Current Implementation:**

```python
def bernstein_polynomial_point(x, i, n):
    return binomial(n, i) * (x**i) * ((1 - x) ** (n - i))
```

**Problems:**

- Recalculates `binomial(n, i)` for every point
- Power operations are slow

**Proposed Fix:**

Precompute binomial coefficients, use De Casteljau's algorithm

**Priority:** 🟢 **LOW** - Optimization

---

## Summary & Recommendations

### Overall Assessment: 7.5/10

#### What's Good

✅ Solid mathematical foundation (Bézier curves)  
✅ Good randomization strategy  
✅ Proper handling of edge cases  
✅ Clean code structure

#### What Needs Improvement

❌ Distortion only on Y-axis (major flaw)  
❌ Duration ignores movement distance (Fitts' Law violation)  
❌ Missing temporal correlation in noise  
❌ Target points calculation needs work  
⚠️ No overshoot behavior  
⚠️ No pause/jitter patterns

---

## Implementation Priority

### 🔴 High Priority

1. **Fix Y-only distortion** → Apply to both axes with velocity-based scaling
2. **Implement Fitts' Law for duration** → Distance-based timing calculation
3. **Scale target points with distance** → Logarithmic formula to prevent inefficiency

### 🟡 Medium Priority

4. **Add overshoot behavior** → Target overshoot with correction
5. **Improve knot distribution logic** → Distance-based knot counts
6. **Use beta distribution for click positions** → Center-biased clicking
7. **Implement pause patterns** → Micro-pauses during long movements
8. **Fix boundary edge simplification** → Gradual complexity reduction

### 🟢 Low Priority

9. **Optimize Bézier calculations** → Precompute coefficients
10. **Add idle jitter** → Simulate natural hand tremor
11. **Implement fatigue simulation** → Progressive slowdown
12. **Contextual speed variation** → Task-based speed adjustment

---

## Conclusion

The script is **functional and better than linear movements**, but could be significantly improved with the changes above to better evade sophisticated bot detection systems. The mathematical foundation is sound, but implementation details need refinement for production-grade anti-detection capabilities.

**Estimated Development Time:**

- High Priority Items: 8-12 hours
- Medium Priority Items: 12-16 hours
- Low Priority Items: 8-10 hours

**Total:** ~28-38 hours of development work
