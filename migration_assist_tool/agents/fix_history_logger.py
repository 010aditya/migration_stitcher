# agents/fix_history_logger.py

import os
import json
from datetime import datetime

class FixHistoryLogger:
    def __init__(self, log_dir="logs/fix_history"):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)

    def log_fix(
        self,
        file_path: str,
        agent: str,
        status: str,
        original_code: str,
        fixed_code: str | None,
        metadata: dict = None,
    ):
        timestamp = datetime.utcnow().isoformat()
        filename = file_path.replace("/", "__").replace("\\", "__")
        log_path = os.path.join(self.log_dir, f"{filename}.json")

        # Load existing history if present
        history = []
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                history = json.load(f)

        # Prepare fix log entry
        fix_entry = {
            "timestamp": timestamp,
            "agent": agent,
            "status": status,
            "original_code": original_code[:2000],  # cap size
            "fixed_code": fixed_code[:2000] if fixed_code else None,
            "metadata": metadata or {}
        }

        # Enhance metadata with type of fix if not manually passed
        fix_types = []
        if metadata:
            if "reference_fixes" in metadata:
                for fix in metadata["reference_fixes"]:
                    if fix.get("method") != fix.get("suggested_method"):
                        fix_types.append("method_name_mismatch")
                    if fix.get("class") not in file_path:
                        fix_types.append("broken_class_ref")

        if fix_types:
            fix_entry["metadata"]["fix_types"] = list(set(fix_types))

        history.append(fix_entry)

        # Save updated history
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)

    def summarize_fix_types(self, file_path: str):
        log_path = os.path.join(self.log_dir, f"{file_path.replace('/', '__')}.json")
        if not os.path.exists(log_path):
            return {}

        with open(log_path, "r", encoding="utf-8") as f:
            history = json.load(f)

        summary = {}
        for entry in history:
            fix_types = entry.get("metadata", {}).get("fix_types", [])
            for fix in fix_types:
                summary[fix] = summary.get(fix, 0) + 1

        return summary
