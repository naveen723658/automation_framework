from typing import Optional
from .base import BaseAssertions, AssertionError


class PositionSizeAssertions(BaseAssertions):
    """
    Position and size assertion methods for mobile test automation
    
    Provides functionality to:
    - Assert element position coordinates
    - Assert element dimensions (width/height)
    - Validate element bounds and layout
    """
    
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
                self.logger.info(f"✅ PASS: Element '{locator_key}' position ({actual_x}, {actual_y}) "
                               f"within tolerance")
                return True
            else:
                error_msg = message or (f"Element '{locator_key}' position mismatch. "
                                      f"Expected: ({expected_x}, {expected_y}), "
                                      f"Actual: ({actual_x}, {actual_y})")
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
                self.logger.info(f"✅ PASS: Element '{locator_key}' size ({actual_width}x{actual_height}) "
                               f"within tolerance")
                return True
            else:
                error_msg = message or (f"Element '{locator_key}' size mismatch. "
                                      f"Expected: {expected_width}x{expected_height}, "
                                      f"Actual: {actual_width}x{actual_height}")
                self.logger.error(f"❌ FAIL: {error_msg}")
                raise AssertionError(error_msg)
                
        except AssertionError:
            raise
        except Exception as e:
            error_msg = message or f"Failed to get size for element '{locator_key}': {e}"
            self.logger.error(f"❌ FAIL: {error_msg}")
            raise AssertionError(error_msg)