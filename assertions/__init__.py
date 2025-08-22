# assertions/__init__.py

# Import all assertion classes
from .base import AssertionError
from .event_assertions import EventAssertions
from .app_state_assertions import AppStateAssertions
from .watching_assertions import WatchingAssertions
from .visibility_assertions import VisibilityAssertions
from .text_assertions import TextAssertions
from .element_state_assertions import ElementStateAssertions
from .attribute_assertions import AttributeAssertions
from .styling_assertions import StylingAssertions
from .count_list_assertions import CountListAssertions
from .position_size_assertions import PositionSizeAssertions


class Assertions(
    EventAssertions,
    AppStateAssertions,
    WatchingAssertions,
    PositionSizeAssertions,

    VisibilityAssertions,
    TextAssertions,
    ElementStateAssertions,
    AttributeAssertions,
    StylingAssertions,
    CountListAssertions
):
    """
    This module provides a comprehensive assertion framework for mobile test automation.

    Args:
        driver: Mobile driver instance (uiautomator2 or Appium)
        device_config: Device configuration dictionary
        locators: Locators dictionary from YAML
        finder: UnifiedElementFinder instance
        logger: Logger instance

    Usage:
        from assertions import Assertions
        
        assertions = Assertions(driver, device_config, locators, finder, logger)
        assertions.assert_visible("login_button")
        assertions.assert_text_contains("welcome_message", "Hello")
        assertions.assert_enabled("submit_button")
    """    
    def __init__(self, driver, device_config, finder, logger, locators, actions: None, helpers: None):
        super().__init__(driver, device_config, finder, logger, locators, actions, helpers)



# Export the main class and factory function
__all__ = [
    'Assertions',
    'AssertionError', 
]