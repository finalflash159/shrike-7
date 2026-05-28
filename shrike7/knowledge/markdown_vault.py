from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from shrike7.knowledge.base import KnowledgeDocument, KnowledgeHit

TOKEN_RE = re.compile(r"\w+", re.UNICODE)
DEFAULT_EXCLUDE_DIRS = (".obsidian", ".trash", "private")
DEFAULT_EXCLUDE_FILES = ("index.md", "log.md")
DEFAULT_INCLUDE_GLOBS = ("**/*.md",)


def fold_accents(text: str) -> str:
    text = text.replace("đ", "d").replace("Đ", "D")
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


def tokenize(text: str) -> set[str]:
    original_terms = set(TOKEN_RE.findall(text.lower()))
    folded_terms = set(TOKEN_RE.findall(fold_accents(text).lower()))
    return original_terms | folded_terms


def is_low_value_snippet_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    return stripped.startswith("#")


class MarkdownVaultKnowledgeSource:
    def __init__(
        self,
        root: str | Path,
        exclude_dirs: tuple[str, ...] = DEFAULT_EXCLUDE_DIRS,
        exclude_files: tuple[str, ...] = DEFAULT_EXCLUDE_FILES,
        include_globs: tuple[str, ...] = DEFAULT_INCLUDE_GLOBS,
        max_file_bytes: int = 256 * 1024,
    ) -> None:
        self.root = Path(root).expanduser().resolve()
        if not self.root.is_dir():
            raise FileNotFoundError(f"Knowledge vault not found: {self.root}")

        self.exclude_dirs = exclude_dirs
        self.exclude_files = exclude_files
        self.include_globs = include_globs
        self.max_file_bytes = max_file_bytes

    def _resolve_relative_path(self, path: str) -> Path:
        candidate = (self.root / path).resolve()

        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise ValueError(f"Path {path} is outside of the knowledge vault") from exc

        if candidate.suffix.lower() != ".md":
            raise ValueError(f"Only markdown files are supported: {path}")

        if self._is_excluded(candidate):
            raise ValueError(f"Path is excluded by configuration: {path}")

        return candidate

    def _is_excluded(self, path: Path) -> bool:
        rel_parts = path.relative_to(self.root).parts
        return any(part.startswith(".") or part in self.exclude_dirs for part in rel_parts)

    def read(self, path: str) -> KnowledgeDocument:
        file_path = self._resolve_relative_path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {path}")

        text = file_path.read_text(encoding="utf-8")
        rel_path = file_path.relative_to(self.root).as_posix()

        return KnowledgeDocument(
            id=rel_path,
            path=rel_path,
            title=self._extract_title(text, fallback=file_path.stem),
            text=text,
            tags=self._extract_tags(text),
        )

    def _extract_title(self, text: str, fallback: str) -> str:
        for line in text.splitlines():
            if line.startswith("# "):
                return line[2:].strip()
        return fallback

    def _extract_tags(self, text: str) -> tuple[str, ...]:
        tags = re.findall(r"(?<!\w)#([\w/-]+)", text)
        return tuple(sorted(set(tags)))

    def _iter_markdown_files(self) -> list[Path]:
        files: list[Path] = []

        for pattern in self.include_globs:
            for path in self.root.glob(pattern):
                if not path.is_file():
                    continue
                if path.name in self.exclude_files:
                    continue
                if self._is_excluded(path):
                    continue
                if path.stat().st_size > self.max_file_bytes:
                    continue
                if path.suffix.lower() != ".md":
                    continue

                files.append(path)
        return sorted(files)

    def search(self, query: str, limit: int = 5) -> list[KnowledgeHit]:
        query_terms = tokenize(query)
        if not query_terms:
            return []

        hits: list[KnowledgeHit] = []

        for path in self._iter_markdown_files():
            doc = self.read(path.relative_to(self.root).as_posix())
            score = self._score(query_terms, doc)
            if score <= 0:
                continue

            hits.append(
                KnowledgeHit(
                    document=doc,
                    score=score,
                    snippet=self._make_snippet(doc.text, query_terms),
                )
            )

        hits.sort(key=lambda hit: (-hit.score, hit.document.path))
        return hits[:limit]

    def _score(self, query_terms: set[str], doc: KnowledgeDocument) -> float:
        title_terms = tokenize(doc.title)
        path_terms = tokenize(doc.path.replace("/", " "))
        tag_terms = set()
        for tag in doc.tags:
            tag_terms.add(tag.lower())
            tag_terms.update(tokenize(tag))
        body_terms = tokenize(doc.text)

        return (
            4.0 * len(query_terms & title_terms) +
            3.0 * len(query_terms & path_terms) +
            2.0 * len(query_terms & tag_terms) +
            1.0 * len(query_terms & body_terms)
        )

    def _make_snippet(self, text: str, query_terms: set[str], max_chars: int = 500) -> str:
        lines = text.splitlines()
        best_index: int | None = None
        best_score = 0

        for index, line in enumerate(lines):
            if is_low_value_snippet_line(line):
                continue

            line_terms = tokenize(line)
            score = len(query_terms & line_terms)
            if score > best_score:
                best_index = index
                best_score = score

        if best_index is not None:
            start = max(0, best_index - 2)
            end = min(len(lines), best_index + 5)
            snippet = "\n".join(
                candidate for candidate in lines[start:end] if not is_low_value_snippet_line(candidate)
            )
            return snippet if len(snippet) <= max_chars else snippet[:max_chars] + "..."

        for line in lines:
            if not is_low_value_snippet_line(line):
                snippet = line.strip()
                return snippet if len(snippet) <= max_chars else snippet[:max_chars] + "..."

        return ""
