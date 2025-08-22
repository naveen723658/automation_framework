# actions/gestures.py
import time
from .base import BaseActions
class GestureActions(BaseActions):

    # ============================================================================
    # Common Config Validator
    # ============================================================================
    def _validate_configs(self, params, configs):
        """Merge params and configs with defaults for swipe actions"""
        return {
            "target": params.get("target"),
            "selector": params.get("selector") or params.get("locator_id"),
            "parent": params.get("parent"),
            "child_selector": params.get("child_selector"),

            # General swipe configs
            "direction": configs.get("direction", params.get("direction", "up")),
            "fallback_direction": configs.get("fallback_direction", ""),
            "max_swipe": configs.get("max_swipe", params.get("max_swipe", 10)),
            "distance": configs.get("distance", params.get("distance", 0.7)),
            "count": configs.get("count", params.get("count", 1)),
            "timeout": configs.get("timeout", 10),
            "message": configs.get("message"),
        }
    
    # ============================================================================
    # Swipe & Gesture Methods
    # ============================================================================

    def swipe_until_visible(self, params, configs=None):
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
        cfg = self._validate_configs(params, configs)
        target, direction, f_direction, max_swipes, selector = (
            cfg["target"], cfg["direction"], cfg["fallback_direction"], cfg["max_swipe"], cfg["selector"]
        )

        if not target:
            raise ValueError("Target element key is required for swipe_until_visible")

        self.logger.debug(f"Starting swipe until visible: direction={direction}, max_swipes={max_swipes}, target={target}")

        if self._swipe_in_direction_until_visible(target, direction, max_swipes, selector):
            return True

        if f_direction and f_direction != direction:
            self.logger.info(f"Primary '{direction}' failed, trying fallback '{f_direction}'")
            if self._swipe_in_direction_until_visible(target, f_direction, max_swipes, selector):
                return True

        self.logger.warning(f"Target '{target}' not found after {max_swipes} swipes")
        return False

    def swipe_until_not_visible(self, params, configs=None):
        """
        Swipe until a target element becomes invisible
        
        Args:
            params: Dictionary containing:
                - direction: "up", "down", "left", "right"
                - max_swipe: Maximum number of swipes (default: 10)
                - selector: Optional element to use as swipe area
                - target: Target element that should disappear
            configs: Additional configurations
        """
        cfg = self._validate_configs(params, configs or {})
        target, direction, max_swipes, selector = (
            cfg["target"], cfg["direction"], cfg["max_swipe"], cfg["selector"]
        )

        if not target:
            raise ValueError("Target element key is required for swipe_until_not_visible")

        self.logger.debug(f"Swipe until not visible: direction={direction}, max_swipes={max_swipes}, target={target}")

        if not self._is_element_visible(target):
            self.logger.info(f"Target '{target}' already not visible")
            return True

        swipe_coords = self._get_swipe_coordinates(selector, direction)
        for swipe_count in range(max_swipes):
            self._perform_swipe(swipe_coords, direction)
            time.sleep(0.5)
            if not self._is_element_visible(target):
                self.logger.info(f"Target '{target}' disappeared after {swipe_count + 1} swipes")
                return True
        self.logger.warning(f"Target '{target}' still visible after {max_swipes} swipes")
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
        cfg = self._validate_configs(params, configs)
        direction, max_swipes, selector, parent_key, child_selector = (
            cfg["direction"], cfg["max_swipe"], cfg["selector"], cfg["parent"], cfg["child_selector"]
        )

        if not parent_key or not child_selector:
            raise ValueError("Parent and child_selector are required for swipe_and_collect_children")

        self.logger.debug(f"Swipe and collect children: dir={direction}, max_swipes={max_swipes}")

        collected, seen = [], set()
        swipe_coords = self._get_swipe_coordinates(selector, direction)

        for swipe_count in range(max_swipes + 1):
            try:
                current_children = self._collect_child_elements(parent_key, child_selector)
                for child in current_children:
                    child_id = self._get_element_identifier(child)
                    if child_id not in seen:
                        seen.add(child_id)
                        collected.append(child)
                        self.logger.debug(f"Collected new child: {child_id}")
            except Exception as e:
                self.logger.debug(f"Error collecting children on swipe {swipe_count}: {e}")

            if swipe_count < max_swipes:
                self._perform_swipe(swipe_coords, direction)
                time.sleep(0.5)

        self.logger.info(f"Collected {len(collected)} unique children after {max_swipes} swipes")
        return collected

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
        cfg = self._validate_configs(params, configs)
        direction, count, selector, distance = (
            cfg["direction"], cfg["count"], cfg["selector"], cfg["distance"]
        )

        self.logger.debug(f"Performing {count} swipe(s) in direction: {direction}, distance={distance}")
        swipe_coords = self._get_swipe_coordinates(selector, direction, distance)

        for i in range(count):
            self._perform_swipe(swipe_coords, direction)

            if i < count - 1:
                time.sleep(0.5)

            self.logger.debug(f"Swipe {i + 1}/{count} completed")

        return True

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
        cfg = self._validate_configs(params, configs)
        target, direction, max_swipes, selector = (
            cfg["target"], cfg["direction"], cfg["max_swipe"], cfg["selector"]
        )

        if not target:
            raise ValueError("Target element key is required for swipe_to_element")

        if self._is_element_visible(target):
            self.logger.info(f"Target '{target}' already visible")
            return True

        if self.swipe_until_visible({"target": target, "direction": direction, "max_swipe": max_swipes // 2, "selector": selector}, cfg):
            return True

        opposite = self._get_opposite_direction(direction)
        self.logger.debug(f"Trying opposite direction: {opposite}")

        return self.swipe_until_visible({"target": target, "direction": opposite, "max_swipe": max_swipes // 2, "selector": selector}, cfg)

    def swipe_refresh(self, params, configs=None):
        """
        Perform a pull-to-refresh swipe gesture
        
        Args:
            params: Dictionary containing:
                - selector: Optional element to use as swipe area
            configs: Additional configurations
        """
        cfg = self._validate_configs(params, configs)
        selector = cfg["selector"]

        self.logger.debug("Performing pull-to-refresh swipe")
        swipe_coords = self._get_swipe_coordinates(selector, "down", distance=0.5)

        if self.driver_type == "uiautomator2":
            info = self.d.info
            screen_height = info['displayHeight']
            swipe_coords = (swipe_coords[0], int(screen_height * 0.1),
                            swipe_coords[2], int(screen_height * 0.6))

        self._perform_swipe(swipe_coords, "down")
        time.sleep(1)  # Wait for refresh

    
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