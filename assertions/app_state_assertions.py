import re
import subprocess
from typing import Optional
from .base import BaseAssertions, AssertionError


class AppStateAssertions(BaseAssertions):
    """
    Application state assertion methods for mobile test automation
    
    Provides functionality to:
    - Assert current foreground application
    - Assert screen orientation
    - Validate application-level states and conditions
    """
    
    def assert_current_app(self, expected_package: str, ignore_interference: bool = False) -> bool:
        """
        Assert that the current app matches the expected package.
        Optionally ignore interference by checking recent apps.

        Args:
            expected_package (str): Expected app package name
            ignore_interference (bool): If True, ignores mismatch caused by popups or interference
                                        and verifies using recent apps list.

        Returns:
            bool: True if assertion passes

        Raises:
            AssertionError: If current app does not match and ignore_interference fails
        """
        try:
            # Get current foreground app
            if self.driver_type == "uiautomator2":
                current_app = self.driver.app_current().get("package", "")
            else:
                current_app = self.driver.current_package

            # Direct match check
            if current_app == expected_package:
                self.logger.info(f"✅ PASS: Current app is '{expected_package}'")
                return True

            # If mismatch and interference allowed → check recent apps
            if ignore_interference:
                self.logger.debug(
                    f"⚠ Current app '{current_app}' does not match '{expected_package}', "
                    f"checking recent apps due to interference..."
                )
                try:
                    cmd = ["adb", "-s", self.device_config["udid"], "shell", "dumpsys", "activity", "recents"]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                    lines = [line.strip() for line in result.stdout.splitlines() if "Recent #" in line]

                    recent_packages = []
                    for line in lines:
                        match = re.search(r"A=\d+:([a-zA-Z0-9_.]+)", line)
                        if match:
                            recent_packages.append(match.group(1))

                    self.logger.debug(
                        f"Recent apps: {recent_packages[:5]}{'...' if len(recent_packages) > 5 else ''}"
                    )

                    if expected_package in recent_packages:
                        self.logger.info(
                            f"✅ PASS: Expected app '{expected_package}' found in recent apps"
                        )
                        return True
                    else:
                        raise AssertionError(
                            f"Expected app '{expected_package}' not in recents. "
                            f"Found: {recent_packages[:3]}..."
                        )

                except Exception as e:
                    raise AssertionError(f"Interference check failed: {e}")

            # Fail if not ignoring interference and no match
            raise AssertionError(
                f"Current app mismatch. Expected: '{expected_package}', Actual: '{current_app}'"
            )

        except AssertionError:
            raise
        except Exception as e:
            raise AssertionError(f"Failed to get current app: {e}")

    
    def assert_screen_orientation(self, expected_orientation: str, message: str = None) -> bool:
        """
        Assert screen orientation
        
        Args:
            expected_orientation: Expected orientation ('portrait', 'landscape')
            message: Custom error message
            
        Returns:
            bool: True if assertion passes
            
        Raises:
            AssertionError: If orientation does not match
        """
        try:
            if self.driver_type == "uiautomator2":
                info = self.driver.info
                # Determine orientation from window size
                window_size = info.get('displaySizeDpY', 0), info.get('displaySizeDpX', 0)
                actual_orientation = "portrait" if window_size[0] > window_size[1] else "landscape"
            else:
                # Appium
                actual_orientation = self.driver.orientation.lower()
            
            if actual_orientation == expected_orientation.lower():
                self.logger.info(f"✅ PASS: Screen orientation is '{expected_orientation}'")
                return True
            else:
                error_msg = message or f"Screen orientation mismatch. Expected: '{expected_orientation}', Actual: '{actual_orientation}'"
                self.logger.error(f"❌ FAIL: {error_msg}")
                raise AssertionError(error_msg)
                
        except AssertionError:
            raise
        except Exception as e:
            error_msg = message or f"Failed to get screen orientation: {e}"
            self.logger.error(f"❌ FAIL: {error_msg}")
            raise AssertionError(error_msg)