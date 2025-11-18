import os
import random
import tkinter as tk
from time import time, sleep
from tkinter import ttk, filedialog, messagebox
from threading import Thread
import pyautogui
from pynput import keyboard, mouse

from humancursor.constants import (
    WINDOW_BACKGROUND_COLOR,
    INDICATOR_BACKGROUND_COLOR,
    INDICATOR_WIDTH,
    INDICATOR_HEIGHT,
    INDICATOR_RECT_X1,
    INDICATOR_RECT_Y1,
    INDICATOR_RECT_X2,
    INDICATOR_RECT_Y2,
    INDICATOR_COLOR_INACTIVE,
    INDICATOR_COLOR_ACTIVE,
    HOLD_TIME_THRESHOLD,
    COORDINATES_UPDATE_INTERVAL,
)
from humancursor import SystemCursor


class AllInOneHCS:
    """All-in-one GUI for HumanCursor Scripter with recording and playback capabilities."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("HCS - All-in-One")
        self.coordinates = []
        
        self.bg = WINDOW_BACKGROUND_COLOR
        self.root.geometry("400x550")
        self.root.config(bg=self.bg)
        self.root.wm_attributes('-topmost', True)
        self.root.resizable(False, False)
        
        self.style = ttk.Style()
        self.style.configure('TLabel', font=('Roboto', 10))
        self.style.configure('Title.TLabel', font=('Roboto', 12, 'bold'))
        
        # === RECORDING SECTION ===
        recording_frame = tk.Frame(self.root, bg=self.bg)
        recording_frame.pack(pady=10, padx=10, fill=tk.X)
        
        ttk.Label(recording_frame, text="📹 RECORDING", style='Title.TLabel', background=self.bg).pack()
        
        # Recording mode selection
        mode_frame = tk.Frame(recording_frame, bg=self.bg)
        mode_frame.pack(pady=5)
        
        ttk.Label(mode_frame, text="Mode:", background=self.bg).pack(side=tk.LEFT, padx=5)
        self.recording_mode = tk.StringVar(value="auto")
        ttk.Radiobutton(mode_frame, text="Auto Capture", variable=self.recording_mode, 
                       value="auto").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="Manual (Hotkeys)", variable=self.recording_mode, 
                       value="manual").pack(side=tk.LEFT, padx=5)
        
        self.coordinates_label = ttk.Label(recording_frame, text="Position: (0, 0)", background=self.bg)
        self.coordinates_label.pack(pady=5)
        
        self.actions_label = ttk.Label(recording_frame, text="Actions: 0", background=self.bg)
        self.actions_label.pack(pady=2)
        
        # Recording indicator
        self.indicator = tk.Canvas(recording_frame, width=INDICATOR_WIDTH, height=INDICATOR_HEIGHT, 
                                   background=INDICATOR_BACKGROUND_COLOR)
        self.indicator.pack(pady=5)
        self.indicator_color = INDICATOR_COLOR_INACTIVE
        self.indicator.create_rectangle(
            INDICATOR_RECT_X1, INDICATOR_RECT_Y1, INDICATOR_RECT_X2, INDICATOR_RECT_Y2, 
            fill=self.indicator_color
        )
        
        # Recording buttons
        rec_buttons = tk.Frame(recording_frame, bg=self.bg)
        rec_buttons.pack(pady=5)
        
        self.record_button = ttk.Button(rec_buttons, text="🔴 Record", command=self.toggle_recording)
        self.record_button.pack(side=tk.LEFT, padx=3)
        
        self.clear_button = ttk.Button(rec_buttons, text="🗑️ Clear", command=self.clear_recording)
        self.clear_button.pack(side=tk.LEFT, padx=3)
        
        # Separator
        ttk.Separator(self.root, orient='horizontal').pack(fill=tk.X, pady=10, padx=10)
        
        # === PLAYBACK SECTION ===
        playback_frame = tk.Frame(self.root, bg=self.bg)
        playback_frame.pack(pady=10, padx=10, fill=tk.X)
        
        ttk.Label(playback_frame, text="▶️ PLAYBACK", style='Title.TLabel', background=self.bg).pack()
        
        # Speed control
        speed_frame = tk.Frame(playback_frame, bg=self.bg)
        speed_frame.pack(pady=5, fill=tk.X)
        
        ttk.Label(speed_frame, text="Speed:", background=self.bg).pack(side=tk.LEFT, padx=5)
        self.speed_var = tk.DoubleVar(value=1.0)
        speed_scale = ttk.Scale(speed_frame, from_=0.1, to=5.0, orient=tk.HORIZONTAL, 
                               variable=self.speed_var, length=150)
        speed_scale.pack(side=tk.LEFT, padx=5)
        self.speed_label = ttk.Label(speed_frame, text="1.0x", background=self.bg, width=6)
        self.speed_label.pack(side=tk.LEFT, padx=5)
        
        # Update speed label when scale changes
        speed_scale.config(command=lambda v: self.speed_label.config(text=f"{float(v):.1f}x"))
        
        # Repetition control
        rep_frame = tk.Frame(playback_frame, bg=self.bg)
        rep_frame.pack(pady=5, fill=tk.X)
        
        ttk.Label(rep_frame, text="Repetitions:", background=self.bg).pack(side=tk.LEFT, padx=5)
        self.repetition_var = tk.IntVar(value=1)
        repetition_spin = ttk.Spinbox(rep_frame, from_=1, to=1000, textvariable=self.repetition_var, 
                                     width=10)
        repetition_spin.pack(side=tk.LEFT, padx=5)
        
        # Infinite loop checkbox
        self.infinite_var = tk.BooleanVar(value=False)
        infinite_check = ttk.Checkbutton(rep_frame, text="Infinite Loop", variable=self.infinite_var,
                                        command=self.toggle_infinite)
        infinite_check.pack(side=tk.LEFT, padx=10)
        
        # Playback status
        self.playback_status = ttk.Label(playback_frame, text="Status: Ready", background=self.bg, 
                                        font=('Roboto', 9))
        self.playback_status.pack(pady=5)
        
        # Playback buttons
        play_buttons = tk.Frame(playback_frame, bg=self.bg)
        play_buttons.pack(pady=5)
        
        self.play_button = ttk.Button(play_buttons, text="▶️ Play", command=self.start_playback, 
                                     state=tk.DISABLED)
        self.play_button.pack(side=tk.LEFT, padx=3)
        
        self.stop_button = ttk.Button(play_buttons, text="⏹️ Stop", command=self.stop_playback, 
                                     state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=3)
        
        # Separator
        ttk.Separator(self.root, orient='horizontal').pack(fill=tk.X, pady=10, padx=10)
        
        # === SAVE/LOAD SECTION ===
        file_frame = tk.Frame(self.root, bg=self.bg)
        file_frame.pack(pady=10, padx=10, fill=tk.X)
        
        ttk.Label(file_frame, text="💾 FILE", style='Title.TLabel', background=self.bg).pack()
        
        # Save/Load buttons
        file_buttons = tk.Frame(file_frame, bg=self.bg)
        file_buttons.pack(pady=5)
        
        ttk.Button(file_buttons, text="💾 Save Recording", command=self.save_recording).pack(side=tk.LEFT, padx=3)
        ttk.Button(file_buttons, text="📂 Load Recording", command=self.load_recording).pack(side=tk.LEFT, padx=3)
        
        # Info label
        info_frame = tk.Frame(self.root, bg='#2a7ab8')
        info_frame.pack(pady=10, padx=10, fill=tk.X)
        
        info_text = "Auto Mode: Press X to start/stop recording\nManual Mode: Z=Move, CTRL(tap)=Click, CTRL(hold)=Drag\nCTRL+ALT = Stop Playback"
        ttk.Label(info_frame, text=info_text, background='#2a7ab8', font=('Roboto', 8), 
                 justify=tk.LEFT).pack(pady=5, padx=5)
        
        # State variables
        self.ctrl_pressed = False
        self.press_time = 0.0
        self.index = -1
        self.hold_time_threshold = HOLD_TIME_THRESHOLD
        
        # Recording state
        self.listener = None
        self.mouse_listener = None
        self.recording_active = False
        self.auto_recording_armed = False
        self.last_position = None
        self.recording_events = []
        self.recording_start_time = None
        
        # Setup X key listener for auto-capture
        self.x_key_listener = keyboard.Listener(on_press=self.on_x_key_press)
        self.x_key_listener.start()
        
        # Playback state
        self.playback_thread = None
        self.playback_running = False
        self.cursor = None
        
        # Global hotkey listener for stopping playback
        self.stop_listener = keyboard.GlobalHotKeys({
            '<ctrl>+<alt>': self.stop_playback
        })
        self.stop_listener.start()
        
        # Start coordinate updates
        self.update_coordinates()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.root.mainloop()
    
    def toggle_infinite(self):
        """Toggle infinite loop mode."""
        if self.infinite_var.get():
            self.repetition_var.set(999999)
        else:
            self.repetition_var.set(1)
    
    def update_coordinates(self):
        """Updates cursor coordinates display."""
        x, y = pyautogui.position()
        self.coordinates_label.config(text=f"Position: ({x}, {y})")
        self.actions_label.config(text=f"Actions: {len(self.coordinates)}")
        self.root.after(COORDINATES_UPDATE_INTERVAL, self.update_coordinates)
    
    def draw_indicator(self):
        """Draws the recording indicator."""
        self.indicator.delete("all")
        self.indicator.create_rectangle(
            INDICATOR_RECT_X1, INDICATOR_RECT_Y1, INDICATOR_RECT_X2, INDICATOR_RECT_Y2,
            fill=self.indicator_color
        )
    
    def toggle_recording(self):
        """Toggles recording on/off based on selected mode."""
        mode = self.recording_mode.get()
        
        if mode == "auto":
            # Auto mode uses X key, just arm/disarm
            if self.auto_recording_armed:
                self.auto_recording_armed = False
                self.record_button.config(text="🔴 Record")
                messagebox.showinfo("Auto Capture", "Press X to start recording when ready.\nPress X again to stop.")
            else:
                self.auto_recording_armed = True
                self.record_button.config(text="⏸️ Armed (Press X)")
                messagebox.showinfo("Auto Capture Armed", "Press X key to start recording.\nPress X again to stop.")
        else:
            # Manual mode - direct toggle
            if self.indicator_color == INDICATOR_COLOR_INACTIVE:
                self.recording_active = True
                self.start_manual_recording()
                self.indicator_color = INDICATOR_COLOR_ACTIVE
                self.record_button.config(text="⏸️ Stop")
            else:
                self.recording_active = False
                self.stop_all_listeners()
                self.indicator_color = INDICATOR_COLOR_INACTIVE
                self.record_button.config(text="🔴 Record")
                
                if len(self.coordinates) > 0:
                    self.play_button.config(state=tk.NORMAL)
            
            self.draw_indicator()
    
    def on_x_key_press(self, key):
        """Handle X key press for auto-capture toggle."""
        try:
            if hasattr(key, 'char') and key.char == 'x':
                if self.recording_mode.get() == "auto" and self.auto_recording_armed:
                    if not self.recording_active:
                        # Start recording
                        self.start_auto_recording()
                    else:
                        # Stop recording
                        self.recording_active = False
                        self.stop_all_listeners()
                        self.indicator_color = INDICATOR_COLOR_INACTIVE
                        self.draw_indicator()
                        
                        if len(self.coordinates) > 0:
                            self.play_button.config(state=tk.NORMAL)
        except AttributeError:
            pass
    
    def start_auto_recording(self):
        """Start auto recording mode - captures all mouse movements and clicks."""
        self.recording_start_time = time()
        self.last_position = pyautogui.position()
        self.recording_events = []
        self.recording_active = True
        self.indicator_color = INDICATOR_COLOR_ACTIVE
        self.draw_indicator()
        
        # Start mouse listener
        self.mouse_listener = mouse.Listener(
            on_move=self.on_mouse_move,
            on_click=self.on_mouse_click
        )
        self.mouse_listener.start()
    
    def start_manual_recording(self):
        """Start manual recording mode - use hotkeys to mark positions."""
        if self.listener is None or not self.listener.running:
            self.listener = keyboard.Listener(
                on_press=self.on_global_press,
                on_release=self.on_global_release
            )
            self.listener.start()
    
    def stop_all_listeners(self):
        """Stop all active listeners."""
        if self.listener is not None and self.listener.running:
            self.listener.stop()
            self.listener = None
        
        if self.mouse_listener is not None and self.mouse_listener.running:
            self.mouse_listener.stop()
            self.mouse_listener = None
            # Process recorded events into coordinates
            self.process_recorded_events()
    
    def on_mouse_move(self, x, y):
        """Handle mouse move events in auto recording mode."""
        if not self.recording_active or self.recording_start_time is None:
            return
        
        current_pos = (x, y)
        
        # Only record if mouse moved significantly (reduce noise)
        if self.last_position:
            distance = ((current_pos[0] - self.last_position[0])**2 + 
                       (current_pos[1] - self.last_position[1])**2)**0.5
            
            # Record movement if distance > 50 pixels (larger threshold for much smoother paths)
            if distance > 50:
                elapsed = time() - self.recording_start_time
                self.recording_events.append({
                    'type': 'move',
                    'position': current_pos,
                    'time': elapsed
                })
                self.last_position = current_pos
        else:
            self.last_position = current_pos
    
    def on_mouse_click(self, x, y, button, pressed):
        """Handle mouse click events in auto recording mode."""
        if not self.recording_active or self.recording_start_time is None:
            return
        
        if pressed:
            # Record click
            elapsed = time() - self.recording_start_time
            self.recording_events.append({
                'type': 'click',
                'position': (x, y),
                'button': button.name,
                'time': elapsed
            })
    
    def process_recorded_events(self):
        """Convert recorded events into coordinates format with trajectory smoothing."""
        if not self.recording_events:
            return
        
        # Separate moves and clicks
        moves = [e for e in self.recording_events if e['type'] == 'move']
        clicks = [e for e in self.recording_events if e['type'] == 'click']
        
        # Simplify movement trajectory (remove zigzags and back-tracking)
        simplified_moves = self.simplify_trajectory(moves)
        
        # Merge moves and clicks by timestamp
        all_events = simplified_moves + clicks
        all_events.sort(key=lambda e: e['time'])
        
        # Convert to coordinates
        for event in all_events:
            if event['type'] == 'move':
                self.coordinates.append(list(event['position']))
            elif event['type'] == 'click':
                self.coordinates.append(tuple(event['position']))
        
        self.index = len(self.coordinates) - 1
        self.recording_events = []
    
    def simplify_trajectory(self, moves):
        """Simplify movement trajectory using Douglas-Peucker-like algorithm."""
        if len(moves) <= 2:
            return moves
        
        # More aggressive simplification - keep only major direction changes
        simplified = [moves[0]]  # Always keep first point
        
        for i in range(1, len(moves) - 1):
            prev = simplified[-1]['position']
            curr = moves[i]['position']
            next_move = moves[i + 1]['position']
            
            # Calculate if current point is on the line between prev and next
            dist_to_line = self.point_to_line_distance(curr, prev, next_move)
            
            # Much higher threshold - only keep major turns
            if dist_to_line > 50:  # 50 pixel threshold for major direction changes only
                simplified.append(moves[i])
        
        simplified.append(moves[-1])  # Always keep last point
        
        # Further reduce by keeping only every Nth point if still too many
        if len(simplified) > 10:
            reduced = [simplified[0]]
            step = len(simplified) // 8  # Keep maximum 8 intermediate points
            for i in range(step, len(simplified) - 1, step):
                reduced.append(simplified[i])
            reduced.append(simplified[-1])
            return reduced
        
        return simplified
    
    def point_to_line_distance(self, point, line_start, line_end):
        """Calculate perpendicular distance from point to line."""
        px, py = point
        x1, y1 = line_start
        x2, y2 = line_end
        
        # Line length
        line_len = ((x2 - x1)**2 + (y2 - y1)**2)**0.5
        
        if line_len == 0:
            return ((px - x1)**2 + (py - y1)**2)**0.5
        
        # Calculate perpendicular distance
        t = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / (line_len ** 2)))
        proj_x = x1 + t * (x2 - x1)
        proj_y = y1 + t * (y2 - y1)
        
        return ((px - proj_x)**2 + (py - proj_y)**2)**0.5
    
    def calculate_move_duration(self, distance, speed):
        """Calculate smooth movement duration based on distance and speed.
        
        Args:
            distance: Distance in pixels
            speed: Speed multiplier
            
        Returns:
            Duration in seconds
        """
        if speed >= 4.0:
            return 0.05  # Very fast but not instant
        
        # Longer base durations for smoother movement
        # Short moves: ~0.4s, Medium moves: ~0.7s, Long moves: ~1.2s
        base_duration = 0.3 + (distance / 1000)  # Much slower, smoother scaling
        base_duration = min(base_duration, 1.5)  # Cap at 1.5s for very long moves
        
        # Apply speed multiplier
        final_duration = base_duration / speed
        
        return max(final_duration, 0.1)  # Minimum 0.1s for any movement
    
    def clear_recording(self):
        """Clears all recorded actions."""
        if messagebox.askyesno("Clear Recording", "Are you sure you want to clear all recorded actions?"):
            self.coordinates = []
            self.index = -1
            self.play_button.config(state=tk.DISABLED)
    
    def move(self):
        """Records a move action at current cursor position."""
        x, y = pyautogui.position()
        self.coordinates.append([x, y])
        self.index += 1
    
    def on_global_press(self, key):
        """Global keyboard press handler for recording."""
        if not self.recording_active:
            return
        
        try:
            # Handle 'Z' key for move action
            if hasattr(key, 'char') and key.char == 'z':
                self.move()
            # Handle left CTRL key for click/drag start
            elif key == keyboard.Key.ctrl_l and not self.ctrl_pressed:
                self.ctrl_pressed = True
                x, y = pyautogui.position()
                self.press_time = time()
                self.coordinates.append([(x, y)])
                self.index += 1
        except AttributeError:
            pass
    
    def on_global_release(self, key):
        """Global keyboard release handler for recording."""
        if not self.recording_active:
            return
        
        try:
            # Handle left CTRL key release
            if key == keyboard.Key.ctrl_l and self.ctrl_pressed:
                self.ctrl_pressed = False
                x, y = pyautogui.position()
                if time() - self.press_time > self.hold_time_threshold:
                    # Drag and drop
                    self.coordinates[self.index].append((x, y))
                else:
                    # Click
                    self.coordinates[self.index] = self.coordinates[self.index][0]
                self.press_time = 0.0
        except AttributeError:
            pass
    
    def start_playback(self):
        """Starts playback in a separate thread."""
        if len(self.coordinates) == 0:
            messagebox.showwarning("No Recording", "Please record some actions first!")
            return
        
        if self.playback_running:
            messagebox.showwarning("Already Playing", "Playback is already running!")
            return
        
        self.playback_running = True
        self.play_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.record_button.config(state=tk.DISABLED)
        
        # Start playback in separate thread
        self.playback_thread = Thread(target=self.playback_worker, daemon=True)
        self.playback_thread.start()
    
    def stop_playback(self):
        """Stops the playback."""
        self.playback_running = False
        self.playback_status.config(text="Status: Stopped")
        self.play_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.record_button.config(state=tk.NORMAL)
    
    def playback_worker(self):
        """Worker thread for executing playback."""
        try:
            self.cursor = SystemCursor()
            speed = self.speed_var.get()
            repetitions = self.repetition_var.get()
            
            for rep in range(repetitions):
                if not self.playback_running:
                    break
                
                # Update status
                self.playback_status.config(text=f"Status: Playing ({rep + 1}/{repetitions})")
                
                current_pos = pyautogui.position()
                
                for i, coordinate in enumerate(self.coordinates):
                    if not self.playback_running:
                        break
                    
                    try:
                        if isinstance(coordinate, tuple):
                            # Click action - move then click
                            distance = ((coordinate[0] - current_pos[0])**2 + 
                                      (coordinate[1] - current_pos[1])**2)**0.5
                            
                            if distance > 5:
                                # Always use steady mode for smooth, predictable movements
                                move_duration = self.calculate_move_duration(distance, speed)
                                self.cursor.move_to(coordinate, duration=move_duration, steady=True)
                            
                            sleep(0.1 / max(speed, 0.5))
                            pyautogui.click()
                            current_pos = coordinate
                            
                        elif isinstance(coordinate, list):
                            if len(coordinate) == 2 and isinstance(coordinate[0], int):
                                # Move action - always steady for smoothness
                                target = tuple(coordinate)
                                distance = ((target[0] - current_pos[0])**2 + 
                                          (target[1] - current_pos[1])**2)**0.5
                                
                                if distance > 5:
                                    move_duration = self.calculate_move_duration(distance, speed)
                                    self.cursor.move_to(target, duration=move_duration, steady=True)
                                    current_pos = target
                                    
                            elif len(coordinate) == 2 and isinstance(coordinate[0], tuple):
                                # Drag and drop action
                                start_pos = coordinate[0]
                                end_pos = coordinate[1]
                                
                                # Move to start if needed
                                distance = ((start_pos[0] - current_pos[0])**2 + 
                                          (start_pos[1] - current_pos[1])**2)**0.5
                                if distance > 5:
                                    move_duration = self.calculate_move_duration(distance, speed)
                                    self.cursor.move_to(start_pos, duration=move_duration, steady=True)
                                
                                sleep(0.1 / max(speed, 0.5))
                                pyautogui.mouseDown()
                                sleep(0.05)
                                
                                # Perform drag - steady mode
                                drag_distance = ((end_pos[0] - start_pos[0])**2 + 
                                               (end_pos[1] - start_pos[1])**2)**0.5
                                drag_duration = self.calculate_move_duration(drag_distance, speed)
                                self.cursor.move_to(end_pos, duration=drag_duration, steady=True)
                                
                                sleep(0.05)
                                pyautogui.mouseUp()
                                current_pos = end_pos
                        
                        # Longer delay between actions for smoothness
                        if speed < 2.0:
                            sleep(0.15 / max(speed, 0.5))
                    
                    except Exception as e:
                        print(f"Error during playback: {e}")
                        continue
            
            # Playback finished
            if self.playback_running:
                self.playback_status.config(text="Status: Completed")
                self.playback_running = False
                self.play_button.config(state=tk.NORMAL)
                self.stop_button.config(state=tk.DISABLED)
                self.record_button.config(state=tk.NORMAL)
        
        except Exception as e:
            print(f"Playback error: {e}")
            self.playback_status.config(text=f"Status: Error - {str(e)[:30]}")
            self.stop_playback()
    
    def save_recording(self):
        """Saves the recorded actions to a file."""
        if len(self.coordinates) == 0:
            messagebox.showwarning("No Recording", "No actions to save!")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".hcs",
            filetypes=[("HCS Recording", "*.hcs"), ("Python Script", "*.py"), ("All Files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            if file_path.endswith('.py'):
                # Save as Python script
                self._save_as_script(file_path)
            else:
                # Save as HCS data file
                import pickle
                with open(file_path, 'wb') as f:
                    pickle.dump(self.coordinates, f)
            
            messagebox.showinfo("Success", f"Recording saved to:\n{file_path}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save recording:\n{str(e)}")
    
    def _save_as_script(self, file_path):
        """Saves recording as an executable Python script."""
        imports = '# Importing SystemCursor from humancursor package\nfrom humancursor import SystemCursor\n\n'
        cursor = '# Initializing the SystemCursor object\ncursor = SystemCursor()\n\n'
        code = '# Script Recorded: \n\n'
        
        for coordinate in self.coordinates:
            if isinstance(coordinate, tuple):
                # Click action
                code += f'cursor.click_on({coordinate}, clicks=1, click_duration=0, steady=False)\n'
            elif isinstance(coordinate, list):
                if len(coordinate) == 2 and isinstance(coordinate[0], int):
                    # Move action
                    code += f'cursor.move_to(({coordinate[0]}, {coordinate[1]}), duration=None, steady=False)\n'
                elif len(coordinate) == 2 and isinstance(coordinate[0], tuple):
                    # Drag and drop action
                    code += f'cursor.drag_and_drop({coordinate[0]}, {coordinate[1]}, duration=None, steady=False)\n'
        
        end = '\n# End\n\n'
        
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(imports + cursor + code + end)
    
    def load_recording(self):
        """Loads a recording from a file."""
        file_path = filedialog.askopenfilename(
            filetypes=[("HCS Recording", "*.hcs"), ("All Files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            import pickle
            with open(file_path, 'rb') as f:
                self.coordinates = pickle.load(f)
            
            self.index = len(self.coordinates) - 1
            
            if len(self.coordinates) > 0:
                self.play_button.config(state=tk.NORMAL)
            
            messagebox.showinfo("Success", f"Loaded {len(self.coordinates)} actions!")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load recording:\n{str(e)}")
    
    def on_closing(self):
        """Cleanup when window is closed."""
        # Stop all listeners
        if self.listener is not None and self.listener.running:
            self.listener.stop()
        
        if self.mouse_listener is not None and self.mouse_listener.running:
            self.mouse_listener.stop()
        
        if self.x_key_listener is not None and self.x_key_listener.running:
            self.x_key_listener.stop()
        
        if self.stop_listener is not None:
            self.stop_listener.stop()
        
        # Stop playback
        self.playback_running = False
        
        self.root.destroy()


def launch_all_in_one():
    """Launch the all-in-one HCS GUI."""
    AllInOneHCS()


if __name__ == "__main__":
    launch_all_in_one()
