# agents/fix_history_logger.py

import os
import json
import datetime
from typing import Dict, Optional


class FixHistoryLogger:
    def __init__(self, log_dir: str = "logs/fix_history"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)

    def log_fix(
        self,
        file_path: str,
        agent: str,
        status: str,
        original_code: Optional[str],
        fixed_code: Optional[str],
        metadata: Dict
    ):
        # Sanitize filename to avoid path separators
        filename = os.path.basename(file_path).replace("/", "_").replace("\\", "_")
        timestamp = datetime.datetime.utcnow().isoformat()

        log_data = {
            "file": file_path,
            "agent": agent,
            "status": status,
            "timestamp": timestamp,
            "original_code": original_code or "",
            "fixed_code": fixed_code or "",
            "metadata": metadata
        }

        # Final path for the fix log
        log_file_path = os.path.join(self.log_dir, f"{filename}_{agent}.json")

        try:
            with open(log_file_path, "w", encoding="utf-8") as f:
                json.dump(log_data, f, indent=2)
            print(f"📝 Fix logged: {log_file_path}")
        except Exception as e:
            print(f"⚠️ Failed to log fix for {file_path}: {e}")
