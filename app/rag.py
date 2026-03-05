from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import math
import re


TOKEN_PATTERN = re.compile(r"[a-z0-9_]+")


@dataclass(frozen=True)
class KnowledgeDoc:
    doc_id: str
    title: str
    body: str


class KnowledgeBase:
    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir
        self.docs: list[KnowledgeDoc] = []
        self.doc_term_freqs: dict[str, Counter[str]] = {}
        self.doc_freqs: Counter[str] = Counter()
        self.doc_lengths: dict[str, int] = {}
        self.avg_doc_length = 1.0
        self._docs_by_id: dict[str, KnowledgeDoc] = {}
        self._load()

    def _load(self) -> None:
        if not self.root_dir.exists():
            self.root_dir.mkdir(parents=True, exist_ok=True)

        text_files = sorted(self.root_dir.glob("*.txt"))
        if not text_files:
            return

        total_terms = 0
        for file_path in text_files:
            raw_text = file_path.read_text(encoding="utf-8")
            lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
            title = lines[0] if lines else file_path.stem
            body = " ".join(lines[1:]) if len(lines) > 1 else ""

            doc = KnowledgeDoc(doc_id=file_path.stem, title=title, body=body)
            self.docs.append(doc)
            self._docs_by_id[doc.doc_id] = doc

            tokens = self._tokenize(f"{title} {body}")
            tf = Counter(tokens)
            self.doc_term_freqs[doc.doc_id] = tf
            self.doc_lengths[doc.doc_id] = len(tokens)
            total_terms += len(tokens)

            for term in tf:
                self.doc_freqs[term] += 1

        self.avg_doc_length = total_terms / max(len(self.docs), 1)

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return TOKEN_PATTERN.findall(text.lower())

    def search(self, query: str, top_k: int = 3) -> list[KnowledgeDoc]:
        query_terms = self._tokenize(query)
        if not query_terms or not self.docs:
            return []

        k1 = 1.2
        b = 0.75
        total_docs = len(self.docs)

        scored: list[tuple[float, str]] = []
        for doc in self.docs:
            tf = self.doc_term_freqs.get(doc.doc_id, Counter())
            doc_len = self.doc_lengths.get(doc.doc_id, 1)

            score = 0.0
            for term in query_terms:
                freq = tf.get(term, 0)
                if freq == 0:
                    continue

                df = self.doc_freqs.get(term, 0)
                idf = math.log(((total_docs - df + 0.5) / (df + 0.5)) + 1.0)
                norm = freq + k1 * (1 - b + b * (doc_len / self.avg_doc_length))
                score += idf * ((freq * (k1 + 1)) / norm)

            if score > 0:
                scored.append((score, doc.doc_id))

        scored.sort(key=lambda item: item[0], reverse=True)

        ranked_docs: list[KnowledgeDoc] = []
        for _, doc_id in scored[:top_k]:
            doc = self._docs_by_id.get(doc_id)
            if doc:
                ranked_docs.append(doc)
        return ranked_docs

    @staticmethod
    def format_context(docs: list[KnowledgeDoc]) -> str:
        if not docs:
            return ""

        sections = []
        for doc in docs:
            sections.append(f"[{doc.doc_id}] {doc.title}\n{doc.body}")
        return "\n\n".join(sections)
