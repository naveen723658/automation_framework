from typing import Optional
from .base import BaseAssertions, AssertionError


class AttributeAssertions(BaseAssertions):
    """
    Attribute assertion methods for mobile test automation
    
    Provides functionality to:
    - Assert attribute values match expected values
    - Assert attribute contains specific content
    - Validate element properties and attributes
    """
    
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
                self.logger.info(f"✅ PASS: Element '{locator_key}' attribute '{attribute_name}' "
                               f"equals '{expected_value}'")
                return True
            else:
                error_msg = message or (f"Element '{locator_key}' attribute '{attribute_name}' mismatch. "
                                      f"Expected: '{expected_value}', Actual: '{actual_value}'")
                self.logger.error(f"❌ FAIL: {error_msg}")
                raise AssertionError(error_msg)
                
        except AssertionError:
            raise
        except Exception as e:
            error_msg = message or (f"Failed to get attribute '{attribute_name}' "
                                  f"from element '{locator_key}': {e}")
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
                self.logger.info(f"✅ PASS: Element '{locator_key}' attribute '{attribute_name}' "
                               f"contains '{expected_value}'")
                return True
            else:
                error_msg = message or (f"Element '{locator_key}' attribute '{attribute_name}' "
                                      f"does not contain '{expected_value}'. Actual: '{actual_value}'")
                self.logger.error(f"❌ FAIL: {error_msg}")
                raise AssertionError(error_msg)
                
        except AssertionError:
            raise
        except Exception as e:
            error_msg = message or (f"Failed to get attribute '{attribute_name}' "
                                  f"from element '{locator_key}': {e}")
            self.logger.error(f"❌ FAIL: {error_msg}")
            raise AssertionError(error_msg)