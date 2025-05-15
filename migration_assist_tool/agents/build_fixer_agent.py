# agents/build_fixer_agent.py

import os
import re

class BuildFixerAgent:
    def __init__(self, migrated_dir: str):
        self.migrated_dir = migrated_dir
        self.build_gradle = os.path.join(migrated_dir, "build.gradle")

    def fix(self, build_output: str) -> dict:
        if not os.path.exists(self.build_gradle):
            return {"status": "skipped", "reason": "No build.gradle"}

        missing_classes = self._extract_missing_classes(build_output)

        if not missing_classes:
            return {"status": "skipped", "reason": "No dependency-related issues found"}

        fixes_applied = []
        with open(self.build_gradle, "r", encoding="utf-8") as f:
            gradle_code = f.read()

        for class_name in missing_classes:
            suggestion = self._suggest_dependency(class_name)
            if suggestion and suggestion not in gradle_code:
                gradle_code = gradle_code.replace("dependencies {", f"dependencies {{\n    {suggestion}")
                fixes_applied.append(suggestion)

        if fixes_applied:
            with open(self.build_gradle, "w", encoding="utf-8") as f:
                f.write(gradle_code)

            return {
                "status": "fixed",
                "fixes": fixes_applied,
                "file": "build.gradle"
            }

        return {
            "status": "skipped",
            "reason": "No actionable suggestions",
            "file": "build.gradle"
        }

    def _extract_missing_classes(self, build_output: str):
        # Look for: cannot find symbol, package xyz does not exist
        missing = set()

        # Pattern 1: symbol:   class Xyz
        for match in re.finditer(r"symbol:\s+class\s+(\w+)", build_output):
            missing.add(match.group(1))

        # Pattern 2: package xyz does not exist
        for match in re.finditer(r"package\s+([a-zA-Z0-9_.]+)\s+does not exist", build_output):
            parts = match.group(1).split(".")
            if parts:
                missing.add(parts[-1])

        return list(missing)

    def _suggest_dependency(self, class_name: str) -> str:
        # Naive suggestions (can be expanded with an LLM or JSON map later)
        suggestions = {
            "RestController": "implementation 'org.springframework.boot:spring-boot-starter-web'",
            "Autowired": "implementation 'org.springframework.boot:spring-boot-starter'",
            "JpaRepository": "implementation 'org.springframework.boot:spring-boot-starter-data-jpa'",
            "Entity": "implementation 'jakarta.persistence:jakarta.persistence-api:3.1.0'",
            "Slf4j": "implementation 'org.slf4j:slf4j-api:2.0.7'",
            "Log": "implementation 'org.apache.logging.log4j:log4j-api:2.20.0'",
            "HttpServletRequest": "implementation 'jakarta.servlet:jakarta.servlet-api:6.0.0'",
            "RequestMapping": "implementation 'org.springframework.boot:spring-boot-starter-web'"
        }
        return suggestions.get(class_name, None)
