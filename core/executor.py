# core/executor.py
import json, time, os
from datetime import datetime
from pathlib import Path
from core.driver_manager import DriverManager
from core.actions import Actions
from core.helpers import ArtifactHelper
from utils.yaml_loader import load_test_case, load_steps, load_locators, load_framework_config
from scripts.selector_transformer import UnifiedElementFinder
from utils.device_logs import create_device_logs_manager, DeviceLogsContext
from core.assertions import create_assertions_helper
class Executor:
    def __init__(self, device_config, tc_id, env):
        self.device_config = device_config
        self.tc_id = tc_id
        self.env = env
        self.cfg = load_framework_config()
        self.helpers = ArtifactHelper(tc_id, device_config)
        self.logger = self.helpers.logger
        self.driver = DriverManager.initialize_driver(device_config, self.logger)
        self.finder = UnifiedElementFinder(self.driver, device_config["driver"])
        self.actions = Actions(self.driver, self.device_config, self.finder, self.logger, self.helpers)
        self.loc_yaml = load_locators()
        self.test_yaml = load_test_case(tc_id)
        self.steps_yaml = load_steps(self.test_yaml.get("step_file", "base_steps.yaml"))

        self.assertions = create_assertions_helper(
            self.driver,
            self.device_config,
            self.loc_yaml,
            self.finder,
            self.logger
        )
        
        # --- Device Logs Integration ---
        self.device_logs = None
        device_log_conf = self.cfg.get("artifacts", {}).get("device_logs", {})
        if device_log_conf.get("enabled", False):
            self.device_logs = create_device_logs_manager(self.device_config["udid"], self.cfg, tc_id)
        self.device_logs_ctx = DeviceLogsContext(self.device_logs) if self.device_logs else None


    def run(self):
        status = "passed" # test status
        steps_results = []  # <-- collect step-level details
        start = time.time() # test start time
        retry_count = self.cfg["core"].get("retry_count", 0)

        # -------- Context Manager for Device Logs --------
        logs_cm = self.device_logs_ctx or self._dummy_context()
        with logs_cm:
            # start video if enabled
            if self.cfg["artifacts"]["videos"]["enabled"]:
                self.helpers.start_video_recording() # start video recording
                time.sleep(2)  # wait for video to start


            for step in self.test_yaml["test_steps"]: # iterate over steps
                step_id = step["step_id"] # get step ID
                action = self.steps_yaml[step_id]["action"] # get action to perform
                params = self.steps_yaml[step_id].get("parameters", {}) # get step parameters
                configs = step.get("configs", {}) # get step configs

                step_status = True # default step status
                step_start = time.time() # step start time
                step_screenshot = None # step screenshot path if needed
                step_assertions = configs.get("assertions", []) # step assertions if any

                attempts = 0 # attempt counter for retries
                step_success = False # flag to track if step succeeded
                while attempts <= retry_count and not step_success:
                    attempts += 1
                    try:
                        self.logger.debug(f"Executing Step {step_id} (Attempt {attempts}) – {action}")

                        # wait if configured
                        if configs.get("wait_timeout"):
                            self.logger.debug(f"Waiting for {configs['wait_timeout']} seconds before executing step {step_id}")
                            time.sleep(configs["wait_timeout"])

                        # take screenshot if enabled
                        if self.cfg["artifacts"]["screenshots"]["enabled"]:
                            step_screenshot = self.helpers.take_screenshot(self.driver, self.device_config["driver"], step_id)

                        if action == "launch_app":
                            self.actions.launch_app(params, configs, self.device_config["driver"])
                        elif action == "click":
                            locator_key = params.get("locator_id") or params.get("locator_key")
                            self.actions.click(locator_key, self.loc_yaml, configs)
                        else:
                            self.logger.warning(f"Unknown action {action}")
                        

                        step_success = True
                    except Exception as e:
                        self.logger.exception(f"Step {step_id} failed (Attempt {attempts}): {e}")
                        if attempts > retry_count:
                            status = "failed"
                            break
                        else:
                            self.logger.warning(f"Retrying step {step_id} ({attempts}/{retry_count})")
                            time.sleep(2)

                # if wait_timeout is configured, then add this time in step_start timestamp
                start_timestamp = step_start + configs.get("wait_timeout", 0)
                # --- Process Step-Level Assertions After Action Execution ---
                if status == "passed" and step_assertions:
                    self.logger.debug(f"Processing assertions for step {step_id}")
                    for assertion in step_assertions:
                        try:
                            if assertion["type"] == "app_launched":

                                step_status = self.assertions.assert_current_app(
                                    expected_package=assertion.get("expected", ""),
                                    ignore_interference=assertion.get("ignore_interference", False)                                                                        
                                )

                            elif assertion["type"] == "event_triggered":
                                log_file = self.device_logs.get_log_file_path()  # Path from DeviceLogs manager

                                step_status = self.assertions.assert_event_triggered(
                                    log_file=log_file,
                                    tag_name=self.cfg["events"].get("filters", ["BobbleEventLogger"]),
                                    start_timestamp=start_timestamp,
                                    expected_event=assertion.get("expected", {}),
                                    buffer_timeout=int(assertion.get("buffer_timeout", 2) + round(time.time() - step_start, 2)),
                                    event_config=self.cfg.get("events", {})
                                )
                            else:
                                self.logger.warning(f"Unknown assertion type {assertion['type']}")

                            
                        except Exception as e:
                            self.logger.error(f"Assertion failed for step {step_id}: {e}")
                            step_status = False
                            break

                        
                    



                step_duration = round(time.time() - step_start, 2)
                steps_results.append({
                    "step_id": step_id,
                    "name": self.steps_yaml[step_id].get("name", ""),
                    "description": self.steps_yaml[step_id].get("description", ""),
                    "status": status,
                    "duration_sec": step_duration,
                    "timestamp": start_timestamp,
                    "assertions": [
                        {
                            "type": a.get("type", ""),
                            "name": a.get("name", ""),
                            "expected": a.get("expected", ""),
                            "status": "passed" if step_status else "failed"
                        }
                        for a in step_assertions
                    ],
                    "artifacts": {
                        "screenshot": str(step_screenshot) if step_screenshot else ""
                    }
                })
                
                # break outer loop if test already failed
                if status == "failed":
                    break

                    

            duration = round(time.time()-start, 2)

            save_video = (
                (status=="failed" and self.cfg["artifacts"]["videos"]["save_on_failure"]) or
                (status=="passed" and self.cfg["artifacts"]["videos"]["save_on_pass"])
            )
            time.sleep(5) # wait for video to finalize
            self.helpers.stop_video_recording(save_video)
            DriverManager.cleanup_driver(self.driver, self.device_config, self.logger)

        # save json results
        results_file = Path(self.cfg["core"]["artifacts_root"]) / "results" / "results.json"
        results_file.parent.mkdir(parents=True, exist_ok=True)
        test_metadata = self.test_yaml.get("test_metadata", {})
        record = {
            "test_id": self.tc_id,
            "name": test_metadata.get("name", ""),
            "description": test_metadata.get("description", ""),
            "tags": test_metadata.get("tags", []),
            "device_id": self.device_config["udid"],
            "driver": self.device_config["driver"],
            "status": status,
            "duration_sec": duration,
            "timestamp": datetime.utcnow().isoformat(),
            "steps": steps_results,
            "artifacts": {
                "screenshots_dir": str(self.helpers.ss_dir),
                "log_file": str(self.helpers.log_file),
                "video_dir": str(self.helpers.video_dir if save_video else "")
            }
        }
        all_results = []
        if results_file.exists():
            try:
                all_results = json.loads(results_file.read_text())
            except Exception:
                all_results = []

        all_results.append(record)
        results_file.write_text(json.dumps(all_results, indent=2))

        return status

    def _dummy_context(self):
        # Used when device logs are disabled or unavailable
        class DummyContext:
            def __enter__(self): return self
            def __exit__(self, exc_type, exc_val, exc_tb): pass
        return DummyContext()