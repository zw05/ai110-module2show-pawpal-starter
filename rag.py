"""Simple retrieval for Ask PawPal: markdown chunking plus in-memory BM25.

Pure Python with no network access, so it is easy to test.
"""

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "do", "does", "for", "from",
    "how", "i", "in", "is", "it", "my", "of", "on", "or", "should", "that", "the",
    "to", "what", "when", "with", "your", "you",
}


@dataclass(frozen=True)
class Chunk:
    source: str   # file name, e.g. "dog-exercise.md"
    heading: str  # the "##" section heading
    text: str


def tokenize(text: str) -> list[str]:
    """Lowercase words with stopwords removed and a crude plural strip."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [w[:-1] if len(w) > 3 and w.endswith("s") else w for w in words if w not in STOPWORDS]


def load_chunks(directory) -> list[Chunk]:
    """Split every *.md file in `directory` into one chunk per '##' section."""
    chunks = []
    for path in sorted(Path(directory).glob("*.md")):
        title = path.stem
        heading, lines = None, []

        def flush():
            body = "\n".join(lines).strip()
            if heading and body:
                chunks.append(Chunk(path.name, heading, f"{title}: {heading}\n{body}"))

        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("## "):
                flush()
                heading, lines = line[3:].strip(), []
            elif line.startswith("# ") and heading is None:
                title = line[2:].strip()
            else:
                lines.append(line)
        flush()
    return chunks


class Retriever:
    """BM25 ranking over a list of chunks."""

    def __init__(self, chunks: list[Chunk], k1: float = 1.5, b: float = 0.75):
        self.chunks = chunks
        self.k1, self.b = k1, b
        self.docs = [Counter(tokenize(f"{c.heading} {c.heading} {c.text}")) for c in chunks]
        self.lengths = [sum(d.values()) for d in self.docs]
        self.avg_len = (sum(self.lengths) / len(self.lengths)) if self.lengths else 0
        df = Counter(term for d in self.docs for term in d)
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def search(self, query: str, k: int = 3, min_score: float = 1.0) -> list[tuple[Chunk, float]]:
        """Return up to k (chunk, score) pairs scoring at least `min_score`, best first."""
        terms = tokenize(query)
        scored = []
        for chunk, doc, length in zip(self.chunks, self.docs, self.lengths):
            score = 0.0
            for t in terms:
                tf = doc.get(t, 0)
                if tf:
                    norm = tf + self.k1 * (1 - self.b + self.b * length / self.avg_len)
                    score += self.idf[t] * tf * (self.k1 + 1) / norm
            if score >= min_score:
                scored.append((chunk, score))
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return scored[:k]
