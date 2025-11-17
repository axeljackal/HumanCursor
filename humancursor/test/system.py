from humancursor.system_cursor import SystemCursor


# Just a couple movements to show how the cursor behaves

def start_sys_demo():
    print('Initializing System Demo')
    # Use context manager to ensure cleanup
    with SystemCursor() as cursor:
        for _ in range(2):
            cursor.move_to([200, 200])  # Moving to coordinates x:200, y:200
            cursor.move_to([800, 200])  # Moving to coordinates x:800, y:200
            cursor.move_to([500, 800])  # Moving to coordinates x:500, y:800
            cursor.move_to([1400, 800])  # Moving to coordinates x:1400, y:800
    print('System Demo ended')


start_sys_demo()
