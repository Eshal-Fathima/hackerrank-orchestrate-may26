"""
retriever.py — Loads the local support corpus and retrieves relevant chunks
using TF-IDF style keyword scoring. No external dependencies beyond stdlib.
"""

import re
import math
from pathlib import Path
from collections import defaultdict


class CorpusRetriever:
    def __init__(self, data_path: Path, chunk_size: int = 400, overlap: int = 80):
        self.data_path = data_path
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.chunks = []       # list of {"text": str, "source": str, "company": str, "area": str}
        self.idf = {}
        self._load()
        self._build_idf()

    def _load(self):
        for company_dir in sorted(self.data_path.iterdir()):
            if not company_dir.is_dir():
                continue
            company = company_dir.name  # claude, hackerrank, visa

            for md_file in company_dir.rglob("*.md"):
                # Derive area from parent folder name relative to company dir
                try:
                    rel = md_file.relative_to(company_dir)
                    area = rel.parts[0] if len(rel.parts) > 1 else company
                except Exception:
                    area = company

                text = md_file.read_text(encoding="utf-8", errors="ignore")
                text = self._clean(text)

                # Split into overlapping chunks
                words = text.split()
                for start in range(0, max(1, len(words) - self.overlap), self.chunk_size - self.overlap):
                    chunk_words = words[start: start + self.chunk_size]
                    chunk_text = " ".join(chunk_words)
                    if len(chunk_text.strip()) < 30:
                        continue
                    self.chunks.append({
                        "text": chunk_text,
                        "source": str(md_file),
                        "company": company,
                        "area": area,
                    })

    def _clean(self, text: str) -> str:
        # Remove markdown links, images, HTML tags, excessive whitespace
        text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
        text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"#{1,6}\s*", "", text)
        text = re.sub(r"[*_`~>|]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _tokenize(self, text: str):
        return re.findall(r"[a-z0-9]+", text.lower())

    def _build_idf(self):
        N = len(self.chunks)
        if N == 0:
            return
        df = defaultdict(int)
        for chunk in self.chunks:
            tokens = set(self._tokenize(chunk["text"]))
            for t in tokens:
                df[t] += 1
        self.idf = {t: math.log((N + 1) / (freq + 1)) + 1 for t, freq in df.items()}

    def _score(self, chunk_text: str, query_tokens: list) -> float:
        tokens = self._tokenize(chunk_text)
        tf = defaultdict(int)
        for t in tokens:
            tf[t] += 1
        total = len(tokens) or 1
        score = 0.0
        for qt in query_tokens:
            if qt in tf:
                tfidf = (tf[qt] / total) * self.idf.get(qt, 1.0)
                score += tfidf
        return score

    def retrieve(self, query: str, company: str = None, top_k: int = 5) -> list:
        """Return top_k most relevant chunks for the query."""
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        scored = []
        for chunk in self.chunks:
            # Boost chunks from the matching company
            company_boost = 1.5 if (company and company.lower() in chunk["company"].lower()) else 1.0
            score = self._score(chunk["text"], query_tokens) * company_boost
            if score > 0:
                scored.append((score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in scored[:top_k]]

    def doc_count(self) -> int:
        return len(self.chunks)