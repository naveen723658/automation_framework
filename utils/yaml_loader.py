"""
Centralised helpers for reading YAML artefacts in test_suite
"""
from pathlib import Path
from typing import Any, Dict, List
import yaml

ROOT = Path(__file__).resolve().parents[1]  # project root


def _read_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_framework_config() -> Dict[str, Any]:
    return _read_yaml(ROOT / "config" / "framework.yaml")


def load_db_config() -> Dict[str, Any]:
    return _read_yaml(ROOT / "config" / "database.yaml")


def load_test_case(tc_id: str) -> Dict[str, Any]:
    fn = ROOT / "test_suite" / "test_cases" / f"{tc_id}.yaml"
    return _read_yaml(fn)


def load_steps(step_file: str = "base_steps.yaml") -> Dict[str, Any]:
    fn = ROOT / "test_suite" / "steps" / step_file
    return _read_yaml(fn)


def load_locators() -> Dict[str, Any]:
    fn = ROOT / "test_suite" / "locators" / "base_locators.yaml"
    return _read_yaml(fn)
