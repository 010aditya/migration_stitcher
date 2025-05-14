import os

# Define the base structure and empty templates for each agent/module
project_structure = {
    "agents": {
        "mapping_loader.py": """\
# agents/mapping_loader.py

import json
from collections import defaultdict
from typing import Dict, List, Any

class MappingLoader:
    def __init__(self, mapping_file: str):
        self.mapping_file = mapping_file
        self.source_to_target = defaultdict(list)
        self.target_to_source = defaultdict(list)
        self.entries = []

    def load(self):
        with open(self.mapping_file, "r", encoding="utf-8") as f:
            raw = json.load(f)

        for entry in raw:
            source_paths = entry["sourcePath"]
            if isinstance(source_paths, str):
                source_paths = [source_paths]

            target_paths = entry["targetPath"]
            if isinstance(target_paths, str):
                target_paths = [target_paths]

            for sp in source_paths:
                for tp in target_paths:
                    self.source_to_target[sp].append(tp)
                    self.target_to_source[tp].append(sp)

            self.entries.append({
                "sourcePaths": source_paths,
                "targetPaths": target_paths,
                "sourceType": entry.get("sourceType", "Unknown"),
                "targetType": entry.get("targetType", "Unknown"),
            })

    def get_targets_for_source(self, source_path: str) -> List[str]:
        return self.source_to_target.get(source_path, [])

    def get_sources_for_target(self, target_path: str) -> List[str]:
        return self.target_to_source.get(target_path, [])

    def get_all_mappings(self) -> List[Dict[str, Any]]:
        return self.entries
""",
        "context_stitcher.py": "# agents/context_stitcher.py\n\n# TODO: implement context stitching\n",
        "fix_and_compile.py": "# agents/fix_and_compile.py\n\n# TODO: implement fix logic and compilation check\n",
        "completion_agent.py": "# agents/completion_agent.py\n\n# TODO: complete logic using legacy reference\n",
        "build_validator.py": "# agents/build_validator.py\n\n# TODO: run gradlew build and parse output\n",
        "retry_agent.py": "# agents/retry_agent.py\n\n# TODO: retry logic for fixing failing builds\n",
        "package_structure_normalizer.py": "# agents/package_structure_normalizer.py\n\n# TODO: normalize package names and imports\n",
        "migrated_file_stitcher.py": "# agents/migrated_file_stitcher.py\n\n# TODO: stitch multiple partial files into one\n",
        "gradle_setup_agent.py": "# agents/gradle_setup_agent.py\n\n# TODO: generate build.gradle, settings.gradle, and wrapper files\n",
        "fix_history_logger.py": "# agents/fix_history_logger.py\n\n# TODO: log each fix attempt for traceability\n"
    },
    "config/templates": {
        "build.gradle.template": "# Spring Boot build.gradle template\n",
        "settings.gradle.template": "# settings.gradle template\n"
    },
    "data": {
        "mapping.json": "[\n  {\n    \"sourcePath\": \"src/legacy/Example.java\",\n    \"targetPath\": \"output/com/example/Example.java\",\n    \"sourceType\": \"Service\",\n    \"targetType\": \"Service\"\n  }\n]"
    },
    "logs/fix_history": {},
    "legacy_codebase": {},
    "enterprise_framework": {},
    "migration_output": {},
}

# Root folder for your project
root_dir = "migration_assist_tool"

def create_structure(base_path, structure):
    for name, content in structure.items():
        path = os.path.join(base_path, name)
        if isinstance(content, dict):
            os.makedirs(path, exist_ok=True)
            create_structure(path, content)
        else:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

if __name__ == "__main__":
    create_structure(root_dir, project_structure)
    print(f"✅ Project structure created at: {os.path.abspath(root_dir)}")
