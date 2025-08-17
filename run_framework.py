"""
Entry-point CLI for running YAML test cases with parallel execution support.
- Centralized logging
- Supports parallel execution per device
- Tracks results in JSON
"""
import sys, re
import argparse
import subprocess
from pathlib import Path
from multiprocessing import Process
from typing import List
from utils.yaml_loader import load_framework_config
from core.executor import Executor
from utils.logger import init_logger


def get_logger():
    """Initialize a global logger for the framework."""
    cfg = load_framework_config()
    log_dir = Path(cfg["core"]["artifacts_root"]) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return init_logger(log_dir / "framework.log")


logger = get_logger()


def get_adb_devices() -> List[str]:
    """Returns a list of online ADB device IDs."""
    try:
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split("\n")[1:]  # skip header
        devices = [line.split("\t")[0] for line in lines if "\tdevice" in line]
        return devices
    except Exception as e:
        logger.error(f"Error getting ADB devices: {e}")
        return []


def get_available_devices(cfg: dict) -> List[dict]:
    """Get available devices based on framework configuration"""
    adb_devices = get_adb_devices()
    logger.info(f"Connected ADB devices: {adb_devices}")

    if not adb_devices:
        logger.error("No connected devices found")
        return []

    available_devices = []

    # Priority 1: uiautomator2
    if cfg.get("drivers", {}).get("uiautomator2", {}).get("enabled", False):
        for udid in cfg["drivers"]["uiautomator2"].get("deviceIds", []):
            if udid in adb_devices:
                available_devices.append({
                    "udid": udid,
                    "driver": "uiautomator2",
                    "server_url": None,
                    "capabilities": {}
                })
                logger.info(f"Added uiautomator2 device: {udid}")
            else:
                logger.debug(f"Skipping uiautomator2 device '{udid}' (not connected)")

    # Priority 2: Appium
    elif cfg.get("drivers", {}).get("appium", {}).get("enabled", False):
        for device in cfg["drivers"]["appium"].get("devices", []):
            udid = device.get("udid")
            if udid in adb_devices:
                available_devices.append({
                    "udid": udid,
                    "driver": "appium",
                    "server_url": device.get("server_url"),
                    "capabilities": device.get("capabilities", {})
                })
                logger.info(f"Added Appium device: {udid}")
            else:
                logger.debug(f"Skipping Appium device '{udid}' (not connected)")

    # Fallback: use the first available device with uiautomator2
    if not available_devices and adb_devices:
        logger.info("No configured devices found, using first available device with uiautomator2")
        available_devices.append({
            "udid": adb_devices[0],
            "driver": "uiautomator2",
            "server_url": None,
            "capabilities": {}
        })

    return available_devices


def run_test(tc_id: str, env: str, device: dict) -> None:
    """Run a single test case on a device"""
    try:
        logger.info(f"Starting test {tc_id} on device {device['udid']} ({device['driver']})")
        executor = Executor(device, tc_id, env)
        status = executor.run()
        logger.info(f"Completed test {tc_id} on device {device['udid']} with status: {status}")
    except Exception as e:
        logger.exception(f"Failed test {tc_id} on device {device['udid']}: {e}")


def list_tests() -> None:
    """List available test cases from test_suite/test_cases"""
    tc_dir = Path(__file__).parent / "test_suite" / "test_cases"
    for y in sorted(tc_dir.glob("*.yaml")):
        logger.info(f"Available Test: {y.stem}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Mobile Test-Automation Runner")
    parser.add_argument("--test-case", default="all", help="TC id (e.g. TC001) or 'all'")
    parser.add_argument("--env", default="stage", help="Environment tag")
    parser.add_argument("--list-tests", action="store_true", help="List available TC ids")
    args = parser.parse_args()

    if args.list_tests:
        list_tests()
        sys.exit(0)

    # collect test cases
    tc_dir = Path(__file__).parent / "test_suite" / "test_cases"
    if args.test_case == "all":
        tc_ids = [p.stem for p in tc_dir.glob("*.yaml")]
    else:
        tc_ids = [args.test_case]

    # Sort by numeric part of tcid (TC001 → 1, TC002 → 2, etc.)
    tc_ids.sort(key=lambda x: int(re.search(r'\d+', x).group()))

    # load config and available devices
    cfg = load_framework_config()
    devices = get_available_devices(cfg)
    if not devices:
        raise SystemExit("No eligible connected devices found.")

    max_parallel = min(cfg["core"].get("max_workers", 3), len(devices))
    parallel_enabled = cfg["core"].get("parallel_execution", False)

    if parallel_enabled:
        processes = []
        for tc in tc_ids:
            for device in devices:
                p = Process(target=run_test, args=(tc, args.env, device))
                p.start()
                processes.append(p)

                # limit concurrent processes
                if len(processes) >= max_parallel:
                    for proc in processes:
                        proc.join()
                    processes = []

        for proc in processes:
            proc.join()

    else:
        # run serially on first device
        device = devices[0]
        for tc in tc_ids:
            run_test(tc, args.env, device)


if __name__ == "__main__":
    main()
