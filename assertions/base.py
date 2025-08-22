import time
import re
import json
import subprocess
import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from datetime import datetime
from scripts.selector_transformer import UnifiedElementFinder, MobileSelectorTransformer


class AssertionError(Exception):
    """Custom assertion error for mobile test assertions"""
    pass


class BaseAssertions:   
    def __init__(self, driver, device_config, finder: UnifiedElementFinder, logger, locators, actions, helpers):
        self.driver = driver
        self.device_config = device_config
        self.locators = locators
        self.finder = finder
        self.logger = logger
        self.driver_type = device_config.get("driver", "uiautomator2")
        self.actions = actions
        self.helpers = helpers
    
    # ============================================================================
    # Common Config Validator
    # ============================================================================
    def _validate_configs(self, configs):
        """Merge params and configs with defaults for swipe actions"""
        return {
            "swipe": configs.get("swipe", False),
            "target": configs.get("expected") or configs.get("target"),
            "selector": configs.get("selector") or configs.get("locator_id"),
            # "parent_selector": configs.get("parent_selector"),
            # "child_selector": configs.get("child_selector"),
            "expected_count": configs.get("expected_count"),

            # General swipe configs
            "direction": configs.get("direction", "up"),
            "fallback_direction": configs.get("fallback_direction", ""),
            "max_swipe": configs.get("max_swipe", 10),
            "distance": configs.get("distance", 0.7),
            "count": configs.get("count", 1),
            "timeout": configs.get("timeout", 10),
            "message": configs.get("message"),
        }

    # ============================================================================
    # ELEMENT FINDING UTILITIES
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
        
    
    # ============================================================================
    # ELEMENT STATE UTILITIES
    # ============================================================================
    
    def _is_element_visible(self, element) -> bool:
        """Check if element is visible"""
        try:
            if self.driver_type == "uiautomator2":
                return element.exists and element.info.get('visibleToUser', False)
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
    
    # ============================================================================
    # ELEMENT DATA UTILITIES
    # ============================================================================
    
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