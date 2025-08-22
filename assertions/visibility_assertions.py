import time
from .base import BaseAssertions, AssertionError


class VisibilityAssertions(BaseAssertions):
    """
    Visibility and existence assertion methods for mobile test automation
    with integrated swipe support using GestureActions.
    """

    def assert_visible(self, configs) -> bool:
        """Assert that an element is visible on screen (with optional swipe)."""
        try:
            cfg = self._validate_configs(configs)
            swipe, expected, timeout = cfg["swipe"], cfg["target"], cfg["timeout"]

            # Try without swipe first
            try:
                element = self._find_element_with_wait(expected, timeout // 2)
                if element and self._is_element_visible(element):
                    self.logger.info(f"✅ PASS: Element '{expected}' is visible")
                    return True
            except Exception:
                self.logger.debug(f"Element '{expected}' not found in first attempt")

            # Try swipe if any
            if swipe:
                if self.actions.swipe_until_visible(cfg, cfg):
                    element = self._find_element_with_wait(expected, timeout // 2)
                    if element and self._is_element_visible(element):
                        self.logger.info(f"✅ PASS: Element '{expected}' is visible (after swipe)")
                        return True

            msg = cfg.get("message") or f"Element '{expected}' is not visible"
            self.logger.error(f"❌ FAIL: {msg}")
            raise AssertionError(msg)

        except AssertionError:
            raise
        except Exception as e:
            msg = f"Element '{configs.get('target')}' not found or not visible: {e}"
            self.logger.error(f"❌ FAIL: {msg}")
            raise AssertionError(msg)

    def assert_not_visible(self, configs) -> bool:
        """Assert that an element is not visible (with optional swipe to confirm)."""
        try:
            cfg = self._validate_configs(configs)
            swipe, expected, timeout = cfg["swipe"], cfg["target"], cfg["timeout"]

            # Swipe check first (try to bring it into view, if not found then pass)
            if swipe:
                if cfg.get("direction") and not self.actions.swipe_until_visible(cfg, cfg):
                    self.logger.info(f"✅ PASS: Element '{expected}' is not visible (not found after swipe)")
                    return True

            # Wait until it becomes invisible
            start = time.time()
            while time.time() - start < timeout:
                try:
                    element = self._find_element(expected)
                    if not self._is_element_visible(element):
                        self.logger.info(f"✅ PASS: Element '{expected}' is not visible")
                        return True
                except Exception:
                    self.logger.info(f"✅ PASS: Element '{expected}' is not visible")
                    return True
                time.sleep(0.5)

            msg = cfg.get("message") or f"Element '{expected}' is still visible"
            self.logger.error(f"❌ FAIL: {msg}")
            raise AssertionError(msg)

        except AssertionError:
            raise
        except Exception:
            self.logger.info(f"✅ PASS: Element '{configs.get('target')}' is not visible")
            return True

    def assert_exists(self, configs) -> bool:
        """Assert that an element exists in DOM (with optional swipe)."""
        try:
            cfg = self._validate_configs(configs)
            swipe, expected, timeout = cfg["swipe"], cfg["target"], cfg["timeout"]

            # Try without swipe first
            try:
                self._find_element_with_wait(expected, timeout // 2)
                self.logger.info(f"✅ PASS: Element '{expected}' exists")
                return True
            except Exception:
                self.logger.debug(f"Element '{expected}' not found initially")

            # Try swipe
            if swipe:
                if self.actions.swipe_until_visible(cfg, cfg):
                    self._find_element_with_wait(expected, timeout // 2)
                    self.logger.info(f"✅ PASS: Element '{expected}' exists (after swipe)")
                    return True

            msg = cfg.get("message") or f"Element '{expected}' does not exist"
            self.logger.error(f"❌ FAIL: {msg}")
            raise AssertionError(msg)

        except AssertionError:
            raise

    def assert_not_exists(self, configs) -> bool:
        """Assert that an element does not exist in DOM (with optional swipe)."""
        try:
            cfg = self._validate_configs(configs)
            swipe, expected, timeout = cfg["swipe"], cfg["target"], cfg["timeout"]

            # Try swipe first to confirm it's not on screen
            if swipe:
                if self.actions.swipe_until_visible(cfg, cfg):
                    msg = cfg.get("message") or f"Element '{expected}' still exists after swipe"
                    self.logger.error(f"❌ FAIL: {msg}")
                    raise AssertionError(msg)

            # Wait until not found
            start = time.time()
            while time.time() - start < timeout:
                try:
                    self._find_element(expected)
                    time.sleep(0.5)
                except Exception:
                    self.logger.info(f"✅ PASS: Element '{expected}' does not exist")
                    return True

            msg = cfg.get("message") or f"Element '{expected}' still exists"
            self.logger.error(f"❌ FAIL: {msg}")
            raise AssertionError(msg)

        except AssertionError:
            raise
        except Exception:
            self.logger.info(f"✅ PASS: Element '{configs.get('target')}' does not exist")
            return True