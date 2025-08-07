# core/driver_manager.py
import time
import uiautomator2 as u2
from appium import webdriver
from appium.options.android import UiAutomator2Options

class DriverManager:
    @staticmethod
    def initialize_driver(device_config, logger):
        driver_type = device_config.get("driver", "").lower()

        if driver_type == "uiautomator2":
            try:
                d = u2.connect(device_config["udid"])
                if not d:
                    raise RuntimeError(f"Failed to connect to device {device_config['udid']}")
                time.sleep(2)  # wait for the device to be ready
                logger.debug(f"Connected to uiautomator2 device {device_config['udid']}")
                return d
            except Exception as e:
                raise RuntimeError(f"Failed to initialize uiautomator2 driver: {e}")

        elif driver_type == "appium":
            try:
                options = UiAutomator2Options()
                for k, v in device_config.get("capabilities", {}).items():
                    options.set_capability(k, v)
                d = webdriver.Remote(device_config.get("server_url", "http://localhost:4723"), options=options)
                logger.debug(f"Appium driver initialized for {device_config['udid']}")
                return d
            except Exception as e:
                raise RuntimeError(f"Failed to initialize Appium driver: {e}")
        else:
            raise RuntimeError(f"Unsupported driver type: {driver_type}")

    @staticmethod
    def cleanup_driver(driver, device_config, logger):
        try:
            if device_config["driver"] == "appium" and driver:
                driver.quit()
                logger.debug("Appium driver session closed")
        except Exception as e:
            logger.error(f"Error during driver cleanup: {e}")
