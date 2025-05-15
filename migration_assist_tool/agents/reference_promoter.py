# agents/reference_promoter.py

import os
import hashlib
import json
from typing import List, Dict, Tuple
from openai import OpenAI
from dotenv import load_dotenv

import tiktoken  # for token count
from pathlib import Path

load_dotenv()

class ReferencePromoterAgent:
    def __init__(self, reference_dir: str, cache_path: str = "data/reference_embeddings.json", model="text-embedding-3-small"):
        self.reference_dir = reference_dir
        self.cache_path = cache_path
        self.model = model
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.embeddings = {}
        self.encoder = tiktoken.encoding_for_model("gpt-4")
        self._load_or_init_cache()

    def _load_or_init_cache(self):
        if os.path.exists(self.cache_path):
            with open(self.cache_path, "r", encoding="utf-8") as f:
                self.embeddings = json.load(f)
        else:
            self.embeddings = {}

    def _save_cache(self):
        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(self.embeddings, f)

    def _hash_file(self, content: str) -> str:
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    def _list_relevant_files(self) -> List[Path]:
        valid_exts = [".java", ".gradle", ".xml", ".properties", ".yml", ".yaml", ".md"]
        paths = []
        for root, _, files in os.walk(self.reference_dir):
            for f in files:
                if any(f.endswith(ext) for ext in valid_exts):
                    paths.append(Path(root) / f)
        return paths

    def build_embedding_index(self):
        files = self._list_relevant_files()
        updated = 0
        for path in files:
            path_str = str(path)
            try:
                with open(path_str, "r", encoding="utf-8") as f:
                    content = f.read()

                content_hash = self._hash_file(content)
                if path_str in self.embeddings and self.embeddings[path_str]["hash"] == content_hash:
                    continue  # Already cached

                response = self.client.embeddings.create(
                    input=[content],
                    model=self.model
                )
                vector = response.data[0].embedding
                self.embeddings[path_str] = {
                    "hash": content_hash,
                    "embedding": vector
                }
                updated += 1
            except Exception as e:
                print(f"⚠️ Error indexing {path_str}: {e}")

        if updated > 0:
            self._save_cache()
            print(f"🔄 Updated {updated} reference embeddings.")
        else:
            print("✅ Reference embedding cache is up to date.")

    def _cosine_similarity(self, vec1, vec2):
        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        return dot / (norm1 * norm2)

    def _token_count(self, text: str) -> int:
        return len(self.encoder.encode(text))

    def search_similar_files(self, query_code: str, top_k: int = 3, max_tokens: int = 3000) -> List[Tuple[str, str]]:
        try:
            query_embed = self.client.embeddings.create(
                input=[query_code],
                model=self.model
            ).data[0].embedding
        except Exception as e:
            print(f"❌ Embedding failed for query: {e}")
            return []

        scored_files = []
        for path, meta in self.embeddings.items():
            try:
                sim = self._cosine_similarity(query_embed, meta["embedding"])
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                tokens = self._token_count(content)
                if tokens <= max_tokens:
                    scored_files.append((path, content, sim))
            except Exception:
                continue

        # Sort by similarity
        top = sorted(scored_files, key=lambda x: x[2], reverse=True)[:top_k]
        return [(path, content) for path, content, _ in top]
