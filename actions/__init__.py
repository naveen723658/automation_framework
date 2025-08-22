# actions/__init__.py
from .gestures import GestureActions


class Actions(GestureActions):
    def __init__(self, driver, device_config, finder, logger, helpers, locators):
        super().__init__(driver, device_config, finder, logger, helpers, locators)