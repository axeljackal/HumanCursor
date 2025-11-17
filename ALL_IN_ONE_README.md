# HCS All-in-One GUI

The All-in-One HumanCursor Scripter provides a complete interface for recording, playing, and managing mouse automation scripts.

## Launch

```bash
python -m humancursor.HCScripter.launch_all_in_one
```

## Features

### 📹 Recording Modes

#### **Auto Capture Mode** (NEW!)
- **Automatic recording**: Simply click "Record" and all your mouse movements and clicks are captured automatically
- **Smart sampling**: Records movements every 10+ pixels to reduce noise
- **Natural playback**: Captures real mouse behavior for realistic automation

#### **Manual Mode** (Hotkey-based)
- **Precise control**: Mark specific positions using hotkeys
- **Keyboard shortcuts**:
  - **Z**: Record move to current position
  - **Left CTRL (tap)**: Record click at current position  
  - **Left CTRL (hold & release)**: Record drag from start to release position

### ▶️ Playback

- **Speed Control**: 0.1x to 5.0x playback speed
  - <1.0x: Slower than recorded
  - 1.0x: Normal speed
  - >1.0x: Faster than recorded
  - ≥3.0x: Ultra-fast instant movements
  
- **Repetitions**: 1 to 1000 repetitions
  - Or use "Infinite Loop" checkbox for continuous playback

- **Playback Controls**:
  - **Play**: Start executing recorded actions
  - **Stop**: Halt playback immediately
  - **CTRL+ALT** (Global Hotkey): Emergency stop from anywhere

### 💾 File Management

- **Save Recording**:
  - `.hcs` format: Binary format for loading back into the GUI
  - `.py` format: Executable Python script

- **Load Recording**: Load previously saved `.hcs` recordings

## Workflow Examples

### Auto Recording (Recommended)

1. Select **"Auto Capture"** mode
2. Click **"🔴 Record"** (indicator turns green)
3. Move your mouse and click naturally - everything is captured!
4. Click **"⏸️ Stop"** when done (indicator turns red)
5. Adjust **Speed** and **Repetitions** as needed
6. Click **"▶️ Play"** to execute
7. Press **CTRL+ALT** anytime to emergency stop

### Manual Recording (Precision)

1. Select **"Manual (Hotkeys)"** mode
2. Click **"🔴 Record"** (indicator turns green)
3. Press **Z** to mark movement points
4. Press **Left CTRL** briefly to record clicks
5. Hold **Left CTRL** and release at destination for drag-and-drop
6. Click **"⏸️ Stop"** when done
7. Play back as desired

## Safety Features

- **Always-on-top window**: GUI stays visible during recording
- **Global stop hotkey**: CTRL+ALT stops playback from anywhere
- **Thread-safe playback**: Runs in background without freezing GUI
- **Clear confirmation**: Asks before clearing recordings
- **Smart movement sampling**: Auto mode filters out jitter

## Notes

- **Auto mode** captures real mouse behavior - great for complex workflows
- **Manual mode** creates minimal, precise scripts - great for simple tasks
- Playback uses smooth, steady movements for reliability
- Speed affects both movement duration and inter-action delays
- Saved `.py` scripts are standalone and executable

