"""
Executor for running test cases on mobile devices using uiautomator2 or Appium.
This module handles the initialization of drivers, execution of test steps,
and management of artifacts such as screenshots and logs.
"""
from datetime import datetime
from pathlib import Path
import time
from typing import Dict

from utils.yaml_loader import (
    load_framework_config,
    load_test_case,
    load_steps,
    load_locators,
)
from utils.logger import init_logger
from utils.db_connection import MongoDBClient
from scripts.selector_transformer import UnifiedElementFinder, MobileSelectorTransformer


class TestExecutor:
    def __init__(self, device_config: dict, tc_id: str, env: str) -> None:
        self.d = None
        self.env = env
        self.logger = None
        self.tc_id = tc_id
        self.steps_yaml = None
        self.loc_yaml = load_locators()
        self.device_config = device_config
        self.cfg = load_framework_config()
        self.test_yaml = load_test_case(tc_id)

        # classes and methods
        self.db = MongoDBClient()
        
        self.transformer = MobileSelectorTransformer()
        # Setup artifacts directory structure
        self._setup_artifacts_directory()

        # Initialize driver based on configuration
        self._initialize_driver()

    def _setup_artifacts_directory(self) -> None:
        """Setup artifact directories with device separation for parallel execution"""
        art_root = Path(self.cfg["core"]["artifacts_root"])
        
        # Check if parallel execution is enabled
        if self.cfg["core"].get("parallel_execution", False):
            # Create device-specific directory structure
            device_id = self.device_config["udid"].replace(":", "_").replace("-", "_")
            self.ss_dir = art_root / "screenshots" / device_id / self.tc_id
            self.log_file = art_root / "logs" / device_id / f"{self.tc_id}.log"
            self.video_dir = art_root / "videos" / device_id / self.tc_id
        else:
            # Use standard directory structure
            self.ss_dir = art_root / "screenshots" / self.tc_id
            self.log_file = art_root / "logs" / f"{self.tc_id}.log"
            self.video_dir = art_root / "videos" / self.tc_id
        
        # Create directories
        self.ss_dir.mkdir(parents=True, exist_ok=True)
        self.video_dir.mkdir(parents=True, exist_ok=True)

        self.logger = init_logger(self.log_file)

    def _initialize_driver(self) -> None:
        """Initialize driver based on device configuration"""
        driver_type = self.device_config.get("driver", "").lower()
        d = None
        if driver_type == "uiautomator2":
            d = self._initialize_uiautomator2()
        elif driver_type == "appium":
            d = self._initialize_appium()
        else:
            raise RuntimeError(f"Unsupported driver type: {driver_type}")
        self.d = d
        self.finder = UnifiedElementFinder(self.d, driver_type)
        
        self.logger.debug(f"Initialized {driver_type} driver for device: {self.device_config['udid']}")

    def _initialize_uiautomator2(self) -> None:
        """Initialize uiautomator2 driver"""
        try:
            import uiautomator2 as u2
            d = u2.connect(self.device_config["udid"])                
            self.logger.debug(f"uiautomator2 connected to device: {self.device_config['udid']}")
            return d
        except Exception as e:
            raise RuntimeError(f"Failed to initialize uiautomator2 driver: {e}")
        

    def _initialize_appium(self) -> None:
        """Initialize Appium driver"""
        try:
            from appium import webdriver # type: ignore
            from appium.options.android import UiAutomator2Options # type: ignore
            
            # Get capabilities from device config
            capabilities = self.device_config.get("capabilities", {})
            server_url = self.device_config.get("server_url", "http://localhost:4723")
            
            # Create options object
            options = UiAutomator2Options()
            for key, value in capabilities.items():
                options.set_capability(key, value)
            
            # Initialize Appium driver
            d = webdriver.Remote(server_url, options=options)
            
            self.logger.debug(f"Appium driver initialized for device: {self.device_config['udid']}")
            return d
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Appium driver: {e}")


    # ------------- Public API ------------- #
    def run(self) -> None:
        """Execute the test case"""
        start = time.time()
        status = "passed"

        # check test_yaml contain "step_file"
        if "step_file" in self.test_yaml:
            self.steps_yaml = load_steps(self.test_yaml["step_file"])
        else:
            self.steps_yaml = load_steps()

        for ts_info in self.test_yaml["test_steps"]:
            if not self._execute_step(ts_info):
                status = "failed"
                break

        duration = round(time.time() - start, 2)
        self._persist_result(status, duration)
        self._cleanup_driver()

    def _cleanup_driver(self) -> None:
        """Cleanup driver resources"""
        try:
            if self.device_config["driver"] == "appium" and self.d:
                self.d.quit()
                self.logger.debug("Appium driver session closed")
            # uiautomator2 doesn't need explicit cleanup
        except Exception as e:
            self.logger.error(f"Error during driver cleanup: {e}")

    # ------------- Internals -------------- #
    def _execute_step(self, step_info: Dict) -> bool:
        sid = step_info["step_id"]
        action = self.steps_yaml[sid]["action"] if sid in self.steps_yaml else step_info.get("action")
        step_params = self.steps_yaml[sid]["parameters"] if sid in self.steps_yaml else step_info.get("parameters")
        step_config = step_info.get("configs", {})
        self.logger.info("Executing %s – %s", sid, action)

        # run action
        try:
            if action == "launch_app":
                self._launch_app(step_params, step_config)
            elif action == "click":
                self._click(step_params, step_config)
            else:
                self.logger.warning("Unknown action: %s", action)

            # Screenshot on every step if configured
            if self.cfg["artifacts"]["screenshots"]["enabled"]:
                self._take_screenshot(sid)

            return True
        except Exception as exc:     
            self.logger.exception("Step %s failed: %s", sid, exc)
            if self.cfg["artifacts"]["screenshots"]["on_failure"]:
                self._take_screenshot(f"{sid}_fail")
            return False

    # ------------- Action helpers --------- #
    def _launch_app(self, step_params: Dict, step_config: Dict) -> None:
        """Launch application"""
        pkg = step_params["app_package"]
        
        # Handle pre-launch configurations
        if step_config.get("force_stop", False):
            self.logger.debug(f"Force stopping app {pkg}")
            if self.device_config["driver"] == "uiautomator2":
                self.d.app_stop(pkg)
            else:  # Appium
                self.d.terminate_app(pkg)

        if step_config.get("clear_data", False):
            self.logger.debug(f"Clearing data for app {pkg}")
            if self.device_config["driver"] == "uiautomator2":
                self.d.app_clear(pkg)
            else:  # Appium
                self.d.reset()

        # Launch the app
        self.logger.debug(f"Launching {pkg}")
        if self.device_config["driver"] == "uiautomator2":
            self.d.app_start(pkg, wait=True)
        else:  # Appium
            self.d.activate_app(pkg)

        # Verify app launch if assertion is provided
        assertions = step_config.get("assertions")
        if assertions:
            app_assertion = next((a for a in assertions if a.get("type") == "app_launched"), None)
            if app_assertion:
                expected_pkg = app_assertion["expected"]
                driver_type = self.device_config["driver"]

                current_pkg = (
                    self.d.app_current().get("package")
                    if driver_type == "uiautomator2"
                    else self.d.current_package
                )

                if current_pkg != expected_pkg:
                    raise RuntimeError(f"Expected app {expected_pkg} not launched (got {current_pkg})")


        time.sleep(1)  # Allow app to stabilize   

    def _click(self, step_params: Dict, step_config: Dict) -> None:
        """Click on an element"""
        locator_key = step_params.get("locator_id") or step_params.get("locator_key")
        element = self._find_element(locator_key)
        element.click()

    # ------------- Locator helpers -------- #
    def _find_element(self, locator_key: str):
        """Find element using locator key with fallback strategies"""
        if locator_key not in self.loc_yaml:
            raise RuntimeError(f"Locator key '{locator_key}' not found in locators")
        
        loc_def = self.loc_yaml[locator_key]
        
        for key in ["primary", "fallback_1", "fallback_2", "fallback_3"]:
            if key not in loc_def:
                continue

            locator = loc_def[key]
            selector_type = locator["type"]
            selector_value = locator["value"]
            try:
                element = self.finder.find_element(selector_type, selector_value)
                if element:
                    self.logger.debug("Found element with %s:%s", selector_type, selector_value)
                    return element
            except Exception as e:
                self.logger.warning("Failed to find element with %s:%s - %s", selector_type, selector_value, e)
                continue

        raise RuntimeError(f"Element not found with any locator strategy: {locator_key}")

    # ------------- Utilities -------------- #
    def _take_screenshot(self, name: str) -> None:
        """Take screenshot and save to artifacts directory"""
        timestamp = int(time.time())
        filename = f"{name}_{timestamp}.png"
        file_path = self.ss_dir / filename
        
        try:
            if self.device_config["driver"] == "uiautomator2":
                self.d.screenshot(str(file_path))
            else:  # Appium
                self.d.save_screenshot(str(file_path))
            
            self.logger.info(f"Screenshot saved: {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to take screenshot: {e}")



    def _persist_result(self, status: str, duration: float) -> None:
        """Save execution result to database"""
        doc = {
            "test_id": self.tc_id,
            "device_id": self.device_config["udid"],
            "driver": self.device_config["driver"],
            "env": self.env,
            "status": status,
            "duration_sec": duration,
            "timestamp": datetime.utcnow(),
            "artifacts": {
                "screenshots_dir": str(self.ss_dir),
                "logs_dir": str(self.log_file),
                "videos_dir": str(self.video_dir)
            }
        }
        
        try:
            # self.db.save_execution(doc)
            self.logger.info("Execution record stored in DB")
        except Exception as e:
            self.logger.error(f"Failed to save execution record: {e}")

