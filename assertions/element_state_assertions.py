from typing import Optional
from .base import BaseAssertions, AssertionError


class ElementStateAssertions(BaseAssertions):
    """
    Element state assertion methods for mobile test automation
    
    Provides functionality to:
    - Assert element is enabled/disabled
    - Assert element is selected/unselected
    - Assert element interaction states
    """
    
    def assert_enabled(self, configs) -> bool:
        """
        Assert that an element is enabled/clickable
        
        Args:
        configs
            locator_key: Key to find element in locators dictionary
            timeout: Maximum time to wait for element
            message: Custom error message
            
        Returns:
            bool: True if assertion passes
            
        Raises:
            AssertionError: If element is not enabled
        """
        try:
            cfg = self._validate_configs(configs)
            swipe, expected, timeout = cfg["swipe"], cfg["target"], cfg["timeout"]

            # Try without swipe first
            try:
                element = self._find_element_with_wait(expected, timeout)
                if element and self._is_element_enabled(element):
                    self.logger.info(f"✅ PASS: Element '{expected}' is enabled")
                    return True
            except Exception:
                self.logger.debug(f"Element '{expected}' not found in first attempt")

            # Try swipe if any
            if swipe:
                if self.actions.swipe_until_visible(cfg, cfg):
                    element = self._find_element_with_wait(expected, timeout)
                    if element and self._is_element_enabled(element):
                        self.logger.info(f"✅ PASS: Element '{expected}' is visible and enabled (after swipe)")
                        return True
        
            msg = cfg.get("message") or f"Element '{expected}' is not enabled"
            self.logger.error(f"❌ FAIL: {msg}")
            raise AssertionError(msg)
        except AssertionError:
            raise
        except Exception as e:
            msg = f"Failed to check if element  '{configs.get('target')}' is enabled: {e}"
            self.logger.error(f"❌ FAIL: {msg}")
            raise AssertionError(msg)
    
    def assert_disabled(self, configs) -> bool:
        """
        Assert that an element is disabled/not clickable
        
        Args: 
        configs
            locator_key: Key to find element in locators dictionary
            timeout: Maximum time to wait for element
            message: Custom error message
            
        Returns:
            bool: True if assertion passes
            
        Raises:
            AssertionError: If element is enabled
        """
        try:
            cfg = self._validate_configs(configs)
            swipe, expected, timeout = cfg["swipe"], cfg["target"], cfg["timeout"]

            # Try without swipe first
            try:
                element = self._find_element_with_wait(expected, timeout)
                if element and not self._is_element_enabled(element):
                    self.logger.info(f"✅ PASS: Element '{expected}' is disabled")
                    return True
            except Exception:
                self.logger.debug(f"Element '{expected}' not found in first attempt")

            # Try swipe if any
            if swipe:
                if self.actions.swipe_until_visible(cfg, cfg):
                    element = self._find_element_with_wait(expected, timeout)
                    if element and not self._is_element_enabled(element):
                        self.logger.info(f"✅ PASS: Element '{expected}' is visible and disabled (after swipe)")
                        return True
        
            msg = cfg.get("message") or f"Element '{expected}' is not disabled"
            self.logger.error(f"❌ FAIL: {msg}")
            raise AssertionError(msg)
        except AssertionError:
            raise
        except Exception as e:
            msg = f"Failed to check if element  '{configs.get('target')}' is disabled: {e}"
            self.logger.error(f"❌ FAIL: {msg}")
            raise AssertionError(msg)

    
    def assert_selected(self, locator_key: str, timeout: int = 10, message: str = None) -> bool:
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
    
    def assert_not_selected(self, locator_key: str, timeout: int = 10, message: str = None) -> bool:
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