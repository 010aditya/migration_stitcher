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
            source_paths = entry.get("source", [])
            target_paths = entry.get("target", [])
            source_type = entry.get("source_component_type", "Unknown")
            target_type = entry.get("target_component_type", "Unknown")

            for sp in source_paths:
                for tp in target_paths:
                    self.source_to_target[sp].append(tp)
                    self.target_to_source[tp].append(sp)

            self.entries.append({
                "sourcePaths": source_paths,
                "targetPaths": target_paths,
                "sourceType": source_type,
                "targetType": target_type,
            })

    def get_targets_for_source(self, source_path: str) -> List[str]:
        return self.source_to_target.get(source_path, [])

    def get_sources_for_target(self, target_path: str) -> List[str]:
        return self.target_to_source.get(target_path, [])

    def get_all_mappings(self) -> List[Dict[str, Any]]:
        return self.entries
