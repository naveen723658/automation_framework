import time
import re
import json
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from .base import BaseAssertions, AssertionError


class EventAssertions(BaseAssertions):
    
    def assert_event_triggered(self, log_file: str, tag_name: Union[str, List[str]], start_timestamp: float, expected_event: Dict[str, Any], buffer_timeout: int = 2, event_config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Assert that a specific event was triggered and logged in the device logs.
        Integrated from event_assertions.py
        """
        # Validate log file
        log_path = Path(log_file)
        if not log_path.exists():
            raise FileNotFoundError(f"Log file not found: {log_file}")
        
        # Normalize tag_name to list
        tag_names = [tag_name] if isinstance(tag_name, str) else tag_name
        
        # Default event config if not provided
        if event_config is None:
            event_config = {
                "event_format": "json",
                "regex": r'(?<=called\\s)\{.*\}$'
            }
        
        min_event_timestamp = start_timestamp
        self.logger.debug(f"[EventAssertion] Checking for event after {min_event_timestamp}")
        
        json_pattern = None
        if event_config.get("regex"):
            try:
                json_pattern = re.compile(event_config["regex"])
            except re.error as e:
                self.logger.warning(f"Invalid regex pattern: {e}. Using fallback.")
                json_pattern = re.compile(r'\{.*\}')
        
        lines_checked, matching_tag_lines, json_parsed_lines = 0, 0, 0
        
        # Keep checking the log file for a short period to allow logs to flush
        timeout_sec = 5
        end_time = time.time() + timeout_sec
        
        while time.time() < end_time:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line_number, line in enumerate(f, 1):
                    lines_checked += 1
                    line = line.strip()
                    if not line:
                        continue

                    if not any(tag in line for tag in tag_names):
                        continue

                    matching_tag_lines += 1
                    self.logger.debug(f"Line {line_number} contains tag: {line}")

                    json_data = self._extract_json_from_log_line(line, json_pattern, event_config)
                    if json_data is None:
                        continue
                    json_parsed_lines += 1

                    if not self._validate_event_timestamp(json_data, min_event_timestamp, buffer_timeout):
                        continue

                    if self._matches_expected_event(json_data, expected_event):
                        self.logger.info(f"Event assertion SUCCESS at line {line_number}: {json_data}")
                        return True
            
            time.sleep(0.5)  # wait before checking again
        
        # Log summary and raise

        self.logger.debug(f"Event assertion failed. Checked {lines_checked} lines, {matching_tag_lines} matched tag, {json_parsed_lines} JSON parsed")
        raise AssertionError(f"Event {expected_event} not found in {log_file}")

    
    # ===================== Internal Helpers =====================
    
    def _extract_json_from_log_line(self, line: str, json_pattern: Optional[re.Pattern], event_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        json_text = None
        try:
            if json_pattern:
                match = json_pattern.search(line)
                if match:
                    json_text = match.group(0)
            if json_text is None:
                start_idx, end_idx = line.find('{'), line.rfind('}')
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_text = line[start_idx:end_idx+1]

            if json_text is None:
                return None

            fmt = event_config.get("event_format", "json").lower()
            if fmt == "json":
                return json.loads(json_text)
            else:
                return None
        except Exception as e:
            self.logger.debug(f"JSON parse failed for line: {e}")
            return None

    def _validate_event_timestamp(self, json_data: Dict[str, Any], min_event_timestamp: float, buffer_timeout: int) -> bool:
        timestamp_fields = ['eventTimestamp', 'timestamp', 'time']
        event_timestamp = None
        for field in timestamp_fields:
            if field in json_data:
                try:
                    event_timestamp = float(json_data[field])
                    break
                except:
                    continue
        if event_timestamp is None:
            return True
        
        # diffrence between event timestamp and min_event_timestamp should be less than buffer_timeout
        if event_timestamp < min_event_timestamp or (event_timestamp - min_event_timestamp) > buffer_timeout:
            self.logger.debug(f"Event timestamp {event_timestamp} is out of bounds ({min_event_timestamp}, {min_event_timestamp + buffer_timeout})")
            return False
        return True

    def _matches_expected_event(self, json_data: Dict[str, Any], expected_event: Dict[str, Any]) -> bool:
        for key, expected_val in expected_event.items():
            if key not in json_data:
                return False
            actual_val = json_data[key]
            if isinstance(expected_val, dict):
                if expected_val and not isinstance(actual_val, dict):
                    return False
            else:
                if str(actual_val).lower() != str(expected_val).lower():
                    return False
        return True