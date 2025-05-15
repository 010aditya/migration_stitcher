# agents/fix_and_compile.py

import os
import re
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

        original_code = context["migrated_code"]

        # 🔍 Step 1: Resolve injected class references + validate method usage
        updated_code, reference_fixes = self._resolve_class_and_method_links(original_code)

        # 🔁 Step 2: If fixes were applied, update migrated file before prompting LLM
        if reference_fixes:
            with open(migrated_file_path, "w", encoding="utf-8") as f:
                f.write(updated_code)
            self._cleanup_java_file(migrated_file_path)

        # 🤖 Step 3: GPT to refine fixed code using full stitched context
        prompt = self._build_prompt(context, updated_code)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a Java Spring Boot migration bot."},
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
                original_code=original_code,
                fixed_code=fixed_code,
                metadata={"model": self.model, "reference_fixes": reference_fixes}
            )

            return {
                "fixed_code": fixed_code,
                "fix_log": {
                    "status": "success",
                    "file": target_path,
                    "model": self.model,
                    "reference_fixes": reference_fixes
                }
            }

        except Exception as e:
            self.logger.log_fix(
                file_path=target_path,
                agent="FixAndCompileAgent",
                status="failed",
                original_code=original_code,
                fixed_code=None,
                metadata={"error": str(e)}
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

    def _build_prompt(self, context, migrated_code):
        return f"""You are a Java code migration assistant.

Your job is to complete or correct the 'MIGRATED FILE'.
Refer to 'LEGACY CODE', 'ENTERPRISE REFERENCES', and 'REFERENCE CODE' for correctness.

Only return the corrected Java file.

LEGACY CODE:
{context['legacy_code']}

ENTERPRISE REFERENCES:
{context['enterprise_code']}

REFERENCE CODE:
{context['reference_code']}

MIGRATED FILE:
{migrated_code}
"""

    def _resolve_class_and_method_links(self, code: str) -> tuple[str, list]:
        """
        Scans the file for injected class references and verifies method calls.
        Returns updated code and list of changes applied.
        """
        applied_fixes = []

        # Step 1: Find all injected classes (via @Autowired or constructor)
        injected = re.findall(r'@Autowired\s+private\s+(\w+)\s+(\w+);', code)
        for class_name, var_name in injected:
            class_file = self._find_class_file(class_name)
            if not class_file:
                continue

            # Step 2: Load that class file and extract available method names
            class_path = os.path.join(self.migrated_dir, class_file)
            if os.path.exists(class_path):
                with open(class_path, "r", encoding="utf-8") as f:
                    class_code = f.read()
                available_methods = re.findall(r'public\s+\w+\s+(\w+)\s*\(', class_code)

                # Step 3: Check for usages of that injected variable
                calls = re.findall(rf'{var_name}\.(\w+)\(', code)
                for call in calls:
                    if call not in available_methods:
                        # 🔁 Try to resolve method name using reference or legacy
                        suggestion = self._resolve_method_fallback(call, class_code)
                        if suggestion and suggestion != call:
                            code = code.replace(f"{var_name}.{call}(", f"{var_name}.{suggestion}(")
                            applied_fixes.append({
                                "var": var_name,
                                "class": class_name,
                                "method": call,
                                "suggested_method": suggestion
                            })

        return code, applied_fixes

    def _find_class_file(self, class_name: str) -> str | None:
        """
        Looks for a .java file in migrated_dir that matches class_name.
        """
        for root, _, files in os.walk(self.migrated_dir):
            for f in files:
                if f == class_name + ".java":
                    return os.path.relpath(os.path.join(root, f), self.migrated_dir)
        return None

    def _resolve_method_fallback(self, missing_method: str, class_code: str) -> str | None:
        """
        Fallback: Use GPT to find best method match in given class code.
        """
        try:
            prompt = f"""In the following Java class, find the most semantically similar method name to '{missing_method}':

{class_code}

Only return the matching method name, nothing else."""
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=20
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return None
