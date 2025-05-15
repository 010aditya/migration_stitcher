# agents/fix_and_compile.py

import os
from dotenv import load_dotenv
from openai import OpenAI
from agents.fix_history_logger import FixHistoryLogger
from agents.context_stitcher import ContextStitcherAgent

load_dotenv()

class FixAndCompileAgent:
    def __init__(self, legacy_dir, migrated_dir, enterprise_dir="", reference_dir=""):
        self.legacy_dir = legacy_dir
        self.migrated_dir = migrated_dir
        self.enterprise_dir = enterprise_dir
        self.reference_dir = reference_dir

        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")
        self.logger = FixHistoryLogger()

    def fix_file(self, target_path, source_paths, enterprise_refs, stitcher: ContextStitcherAgent):
        assert self.legacy_dir not in target_path, "❌ Attempted to write to legacy directory. Aborting."

        migrated_file_path = os.path.join(self.migrated_dir, target_path)
        if not os.path.exists(migrated_file_path):
            print(f"❌ File not found: {migrated_file_path}")
            return {"fix_log": {"file_missing": True}, "fixed_code": ""}

        context = stitcher.build_context(
            source_paths=source_paths,
            target_path=target_path,
            enterprise_refs=enterprise_refs
        )

        prompt = f"""You are a Java code migration assistant.

Your job is to fix compilation issues and complete missing logic in the 'MIGRATED FILE'.
Refer to 'LEGACY CODE', 'ENTERPRISE REFERENCES', and 'REFERENCE CODE' for guidance.

Only return the complete, corrected Java code.

LEGACY CODE:
{context['legacy_code']}

ENTERPRISE REFERENCES:
{context['enterprise_code']}

REFERENCE CODE:
{context['reference_code']}

MIGRATED FILE:
{context['migrated_code']}
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful Java Spring Boot migration bot."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=4000
            )

            fixed_code = response.choices[0].message.content.strip()
            with open(migrated_file_path, "w", encoding="utf-8") as f:
                f.write(fixed_code)

            self._cleanup_java_file(migrated_file_path)

            self.logger.log_fix(
                file_path=target_path,
                agent="FixAndCompileAgent",
                status="success",
                original_code=context["migrated_code"],
                fixed_code=fixed_code,
                metadata={"model": self.model}
            )

            return {
                "fixed_code": fixed_code,
                "fix_log": {
                    "status": "success",
                    "file": target_path,
                    "model": self.model
                }
            }

        except Exception as e:
            self.logger.log_fix(
                file_path=target_path,
                agent="FixAndCompileAgent",
                status="failed",
                original_code=context["migrated_code"],
                fixed_code=None,
                metadata={"error": str(e), "model": self.model}
            )

            return {
                "fix_log": {
                    "status": "failed",
                    "file": target_path,
                    "error": str(e)
                },
                "fixed_code": ""
            }

    def _cleanup_java_file(self, filepath):
        if filepath.endswith(".java") and os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()
            cleaned = [line for line in lines if line.strip() not in ("```java", "```")]
            with open(filepath, "w", encoding="utf-8") as f:
                f.writelines(cleaned)
