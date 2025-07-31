"""
Lightweight MongoDB client wrapper
"""
import os
from typing import Any, Dict
from pymongo import MongoClient
from utils.yaml_loader import load_db_config


class MongoDBClient:
    def __init__(self) -> None:
        cfg = load_db_config()["mongodb"]
        self.client = MongoClient(
            host=cfg["host"],
            port=int(cfg["port"]),
            username=cfg["username"],
            password=cfg["password"],
            serverSelectionTimeoutMS=5000,
        )
        self.db = self.client[
            os.getenv("MONGO_DB", cfg["database"])
        ]

        col_cfg = load_db_config()["collections"]
        self.exec_col = self.db[col_cfg["test_executions"]]
        self.heal_col = self.db[col_cfg["healing_data"]]

    def save_execution(self, doc: Dict[str, Any]) -> None:
        self.exec_col.insert_one(doc)

    def save_healing(self, doc: Dict[str, Any]) -> None:
        self.heal_col.insert_one(doc)
