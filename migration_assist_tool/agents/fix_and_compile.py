import os
import re
from dotenv import load_dotenv
from agents.fix_history_logger import FixHistoryLogger
from agents.context_stitcher import ContextStitcherAgent
from utils.llm_loader import get_llm

load_dotenv()

class FixAndCompileAgent:
    def __init__(self, legacy_dir, migrated_dir, enterprise_dir="", reference_dir=""):
        self.legacy_dir = legacy_dir
        self.migrated_dir = migrated_dir
        self.enterprise_dir = enterprise_dir
        self.reference_dir = reference_dir

        self.client = get_llm()
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

        updated_code, reference_fixes = self._resolve_class_and_method_links(original_code)
        updated_code, injection_fixes = self._insert_missing_injections(updated_code)

        if reference_fixes or injection_fixes:
            with open(migrated_file_path, "w", encoding="utf-8") as f:
                f.write(updated_code)
            self._cleanup_java_file(migrated_file_path)

        prompt = self._build_prompt(context, updated_code)

        try:
            response = self.client.invoke([
                {"role": "system", "content": "You are a helpful Java Spring Boot migration bot."},
                {"role": "user", "content": prompt}
            ])

            fixed_code = response.content.strip()
            with open(migrated_file_path, "w", encoding="utf-8") as f:
                f.write(fixed_code)

            self._cleanup_java_file(migrated_file_path)

            self.logger.log_fix(
                file_path=target_path,
                agent="FixAndCompileAgent",
                status="success",
                original_code=original_code,
                fixed_code=fixed_code,
                metadata={
                    "reference_fixes": reference_fixes,
                    "injection_fixes": injection_fixes
                }
            )

            return {
                "fixed_code": fixed_code,
                "fix_log": {
                    "status": "success",
                    "file": target_path,
                    "reference_fixes": reference_fixes,
                    "injection_fixes": injection_fixes
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

    def _insert_missing_injections(self, code: str) -> tuple[str, list]:
        lines = code.splitlines()
        declared_fields = re.findall(r'private\s+(\w+)\s+(\w+);', code)
        declared_vars = {var for _, var in declared_fields}
        used_vars = re.findall(r'(\w+)\.', code)

        missing = set(used_vars) - declared_vars
        fixes = []

        for var in missing:
            guessed_class = var[0].upper() + var[1:]  # e.g., userService -> UserService
            class_file = self._find_class_file(guessed_class)
            if class_file:
                inject_line = f"    @Autowired\n    private {guessed_class} {var};"
                for idx, line in enumerate(lines):
                    if line.strip().startswith("public class"):
                        lines.insert(idx + 1, inject_line)
                        fixes.append({"field": var, "injected_class": guessed_class})
                        break
        return "\n".join(lines), fixes

    def _cleanup_java_file(self, filepath):
        if filepath.endswith(".java") and os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()
            ignore_starts = ("```", "// Here", "Here is", "/*", "This method", "#", "```java", "-")
            cleaned = [
                line for line in lines
                if not any(line.strip().startswith(prefix) for prefix in ignore_starts)
            ]
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
        applied_fixes = []
        injected = re.findall(r'@Autowired\s+private\s+(\w+)\s+(\w+);', code)
        for class_name, var_name in injected:
            class_file = self._find_class_file(class_name)
            if not class_file:
                continue
            class_path = os.path.join(self.migrated_dir, class_file)
            if os.path.exists(class_path):
                with open(class_path, "r", encoding="utf-8") as f:
                    class_code = f.read()
                available_methods = re.findall(r'public\s+\w+\s+(\w+)\s*\(', class_code)
                calls = re.findall(rf'{var_name}\.(\w+)\(', code)
                for call in calls:
                    if call not in available_methods:
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
        for root, _, files in os.walk(self.migrated_dir):
            for f in files:
                if f == class_name + ".java":
                    return os.path.relpath(os.path.join(root, f), self.migrated_dir)
        return None

    def _resolve_method_fallback(self, missing_method: str, class_code: str) -> str | None:
        try:
            prompt = f"""In the following Java class, find the most semantically similar method name to '{missing_method}':

{class_code}

Only return the method name. No explanation."""
            response = self.client.invoke([
                {"role": "user", "content": prompt}
            ])
            return response.content.strip()
        except Exception:
            return None
