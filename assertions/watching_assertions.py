import time
from .base import BaseAssertions, AssertionError


class WatchingAssertions(BaseAssertions):
    """
    Continuous element watching assertion methods for mobile test automation
    
    Provides functionality to:
    - Wait for elements to appear continuously
    - Monitor element state changes over time
    - Assert element appearance within timeout periods
    """
    
    def assert_element_appears(self, expected: str, timeout: int = 30, check_interval: float = 0.5) -> bool:

        """
        Continuously watch for an element to appear within the specified timeout
        
        Args:
            expected: locator Key to find element in locators dictionary
            timeout: Maximum time to wait for element to appear (seconds)
            check_interval: Time between checks (seconds)
            
        Returns:
            bool: True if element appears within timeout
            
        Raises:
            AssertionError: If element does not appear within timeout
        """
        start_time = time.time()
        elapsed_time = 0
        check_count = 0
        
        self.logger.debug(f"Starting continuous watch for element '{expected}' "
                        f"(timeout: {timeout}s, interval: {check_interval}s)")
        
        while elapsed_time < timeout:
            check_count += 1
            try:
                # Try to find the element
                element = self._find_element(expected)
                if element and self._is_element_visible(element):
                    elapsed_time = time.time() - start_time
                    self.logger.info(f"✅ PASS: Element '{expected}' appeared after "
                                f"{elapsed_time:.2f}s ({check_count} checks)")
                    return True
                    
            except Exception as e:
                # Element not found or not visible yet, continue watching
                continue
            
            # Wait before next check
            time.sleep(check_interval)
            elapsed_time = time.time() - start_time
        
        # Element did not appear within timeout
        error_msg = (f"Element '{expected}' did not appear within "f"{timeout}s (checked {check_count} times)")
        self.logger.debug(f"assertion failed: {error_msg}")
        raise AssertionError(error_msg)