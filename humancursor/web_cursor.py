from time import sleep
import random

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement

from humancursor.utilities.web_adjuster import WebAdjuster
from humancursor.constants import CLICK_PAUSE_MIN, CLICK_PAUSE_MAX, SCROLL_WAIT_MIN, SCROLL_WAIT_MAX


class WebCursor:
    """Simulates human-like cursor movements in web browsers using Selenium.
    
    This class provides methods to interact with web elements using natural,
    human-like mouse movements to avoid detection by bot-detection systems.
    """
    
    def __init__(self, driver):
        self.__driver = driver
        self.__action = ActionChains(self.__driver, duration=0)
        self.human = WebAdjuster(self.__driver)
        self.origin_coordinates = [0, 0]

    def move_to(
            self,
            element: WebElement | list,
            relative_position: list | None = None,
            absolute_offset: bool = False,
            origin_coordinates=None,
            steady=False
    ):
        """Moves to element or coordinates with human curve
        
        Args:
            element: WebElement or [x, y] coordinates
            relative_position: [x_pct, y_pct] position within element (0.0 to 1.0)
            absolute_offset: If True, coordinates are absolute pixel offsets
            origin_coordinates: Starting position, None uses last position
            steady: If True, uses straighter movement path
            
        Returns:
            New cursor coordinates as [x, y] or False if scroll failed
            
        Raises:
            ValueError: If relative_position values are not between 0 and 1
        """
        if relative_position is not None:
            if not isinstance(relative_position, list) or len(relative_position) != 2:
                raise ValueError("relative_position must be a list of 2 values [x, y]")
            if not all(0 <= val <= 1 for val in relative_position):
                raise ValueError("relative_position values must be between 0.0 and 1.0")
        
        if not self.scroll_into_view_of_element(element):
            return False
        if origin_coordinates is None:
            origin_coordinates = self.origin_coordinates
        self.origin_coordinates = self.human.move_to(
            element,
            origin_coordinates=origin_coordinates,
            absolute_offset=absolute_offset,
            relative_position=relative_position,
            steady=steady
        )
        return self.origin_coordinates

    def click_on(
            self,
            element: WebElement | list,
            number_of_clicks: int = 1,
            click_duration: float = 0,
            relative_position: list | None = None,
            absolute_offset: bool = False,
            origin_coordinates=None,
            steady=False
    ):
        """Moves to element or coordinates with human curve, and clicks on it a specified number of times, default is 1
        
        Args:
            element: WebElement or [x, y] coordinates to click
            number_of_clicks: Number of times to click (must be positive)
            click_duration: Duration to hold mouse button in seconds
            relative_position: [x_pct, y_pct] position within element
            absolute_offset: If True, coordinates are absolute pixel offsets
            origin_coordinates: Starting position
            steady: If True, uses straighter movement path
            
        Raises:
            ValueError: If number_of_clicks is not positive or click_duration is negative
        """
        if not isinstance(number_of_clicks, int) or number_of_clicks < 1:
            raise ValueError(f"number_of_clicks must be a positive integer, got {number_of_clicks}")
        if not isinstance(click_duration, (int, float)) or click_duration < 0:
            raise ValueError(f"click_duration must be non-negative, got {click_duration}")
        
        self.move_to(
            element,
            origin_coordinates=origin_coordinates,
            absolute_offset=absolute_offset,
            relative_position=relative_position,
            steady=steady
        )
        self.click(number_of_clicks=number_of_clicks, click_duration=click_duration)
        return True

    def click(self, number_of_clicks: int = 1, click_duration: float = 0):
        """Performs the click action.
        
        Args:
            number_of_clicks: Number of times to click
            click_duration: Duration to hold the mouse button
            
        Returns:
            True when complete
        """
        if click_duration:
            click_action = lambda: self.__action.click_and_hold().pause(click_duration).release().pause(
                random.randint(int(CLICK_PAUSE_MIN * 1000), int(CLICK_PAUSE_MAX * 1000)) / 1000)
        else:
            click_action = lambda: self.__action.click().pause(
                random.randint(int(CLICK_PAUSE_MIN * 1000), int(CLICK_PAUSE_MAX * 1000)) / 1000)
        
        for _ in range(number_of_clicks):
            click_action()
        self.__action.perform()
        return True

    def move_by_offset(self, x: int, y: int, steady=False):
        """Moves the cursor with human curve, by specified number of x and y pixels"""
        self.origin_coordinates = self.human.move_to([x, y], absolute_offset=True, steady=steady)
        return True

    def drag_and_drop(
            self,
            drag_from_element: WebElement | list,
            drag_to_element: WebElement | list,
            drag_from_relative_position: list | None = None,
            drag_to_relative_position: list | None = None,
            steady=False
    ):
        """Moves to element or coordinates, clicks and holds, dragging it to another element, with human curve
        
        Args:
            drag_from_element: Source WebElement or [x, y] coordinates
            drag_to_element: Target WebElement or [x, y] coordinates (None to just click)
            drag_from_relative_position: [x_pct, y_pct] position within source
            drag_to_relative_position: [x_pct, y_pct] position within target
            steady: If True, uses straighter movement path
        """
        if drag_from_relative_position is None:
            self.move_to(drag_from_element)
        else:
            self.move_to(
                drag_from_element, relative_position=drag_from_relative_position
            )

        if drag_to_element is None:
            self.__action.click().perform()
        else:
            self.__action.click_and_hold().perform()
            if drag_to_relative_position is None:
                self.move_to(drag_to_element, steady=steady)
            else:
                self.move_to(
                    drag_to_element, relative_position=drag_to_relative_position, steady=steady
                )
            self.__action.release().perform()

        return True

    def control_scroll_bar(
            self,
            scroll_bar_element: WebElement,
            amount_by_percentage: list,
            orientation: str = "horizontal",
            steady=False
    ):
        """Adjusts any scroll bar on the webpage, by the amount you want in float number from 0 to 1
        representing percentage of fullness, orientation of the scroll bar must also be defined by user
        horizontal or vertical
        
        Args:
            scroll_bar_element: The scrollbar WebElement
            amount_by_percentage: Target percentage as float (0.0 to 1.0)
            orientation: 'horizontal' or 'vertical'
            steady: If True, uses straighter movement path
            
        Raises:
            ValueError: If orientation is invalid or amount is out of range
        """
        if orientation not in ("horizontal", "vertical"):
            raise ValueError(f"orientation must be 'horizontal' or 'vertical', got '{orientation}'")
        
        direction = True if orientation == "horizontal" else False

        self.move_to(scroll_bar_element)
        self.__action.click_and_hold().perform()
        # TODO: this needs rework, it will be more natural if it goes out of scroll bar, up or down randomly
        if direction:
            self.move_to(
                scroll_bar_element,
                relative_position=[amount_by_percentage, random.randint(0, 100) / 100],
                steady=steady
            )
        else:
            self.move_to(
                scroll_bar_element,
                relative_position=[random.randint(0, 100) / 100, amount_by_percentage],
                steady=steady
            )

        self.__action.release().perform()

        return True

    def scroll_into_view_of_element(self, element: WebElement | list):
        """Scrolls the element into viewport, if not already in it
        
        Args:
            element: WebElement to scroll into view, or list of coordinates
            
        Returns:
            True if successful or if element is coordinates
            
        Raises:
            TypeError: If element is not a WebElement or list
        """
        if isinstance(element, WebElement):
            is_in_viewport = self.__driver.execute_script(
                """
              var element = arguments[0];
              var rect = element.getBoundingClientRect();
              return (
                rect.top >= 0 &&
                rect.left >= 0 &&
                rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
                rect.right <= (window.innerWidth || document.documentElement.clientWidth)
              );
            """,
                element,
            )
            if not is_in_viewport:
                self.__driver.execute_script(
                    "arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });",
                    element,
                )
                sleep(random.uniform(SCROLL_WAIT_MIN, SCROLL_WAIT_MAX))
            return True
        elif isinstance(element, list):
            # Coordinates don't need scrolling
            return True
        else:
            raise TypeError(
                f"Element must be WebElement or list of coordinates, got {type(element).__name__}"
            )

    def show_cursor(self):
        self.__driver.execute_script('''
        let dot;
            function displayRedDot() {
              // Get the cursor position
              const x = event.clientX;
              const y = event.clientY;

              if (!dot) {
                // Create a new div element for the red dot if it doesn't exist
                dot = document.createElement("div");
                // Style the dot with CSS
                dot.style.position = "fixed";
                dot.style.width = "5px";
                dot.style.height = "5px";
                dot.style.borderRadius = "50%";
                dot.style.backgroundColor = "red";
                // Add the dot to the page
                document.body.appendChild(dot);
              }

              // Update the dot's position
              dot.style.left = x + "px";
              dot.style.top = y + "px";
            }

            // Add event listener to update the dot's position on mousemove
            document.addEventListener("mousemove", displayRedDot);''')
