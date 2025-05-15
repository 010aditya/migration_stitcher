import os
from agents.reference_promoter import ReferencePromoterAgent

class ContextStitcherAgent:
    def __init__(self, legacy_dir, migrated_dir, enterprise_dir="", reference_dir=""):
        self.legacy_dir = legacy_dir
        self.migrated_dir = migrated_dir
        self.enterprise_dir = enterprise_dir
        self.reference_dir = reference_dir

        self.promoter = None
        if reference_dir:
            self.promoter = ReferencePromoterAgent(reference_dir)
            self.promoter.build_embedding_index()

    def build_context(self, source_paths, target_path, enterprise_refs):
        migrated_code = self._read_file(self.migrated_dir, target_path)
        context = {
            "legacy_code": self._read_files(self.legacy_dir, source_paths),
            "migrated_code": migrated_code,
            "enterprise_code": self._read_files(self.enterprise_dir, enterprise_refs) if self.enterprise_dir else "",
            "reference_code": self._get_reference_code(migrated_code) if self.promoter else ""
        }
        return context

    def _read_files(self, base_dir, paths):
        code_blocks = []
        for path in paths:
            full_path = os.path.join(base_dir, path)
            if os.path.exists(full_path):
                with open(full_path, "r", encoding="utf-8") as f:
                    code_blocks.append(f.read())
        return "\n\n".join(code_blocks)

    def _read_file(self, base_dir, path):
        full_path = os.path.join(base_dir, path)
        if os.path.exists(full_path):
            with open(full_path, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    def _get_reference_code(self, migrated_code):
        top_matches = self.promoter.search_similar_files(migrated_code, top_k=2, max_tokens=3000)
        return "\n\n".join(content for _, content in top_matches)
