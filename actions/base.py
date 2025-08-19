# actions/base.py
import time, subprocess, re

class BaseActions:
    def __init__(self, driver, device_config, finder, logger, helpers, locators):
        self.d = driver
        self.device_id = device_config["udid"]
        self.driver_type = device_config["driver"]
        self.finder = finder
        self.logger = logger
        self.helpers = helpers
        self.locators = locators

    def launch_app(self, params, config):
        pkg = params["app_package"]

        if config.get("force_stop", False):
            self.logger.debug(f"Force stopping {pkg}")
            self.d.app_stop(pkg) if self.driver_type=="uiautomator2" else self.d.terminate_app(pkg)

        if config.get("clear_data", False):
            self.logger.debug(f"Clearing data for {pkg} using ADB")
            cmd = ["adb", "-s", self.device_id, "shell", "pm", "clear", pkg]
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode != 0 or "Success" not in result.stdout:
                    self.logger.error(f"Failed to clear data for {pkg}: {result.stderr.strip()} {result.stdout.strip()}")
                    raise RuntimeError(f"Failed to clear data for {pkg}")
                else:
                    self.logger.debug(f"Data cleared for {pkg}")
            except subprocess.TimeoutExpired:
                self.logger.error(f"Timeout while clearing data for {pkg}")
                raise
            
        
        # launch app
        self.logger.debug(f"Launching {pkg}")
        self.d.app_start(pkg, wait=True) if self.driver_type=="uiautomator2" else self.d.activate_app(pkg)            

    def click(self, locator_key, configs=None):
        loc_def = self.locators[locator_key]
        for key in ["primary", "fallback_1", "fallback_2"]:
            if key in loc_def:
                try:
                    element = self.finder.find_element(loc_def[key]["type"], loc_def[key]["value"])
                    time.sleep(1)
                    self.logger.debug(f"Element found: {element}")
                    element.click()
                    return
                except Exception as e:
                    self.logger.debug(f"Click failed with {key}: {e}")
                    if configs and configs.get("ignore", False):
                        self.logger.warning(f"Element {locator_key} not found, but ignoring due to config")
                        return
            raise RuntimeError(f"Element not found for {locator_key}")