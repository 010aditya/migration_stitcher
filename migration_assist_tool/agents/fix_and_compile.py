# agents/fix_and_compile.py

import os
from dotenv import load_dotenv
from openai import AzureOpenAI
from agents.context_stitcher import ContextStitcherAgent

class FixAndCompileAgent:
    def __init__(self, legacy_dir: str, migrated_dir: str, enterprise_dir: str = ""):
        load_dotenv()
        self.legacy_dir = legacy_dir
        self.migrated_dir = migrated_dir
        self.enterprise_dir = enterprise_dir

        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.model = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")

    def fix_file(self, target_path: str, source_paths: list, enterprise_refs: list, stitcher: ContextStitcherAgent):
        full_target_path = os.path.join(self.migrated_dir, target_path)

        if not os.path.exists(full_target_path):
            return {
                "fixed_code": "",
                "fix_log": {"status": "failed", "reason": "Target file not found", "file": target_path}
            }

        context = stitcher.build_context(
            source_paths=source_paths,
            target_path=target_path,
            enterprise_refs=enterprise_refs
        )

        # Estimate token length (approx. 4 chars per token)
        total_chars = len(context['migrated_code']) + len(context['legacy_code']) + len(context['enterprise_code'])
        approx_tokens = total_chars // 4
        if approx_tokens > 9500:
            return {
                "fixed_code": "",
                "fix_log": {
                    "status": "skipped",
                    "reason": "Stitched context too large (~%d tokens)" % approx_tokens,
                    "file": target_path
                }
            }

        prompt = f"""You are a migration assistant. Your job is to fix broken or incomplete Java code.
Only edit the code under 'MIGRATED FILE'. Use 'LEGACY FILE(S)' and 'ENTERPRISE REFERENCES' for reference.

LEGACY FILE(S):
{context['legacy_code']}

ENTERPRISE REFERENCES:
{context['enterprise_code']}

MIGRATED FILE:
{context['migrated_code']}

Your response should contain ONLY the updated Java code for the migrated file.
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a Java Spring Boot migration assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=4000
            )

            fixed_code = response.choices[0].message.content.strip()

            with open(full_target_path, "w", encoding="utf-8") as f:
                f.write(fixed_code)

            return {
                "fixed_code": fixed_code,
                "fix_log": {
                    "status": "success",
                    "file": target_path,
                    "tokens_used": response.usage.total_tokens,
                    "model": self.model,
                    "partial_context_used": True if len(context['legacy_code']) < 1000 else False
                }
            }

        except Exception as e:
            return {
                "fixed_code": "",
                "fix_log": {
                    "status": "failed",
                    "file": target_path,
                    "error": str(e)
                }
            }
