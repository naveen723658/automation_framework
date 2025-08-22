from typing import Optional
from .base import BaseAssertions, AssertionError


class TextAssertions(BaseAssertions):
    """
    Text-related assertion methods for mobile test automation
    
    Provides functionality to:
    - Assert exact text matches
    - Assert text contains specific content
    - Assert text starts/ends with specific content  
    - Assert text does not contain unwanted content
    """
    
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
                error_msg = message or (f"Element '{locator_key}' text mismatch. "
                                      f"Expected: '{expected_text}', Actual: '{actual_text}'")
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
                error_msg = message or (f"Element '{locator_key}' text does not contain '{expected_text}'. "
                                      f"Actual text: '{actual_text}'")
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
                error_msg = message or (f"Element '{locator_key}' text contains unwanted text '{unwanted_text}'. "
                                      f"Actual text: '{actual_text}'")
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
                error_msg = message or (f"Element '{locator_key}' text does not start with '{prefix}'. "
                                      f"Actual text: '{actual_text}'")
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
                error_msg = message or (f"Element '{locator_key}' text does not end with '{suffix}'. "
                                      f"Actual text: '{actual_text}'")
                self.logger.error(f"❌ FAIL: {error_msg}")
                raise AssertionError(error_msg)
                
        except AssertionError:
            raise
        except Exception as e:
            error_msg = message or f"Failed to get text from element '{locator_key}': {e}"
            self.logger.error(f"❌ FAIL: {error_msg}")
            raise AssertionError(error_msg)