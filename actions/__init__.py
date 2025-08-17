# actions/__init__.py

from .base import BaseActions
from .gestures import GestureActions


class Actions(BaseActions, GestureActions):
    def __init__(self, driver, device_config, finder, logger, helpers, locators):
        BaseActions.__init__(self, driver, device_config, finder, logger, helpers, locators)
        GestureActions.__init__(self, driver, device_config, finder, logger, helpers, locators)