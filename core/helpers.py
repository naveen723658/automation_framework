# core/helpers.py
import signal, time, subprocess, shutil
from pathlib import Path
from utils.logger import init_logger
from utils.yaml_loader import load_framework_config

class ArtifactHelper:
    def __init__(self, tc_id, device_config):
        self.cfg = load_framework_config()
        self.tc_id = tc_id
        self.device_id = device_config["udid"]
        self.artifact_id = self.device_id.replace(":", "_").replace("-", "_")
        self.root = Path(self.cfg["core"]["artifacts_root"])

        if self.cfg["core"].get("parallel_execution", False):
            self.ss_dir = self.root / "screenshots" / self.artifact_id / tc_id
            self.video_dir = self.root / "videos" / self.artifact_id / tc_id
            self.log_file = self.root / "logs" / self.artifact_id / f"{tc_id}.log"
        else:
            self.ss_dir = self.root / "screenshots" / tc_id
            self.video_dir = self.root / "videos" / tc_id
            self.log_file = self.root / "logs" / f"{tc_id}.log"

        self.ss_dir.mkdir(parents=True, exist_ok=True)
        self.video_dir.mkdir(parents=True, exist_ok=True)
        self.logger = init_logger(self.log_file)
        self.video_file = self.video_dir / "execution.mp4"
        self._record_proc = None

    # ---------------- Video ---------------- #
    def start_video_recording(self):
        try:
            self._record_proc = subprocess.Popen(
                ["adb", "-s", self.device_id, "shell", "screenrecord", "/sdcard/execution.mp4"]
            )
            self.logger.debug("Video recording started")
        except Exception as e:
            self.logger.error(f"Failed to start video recording: {e}")

    def stop_video_recording(self, save_video: bool):
        if self._record_proc:
            try:
                # Gracefully send SIGINT to allow screenrecord to finalize the file
                self._record_proc.send_signal(signal.SIGINT)
                self._record_proc.wait(timeout=5)
                time.sleep(2)  # small delay to flush file
            except Exception as e:
                self.logger.warning(f"Graceful stop failed, terminating: {e}")
                self._record_proc.terminate()

            try:
                if save_video:
                    subprocess.run(["adb", "-s", self.device_id, "pull", "/sdcard/execution.mp4", str(self.video_file)], check=True)
                subprocess.run(["adb", "-s", self.device_id, "shell", "rm", "/sdcard/execution.mp4"])
            except Exception as e:
                self.logger.error(f"Error handling video file: {e}")

        # Remove directory if not saving
        if not save_video and self.video_dir.exists():
            shutil.rmtree(self.video_dir, ignore_errors=True)

    # ---------------- Screenshots ---------------- #
    def take_screenshot(self, driver, driver_type, step_name):
        ts = int(time.time())
        file_path = self.ss_dir / f"{step_name}_{ts}.png"
        try:
            if driver_type == "uiautomator2":
                driver.screenshot(str(file_path))
            else:
                driver.save_screenshot(str(file_path))
            self.logger.info(f"Screenshot saved: {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to take screenshot: {e}")
