# agents/retry_agent.py

import os
from agents.fix_and_compile import FixAndCompileAgent
from agents.completion_agent import CompletionAgent
from agents.context_stitcher import ContextStitcherAgent
from agents.build_validator import BuildValidatorAgent
from agents.build_fixer_agent import BuildFixerAgent
from agents.mapping_loader import MappingLoader

class RetryAgent:
    def __init__(self, legacy_dir: str, migrated_dir: str, enterprise_dir: str = "", reference_dir: str = ""):
        self.legacy_dir = legacy_dir
        self.migrated_dir = migrated_dir
        self.enterprise_dir = enterprise_dir
        self.reference_dir = reference_dir

        self.stitcher = ContextStitcherAgent(legacy_dir, migrated_dir, enterprise_dir, reference_dir)
        self.fixer = FixAndCompileAgent(legacy_dir, migrated_dir, enterprise_dir, reference_dir)
        self.completer = CompletionAgent(legacy_dir, migrated_dir, enterprise_dir, reference_dir)
        self.validator = BuildValidatorAgent(migrated_dir)
        self.build_fixer = BuildFixerAgent(migrated_dir)

    def retry_fixes(self, mapping: MappingLoader, max_retries: int = 2):
        result = self.validator.validate_build()

        if result["build_success"]:
            print("✅ Build passed, no retry needed.")
            return {"status": "success", "retry_attempts": 0, "errors": []}

        print("🔍 Build failed. Attempting to fix build.gradle...")
        build_fixer_result = self.build_fixer.fix(result["raw_output"])
        if build_fixer_result["status"] == "fixed":
            print(f"🛠 Applied build.gradle fixes: {build_fixer_result['fixes']}")
            result = self.validator.validate_build()
            if result["build_success"]:
                print("✅ Build succeeded after build.gradle fix.")
                return {
                    "status": "success_after_build_gradle_fix",
                    "retry_attempts": 0,
                    "fixes": build_fixer_result["fixes"]
                }

        # File-level retry
        error_files = set()
        for err in result["errors"]:
            relative_path = os.path.relpath(err["file"], self.migrated_dir)
            error_files.add(relative_path)

        retry_logs = []
        for i in range(max_retries):
            print(f"\n🔁 Retry attempt {i + 1} for {len(error_files)} file(s)...")

            for file in error_files:
                sources = mapping.get_sources_for_target(file)
                if not sources:
                    print(f"⚠️  No mapping found for {file}, skipping...")
                    continue

                print(f"🔧 Retrying fix for: {file}")
                fix_log = self.fixer.fix_file(file, sources, [], self.stitcher)
                retry_logs.append(fix_log["fix_log"])

                if fix_log["fix_log"]["status"] != "success":
                    print(f"🔍 Trying completion for: {file}")
                    completion_log = self.completer.complete_missing_logic(file, sources, [], self.stitcher)
                    retry_logs.append(completion_log["completion_log"])

            # Re-validate build
            validation = self.validator.validate_build()
            if validation["build_success"]:
                print("✅ Build succeeded after retry!")
                return {
                    "status": "success_after_retry",
                    "retry_attempts": i + 1,
                    "errors": [],
                    "retry_logs": retry_logs
                }

            error_files = set(
                os.path.relpath(err["file"], self.migrated_dir) for err in validation["errors"]
            )

        print("❌ Build still failing after max retries.")
        return {
            "status": "failed_after_retries",
            "retry_attempts": max_retries,
            "errors": result["errors"],
            "retry_logs": retry_logs
        }
