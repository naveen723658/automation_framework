"""
Entry-point CLI for running YAML test cases with parallel execution support.
Usage examples:
  python run_framework.py --test-case TC001 --env dev
  python run_framework.py --test-case all --env prod
  python run_framework.py --list-tests
"""
import sys
import queue
import argparse
import subprocess
import multiprocessing
from pathlib import Path
from multiprocessing import Process
# from utils.logger import init_logger
from typing import List, Tuple, Dict
from core.test_executor import TestExecutor
from utils.yaml_loader import load_test_case, load_framework_config

def get_adb_devices() -> List[str]:
    """Returns a list of online ADB device IDs."""
    try:
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split("\n")[1:]  # skip header
        devices = [line.split("\t")[0] for line in lines if "\tdevice" in line]
        return devices
    except subprocess.CalledProcessError:
        print("❌ Error: ADB not found or not working")
        return []
    except Exception as e:
        print(f"❌ Error getting ADB devices: {e}")
        return []

def get_available_devices(cfg: dict) -> List[dict]:
    """Get available devices based on framework configuration"""
    adb_devices = get_adb_devices()
    print(f"[INFO] Connected ADB devices: {adb_devices}")
    
    if not adb_devices:
        print("❌ No connected devices found")
        return []

    available_devices = []

    # Priority 1: uiautomator2
    if cfg.get("drivers", {}).get("uiautomator2", {}).get("enabled", False):
        device_ids = cfg["drivers"]["uiautomator2"].get("deviceIds", [])
        
        for udid in device_ids:
            if udid in adb_devices:
                available_devices.append({
                    "udid": udid,
                    "driver": "uiautomator2",
                    "server_url": None,
                    "capabilities": None
                })
                print(f"✅ Added uiautomator2 device: {udid}")
            else:
                print(f"⚠️ Skipping uiautomator2 device '{udid}' (not connected)")

    # Priority 2: Appium
    elif cfg.get("drivers", {}).get("appium", {}).get("enabled", False):
        for device in cfg["drivers"]["appium"].get("devices", []):
            udid = device.get("udid")
            if udid in adb_devices:
                available_devices.append({
                    "udid": udid,
                    "driver": "appium",
                    "server_url": device["server_url"],
                    "capabilities": device["capabilities"]
                })
                print(f"✅ Added Appium device: {udid}")
            else:
                print(f"⚠️ Skipping Appium device '{udid}' (not connected)")

    # Fallback: Use any available device with uiautomator2
    if not available_devices and adb_devices:
        print("ℹ️  No configured devices found, using first available device with uiautomator2")
        available_devices.append({
            "udid": adb_devices[0],
            "driver": "uiautomator2",
            "server_url": None,
            "capabilities": None
        })

    return available_devices

def run_test(tc_id: str, env: str, device: dict) -> None:
    """Run a single test case on a device"""
    # try:
    print(f"🚀 Starting test {tc_id} on device {device['udid']} ({device['driver']})")
    executor = TestExecutor(device, tc_id, env)
    executor.run()
    print(f"✅ Completed test {tc_id} on device {device['udid']}")
    # except Exception as e:
    #     print(f"❌ Failed test {tc_id} on device {device['udid']}: {e}")


def list_tests() -> None:
    tc_dir = Path(__file__).parent / "test_suite" / "test_cases"
    for y in sorted(tc_dir.glob("*.yaml")):
        print(y.stem)


def main() -> None:
    parser = argparse.ArgumentParser(description="Mobile Test-Automation Runner")
    parser.add_argument(
        "--test-case", default="all", help="TC id (e.g. TC001) or 'all'"
    )
    parser.add_argument("--env", default="stage", help="Environment tag")
    parser.add_argument("--list-tests", action="store_true", help="List available TC ids")
    args = parser.parse_args()

    if args.list_tests:
        list_tests()
        sys.exit(0)

    if args.test_case == "all":
        # iterate over every YAML in test_suite/test_cases
        tc_dir = Path(__file__).parent / "test_suite" / "test_cases"
        tc_ids = [p.stem for p in tc_dir.glob("*.yaml")]
    else:
        tc_ids = [args.test_case]

    # Load framework config
    cfg = load_framework_config()
    devices = get_available_devices(cfg)
    if not devices:
        raise SystemExit("[ERROR] No eligible connected devices found.")
    max_parallel = min(cfg["core"].get("max_workers", 3), len(devices))

    if cfg["core"].get("parallel_execution", False):
        processes = []
        for device in devices:
            for tc in tc_ids:
                p = Process(target=run_test, args=(tc, args.env, device))
                p.start()
                processes.append(p)
            
                # Limit concurrent processes
                if len(processes) >= max_parallel:
                    for p in processes:
                        p.join()
                    processes = []

        # Wait for all to complete
        for p in processes:
            p.join()

    else:
        # Run serially using the first device
        device = devices[0] 
        for tc in tc_ids:
            run_test(tc, args.env, device)

if __name__ == "__main__":
    main()
