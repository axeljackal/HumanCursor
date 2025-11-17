import os
import random
import tkinter as tk
from time import time
from tkinter import ttk, filedialog

import pyautogui

from humancursor.constants import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
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
    DEFAULT_FILENAME_RANDOM_MIN,
    DEFAULT_FILENAME_RANDOM_MAX,
)


class HCSWindow:
    """GUI window for HumanCursor Scripter application.
    
    This window allows users to record mouse movements and actions
    that will be saved as a Python script.
    """
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("HCS")
        self.coordinates = []

        self.bg = WINDOW_BACKGROUND_COLOR
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.config(bg=self.bg)
        self.root.wm_attributes('-topmost', True)
        self.root.resizable(False, False)

        self.style = ttk.Style()
        self.style.configure('TLabel', font=('Roboto', 11))

        self.label = ttk.Label(self.root, text="Cursor Position", background=self.bg)
        self.label.pack(pady=10)
        self.coordinates_label = ttk.Label(self.root, text="", background=self.bg)
        self.coordinates_label.pack(pady=10)

        self.file_name_label = ttk.Label(self.root, text="File Name (optional)", font=("Roboto", 10), background=self.bg)
        self.file_name_label.pack()
        self.file_name = ttk.Entry(self.root)
        self.file_name.pack(pady=5)

        self.destination_label = ttk.Label(self.root, text="File Destination", font=("Roboto", 10), background=self.bg)
        self.destination_label.pack()
        self.entry_var = tk.StringVar()
        self.destination = ttk.Entry(self.root, textvariable=self.entry_var, width=20)
        self.destination.pack(pady=5)

        self.browse_button = ttk.Button(self.root, text="Browse", command=self.browse_directory, style="TButton", width=6)
        self.browse_button.pack(anchor=tk.S, pady=3)

        self.activate_button = ttk.Button(self.root, text="ON/OFF", command=self.toggle_color, style="TButton")
        self.activate_button.pack(side=tk.LEFT, anchor=tk.S, padx=3, pady=3)

        self.confirm_button = ttk.Button(self.root, text="Finish", command=self.confirm, style="TButton")
        self.confirm_button.pack(side=tk.RIGHT, anchor=tk.S, padx=3, pady=3)

        self.indicator = tk.Canvas(self.root, width=INDICATOR_WIDTH, height=INDICATOR_HEIGHT, background=INDICATOR_BACKGROUND_COLOR)
        self.indicator.pack()

        self.indicator_color = INDICATOR_COLOR_INACTIVE

        self.indicator.create_rectangle(
            INDICATOR_RECT_X1, INDICATOR_RECT_Y1, INDICATOR_RECT_X2, INDICATOR_RECT_Y2, 
            fill=self.indicator_color
        )

        self.root.bind("<Button-1>", self.remove_focus)
        self.activate_button.bind("<Button-1>", self.remove_focus)

        self.file = None
        self.dest = None

        self.ctrl_pressed = False
        self.press_time = 0.0
        self.index = -1

        self.hold_time_threshold = HOLD_TIME_THRESHOLD

        self.update_coordinates()
        self.root.mainloop()

    def __call__(self):
        """Returns these values when calling the instance of the HCSWindow object as a function.
        
        Returns:
            tuple: (coordinates, file_name, destination_path)
        """
        return self.coordinates, self.file, self.dest

    def browse_directory(self):
        """Opens file browser to select destination directory."""
        folder_selected = filedialog.askdirectory()
        self.entry_var.set(folder_selected)

    def draw_indicator(self):
        """Draws the square indicating status of movement registration."""
        self.indicator.delete("all")
        self.indicator.create_rectangle(
            INDICATOR_RECT_X1, INDICATOR_RECT_Y1, INDICATOR_RECT_X2, INDICATOR_RECT_Y2,
            fill=self.indicator_color
        )

    def remove_focus(self, event):
        """Removes focus from field inputs when clicking the window or buttons.
        
        Args:
            event: Tkinter event object
        """
        if event.widget != self.file_name and event.widget != self.destination:
            self.root.focus_force()

    def toggle_color(self):
        """Toggles movement recording on/off by binding/unbinding keys.
        
        Binds CTRL and Z keys when activating recording mode.
        """
        if self.indicator_color == INDICATOR_COLOR_INACTIVE:
            self.root.bind("<KeyPress>", self.on_press_ctrl)
            self.root.bind("<KeyRelease>", self.on_release_ctrl)
            self.root.bind("<z>", self.move)
            self.indicator_color = INDICATOR_COLOR_ACTIVE
        else:
            self.root.unbind("<KeyPress>")
            self.root.unbind("<KeyRelease>")
            self.root.unbind("<z>")
            self.indicator_color = INDICATOR_COLOR_INACTIVE

        self.draw_indicator()

    def confirm(self):
        """Validates input and closes window to save the script.
        
        Sets return values before destroying the window.
        """
        self.file = self.file_name.get()
        self.dest = self.destination.get()

        if not self.file:
            self.file = f'humancursor_{random.randint(DEFAULT_FILENAME_RANDOM_MIN, DEFAULT_FILENAME_RANDOM_MAX)}'

        if self.is_valid_file_location(self.dest):
            self.root.destroy()
        else:
            self.destination_label.config(background='red')

    @staticmethod
    def is_valid_file_location(file_path: str) -> bool:
        """Checks if the provided file path exists.
        
        Args:
            file_path: Path to validate
            
        Returns:
            True if path exists, False otherwise
        """
        return os.path.exists(file_path)

    def update_coordinates(self):
        """Updates cursor coordinates display every COORDINATES_UPDATE_INTERVAL milliseconds."""
        x, y = pyautogui.position()
        self.coordinates_label.config(text=f"x: {x}, y: {y}")
        self.root.after(COORDINATES_UPDATE_INTERVAL, self.update_coordinates)

    def move(self, event):
        """Records a move action at current cursor position.
        
        Args:
            event: Tkinter event object (triggered by 'Z' key)
        """
        x, y = pyautogui.position()
        self.coordinates.append([x, y])
        self.index += 1

    def on_press_ctrl(self, event):
        """Records the start of a click or drag action.
        
        Args:
            event: Tkinter event object (triggered by CTRL key press)
        """
        if event.keysym == "Control_L" and not self.ctrl_pressed:
            self.ctrl_pressed = True
            x, y = pyautogui.position()
            self.press_time = time()
            self.coordinates.append([(x, y)])
            self.index += 1

    def on_release_ctrl(self, event):
        """Finalizes a click or drag action based on hold duration.
        
        If CTRL was held less than HOLD_TIME_THRESHOLD, records a click.
        If held longer, records a drag-and-drop action.
        
        Args:
            event: Tkinter event object (triggered by CTRL key release)
        """
        if event.keysym == "Control_L":
            self.ctrl_pressed = False
            x, y = pyautogui.position()
            if time() - self.press_time > self.hold_time_threshold:
                self.coordinates[self.index].append((x, y))
            else:
                self.coordinates[self.index] = self.coordinates[self.index][0]
            self.press_time = 0.0
