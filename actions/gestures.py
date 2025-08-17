# actions/gestures.py
import time
class GestureActions:
    def __init__(self, driver, device_config, finder, logger, helpers, locators):
        self.d = driver # Device instance 
        self.device_id = device_config["udid"] # Device seral id
        self.driver_type = device_config["driver"] # Driver name e.g. uiautomator2 or appium
        self.finder = finder
        self.logger = logger
        self.helpers = helpers
        self.locators = locators

    # ============================================================================
    # Swipe & Gesture Methods
    # ============================================================================

    def swipe_until_visible(self, params, config):
        """
        Swipe until a target element becomes visible
        
        Args:
            params: Dictionary containing:
                - direction: "up", "down", "left", "right"
                - maxswipe: Maximum number of swipes (default: 10)
                - selector: Optional element to use as swipe area
                - target: Target element to find
            configs: Additional configurations
        """
        direction = config.get("direction", "left")
        f_direction = config.get("fallback_direction", "right")
        max_swipes = config.get("max_swipe", 10)

        selector_key = params.get("locator_id", None)
        target_key = params.get("target", None)
        
        if not target_key:
            raise ValueError("Target element key is required for swipe_until_visible")
        
        self.logger.debug(f"Starting swipe until visible: direction={direction}, max_swipes={max_swipes}, target={target_key}")
        
        # First attempt: main direction
        if self._swipe_in_direction_until_visible(target_key, direction, max_swipes, selector_key):
            return True
        
        # Try fallback direction if specified
        if f_direction and f_direction != direction:
            self.logger.info(f"Primary direction '{direction}' failed, trying fallback direction '{f_direction}'")
            if self._swipe_in_direction_until_visible(target_key, f_direction, max_swipes, selector_key):
                return True
        
        self.logger.warning(f"Target element '{target_key}' not found after {max_swipes} swipes")
        return False

    def swipe_until_not_visible(self, params, configs=None):
        """
        Swipe until a target element becomes invisible
        
        Args:
            params: Dictionary containing:
                - direction: "up", "down", "left", "right"
                - maxswipe: Maximum number of swipes (default: 10)
                - selector: Optional element to use as swipe area
                - target: Target element that should disappear
            configs: Additional configurations
        """
        direction = params.get("direction", "up")
        max_swipes = params.get("maxswipe", 10)
        selector_key = params.get("selector")
        target_key = params.get("target")
        
        if not target_key:
            raise ValueError("Target element key is required for swipe_until_not_visible")
        
        self.logger.debug(f"Starting swipe until not visible: direction={direction}, max_swipes={max_swipes}, target={target_key}")
        
        # Check if target element is initially visible
        if not self._is_element_visible(target_key):
            self.logger.info(f"Target element '{target_key}' is already not visible")
            return True
        
        # Get swipe coordinates
        swipe_coords = self._get_swipe_coordinates(selector_key, direction)
        
        for swipe_count in range(max_swipes):
            # Perform swipe
            self._perform_swipe(swipe_coords, direction)
            time.sleep(0.5)  # Brief pause between swipes
            
            # Check if target element is no longer visible
            if not self._is_element_visible(target_key):
                self.logger.info(f"Target element '{target_key}' disappeared after {swipe_count + 1} swipes")
                return True
            
            self.logger.debug(f"Swipe {swipe_count + 1}/{max_swipes} completed, target still visible")
        
        self.logger.warning(f"Target element '{target_key}' still visible after {max_swipes} swipes")
        return False

    def swipe_and_collect_children(self, params, configs=None):
        """
        Swipe and collect child elements during the swipe process
        
        Args:
            params: Dictionary containing:
                - direction: "up", "down", "left", "right"
                - maxswipe: Maximum number of swipes (default: 10)
                - selector: Optional element to use as swipe area
                - parent: Parent element containing children
                - child_selector: Selector for child elements to collect
            configs: Additional configurations
            
        Returns:
            List of collected child elements information
        """
        direction = params.get("direction", "up")
        max_swipes = params.get("maxswipe", 10)
        selector_key = params.get("selector")
        parent_key = params.get("parent")
        child_selector = params.get("child_selector")
        
        if not parent_key or not child_selector:
            raise ValueError("Parent and child_selector are required for swipe_and_collect_children")
        
        self.logger.debug(f"Starting swipe and collect children: direction={direction}, max_swipes={max_swipes}")
        
        collected_elements = []
        seen_elements = set()  # To avoid duplicates
        
        # Get swipe coordinates
        swipe_coords = self._get_swipe_coordinates(selector_key, direction)
        
        for swipe_count in range(max_swipes + 1):  # +1 to collect initial elements
            # Collect current child elements
            try:
                current_children = self._collect_child_elements(parent_key, child_selector)
                
                for child in current_children:
                    # Create a unique identifier for the child (could be text, bounds, etc.)
                    child_id = self._get_element_identifier(child)
                    
                    if child_id not in seen_elements:
                        seen_elements.add(child_id)
                        collected_elements.append(child)
                        self.logger.debug(f"Collected new child element: {child_id}")
                
            except Exception as e:
                self.logger.debug(f"Error collecting children on swipe {swipe_count}: {e}")
            
            # Don't swipe on the last iteration
            if swipe_count < max_swipes:
                self._perform_swipe(swipe_coords, direction)
                time.sleep(0.5)  # Brief pause between swipes
        
        self.logger.info(f"Collected {len(collected_elements)} unique child elements after {max_swipes} swipes")
        return collected_elements

    def swipe(self, params, configs=None):
        """
        Perform a basic swipe action
        
        Args:
            params: Dictionary containing:
                - direction: "up", "down", "left", "right"
                - count: Number of swipes (default: 1)
                - selector: Optional element to use as swipe area
                - distance: Swipe distance as percentage (default: 0.7)
            configs: Additional configurations
        """
        direction = params.get("direction", "up")
        count = params.get("count", 1)
        selector_key = params.get("selector")
        distance = params.get("distance", 0.7)
        
        self.logger.debug(f"Performing {count} swipe(s) in direction: {direction}")
        
        # Get swipe coordinates
        swipe_coords = self._get_swipe_coordinates(selector_key, direction, distance)
        
        for i in range(count):
            self._perform_swipe(swipe_coords, direction)
            
            if i < count - 1:  # Don't sleep after the last swipe
                time.sleep(0.5)
            
            self.logger.debug(f"Swipe {i + 1}/{count} completed")

    def swipe_to_element(self, params, configs=None):
        """
        Swipe to bring a specific element into view
        
        Args:
            params: Dictionary containing:
                - target: Target element to scroll to
                - direction: "up", "down", "left", "right" (optional, auto-detected)
                - maxswipe: Maximum number of swipes (default: 10)
                - selector: Optional element to use as swipe area
            configs: Additional configurations
        """
        target_key = params.get("target")
        direction = params.get("direction", "up")
        max_swipes = params.get("maxswipe", 10)
        selector_key = params.get("selector")
        
        if not target_key:
            raise ValueError("Target element key is required for swipe_to_element")
        
        # First, try to find the element without swiping
        if self._is_element_visible(target_key):
            self.logger.info(f"Target element '{target_key}' is already visible")
            return True
        
        # Try swiping in the specified direction first
        if self.swipe_until_visible({"direction": direction, "maxswipe": max_swipes//2, 
                                    "selector": selector_key, "target": target_key}):
            return True
        
        # If not found, try the opposite direction
        opposite_direction = self._get_opposite_direction(direction)
        self.logger.debug(f"Trying opposite direction: {opposite_direction}")
        
        return self.swipe_until_visible({"direction": opposite_direction, "maxswipe": max_swipes//2,
                                        "selector": selector_key, "target": target_key})

    def swipe_refresh(self, params, configs=None):
        """
        Perform a pull-to-refresh swipe gesture
        
        Args:
            params: Dictionary containing:
                - selector: Optional element to use as swipe area
            configs: Additional configurations
        """
        selector_key = params.get("selector")
        
        self.logger.debug("Performing pull-to-refresh swipe")
        
        # For refresh, we always swipe down from top
        swipe_coords = self._get_swipe_coordinates(selector_key, "down", distance=0.5)
        
        # Adjust start point to be near the top for refresh
        if self.driver_type == "uiautomator2":
            # Get screen size
            info = self.d.info
            screen_height = info['displayHeight']
            swipe_coords = (swipe_coords[0], int(screen_height * 0.1), 
                           swipe_coords[2], int(screen_height * 0.6))
        
        self._perform_swipe(swipe_coords, "down")
        time.sleep(1)  # Wait for refresh to complete

    
    # ============================================================================
    # Private Helper Methods for Fallback Direction Support
    # ============================================================================

    def _swipe_in_direction_until_visible(self, target_key, direction, max_swipes, selector_key):
        """Helper method to swipe in a specific direction until element is visible"""
        swipe_coords = self._get_swipe_coordinates(selector_key, direction)

        for swipe_count in range(max_swipes):
            # Check if target element is visible
            if self._is_element_visible(target_key):
                self.logger.info(f"Target element '{target_key}' found after {swipe_count} swipes in direction '{direction}'")
                return True

            # Perform swipe
            self._perform_swipe(swipe_coords, direction)
            time.sleep(0.5)  # Brief pause between swipes

            self.logger.debug(f"Swipe {swipe_count + 1}/{max_swipes} completed in direction '{direction}'")

        return False

    # ============================================================================
    # Gesture Helpers
    # ============================================================================

    def _get_swipe_coordinates(self, selector_key, direction, distance=0.7):
        """
        Get swipe coordinates based on selector element or screen
        
        Args:
            selector_key: Optional element key to use as swipe area
            direction: Swipe direction
            distance: Swipe distance as percentage (0.0 to 1.0)
            
        Returns:
            Tuple of (start_x, start_y, end_x, end_y)
        """
        if selector_key:
            # Use element bounds for swipe area
            try:
                element_bounds = self._get_element_bounds(selector_key)
                if element_bounds:
                    return self._calculate_swipe_coords_from_bounds(element_bounds, direction, distance)
            except Exception as e:
                self.logger.debug(f"Could not get bounds for selector '{selector_key}': {e}")
        
        # Fallback to screen dimensions
        return self._get_screen_swipe_coordinates(direction, distance)

    def _get_element_bounds(self, element_key):
        """Get bounds of an element using locator fallback strategy"""
        loc_yaml = self.locators
        
        if element_key not in loc_yaml:
            return None
        
        loc_def = loc_yaml[element_key]
        
        for key in ["primary", "fallback_1", "fallback_2"]:
            if key in loc_def:
                try:
                    element = self.finder.find_element(loc_def[key]["type"], loc_def[key]["value"])
                    
                    if self.driver_type == "uiautomator2":
                        # uiautomator2 element bounds
                        bounds = element.info.get("bounds", {})
                        return (bounds.get("left", 0), bounds.get("top", 0),
                               bounds.get("right", 0), bounds.get("bottom", 0))
                    else:
                        # Appium element bounds
                        location = element.location
                        size = element.size
                        return (location['x'], location['y'],
                               location['x'] + size['width'], location['y'] + size['height'])
                
                except Exception as e:
                    self.logger.debug(f"Could not get bounds with {key}: {e}")
        
        return None

    def _calculate_swipe_coords_from_bounds(self, bounds, direction, distance):
        """Calculate swipe coordinates from element bounds"""
        left, top, right, bottom = bounds
        center_x = (left + right) // 2
        center_y = (top + bottom) // 2
        width = right - left
        height = bottom - top
        
        if direction == "up":
            start_x, start_y = center_x, int(bottom - height * 0.1)
            end_x, end_y = center_x, int(top + height * (1 - distance))
        elif direction == "down":
            start_x, start_y = center_x, int(top + height * 0.1)
            end_x, end_y = center_x, int(bottom - height * (1 - distance))
        elif direction == "left":
            start_x, start_y = int(right - width * 0.1), center_y
            end_x, end_y = int(left + width * (1 - distance)), center_y
        elif direction == "right":
            start_x, start_y = int(left + width * 0.1), center_y
            end_x, end_y = int(right - width * (1 - distance)), center_y
        else:
            raise ValueError(f"Invalid swipe direction: {direction}")
        
        return (start_x, start_y, end_x, end_y)

    def _get_screen_swipe_coordinates(self, direction, distance=0.7):
        """Get swipe coordinates based on screen dimensions"""
        if self.driver_type == "uiautomator2":
            info = self.d.info
            width = info['displayWidth']
            height = info['displayHeight']
        else:
            # Appium
            size = self.d.get_window_size()
            width = size['width']
            height = size['height']
        
        center_x = width // 2
        center_y = height // 2
        
        # Calculate coordinates based on direction
        if direction == "up":
            start_x, start_y = center_x, int(height * 0.8)
            end_x, end_y = center_x, int(height * (0.8 - distance))
        elif direction == "down":
            start_x, start_y = center_x, int(height * 0.2)
            end_x, end_y = center_x, int(height * (0.2 + distance))
        elif direction == "left":
            start_x, start_y = int(width * 0.8), center_y
            end_x, end_y = int(width * (0.8 - distance)), center_y
        elif direction == "right":
            start_x, start_y = int(width * 0.2), center_y
            end_x, end_y = int(width * (0.2 + distance)), center_y
        else:
            raise ValueError(f"Invalid swipe direction: {direction}")
        
        return (start_x, start_y, end_x, end_y)

    def _perform_swipe(self, coords, direction):
        """Perform the actual swipe gesture"""
        start_x, start_y, end_x, end_y = coords
        
        self.logger.debug(f"Swiping from ({start_x}, {start_y}) to ({end_x}, {end_y})")
        
        if self.driver_type == "uiautomator2":
            self.d.swipe(start_x, start_y, end_x, end_y, duration=0.5)
        else:
            # Appium
            self.d.swipe(start_x, start_y, end_x, end_y, duration=500)

    def _is_element_visible(self, element_key):
        """Check if an element is visible on screen"""
        try:
            
            loc_yaml = self.locators
            
            if element_key not in loc_yaml:
                return False
            
            loc_def = loc_yaml[element_key]
            
            for key in ["primary", "fallback_1", "fallback_2"]:
                if key in loc_def:
                    try:
                        element = self.finder.find_element(loc_def[key]["type"], loc_def[key]["value"])
                        if element:
                            return True
                    except Exception:
                        continue
            
            return False
        except Exception as e:
            self.logger.debug(f"Error checking element visibility for '{element_key}': {e}")
            return False

    def _collect_child_elements(self, parent_key, child_selector):
        """Collect child elements from a parent element"""
        try:
            from utils.yaml_loader import load_locators
            loc_yaml = load_locators()
            
            # Find parent element
            parent_element = None
            if parent_key in loc_yaml:
                loc_def = loc_yaml[parent_key]
                for key in ["primary", "fallback_1", "fallback_2"]:
                    if key in loc_def:
                        try:
                            parent_element = self.finder.find_element(loc_def[key]["type"], loc_def[key]["value"])
                            break
                        except Exception:
                            continue
            
            if not parent_element:
                raise RuntimeError(f"Parent element '{parent_key}' not found")
            
            # Find child elements
            children = []
            if self.driver_type == "uiautomator2":
                # For uiautomator2, use child selector within parent
                if child_selector.get("type") == "class":
                    children = parent_element.child(className=child_selector["value"])
                elif child_selector.get("type") == "text":
                    children = parent_element.child(text=child_selector["value"])
                elif child_selector.get("type") == "xpath":
                    # For xpath, find all matching children
                    xpath = child_selector["value"]
                    children = parent_element.xpath(xpath).all()
            else:
                # Appium
                if child_selector.get("type") == "class":
                    children = parent_element.find_elements_by_class_name(child_selector["value"])
                elif child_selector.get("type") == "xpath":
                    children = parent_element.find_elements_by_xpath(child_selector["value"])
            
            return children if isinstance(children, list) else [children] if children else []
            
        except Exception as e:
            self.logger.debug(f"Error collecting child elements: {e}")
            return []

    def _get_element_identifier(self, element):
        """Get a unique identifier for an element to avoid duplicates"""
        try:
            if self.driver_type == "uiautomator2":
                info = element.info
                # Create identifier from text, class, and bounds
                text = info.get("text", "")
                class_name = info.get("className", "")
                bounds = info.get("bounds", {})
                return f"{text}_{class_name}_{bounds.get('left', 0)}_{bounds.get('top', 0)}"
            else:
                # Appium
                text = element.text or ""
                tag_name = element.tag_name or ""
                location = element.location
                return f"{text}_{tag_name}_{location.get('x', 0)}_{location.get('y', 0)}"
        except Exception:
            # Fallback to string representation
            return str(element)

    def _get_opposite_direction(self, direction):
        """Get the opposite swipe direction"""
        direction_map = {
            "up": "down",
            "down": "up", 
            "left": "right",
            "right": "left"
        }
        return direction_map.get(direction, "up") 