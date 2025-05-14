# agents/migrated_file_stitcher.py

import os
import re
from typing import List, Dict

class MigratedFileStitcherAgent:
    def __init__(self, migrated_dir: str):
        self.migrated_dir = migrated_dir

    def stitch_files(self, target_path: str, fragment_paths: List[str]) -> dict:
        stitched_code = ""
        method_signatures = set()
        seen_imports = set()
        class_declared = False

        stitched_path = os.path.join(self.migrated_dir, target_path)
        fragments = []

        for frag_path in fragment_paths:
            full_path = os.path.join(self.migrated_dir, frag_path)
            if not os.path.exists(full_path):
                continue

            with open(full_path, "r", encoding="utf-8") as f:
                code = f.read()

            # Extract imports and deduplicate
            imports = re.findall(r'^import\s+[\w\.]+;', code, re.MULTILINE)
            for imp in imports:
                if imp not in seen_imports:
                    stitched_code += imp + "\n"
                    seen_imports.add(imp)

            # Extract class body
            match = re.search(r'(public|class).*?class\s+(\w+)\s*{', code, re.DOTALL)
            if match and not class_declared:
                class_declared = True
                header = code[:match.end()]
                stitched_code += "\n\n" + header + "\n"
            elif class_declared:
                code = re.sub(r'(public|class).*?class\s+\w+\s*{', '', code, flags=re.DOTALL)

            # Extract and deduplicate methods
            methods = re.findall(r'(public|private|protected|static|\s)+[\w<>\[\]]+\s+\w+\s*\([^)]*\)\s*{(?:[^{}]*|{[^{}]*})*}', code, re.DOTALL)
            for method in methods:
                signature = re.findall(r'\s+(\w+)\s*\(', method)
                if signature:
                    method_name = signature[0]
                    if method_name not in method_signatures:
                        stitched_code += "\n\n" + method.strip()
                        method_signatures.add(method_name)

            fragments.append(frag_path)

        stitched_code += "\n\n}"

        # Write final stitched file
        os.makedirs(os.path.dirname(stitched_path), exist_ok=True)
        with open(stitched_path, "w", encoding="utf-8") as f:
            f.write(stitched_code)

        return {
            "status": "stitched",
            "target_file": target_path,
            "fragments_used": fragments
        }
