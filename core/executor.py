# core/executor.py
import json, time
from datetime import datetime
from pathlib import Path
from core.driver_manager import DriverManager
from core.actions import Actions
from core.helpers import ArtifactHelper
from utils.yaml_loader import load_test_case, load_steps, load_locators, load_framework_config
from scripts.selector_transformer import UnifiedElementFinder, MobileSelectorTransformer

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

    def run(self):
        status = "passed" # test status
        steps_results = []  # <-- collect step-level details
        start = time.time() # test start time
        # start video if enabled
        retry_count = self.cfg["core"].get("retry_count", 0)
        self.helpers.start_video_recording() # start video recording
        time.sleep(2)  # wait for video to start


        for step in self.test_yaml["test_steps"]: # iterate over steps
            step_id = step["step_id"] # get step ID
            action = self.steps_yaml[step_id]["action"] # get action to perform
            params = self.steps_yaml[step_id].get("parameters", {}) # get step parameters
            configs = step.get("configs", {}) # get step configs

            step_status = "passed" # default step status
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

                    if action == "launch_app":
                        self.actions.launch_app(params, configs, self.device_config["driver"])
                    elif action == "click":
                        locator_key = params.get("locator_id") or params.get("locator_key")
                        self.actions.click(locator_key, self.loc_yaml)
                    else:
                        self.logger.warning(f"Unknown action {action}")
                    
                    # take screenshot if enabled
                    if self.cfg["artifacts"]["screenshots"]["enabled"]:
                        self.helpers.take_screenshot(self.driver, self.device_config["driver"], step_id)

                    step_success = True
                except Exception as e:
                    self.logger.exception(f"Step {step_id} failed (Attempt {attempts}): {e}")
                    status = "failed"
                    if self.cfg["artifacts"]["screenshots"]["on_failure"]:
                        self.helpers.take_screenshot(self.driver, self.device_config["driver"], f"{step_id}_fail")
                    
                    if attempts > retry_count:
                        status = "failed"
                        break
                    else:
                        self.logger.warning(f"Retrying step {step_id} ({attempts}/{retry_count})")
                        time.sleep(2)

            step_duration = round(time.time() - step_start, 2)
            steps_results.append({
                "step_id": step_id,
                "name": self.steps_yaml[step_id].get("name", ""),
                "description": self.steps_yaml[step_id].get("description", ""),
                "status": step_status,
                "duration_sec": step_duration,
                "timestamp": datetime.utcnow().isoformat(),
                "assertions": [
                    {
                        "type": a.get("type", ""),
                        "expected": a.get("expected", ""),
                        "status": "passed" if step_status=="passed" else "failed"
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
