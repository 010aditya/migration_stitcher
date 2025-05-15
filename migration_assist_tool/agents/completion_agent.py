import os
from dotenv import load_dotenv
from agents.fix_history_logger import FixHistoryLogger
from agents.context_stitcher import ContextStitcherAgent
from utils.llm_loader import get_llm

load_dotenv()

class CompletionAgent:
    def __init__(self, legacy_dir: str, migrated_dir: str, enterprise_dir: str = "", reference_dir: str = ""):
        self.legacy_dir = legacy_dir
        self.migrated_dir = migrated_dir
        self.enterprise_dir = enterprise_dir
        self.reference_dir = reference_dir

        self.client = get_llm()
        self.logger = FixHistoryLogger()

    def complete_missing_logic(self, target_path: str, source_paths: list, enterprise_refs: list, stitcher: ContextStitcherAgent):
        full_target_path = os.path.join(self.migrated_dir, target_path)

        if not os.path.exists(full_target_path):
            self.logger.log_fix(
                file_path=target_path,
                agent="CompletionAgent",
                status="failed",
                original_code="",
                fixed_code=None,
                metadata={"error": "Target file not found"}
            )
            return {
                "fixed_code": "",
                "completion_log": {
                    "status": "failed",
                    "reason": "Target file not found",
                    "file": target_path
                }
            }

        context = stitcher.build_context(
            source_paths=source_paths,
            target_path=target_path,
            enterprise_refs=enterprise_refs
        )
        original_code = context["migrated_code"]

        prompt = f"""You are a Java Spring Boot migration assistant.

Your task is to detect and complete any missing methods or logic in the 'MIGRATED FILE'.
Use the 'LEGACY CODE', 'ENTERPRISE REFERENCES', and 'REFERENCE CODE' as guidance.

Only return the complete, corrected Java file.

LEGACY CODE:
{context['legacy_code']}

ENTERPRISE REFERENCES:
{context['enterprise_code']}

REFERENCE CODE:
{context['reference_code']}

MIGRATED FILE:
{original_code}
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a Java Spring Boot code completion agent."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=4000
            )

            completed_code = response.choices[0].message.content.strip()

            with open(full_target_path, "w", encoding="utf-8") as f:
                f.write(completed_code)

            self._cleanup_java_file(full_target_path)

            self.logger.log_fix(
                file_path=target_path,
                agent="CompletionAgent",
                status="success",
                original_code=original_code,
                fixed_code=completed_code,
                metadata={"model": "gpt-4o"}
            )

            return {
                "fixed_code": completed_code,
                "completion_log": {
                    "status": "success",
                    "file": target_path
                }
            }

        except Exception as e:
            self.logger.log_fix(
                file_path=target_path,
                agent="CompletionAgent",
                status="failed",
                original_code=original_code,
                fixed_code=None,
                metadata={"error": str(e)}
            )

            return {
                "fixed_code": "",
                "completion_log": {
                    "status": "failed",
                    "file": target_path,
                    "error": str(e)
                }
            }

    def _cleanup_java_file(self, filepath):
        if filepath.endswith(".java") and os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()
            cleaned = [line for line in lines if line.strip() not in ("```java", "```")]
            with open(filepath, "w", encoding="utf-8") as f:
                f.writelines(cleaned)
