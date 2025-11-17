from pathlib import Path
from humancursor.HCScripter.gui import HCSWindow

mouse_coordinates, file_name, file_destination = HCSWindow()()

imports = '# Importing SystemCursor from humancursor package\nfrom humancursor import SystemCursor\n\n'

cursor = '# Initializing the SystemCursor object\ncursor = SystemCursor()\n\n'

code = '# Script Recorded: \n\n'

for coordinate in mouse_coordinates:
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

# Only create script if file_name and file_destination are provided
if file_name and file_destination:
    try:
        # Use pathlib for cross-platform path handling
        script_path = Path(file_destination) / f"{file_name}.py"
        
        with open(script_path, 'w', encoding='utf-8') as file:
            file.write(imports + cursor + code + end)
        
        print(f"Script successfully created at: {script_path}")
        
    except FileNotFoundError as e:
        print(f"Error: Directory not found - {file_destination}")
        print(f"Details: {e}")
    except PermissionError as e:
        print(f"Error: Permission denied when writing to {file_destination}")
        print(f"Details: {e}")
    except OSError as e:
        print(f"Error: Could not create file due to OS error")
        print(f"Details: {e}")
