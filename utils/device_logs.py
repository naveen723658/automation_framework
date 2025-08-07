"""
Android Device Logs Manager for Mobile Test Automation Framework
Provides comprehensive logcat management with configuration-driven filtering and output
"""

import os
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging


class DeviceLogs:
    """
    Android device logs manager for capturing, filtering, and managing logcat output
    
    Features:
    - Configuration-driven log management
    - Log level filtering (VERBOSE, DEBUG, INFO, WARN, ERROR)
    - Tag-based include/exclude filtering
    - Device-specific log separation for parallel execution
    - Automatic timestamped file creation
    - Graceful process cleanup
    """
    
    def __init__(self, device_id: str, config: Dict[str, Any], test_id: str = None):
        """
        Initialize DeviceLogs manager
        
        Args:
            device_id: Android device ID (from adb devices)
            config: Framework configuration dictionary
            test_id: Optional test case ID for file naming
        """
        self.device_id = device_id
        self.config = config
        self.test_id = test_id or "general"
        self.logger = logging.getLogger(f"DeviceLogs_{device_id}")
        
        # Device logs configuration
        self.device_logs_config = config.get("artifacts", {}).get("device_logs", {})
        self.enabled = self.device_logs_config.get("enabled", False)
        
        # Logcat process management
        self.logcat_process: Optional[subprocess.Popen] = None
        self.log_file_path: Optional[str] = None
        self.is_logging = False
        self.log_thread: Optional[threading.Thread] = None
        
        # Setup output directory
        self._setup_output_directory()
        
        # Validate configuration
        self._validate_config()
    
    def _setup_output_directory(self):
        """Setup device-specific output directory for log files"""
        base_output_dir = self.device_logs_config.get("output_dir", "artifacts/device_logs/")
        
        # Create device-specific directory for parallel execution
        if self.config.get("core", {}).get("parallel_execution", False):
            device_folder = self.device_id.replace(":", "_").replace(" ", "_")
            self.output_dir = Path(base_output_dir) / device_folder
        else:
            self.output_dir = Path(base_output_dir)
        
        # Create directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger.debug(f"Device logs output directory: {self.output_dir}")
    
    def _validate_config(self):
        """Validate device logs configuration"""
        if not self.enabled:
            self.logger.info("Device logs collection is disabled")
            return
        
        # Validate log level
        valid_levels = ["VERBOSE", "DEBUG", "INFO", "WARN", "ERROR"]
        log_level = self.device_logs_config.get("log_level", "INFO")
        if log_level not in valid_levels:
            self.logger.warning(f"Invalid log level '{log_level}', using 'INFO'")
            self.device_logs_config["log_level"] = "INFO"
        
        # Validate filters
        filters = self.device_logs_config.get("filters", {})
        if not isinstance(filters, dict):
            self.logger.warning("Invalid filters configuration, using empty filters")
            self.device_logs_config["filters"] = {}
        
        self.logger.info(f"Device logs configuration validated for device {self.device_id}")
    
    def start_logcat(self) -> bool:
        """
        Start logcat logging based on configuration
        
        Returns:
            bool: True if logging started successfully, False otherwise
        """
        if not self.enabled:
            self.logger.debug("Device logs collection is disabled, skipping logcat start")
            return False
        
        if self.is_logging:
            self.logger.warning("Logcat is already running")
            return True
        
        try:
            # Clear logs if configured
            if self.device_logs_config.get("clear_logs", True):
                self.clear_logcat()
            
            # Generate timestamped log file path
            if self.device_logs_config.get("save_to_file", True):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{self.test_id}_{timestamp}.log"
                self.log_file_path = str(self.output_dir / filename)
            
            # Build logcat command
            logcat_cmd = self._build_logcat_command()
            
            # Start logcat process
            if self.log_file_path:
                # Log to file
                with open(self.log_file_path, 'w') as log_file:
                    self.logcat_process = subprocess.Popen(
                        logcat_cmd,
                        stdout=log_file,
                        stderr=subprocess.PIPE,
                        universal_newlines=True,
                        bufsize=1
                    )
            else:
                # Log to stdout (for debugging)
                self.logcat_process = subprocess.Popen(
                    logcat_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                    bufsize=1
                )
            
            self.is_logging = True
            
            # Start monitoring thread
            self.log_thread = threading.Thread(
                target=self._monitor_logcat_process,
                daemon=True
            )
            self.log_thread.start()
            
            self.logger.info(f"Logcat started for device {self.device_id}")
            if self.log_file_path:
                self.logger.info(f"Logs saving to: {self.log_file_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start logcat for device {self.device_id}: {e}")
            self._cleanup_process()
            return False
    
    def stop_logcat(self) -> bool:
        """
        Stop logcat logging gracefully
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        if not self.is_logging:
            self.logger.debug("Logcat is not running")
            return True
        
        try:
            self.is_logging = False
            
            # Terminate logcat process
            if self.logcat_process:
                self.logcat_process.terminate()
                
                # Wait for process to terminate gracefully
                try:
                    self.logcat_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.logger.warning("Logcat process did not terminate gracefully, killing")
                    self.logcat_process.kill()
                    self.logcat_process.wait()
            
            # Wait for monitoring thread to finish
            if self.log_thread and self.log_thread.is_alive():
                self.log_thread.join(timeout=3)
            
            self._cleanup_process()
            
            self.logger.info(f"Logcat stopped for device {self.device_id}")
            if self.log_file_path and os.path.exists(self.log_file_path):
                file_size = os.path.getsize(self.log_file_path)
                self.logger.info(f"Log file size: {file_size} bytes")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping logcat for device {self.device_id}: {e}")
            self._cleanup_process()
            return False
    
    def clear_logcat(self) -> bool:
        """
        Clear device log buffer
        
        Returns:
            bool: True if cleared successfully, False otherwise
        """
        try:
            clear_cmd = ["adb", "-s", self.device_id, "logcat", "-c"]
            result = subprocess.run(
                clear_cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self.logger.info(f"Device log buffer cleared for {self.device_id}")
                return True
            else:
                self.logger.error(f"Failed to clear log buffer: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"Timeout clearing log buffer for device {self.device_id}")
            return False
        except Exception as e:
            self.logger.error(f"Error clearing log buffer for device {self.device_id}: {e}")
            return False
    
    def get_log_file_path(self) -> Optional[str]:
        """
        Get the current log file path
        
        Returns:
            str: Path to log file if exists, None otherwise
        """
        return self.log_file_path if self.log_file_path and os.path.exists(self.log_file_path) else None
    
    def is_logging_active(self) -> bool:
        """
        Check if logging is currently active
        
        Returns:
            bool: True if logging is active, False otherwise
        """
        return self.is_logging and self.logcat_process and self.logcat_process.poll() is None
    
    def get_log_stats(self) -> Dict[str, Any]:
        """
        Get logging statistics
        
        Returns:
            dict: Statistics about current logging session
        """
        stats = {
            "enabled": self.enabled,
            "is_logging": self.is_logging,
            "device_id": self.device_id,
            "test_id": self.test_id,
            "log_file_path": self.log_file_path,
            "log_file_size": 0,
            "process_running": False
        }
        
        if self.log_file_path and os.path.exists(self.log_file_path):
            stats["log_file_size"] = os.path.getsize(self.log_file_path)
        
        if self.logcat_process:
            stats["process_running"] = self.logcat_process.poll() is None
        
        return stats
    
    def _build_logcat_command(self) -> List[str]:
        """
        Build logcat command based on configuration
        
        Returns:
            List[str]: Complete logcat command with arguments
        """
        cmd = ["adb", "-s", self.device_id, "logcat"]
        
        # Add log level filter
        log_level = self.device_logs_config.get("log_level", "INFO")
        level_map = {
            "VERBOSE": "V",
            "DEBUG": "D", 
            "INFO": "I",
            "WARN": "W",
            "ERROR": "E"
        }
        if log_level in level_map:
            cmd.extend(["-v", "time"])  # Add timestamp format
            cmd.append(f"*:{level_map[log_level]}")
        
        # Add tag-based filters
        filters = self.device_logs_config.get("filters", {})
        
        # Include filters (specific tags to include)
        include_tags = filters.get("include", [])
        if include_tags:
            # For include filters, we need to set specific tags to desired level
            # and others to silent
            tag_filters = []
            for tag in include_tags:
                tag_filters.append(f"{tag}:{level_map.get(log_level, 'I')}")
            
            # Add silent filter for other tags if we have specific includes
            if tag_filters:
                cmd.extend(tag_filters)
                cmd.append("*:S")  # Silent for all other tags
        
        # Note: Exclude filters are handled in post-processing since
        # logcat doesn't have native exclude functionality
        
        self.logger.debug(f"Built logcat command: {' '.join(cmd)}")
        return cmd
    
    def _monitor_logcat_process(self):
        """Monitor logcat process and handle output filtering"""
        if not self.logcat_process:
            return
        
        exclude_tags = self.device_logs_config.get("filters", {}).get("exclude", [])
        
        try:
            # If logging to stdout and we have exclude filters, we need to filter
            if not self.log_file_path and exclude_tags:
                for line in iter(self.logcat_process.stdout.readline, ''):
                    if not self.is_logging:
                        break
                    
                    # Check if line should be excluded
                    should_exclude = any(tag in line for tag in exclude_tags)
                    if not should_exclude:
                        print(line.rstrip())
            
            # Wait for process completion
            self.logcat_process.wait()
            
        except Exception as e:
            self.logger.error(f"Error in logcat monitoring thread: {e}")
        finally:
            self.logger.debug("Logcat monitoring thread finished")
    
    def _cleanup_process(self):
        """Clean up logcat process and reset state"""
        if self.logcat_process:
            try:
                if self.logcat_process.poll() is None:
                    self.logcat_process.terminate()
                    self.logcat_process.wait(timeout=3)
            except:
                pass
            finally:
                self.logcat_process = None
        
        self.is_logging = False
        self.log_thread = None
    
    def __enter__(self):
        """Context manager entry"""
        self.start_logcat()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop_logcat()
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        if self.is_logging:
            self.stop_logcat()


# Factory function for easy integration
def create_device_logs_manager(device_id: str, config: Dict[str, Any], test_id: str = None) -> DeviceLogs:
    """
    Factory function to create DeviceLogs manager
    
    Args:
        device_id: Android device ID
        config: Framework configuration dictionary
        test_id: Optional test case ID
        
    Returns:
        DeviceLogs: Configured device logs manager instance
    """
    return DeviceLogs(device_id, config, test_id)


# Context manager for automatic log management
class DeviceLogsContext:
    """Context manager for automatic device logs management during test execution"""
    
    def __init__(self, device_logs_manager: DeviceLogs):
        self.manager = device_logs_manager
    
    def __enter__(self):
        self.manager.start_logcat()
        return self.manager
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.manager.stop_logcat()
        
        # Log final statistics
        stats = self.manager.get_log_stats()
        if stats["log_file_path"] and stats["log_file_size"] > 0:
            logging.getLogger("DeviceLogsContext").info(
                f"Device logs captured: {stats['log_file_size']} bytes in {stats['log_file_path']}"
            )


# Utility functions for integration with test framework
def setup_device_logs_for_test(device_config: Dict[str, Any], framework_config: Dict[str, Any], 
                              test_id: str) -> Optional[DeviceLogs]:
    """
    Setup device logs manager for a test execution
    
    Args:
        device_config: Device configuration with udid
        framework_config: Framework configuration
        test_id: Test case ID
        
    Returns:
        DeviceLogs: Manager instance if enabled, None otherwise
    """
    device_id = device_config.get("udid")
    if not device_id:
        return None
    
    logs_config = framework_config.get("artifacts", {}).get("device_logs", {})
    if not logs_config.get("enabled", False):
        return None
    
    return create_device_logs_manager(device_id, framework_config, test_id)


def cleanup_old_log_files(output_dir: str, days_to_keep: int = 7):
    """
    Clean up old log files
    
    Args:
        output_dir: Directory containing log files
        days_to_keep: Number of days to keep files
    """
    try:
        output_path = Path(output_dir)
        if not output_path.exists():
            return
        
        cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
        
        for log_file in output_path.glob("*.log"):
            if log_file.stat().st_mtime < cutoff_time:
                log_file.unlink()
                logging.getLogger("DeviceLogs").info(f"Cleaned up old log file: {log_file}")
                
    except Exception as e:
        logging.getLogger("DeviceLogs").error(f"Error cleaning up log files: {e}")