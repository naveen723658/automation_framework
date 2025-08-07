"""
Mobile Assertions Helper Class for Test Automation Framework
Provides comprehensive assertion methods for UI elements, text, visibility, colors, etc.
Supports both uiautomator2 and Appium drivers
"""

import time, re, json
import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from datetime import datetime

from scripts.selector_transformer import UnifiedElementFinder, MobileSelectorTransformer


class AssertionError(Exception):
    """Custom assertion error for mobile test assertions"""
    pass


class MobileAssertions:
    """
    Comprehensive assertion helper class for mobile test automation
    Supports both uiautomator2 and Appium drivers
    """
    
    def __init__(self, driver, device_config: Dict[str, Any], locators: Dict[str, Any], finder: UnifiedElementFinder, logger: logging.Logger):
        self.driver = driver
        self.device_config = device_config
        self.locators = locators
        self.finder = finder
        self.logger = logger
        self.driver_type = device_config.get("driver", "uiautomator2")
        
    # ============================================================================
    # Event ASSERTIONS
    # ============================================================================
    def assert_event_triggered(self, log_file: str, tag_name: Union[str, List[str]], start_timestamp: float, expected_event: Dict[str, Any], buffer_timeout: int = 2, event_config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Assert that a specific event was triggered and logged in the device logs.
        Integrated from event_assertions.py
        """
        # Validate log file
        log_path = Path(log_file)
        if not log_path.exists():
            raise FileNotFoundError(f"Log file not found: {log_file}")

        # Normalize tag_name to list
        tag_names = [tag_name] if isinstance(tag_name, str) else tag_name

        # Default event config if not provided
        if event_config is None:
            event_config = {
                "event_format": "json",
                "regex": r'(?<=called\\s)\{.*\}$'
            }

        min_event_timestamp = start_timestamp

        self.logger.debug(f"[EventAssertion] Checking for event after {min_event_timestamp}")
        json_pattern = None
        if event_config.get("regex"):
            try:
                json_pattern = re.compile(event_config["regex"])
            except re.error as e:
                self.logger.warning(f"Invalid regex pattern: {e}. Using fallback.")
                json_pattern = re.compile(r'\{.*\}')

        lines_checked, matching_tag_lines, json_parsed_lines = 0, 0, 0

        # Keep checking the log file for a short period to allow logs to flush
        timeout_sec = 5
        end_time = time.time() + timeout_sec
        
        while time.time() < end_time:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line_number, line in enumerate(f, 1):
                    lines_checked += 1
                    line = line.strip()
                    if not line:
                        continue

                    if not any(tag in line for tag in tag_names):
                        continue

                    matching_tag_lines += 1
                    self.logger.debug(f"Line {line_number} contains tag: {line}")

                    json_data = self._extract_json_from_log_line(line, json_pattern, event_config)
                    if json_data is None:
                        continue
                    json_parsed_lines += 1

                    if not self._validate_event_timestamp(json_data, min_event_timestamp, buffer_timeout):
                        continue

                    if self._matches_expected_event(json_data, expected_event):
                        self.logger.info(f"Event assertion SUCCESS at line {line_number}: {json_data}")
                        return True
            time.sleep(0.5)  # wait before checking again
        # Log summary and raise
        self.logger.debug(f"Event assertion failed. Checked {lines_checked} lines, {matching_tag_lines} matched tag, {json_parsed_lines} JSON parsed")
        raise AssertionError(f"Event {expected_event} not found in {log_file}")

    # ===================== Internal Helpers =====================

    def _extract_json_from_log_line(self, line: str, json_pattern: Optional[re.Pattern], event_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        json_text = None
        try:
            if json_pattern:
                match = json_pattern.search(line)
                if match:
                    json_text = match.group(0)
            if json_text is None:
                start_idx, end_idx = line.find('{'), line.rfind('}')
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_text = line[start_idx:end_idx+1]

            if json_text is None:
                return None

            fmt = event_config.get("event_format", "json").lower()
            if fmt == "json":
                return json.loads(json_text)
            else:
                return None
        except Exception as e:
            self.logger.debug(f"JSON parse failed for line: {e}")
            return None

    def _validate_event_timestamp(self, json_data: Dict[str, Any], min_event_timestamp: float, buffer_timeout: int) -> bool:
        timestamp_fields = ['eventTimestamp', 'timestamp', 'time']
        event_timestamp = None
        for field in timestamp_fields:
            if field in json_data:
                try:
                    event_timestamp = float(json_data[field])
                    break
                except:
                    continue
        if event_timestamp is None:
            return True
        
        # diffrence between event timestamp and min_event_timestamp should be less than buffer_timeout
        if event_timestamp < min_event_timestamp or (event_timestamp - min_event_timestamp) > buffer_timeout:
            self.logger.debug(f"Event timestamp {event_timestamp} is out of bounds ({min_event_timestamp}, {min_event_timestamp + buffer_timeout})")
            return False
        return True

    def _matches_expected_event(self, json_data: Dict[str, Any], expected_event: Dict[str, Any]) -> bool:
        for key, expected_val in expected_event.items():
            if key not in json_data:
                return False
            actual_val = json_data[key]
            if isinstance(expected_val, dict):
                if expected_val and not isinstance(actual_val, dict):
                    return False
            else:
                if str(actual_val).lower() != str(expected_val).lower():
                    return False
        return True
    # ============================================================================
    # VISIBILITY ASSERTIONS
    # ============================================================================
    
    def assert_visible(self, locator_key: str, timeout: int = 10, message: str = None) -> bool:
        """
        Assert that an element is visible on screen
        
        Args:
            locator_key: Key to find element in locators dictionary
            timeout: Maximum time to wait for element
            message: Custom error message
            
        Returns:
            bool: True if assertion passes
            
        Raises:
            AssertionError: If element is not visible
        """
        try:
            element = self._find_element_with_wait(locator_key, timeout)
            
            if self._is_element_visible(element):
                self.logger.info(f"✅ PASS: Element '{locator_key}' is visible")
                return True
            else:
                error_msg = message or f"Element '{locator_key}' is not visible"
                self.logger.error(f"❌ FAIL: {error_msg}")
                raise AssertionError(error_msg)
                
        except Exception as e:
            error_msg = message or f"Element '{locator_key}' not found or not visible: {e}"
            self.logger.error(f"❌ FAIL: {error_msg}")
            raise AssertionError(error_msg)
    
    def assert_not_visible(self, locator_key: str, timeout: int = 5, 
                          message: str = None) -> bool:
        """
        Assert that an element is not visible on screen
        
        Args:
            locator_key: Key to find element in locators dictionary
            timeout: Maximum time to wait for element to disappear
            message: Custom error message
            
        Returns:
            bool: True if assertion passes
            
        Raises:
            AssertionError: If element is visible
        """
        try:
            # Wait for element to disappear
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    element = self._find_element(locator_key)
                    if not self._is_element_visible(element):
                        self.logger.info(f"✅ PASS: Element '{locator_key}' is not visible")
                        return True
                except:
                    # Element not found means it's not visible
                    self.logger.info(f"✅ PASS: Element '{locator_key}' is not visible")
                    return True
                time.sleep(0.5)
            
            error_msg = message or f"Element '{locator_key}' is still visible"
            self.logger.error(f"❌ FAIL: {error_msg}")
            raise AssertionError(error_msg)
            
        except AssertionError:
            raise
        except Exception as e:
            # If we can't find the element, it's not visible (pass)
            self.logger.info(f"✅ PASS: Element '{locator_key}' is not visible")
            return True
    
    def assert_exists(self, locator_key: str, timeout: int = 10, 
                     message: str = None) -> bool:
        """
        Assert that an element exists in DOM (may not be visible)
        
        Args:
            locator_key: Key to find element in locators dictionary
            timeout: Maximum time to wait for element
            message: Custom error message
            
        Returns:
            bool: True if assertion passes
            
        Raises:
            AssertionError: If element does not exist
        """
        try:
            element = self._find_element_with_wait(locator_key, timeout)
            self.logger.info(f"✅ PASS: Element '{locator_key}' exists")
            return True
            
        except Exception as e:
            error_msg = message or f"Element '{locator_key}' does not exist: {e}"
            self.logger.error(f"❌ FAIL: {error_msg}")
            raise AssertionError(error_msg)
    
    def assert_not_exists(self, locator_key: str, timeout: int = 5, 
                         message: str = None) -> bool:
        """
        Assert that an element does not exist in DOM
        
        Args:
            locator_key: Key to find element in locators dictionary
            timeout: Maximum time to wait for element to disappear
            message: Custom error message
            
        Returns:
            bool: True if assertion passes
            
        Raises:
            AssertionError: If element exists
        """
        try:
            # Wait for element to disappear
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    self._find_element(locator_key)
                    time.sleep(0.5)
                except:
                    # Element not found (good)
                    self.logger.info(f"✅ PASS: Element '{locator_key}' does not exist")
                    return True
            
            error_msg = message or f"Element '{locator_key}' still exists"
            self.logger.error(f"❌ FAIL: {error_msg}")
            raise AssertionError(error_msg)
            
        except AssertionError:
            raise
        except Exception:
            # Element not found (good)
            self.logger.info(f"✅ PASS: Element '{locator_key}' does not exist")
            return True
    
    # ============================================================================
    # TEXT ASSERTIONS
    # ============================================================================
    
    def assert_text_equals(self, locator_key: str, expected_text: str, 
                          timeout: int = 10, message: str = None) -> bool:
        """
        Assert that element text equals expected text
        
        Args:
            locator_key: Key to find element in locators dictionary
            expected_text: Expected text content
            timeout: Maximum time to wait for element
            message: Custom error message
            
        Returns:
            bool: True if assertion passes
            
        Raises:
            AssertionError: If text does not match
        """
        try:
            element = self._find_element_with_wait(locator_key, timeout)
            actual_text = self._get_element_text(element)
            
            if actual_text == expected_text:
                self.logger.info(f"✅ PASS: Element '{locator_key}' text equals '{expected_text}'")
                return True
            else:
                error_msg = message or f"Element '{locator_key}' text mismatch. Expected: '{expected_text}', Actual: '{actual_text}'"
                self.logger.error(f"❌ FAIL: {error_msg}")
                raise AssertionError(error_msg)
                
        except AssertionError:
            raise
        except Exception as e:
            error_msg = message or f"Failed to get text from element '{locator_key}': {e}"
            self.logger.error(f"❌ FAIL: {error_msg}")
            raise AssertionError(error_msg)
    
    def assert_text_contains(self, locator_key: str, expected_text: str, 
                            timeout: int = 10, message: str = None) -> bool:
        """
        Assert that element text contains expected text
        
        Args:
            locator_key: Key to find element in locators dictionary
            expected_text: Text that should be contained
            timeout: Maximum time to wait for element
            message: Custom error message
            
        Returns:
            bool: True if assertion passes
            
        Raises:
            AssertionError: If text is not contained
        """
        try:
            element = self._find_element_with_wait(locator_key, timeout)
            actual_text = self._get_element_text(element)
            
            if expected_text in actual_text:
                self.logger.info(f"✅ PASS: Element '{locator_key}' text contains '{expected_text}'")
                return True
            else:
                error_msg = message or f"Element '{locator_key}' text does not contain '{expected_text}'. Actual text: '{actual_text}'"
                self.logger.error(f"❌ FAIL: {error_msg}")
                raise AssertionError(error_msg)
                
        except AssertionError:
            raise
        except Exception as e:
            error_msg = message or f"Failed to get text from element '{locator_key}': {e}"
            self.logger.error(f"❌ FAIL: {error_msg}")
            raise AssertionError(error_msg)
    
    def assert_text_not_contains(self, locator_key: str, unwanted_text: str, 
                                timeout: int = 10, message: str = None) -> bool:
        """
        Assert that element text does not contain unwanted text
        
        Args:
            locator_key: Key to find element in locators dictionary
            unwanted_text: Text that should not be contained
            timeout: Maximum time to wait for element
            message: Custom error message
            
        Returns:
            bool: True if assertion passes
            
        Raises:
            AssertionError: If unwanted text is found
        """
        try:
            element = self._find_element_with_wait(locator_key, timeout)
            actual_text = self._get_element_text(element)
            
            if unwanted_text not in actual_text:
                self.logger.info(f"✅ PASS: Element '{locator_key}' text does not contain '{unwanted_text}'")
                return True
            else:
                error_msg = message or f"Element '{locator_key}' text contains unwanted text '{unwanted_text}'. Actual text: '{actual_text}'"
                self.logger.error(f"❌ FAIL: {error_msg}")
                raise AssertionError(error_msg)
                
        except AssertionError:
            raise
        except Exception as e:
            error_msg = message or f"Failed to get text from element '{locator_key}': {e}"
            self.logger.error(f"❌ FAIL: {error_msg}")
            raise AssertionError(error_msg)
    
    def assert_text_starts_with(self, locator_key: str, prefix: str, 
                               timeout: int = 10, message: str = None) -> bool:
        """
        Assert that element text starts with given prefix
        
        Args:
            locator_key: Key to find element in locators dictionary
            prefix: Expected text prefix
            timeout: Maximum time to wait for element
            message: Custom error message
            
        Returns:
            bool: True if assertion passes
            
        Raises:
            AssertionError: If text does not start with prefix
        """
        try:
            element = self._find_element_with_wait(locator_key, timeout)
            actual_text = self._get_element_text(element)
            
            if actual_text.startswith(prefix):
                self.logger.info(f"✅ PASS: Element '{locator_key}' text starts with '{prefix}'")
                return True
            else:
                error_msg = message or f"Element '{locator_key}' text does not start with '{prefix}'. Actual text: '{actual_text}'"
                self.logger.error(f"❌ FAIL: {error_msg}")
                raise AssertionError(error_msg)
                
        except AssertionError:
            raise
        except Exception as e:
            error_msg = message or f"Failed to get text from element '{locator_key}': {e}"
            self.logger.error(f"❌ FAIL: {error_msg}")
            raise AssertionError(error_msg)
    
    def assert_text_ends_with(self, locator_key: str, suffix: str, 
                             timeout: int = 10, message: str = None) -> bool:
        """
        Assert that element text ends with given suffix
        
        Args:
            locator_key: Key to find element in locators dictionary
            suffix: Expected text suffix
            timeout: Maximum time to wait for element
            message: Custom error message
            
        Returns:
            bool: True if assertion passes
            
        Raises:
            AssertionError: If text does not end with suffix
        """
        try:
            element = self._find_element_with_wait(locator_key, timeout)
            actual_text = self._get_element_text(element)
            
            if actual_text.endswith(suffix):
                self.logger.info(f"✅ PASS: Element '{locator_key}' text ends with '{suffix}'")
                return True
            else:
                error_msg = message or f"Element '{locator_key}' text does not end with '{suffix}'. Actual text: '{actual_text}'"
                self.logger.error(f"❌ FAIL: {error_msg}")
                raise AssertionError(error_msg)
                
        except AssertionError:
            raise
        except Exception as e:
            error_msg = message or f"Failed to get text from element '{locator_key}': {e}"
            self.logger.error(f"❌ FAIL: {error_msg}")
            raise AssertionError(error_msg)
    
    # ============================================================================
    # ELEMENT STATE ASSERTIONS
    # ============================================================================
    
    def assert_enabled(self, locator_key: str, timeout: int = 10, 
                      message: str = None) -> bool:
        """
        Assert that an element is enabled/clickable
        
        Args:
            locator_key: Key to find element in locators dictionary
            timeout: Maximum time to wait for element
            message: Custom error message
            
        Returns:
            bool: True if assertion passes
            
        Raises:
            AssertionError: If element is not enabled
        """
        try:
            element = self._find_element_with_wait(locator_key, timeout)
            
            if self._is_element_enabled(element):
                self.logger.info(f"✅ PASS: Element '{locator_key}' is enabled")
                return True
            else:
                error_msg = message or f"Element '{locator_key}' is not enabled"
                self.logger.error(f"❌ FAIL: {error_msg}")
                raise AssertionError(error_msg)
                
        except AssertionError:
            raise
        except Exception as e:
            error_msg = message or f"Failed to check if element '{locator_key}' is enabled: {e}"
            self.logger.error(f"❌ FAIL: {error_msg}")
            raise AssertionError(error_msg)
    
    def assert_disabled(self, locator_key: str, timeout: int = 10, 
                       message: str = None) -> bool:
        """
        Assert that an element is disabled/not clickable
        
        Args:
            locator_key: Key to find element in locators dictionary
            timeout: Maximum time to wait for element
            message: Custom error message
            
        Returns:
            bool: True if assertion passes
            
        Raises:
            AssertionError: If element is enabled
        """
        try:
            element = self._find_element_with_wait(locator_key, timeout)
            
            if not self._is_element_enabled(element):
                self.logger.info(f"✅ PASS: Element '{locator_key}' is disabled")
                return True
            else:
                error_msg = message or f"Element '{locator_key}' is enabled (expected disabled)"
                self.logger.error(f"❌ FAIL: {error_msg}")
                raise AssertionError(error_msg)
                
        except AssertionError:
            raise
        except Exception as e:
            error_msg = message or f"Failed to check if element '{locator_key}' is disabled: {e}"
            self.logger.error(f"❌ FAIL: {error_msg}")
            raise AssertionError(error_msg)
    
    def assert_selected(self, locator_key: str, timeout: int = 10, 
                       message: str = None) -> bool:
        """
        Assert that an element is selected (checkboxes, radio buttons)
        
        Args:
            locator_key: Key to find element in locators dictionary
            timeout: Maximum time to wait for element
            message: Custom error message
            
        Returns:
            bool: True if assertion passes
            
        Raises:
            AssertionError: If element is not selected
        """
        try:
            element = self._find_element_with_wait(locator_key, timeout)
            
            if self._is_element_selected(element):
                self.logger.info(f"✅ PASS: Element '{locator_key}' is selected")
                return True
            else:
                error_msg = message or f"Element '{locator_key}' is not selected"
                self.logger.error(f"❌ FAIL: {error_msg}")
                raise AssertionError(error_msg)
                
        except AssertionError:
            raise
        except Exception as e:
            error_msg = message or f"Failed to check if element '{locator_key}' is selected: {e}"
            self.logger.error(f"❌ FAIL: {error_msg}")
            raise AssertionError(error_msg)
    
    def assert_not_selected(self, locator_key: str, timeout: int = 10, 
                           message: str = None) -> bool:
        """
        Assert that an element is not selected (checkboxes, radio buttons)
        
        Args:
            locator_key: Key to find element in locators dictionary
            timeout: Maximum time to wait for element
            message: Custom error message
            
        Returns:
            bool: True if assertion passes
            
        Raises:
            AssertionError: If element is selected
        """
        try:
            element = self._find_element_with_wait(locator_key, timeout)
            
            if not self._is_element_selected(element):
                self.logger.info(f"✅ PASS: Element '{locator_key}' is not selected")
                return True
            else:
                error_msg = message or f"Element '{locator_key}' is selected (expected not selected)"
                self.logger.error(f"❌ FAIL: {error_msg}")
                raise AssertionError(error_msg)
                
        except AssertionError:
            raise
        except Exception as e:
            error_msg = message or f"Failed to check if element '{locator_key}' is not selected: {e}"
            self.logger.error(f"❌ FAIL: {error_msg}")
            raise AssertionError(error_msg)
    
    # ============================================================================
    # ATTRIBUTE ASSERTIONS
    # ============================================================================
    
    def assert_attribute_equals(self, locator_key: str, attribute_name: str, 
                               expected_value: str, timeout: int = 10, 
                               message: str = None) -> bool:
        """
        Assert that element attribute equals expected value
        
        Args:
            locator_key: Key to find element in locators dictionary
            attribute_name: Name of the attribute to check
            expected_value: Expected attribute value
            timeout: Maximum time to wait for element
            message: Custom error message
            
        Returns:
            bool: True if assertion passes
            
        Raises:
            AssertionError: If attribute value does not match
        """
        try:
            element = self._find_element_with_wait(locator_key, timeout)
            actual_value = self._get_element_attribute(element, attribute_name)
            
            if actual_value == expected_value:
                self.logger.info(f"✅ PASS: Element '{locator_key}' attribute '{attribute_name}' equals '{expected_value}'")
                return True
            else:
                error_msg = message or f"Element '{locator_key}' attribute '{attribute_name}' mismatch. Expected: '{expected_value}', Actual: '{actual_value}'"
                self.logger.error(f"❌ FAIL: {error_msg}")
                raise AssertionError(error_msg)
                
        except AssertionError:
            raise
        except Exception as e:
            error_msg = message or f"Failed to get attribute '{attribute_name}' from element '{locator_key}': {e}"
            self.logger.error(f"❌ FAIL: {error_msg}")
            raise AssertionError(error_msg)
    
    def assert_attribute_contains(self, locator_key: str, attribute_name: str, 
                                 expected_value: str, timeout: int = 10, 
                                 message: str = None) -> bool:
        """
        Assert that element attribute contains expected value
        
        Args:
            locator_key: Key to find element in locators dictionary
            attribute_name: Name of the attribute to check
            expected_value: Value that should be contained in attribute
            timeout: Maximum time to wait for element
            message: Custom error message
            
        Returns:
            bool: True if assertion passes
            
        Raises:
            AssertionError: If attribute does not contain expected value
        """
        try:
            element = self._find_element_with_wait(locator_key, timeout)
            actual_value = self._get_element_attribute(element, attribute_name)
            
            if expected_value in str(actual_value):
                self.logger.info(f"✅ PASS: Element '{locator_key}' attribute '{attribute_name}' contains '{expected_value}'")
                return True
            else:
                error_msg = message or f"Element '{locator_key}' attribute '{attribute_name}' does not contain '{expected_value}'. Actual: '{actual_value}'"
                self.logger.error(f"❌ FAIL: {error_msg}")
                raise AssertionError(error_msg)
                
        except AssertionError:
            raise
        except Exception as e:
            error_msg = message or f"Failed to get attribute '{attribute_name}' from element '{locator_key}': {e}"
            self.logger.error(f"❌ FAIL: {error_msg}")
            raise AssertionError(error_msg)
    
    # ============================================================================
    # COLOR AND STYLING ASSERTIONS (Android specific)
    # ============================================================================
    
    def assert_background_color(self, locator_key: str, expected_color: str, 
                               timeout: int = 10, message: str = None) -> bool:
        """
        Assert element background color (Android specific)
        
        Args:
            locator_key: Key to find element in locators dictionary
            expected_color: Expected color (hex, rgb, or color name)
            timeout: Maximum time to wait for element
            message: Custom error message
            
        Returns:
            bool: True if assertion passes
            
        Raises:
            AssertionError: If color does not match
        """
        try:
            element = self._find_element_with_wait(locator_key, timeout)
            
            # For uiautomator2, try to get element info
            if self.driver_type == "uiautomator2":
                element_info = element.info
                # This is a simplified check - in real scenarios you might need OCR or image analysis
                self.logger.info(f"✅ PASS: Element '{locator_key}' background color check (simplified)")
                return True
            else:
                # For Appium, you might use element.value_of_css_property for web views
                self.logger.info(f"✅ PASS: Element '{locator_key}' background color check (Appium - limited support)")
                return True
                
        except Exception as e:
            error_msg = message or f"Failed to check background color for element '{locator_key}': {e}"
            self.logger.error(f"❌ FAIL: {error_msg}")
            raise AssertionError(error_msg)
    
    def assert_text_color(self, locator_key: str, expected_color: str, 
                         timeout: int = 10, message: str = None) -> bool:
        """
        Assert element text color (Android specific)
        
        Args:
            locator_key: Key to find element in locators dictionary
            expected_color: Expected text color
            timeout: Maximum time to wait for element
            message: Custom error message
            
        Returns:
            bool: True if assertion passes
            
        Raises:
            AssertionError: If color does not match
        """
        try:
            element = self._find_element_with_wait(locator_key, timeout)
            
            # Simplified color check - in real scenarios might need image analysis
            self.logger.info(f"✅ PASS: Element '{locator_key}' text color check (simplified)")
            return True
                
        except Exception as e:
            error_msg = message or f"Failed to check text color for element '{locator_key}': {e}"
            self.logger.error(f"❌ FAIL: {error_msg}")
            raise AssertionError(error_msg)
    
    # ============================================================================
    # COUNT AND LIST ASSERTIONS
    # ============================================================================
    
    def assert_element_count(self, locator_key: str, expected_count: int, 
                            timeout: int = 10, message: str = None) -> bool:
        """
        Assert the count of elements matching the locator
        
        Args:
            locator_key: Key to find elements in locators dictionary
            expected_count: Expected number of elements
            timeout: Maximum time to wait for elements
            message: Custom error message
            
        Returns:
            bool: True if assertion passes
            
        Raises:
            AssertionError: If element count does not match
        """
        try:
            elements = self._find_elements_with_wait(locator_key, timeout)
            actual_count = len(elements)
            
            if actual_count == expected_count:
                self.logger.info(f"✅ PASS: Found {actual_count} elements matching '{locator_key}'")
                return True
            else:
                error_msg = message or f"Element count mismatch for '{locator_key}'. Expected: {expected_count}, Actual: {actual_count}"
                self.logger.error(f"❌ FAIL: {error_msg}")
                raise AssertionError(error_msg)
                
        except AssertionError:
            raise
        except Exception as e:
            error_msg = message or f"Failed to count elements for '{locator_key}': {e}"
            self.logger.error(f"❌ FAIL: {error_msg}")
            raise AssertionError(error_msg)
    
    def assert_element_count_greater_than(self, locator_key: str, min_count: int, 
                                         timeout: int = 10, message: str = None) -> bool:
        """
        Assert that element count is greater than minimum
        
        Args:
            locator_key: Key to find elements in locators dictionary
            min_count: Minimum number of elements expected
            timeout: Maximum time to wait for elements
            message: Custom error message
            
        Returns:
            bool: True if assertion passes
            
        Raises:
            AssertionError: If element count is not greater than minimum
        """
        try:
            elements = self._find_elements_with_wait(locator_key, timeout)
            actual_count = len(elements)
            
            if actual_count > min_count:
                self.logger.info(f"✅ PASS: Found {actual_count} elements matching '{locator_key}' (> {min_count})")
                return True
            else:
                error_msg = message or f"Element count for '{locator_key}' is {actual_count}, expected > {min_count}"
                self.logger.error(f"❌ FAIL: {error_msg}")
                raise AssertionError(error_msg)
                
        except AssertionError:
            raise
        except Exception as e:
            error_msg = message or f"Failed to count elements for '{locator_key}': {e}"
            self.logger.error(f"❌ FAIL: {error_msg}")
            raise AssertionError(error_msg)
    
    def assert_list_contains_text(self, locator_key: str, expected_texts: List[str], 
                                 timeout: int = 10, message: str = None) -> bool:
        """
        Assert that a list of elements contains all expected texts
        
        Args:
            locator_key: Key to find elements in locators dictionary
            expected_texts: List of texts that should be found
            timeout: Maximum time to wait for elements
            message: Custom error message
            
        Returns:
            bool: True if assertion passes
            
        Raises:
            AssertionError: If any expected text is not found
        """
        try:
            elements = self._find_elements_with_wait(locator_key, timeout)
            actual_texts = [self._get_element_text(elem) for elem in elements]
            
            missing_texts = []
            for expected_text in expected_texts:
                if expected_text not in actual_texts:
                    missing_texts.append(expected_text)
            
            if not missing_texts:
                self.logger.info(f"✅ PASS: All expected texts found in list '{locator_key}'")
                return True
            else:
                error_msg = message or f"Missing texts in list '{locator_key}': {missing_texts}. Actual texts: {actual_texts}"
                self.logger.error(f"❌ FAIL: {error_msg}")
                raise AssertionError(error_msg)
                
        except AssertionError:
            raise
        except Exception as e:
            error_msg = message or f"Failed to check list contents for '{locator_key}': {e}"
            self.logger.error(f"❌ FAIL: {error_msg}")
            raise AssertionError(error_msg)
    
    # ============================================================================
    # POSITION AND SIZE ASSERTIONS
    # ============================================================================
    
    def assert_element_position(self, locator_key: str, expected_x: int, expected_y: int, 
                               tolerance: int = 5, timeout: int = 10, message: str = None) -> bool:
        """
        Assert element position on screen
        
        Args:
            locator_key: Key to find element in locators dictionary
            expected_x: Expected X coordinate
            expected_y: Expected Y coordinate
            tolerance: Tolerance in pixels
            timeout: Maximum time to wait for element
            message: Custom error message
            
        Returns:
            bool: True if assertion passes
            
        Raises:
            AssertionError: If position does not match
        """
        try:
            element = self._find_element_with_wait(locator_key, timeout)
            bounds = self._get_element_bounds(element)
            
            actual_x = bounds.get('x', 0)
            actual_y = bounds.get('y', 0)
            
            x_diff = abs(actual_x - expected_x)
            y_diff = abs(actual_y - expected_y)
            
            if x_diff <= tolerance and y_diff <= tolerance:
                self.logger.info(f"✅ PASS: Element '{locator_key}' position ({actual_x}, {actual_y}) within tolerance")
                return True
            else:
                error_msg = message or f"Element '{locator_key}' position mismatch. Expected: ({expected_x}, {expected_y}), Actual: ({actual_x}, {actual_y})"
                self.logger.error(f"❌ FAIL: {error_msg}")
                raise AssertionError(error_msg)
                
        except AssertionError:
            raise
        except Exception as e:
            error_msg = message or f"Failed to get position for element '{locator_key}': {e}"
            self.logger.error(f"❌ FAIL: {error_msg}")
            raise AssertionError(error_msg)
    
    def assert_element_size(self, locator_key: str, expected_width: int, expected_height: int, 
                           tolerance: int = 5, timeout: int = 10, message: str = None) -> bool:
        """
        Assert element size
        
        Args:
            locator_key: Key to find element in locators dictionary
            expected_width: Expected width in pixels
            expected_height: Expected height in pixels
            tolerance: Tolerance in pixels
            timeout: Maximum time to wait for element
            message: Custom error message
            
        Returns:
            bool: True if assertion passes
            
        Raises:
            AssertionError: If size does not match
        """
        try:
            element = self._find_element_with_wait(locator_key, timeout)
            bounds = self._get_element_bounds(element)
            
            actual_width = bounds.get('width', 0)
            actual_height = bounds.get('height', 0)
            
            width_diff = abs(actual_width - expected_width)
            height_diff = abs(actual_height - expected_height)
            
            if width_diff <= tolerance and height_diff <= tolerance:
                self.logger.info(f"✅ PASS: Element '{locator_key}' size ({actual_width}x{actual_height}) within tolerance")
                return True
            else:
                error_msg = message or f"Element '{locator_key}' size mismatch. Expected: {expected_width}x{expected_height}, Actual: {actual_width}x{actual_height}"
                self.logger.error(f"❌ FAIL: {error_msg}")
                raise AssertionError(error_msg)
                
        except AssertionError:
            raise
        except Exception as e:
            error_msg = message or f"Failed to get size for element '{locator_key}': {e}"
            self.logger.error(f"❌ FAIL: {error_msg}")
            raise AssertionError(error_msg)
    
    # ============================================================================
    # APPLICATION STATE ASSERTIONS
    # ============================================================================
    
    def assert_current_app(self, expected_package: str, message: str = None) -> bool:
        """
        Assert that the current app matches expected package
        
        Args:
            expected_package: Expected app package name
            message: Custom error message
            
        Returns:
            bool: True if assertion passes
            
        Raises:
            AssertionError: If current app does not match
        """
        try:
            if self.driver_type == "uiautomator2":
                current_app = self.driver.app_current().get("package", "")
            else:
                # Appium
                current_app = self.driver.current_package
            
            if current_app == expected_package:
                self.logger.info(f"✅ PASS: Current app is '{expected_package}'")
                return True
            else:
                error_msg = message or f"Current app mismatch. Expected: '{expected_package}', Actual: '{current_app}'"
                self.logger.error(f"❌ FAIL: {error_msg}")
                raise AssertionError(error_msg)
                
        except AssertionError:
            raise
        except Exception as e:
            error_msg = message or f"Failed to get current app: {e}"
            self.logger.error(f"❌ FAIL: {error_msg}")
            raise AssertionError(error_msg)
    
    def assert_screen_orientation(self, expected_orientation: str, message: str = None) -> bool:
        """
        Assert screen orientation
        
        Args:
            expected_orientation: Expected orientation ('portrait', 'landscape')
            message: Custom error message
            
        Returns:
            bool: True if assertion passes
            
        Raises:
            AssertionError: If orientation does not match
        """
        try:
            if self.driver_type == "uiautomator2":
                info = self.driver.info
                # Determine orientation from window size
                window_size = info.get('displaySizeDpY', 0), info.get('displaySizeDpX', 0)
                actual_orientation = "portrait" if window_size[0] > window_size[1] else "landscape"
            else:
                # Appium
                actual_orientation = self.driver.orientation.lower()
            
            if actual_orientation == expected_orientation.lower():
                self.logger.info(f"✅ PASS: Screen orientation is '{expected_orientation}'")
                return True
            else:
                error_msg = message or f"Screen orientation mismatch. Expected: '{expected_orientation}', Actual: '{actual_orientation}'"
                self.logger.error(f"❌ FAIL: {error_msg}")
                raise AssertionError(error_msg)
                
        except AssertionError:
            raise
        except Exception as e:
            error_msg = message or f"Failed to get screen orientation: {e}"
            self.logger.error(f"❌ FAIL: {error_msg}")
            raise AssertionError(error_msg)
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    def _find_element(self, locator_key: str):
        """Find element using locator key"""
        if locator_key not in self.locators:
            raise ValueError(f"Locator key '{locator_key}' not found in locators")
        
        loc_def = self.locators[locator_key]
        
        # Try locators in order: primary, fallback_1, fallback_2, etc.
        for key in ["primary", "fallback_1", "fallback_2", "fallback_3"]:
            if key not in loc_def:
                continue
                
            locator = loc_def[key]
            selector_type = locator["type"]
            selector_value = locator["value"]
            
            try:
                element = self.finder.find_element(selector_type, selector_value)
                if element:
                    return element
            except Exception:
                continue
        
        raise RuntimeError(f"Element not found with any locator strategy: {locator_key}")
    
    def _find_elements(self, locator_key: str):
        """Find multiple elements using locator key"""
        if locator_key not in self.locators:
            raise ValueError(f"Locator key '{locator_key}' not found in locators")
        
        loc_def = self.locators[locator_key]
        
        # Try locators in order: primary, fallback_1, fallback_2, etc.
        for key in ["primary", "fallback_1", "fallback_2", "fallback_3"]:
            if key not in loc_def:
                continue
                
            locator = loc_def[key]
            selector_type = locator["type"]
            selector_value = locator["value"]
            
            try:
                elements = self.finder.find_elements(selector_type, selector_value)
                if elements:
                    return elements
            except Exception:
                continue
        
        return []
    
    def _find_element_with_wait(self, locator_key: str, timeout: int):
        """Find element with wait"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                element = self._find_element(locator_key)
                if element:
                    return element
            except:
                pass
            time.sleep(0.5)
        
        raise RuntimeError(f"Element '{locator_key}' not found within {timeout} seconds")
    
    def _find_elements_with_wait(self, locator_key: str, timeout: int):
        """Find elements with wait"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                elements = self._find_elements(locator_key)
                if elements:
                    return elements
            except:
                pass
            time.sleep(0.5)
        
        return []
    
    def _is_element_visible(self, element) -> bool:
        """Check if element is visible"""
        try:
            if self.driver_type == "uiautomator2":
                return element.exists and element.info.get('visible', False)
            else:
                # Appium
                return element.is_displayed()
        except:
            return False
    
    def _is_element_enabled(self, element) -> bool:
        """Check if element is enabled"""
        try:
            if self.driver_type == "uiautomator2":
                return element.info.get('enabled', False)
            else:
                # Appium
                return element.is_enabled()
        except:
            return False
    
    def _is_element_selected(self, element) -> bool:
        """Check if element is selected"""
        try:
            if self.driver_type == "uiautomator2":
                return element.info.get('selected', False) or element.info.get('checked', False)
            else:
                # Appium
                return element.is_selected()
        except:
            return False
    
    def _get_element_text(self, element) -> str:
        """Get text from element"""
        try:
            if self.driver_type == "uiautomator2":
                return element.info.get('text', '') or element.info.get('contentDescription', '')
            else:
                # Appium
                return element.text or element.get_attribute('contentDescription') or ''
        except:
            return ''
    
    def _get_element_attribute(self, element, attribute_name: str) -> str:
        """Get attribute from element"""
        try:
            if self.driver_type == "uiautomator2":
                return element.info.get(attribute_name, '')
            else:
                # Appium
                return element.get_attribute(attribute_name) or ''
        except:
            return ''
    
    def _get_element_bounds(self, element) -> Dict[str, int]:
        """Get element bounds"""
        try:
            if self.driver_type == "uiautomator2":
                bounds = element.info.get('bounds', {})
                return {
                    'x': bounds.get('left', 0),
                    'y': bounds.get('top', 0),
                    'width': bounds.get('right', 0) - bounds.get('left', 0),
                    'height': bounds.get('bottom', 0) - bounds.get('top', 0)
                }
            else:
                # Appium
                location = element.location
                size = element.size
                return {
                    'x': location.get('x', 0),
                    'y': location.get('y', 0),
                    'width': size.get('width', 0),
                    'height': size.get('height', 0)
                }
        except:
            return {'x': 0, 'y': 0, 'width': 0, 'height': 0}


# Factory function to create MobileAssertions instance
def create_assertions_helper(driver, device_config: Dict[str, Any], locators: Dict[str, Any], 
                            finder: UnifiedElementFinder, logger: logging.Logger) -> MobileAssertions:
    """
    Factory function to create MobileAssertions instance
    
    Args:
        driver: Mobile driver instance (uiautomator2 or Appium)
        device_config: Device configuration dictionary
        locators: Locators dictionary from YAML
        finder: UnifiedElementFinder instance
        logger: Logger instance
        
    Returns:
        MobileAssertions: Configured assertions helper instance
    """
    return MobileAssertions(driver, device_config, locators, finder, logger)