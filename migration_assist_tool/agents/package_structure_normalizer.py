# agents/package_structure_normalizer.py

import os
import re

class PackageStructureNormalizerAgent:
    def __init__(self, migrated_dir: str, base_package: str = "com.migrated"):
        self.migrated_dir = migrated_dir
        self.base_package = base_package

    def normalize_file(self, relative_path: str) -> dict:
        full_path = os.path.join(self.migrated_dir, relative_path)
        if not os.path.exists(full_path):
            return {"status": "skipped", "reason": "File not found", "file": relative_path}

        with open(full_path, "r", encoding="utf-8") as f:
            code = f.read()

        # Remove any existing package line
        code = re.sub(r'^\s*package\s+[\w\.]+;\s*', '', code, flags=re.MULTILINE)

        # Infer package from path
        path_after_src = relative_path.replace("\\", "/")
        if "/java/" in path_after_src:
            pkg_path = path_after_src.split("/java/", 1)[1]
        elif "/output/" in path_after_src:
            pkg_path = path_after_src.split("/output/", 1)[1]
        else:
            pkg_path = path_after_src

        package = self.base_package + '.' + '.'.join(os.path.splitext(pkg_path)[0].split('/')[:-1])
        package = package.strip('.')

        # Insert new package declaration
        fixed_code = f"package {package};\n\n{code}"

        # Write updated file
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(fixed_code)

        return {
            "status": "normalized",
            "file": relative_path,
            "new_package": package
        }

    def normalize_all(self) -> list:
        normalized = []
        for root, _, files in os.walk(self.migrated_dir):
            for file in files:
                if file.endswith(".java"):
                    rel_path = os.path.relpath(os.path.join(root, file), self.migrated_dir)
                    result = self.normalize_file(rel_path)
                    normalized.append(result)
        return normalized
