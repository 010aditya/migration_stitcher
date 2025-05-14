# agents/build_validator.py

import subprocess
import os
import re
from typing import Dict, List

class BuildValidatorAgent:
    def __init__(self, migrated_dir: str):
        self.migrated_dir = migrated_dir
        self.gradle_cmd = "./gradlew" if os.name != "nt" else "gradlew.bat"

    def _run_gradle_build(self) -> subprocess.CompletedProcess:
        return subprocess.run(
            [self.gradle_cmd, "build", "--stacktrace"],
            cwd=self.migrated_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            shell=True
        )

    def _parse_build_output(self, output: str) -> List[Dict[str, str]]:
        errors = []
        # Sample match: > [ERROR] /path/to/Class.java:25: error: cannot find symbol
        pattern = re.compile(r"> Task :.*?\n(.*?\.java):(\d+):\s+error:\s+(.*?)\n", re.MULTILINE)

        for match in pattern.finditer(output):
            errors.append({
                "file": match.group(1).strip(),
                "line": match.group(2).strip(),
                "error": match.group(3).strip()
            })

        return errors

    def validate_build(self) -> Dict[str, any]:
        result = self._run_gradle_build()
        output = result.stdout

        if "BUILD SUCCESSFUL" in output:
            return {
                "build_success": True,
                "errors": [],
                "raw_output": output
            }

        parsed_errors = self._parse_build_output(output)

        return {
            "build_success": False,
            "errors": parsed_errors,
            "raw_output": output
        }
