# agents/context_stitcher.py

import os
import re
from typing import List, Dict, Optional

class ContextStitcherAgent:
    def __init__(self, legacy_root: str, migrated_root: str, enterprise_root: Optional[str] = None):
        self.legacy_root = legacy_root
        self.migrated_root = migrated_root
        self.enterprise_root = enterprise_root

    def _read_file(self, full_path: str) -> str:
        if not os.path.exists(full_path):
            return f"// FILE NOT FOUND: {full_path}\n"
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    def _extract_method_calls(self, code: str) -> List[str]:
        # Naive method call extractor: matches `xyz();`, `xyz(param)` etc.
        matches = re.findall(r'\b(\w+)\s*\(', code)
        excluded = {'if', 'for', 'while', 'switch', 'return', 'catch', 'super', 'this', 'new'}
        return list(set([m for m in matches if m not in excluded]))

    def _extract_methods_from_legacy(self, legacy_code: str, method_names: List[str]) -> str:
        extracted = []
        for method in method_names:
            # Match method signature and body (naive but useful)
            pattern = re.compile(
                rf"(public|protected|private|static|\s)+[\w<>\[\]]+\s+{re.escape(method)}\s*\([^)]*\)\s*\{{(?:[^{{}}]*|\{{[^{{}}]*\}})*\}}",
                re.MULTILINE
            )
            matches = pattern.findall(legacy_code)
            if matches:
                extracted.extend(matches)
        return "\n\n".join(extracted)

    def build_context(
        self,
        source_paths: List[str],
        target_path: str,
        enterprise_refs: Optional[List[str]] = None
    ) -> Dict[str, str]:
        context = {}

        # ✅ Load migrated file
        migrated_full_path = os.path.join(self.migrated_root, target_path)
        migrated_code = self._read_file(migrated_full_path)
        context["migrated_code"] = migrated_code

        # ✅ Extract called methods
        called_methods = self._extract_method_calls(migrated_code)

        # ✅ Load legacy method(s)
        legacy_contents = []
        for src in source_paths:
            legacy_full_path = os.path.join(self.legacy_root, src)
            legacy_code = self._read_file(legacy_full_path)
            partial_code = self._extract_methods_from_legacy(legacy_code, called_methods)
            legacy_contents.append(f"// Extracted from: {src}\n" + partial_code)

        context["legacy_code"] = "\n\n".join(legacy_contents)

        # ✅ Load enterprise references
        enterprise_contents = []
        if self.enterprise_root and enterprise_refs:
            for ref in enterprise_refs:
                full_path = os.path.join(self.enterprise_root, ref)
                enterprise_contents.append(f"// Enterprise: {ref}\n" + self._read_file(full_path))

        context["enterprise_code"] = "\n\n".join(enterprise_contents)

        return context
