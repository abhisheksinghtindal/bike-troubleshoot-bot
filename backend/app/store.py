"""In-memory manual store with file-based persistence.

Manuals survive backend restarts: each is serialised as JSON under data/manuals/.
"""
from __future__ import annotations

import json
import os
import threading
import time
import uuid
from dataclasses import dataclass, field

_STORE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "manuals")


@dataclass
class Manual:
    id: str
    filename: str
    page_count: int
    pages: list[str] = field(default_factory=list)
    uploaded_at: float = field(default_factory=time.time)

    @property
    def full_text(self) -> str:
        parts = []
        for i, page in enumerate(self.pages, start=1):
            parts.append(f"<page number=\"{i}\">\n{page}\n</page>")
        return "\n".join(parts)

    @property
    def approx_tokens(self) -> int:
        return sum(len(p) for p in self.pages) // 4


class ManualStore:
    def __init__(self) -> None:
        self._store: dict[str, Manual] = {}
        self._lock = threading.Lock()
        self._ensure_dir()
        self._load_from_disk()

    def _ensure_dir(self) -> None:
        os.makedirs(_STORE_DIR, exist_ok=True)

    def _path(self, manual_id: str) -> str:
        return os.path.join(_STORE_DIR, f"{manual_id}.json")

    def _save(self, manual: Manual) -> None:
        try:
            with open(self._path(manual.id), "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "id": manual.id,
                        "filename": manual.filename,
                        "pages": manual.pages,
                        "uploaded_at": manual.uploaded_at,
                    },
                    f,
                )
        except OSError:
            pass  # disk write failing shouldn't crash the request

    def _load_from_disk(self) -> None:
        for fname in os.listdir(_STORE_DIR):
            if not fname.endswith(".json"):
                continue
            try:
                with open(os.path.join(_STORE_DIR, fname), encoding="utf-8") as f:
                    data = json.load(f)
                manual = Manual(
                    id=data["id"],
                    filename=data["filename"],
                    page_count=len(data["pages"]),
                    pages=data["pages"],
                    uploaded_at=data.get("uploaded_at", time.time()),
                )
                self._store[manual.id] = manual
            except Exception:
                pass  # skip corrupt files

    def add(self, filename: str, pages: list[str]) -> Manual:
        manual = Manual(
            id=uuid.uuid4().hex,
            filename=filename,
            page_count=len(pages),
            pages=pages,
        )
        with self._lock:
            self._store[manual.id] = manual
        self._save(manual)
        return manual

    def get(self, manual_id: str) -> Manual | None:
        with self._lock:
            return self._store.get(manual_id)

    def list_summaries(self) -> list[dict]:
        with self._lock:
            return [
                {
                    "id": m.id,
                    "filename": m.filename,
                    "page_count": m.page_count,
                    "approx_tokens": m.approx_tokens,
                    "uploaded_at": m.uploaded_at,
                }
                for m in self._store.values()
            ]


store = ManualStore()
