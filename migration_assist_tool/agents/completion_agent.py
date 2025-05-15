# agents/completion_agent.py

import os
from dotenv import load_dotenv
from openai import OpenAI
from agents.context_stitcher import ContextStitcherAgent
from agents.fix_history_logger import FixHistoryLogger

class CompletionAgent:
    def __init__(self, legacy_dir: str, migrated_dir: str, enterprise_dir: str = ""):
        load_dotenv()
        self.legacy_dir = legacy_dir
        self.migrated_dir = migrated_dir
        self.enterprise_dir = enterprise_dir

        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")
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
                "completion_log": {"status": "failed", "reason": "Target file not found", "file": target_path}
            }

        # Build stitched context
        context = stitcher.build_context(
            source_paths=source_paths,
            target_path=target_path,
            enterprise_refs=enterprise_refs
        )

        prompt = f"""You are a Java migration assistant.

Your task is to detect and complete any missing methods or logic in the 'MIGRATED FILE'.
Use 'LEGACY FILE(S)' and 'ENTERPRISE REFERENCES' for reference.

Only return the complete updated Java file.

LEGACY FILE(S):
{context['legacy_code']}

ENTERPRISE REFERENCES:
{context['enterprise_code']}

MIGRATED FILE (Incomplete):
{context['migrated_code']}
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
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

            self.logger.log_fix(
                file_path=target_path,
                agent="CompletionAgent",
                status="success",
                original_code=context["migrated_code"],
                fixed_code=completed_code,
                metadata={
                    "tokens_used": getattr(response.usage, "total_tokens", "unknown"),
                    "model": self.model
                }
            )

            return {
                "fixed_code": completed_code,
                "completion_log": {
                    "status": "success",
                    "file": target_path,
                    "tokens_used": getattr(response.usage, "total_tokens", "unknown"),
                    "model": self.model
                }
            }

        except Exception as e:
            self.logger.log_fix(
                file_path=target_path,
                agent="CompletionAgent",
                status="failed",
                original_code=context["migrated_code"],
                fixed_code=None,
                metadata={"error": str(e), "model": self.model}
            )

            return {
                "fixed_code": "",
                "completion_log": {
                    "status": "failed",
                    "file": target_path,
                    "error": str(e)
                }
            }
