from typing import List, Optional
from .base import BaseAssertions, AssertionError


class CountListAssertions(BaseAssertions):
    """
    Count and list assertion methods for mobile test automation
    
    Provides functionality to:
    - Assert element counts
    - Assert minimum element counts
    - Assert list contains expected texts
    - Validate collections and arrays of elements
    """
    
    # def assert_element_count(self, configs) -> bool:
    #     """
    #     Assert the count of elements matching the locator
        
    #     Args:
    #         locator_key: Key to find elements in locators dictionary
    #         expected_count: Expected number of elements
    #         timeout: Maximum time to wait for elements
    #         message: Custom error message
            
    #     Returns:
    #         bool: True if assertion passes
            
    #     Raises:
    #         AssertionError: If element count does not match
    #     """
    #     try:
    #         cfg = self._validate_configs(configs)
    #         expected_count, swipe, expected, selector, timeout, max_swipe = cfg["expected_count"], cfg["swipe"], cfg["target"], cfg["selector"], cfg["timeout"], max_swipe["max_swipe"]

    #         collected = []
    #         # verify the parent or selector is present
    #         parent = self._find_element_with_wait(selector, timeout)
    #         if parent:
    #             # Try without swipe first
    #             try:
    #                 elements = self._find_elements_with_wait(expected, timeout // 2)
    #                 if elements:
    #                     collected.append(elements)
    #             except Exception:
    #                 self.logger.debug(f"Element '{expected}' not found in first attempt")


    #             if swipe:
    #                 for i in range(max_swipe):
    #                     if self.actions.swipe(cfg, cfg):
    #                         elements = self._find_elements_with_wait(expected, timeout // 2)
    #                         if elements:
    #                             collected.append(elements)

                            

    #             else:
    #                 return

    #         # Try swipe first if any
    #         if swipe:
    #             if self.actions.swipe_until_visible(cfg, cfg):
    #                 element = self._find_element_with_wait(expected, timeout // 2)
    #                 if element and self._is_element_visible(element):
    #                     self.logger.info(f"✅ PASS: Element '{expected}' is visible (after swipe)")
    #                     return True

    #         elements = self._find_elements_with_wait(locator_key, timeout)
    #         actual_count = len(elements)
            
    #         if actual_count == expected_count:
    #             self.logger.info(f"✅ PASS: Found {actual_count} elements matching '{locator_key}'")
    #             return True
    #         else:
    #             error_msg = message or (f"Element count mismatch for '{locator_key}'. "
    #                                   f"Expected: {expected_count}, Actual: {actual_count}")
    #             self.logger.error(f"❌ FAIL: {error_msg}")
    #             raise AssertionError(error_msg)
                
    #     except AssertionError:
    #         raise
    #     except Exception as e:
    #         error_msg = message or f"Failed to count elements for '{locator_key}': {e}"
    #         self.logger.error(f"❌ FAIL: {error_msg}")
    #         raise AssertionError(error_msg)
    
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
                self.logger.info(f"✅ PASS: Found {actual_count} elements matching '{locator_key}' "
                               f"(> {min_count})")
                return True
            else:
                error_msg = message or (f"Element count for '{locator_key}' is {actual_count}, "
                                      f"expected > {min_count}")
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
                error_msg = message or (f"Missing texts in list '{locator_key}': {missing_texts}. "
                                      f"Actual texts: {actual_texts}")
                self.logger.error(f"❌ FAIL: {error_msg}")
                raise AssertionError(error_msg)
                
        except AssertionError:
            raise
        except Exception as e:
            error_msg = message or f"Failed to check list contents for '{locator_key}': {e}"
            self.logger.error(f"❌ FAIL: {error_msg}")
            raise AssertionError(error_msg)