# core/actions.py
import time, subprocess, re

class Actions:
    def __init__(self, driver, device_config, finder, logger, helpers):
        self.d = driver
        self.device_id = device_config["udid"]
        self.finder = finder
        self.logger = logger
        self.helpers = helpers

    def launch_app(self, params, config, driver_type):
        pkg = params["app_package"]

        if config.get("force_stop", False):
            self.logger.debug(f"Force stopping {pkg}")
            self.d.app_stop(pkg) if driver_type=="uiautomator2" else self.d.terminate_app(pkg)

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
        self.d.app_start(pkg, wait=True) if driver_type=="uiautomator2" else self.d.activate_app(pkg)
        
        # handle assertions
        assertion = next((a for a in config.get("assertions", []) if a.get("type") == "app_launched"), None)
        if assertion:
            expected_pkg = assertion["expected"]

            try:
                # Use dumpsys recents to get the most recent tasks
                cmd = ["adb", "-s", self.device_id, "shell", "dumpsys", "activity", "recents"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                lines = [line.strip() for line in result.stdout.splitlines() if "Recent #" in line]

                recent_packages = []
                for line in lines:
                    match = re.search(r"A=\d+:([a-zA-Z0-9_.]+)", line)
                    if match:
                        recent_packages.append(match.group(1))

                self.logger.debug(f"Recent apps: {recent_packages[:5]}{'...' if len(recent_packages)>5 else ''}")

                if expected_pkg not in recent_packages:
                    raise RuntimeError(
                        f"Expected app '{expected_pkg}' not in recents. Found: {recent_packages[:3]}..."
                    )
            except Exception as e:
                self.logger.error(f"App launch verification failed: {e}")
                raise
        time.sleep(2)

    def click(self, locator_key, loc_yaml):
        loc_def = loc_yaml[locator_key]
        for key in ["primary", "fallback_1", "fallback_2"]:
            if key in loc_def:
                try:
                    element = self.finder.find_element(loc_def[key]["type"], loc_def[key]["value"])
                    self.logger.debug(f"Element found: {element}")
                    time.sleep(1)
                    element.click()
                    return
                except Exception as e:
                    self.logger.warning(f"Click failed with {key}: {e}")
        raise RuntimeError(f"Element not found for {locator_key}")
