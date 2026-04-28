"""PDF text extraction with injection-pattern sanitisation."""
from __future__ import annotations

import io
import re

import pypdf


_WS = re.compile(r"[ \t]+")
_MULTI_NL = re.compile(r"\n{3,}")

# Lines in a PDF that look like system-prompt injection attempts get neutralised.
_INJECTION = re.compile(
    r"ignore\s+(previous|prior|all)\s+instructions?"
    r"|you\s+are\s+now\s+"
    r"|forget\s+(your|all)\s+"
    r"|new\s+instructions?\s*:"
    r"|system\s*:\s*you"
    r"|disregard\s+(all|previous|prior)"
    r"|act\s+as\s+(a|an)\s+"
    r"|pretend\s+(you\s+are|to\s+be)",
    re.IGNORECASE,
)


def _normalize(text: str) -> str:
    text = _WS.sub(" ", text)
    text = _MULTI_NL.sub("\n\n", text)
    return text.strip()


def _sanitize(text: str) -> str:
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        if _INJECTION.search(line):
            cleaned.append("[redacted]")
        else:
            cleaned.append(line)
    return "\n".join(cleaned)


def extract_pages(pdf_bytes: bytes) -> list[str]:
    """Extract and sanitise text from each PDF page."""
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    pages: list[str] = []
    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        pages.append(_sanitize(_normalize(text)))
    return pages


def sparse_page_ratio(pages: list[str]) -> float:
    """Fraction of pages with fewer than 50 chars — proxy for scanned content."""
    if not pages:
        return 0.0
    sparse = sum(1 for p in pages if len(p.strip()) < 50)
    return sparse / len(pages)


_BIKE_TERMS = re.compile(
    r"\b(?:engine|motorcycle|motorbike|scooter|moped|wheel|brake|throttle|clutch|"
    r"chain|sprocket|tyre|tire|carburetor|carburettor|exhaust|transmission|gearbox|"
    r"spark\s*plug|coolant|torque|crankshaft|piston|cylinder|handlebar|fork|"
    r"suspension|oil\s*filter|air\s*filter|fuel\s*tank|footpeg|kickstand|"
    r"owner.?s\s*manual|service\s*manual|workshop\s*manual|rider|riding)\b",
    re.IGNORECASE,
)

_MIN_BIKE_TERMS = 4
_SAMPLE_PAGES = 15


def is_bike_manual(pages: list[str]) -> bool:
    """Return True if the document looks like a bike/motorcycle manual."""
    sample = " ".join(pages[:_SAMPLE_PAGES])
    unique_matches = {m.group().lower().split()[0] for m in _BIKE_TERMS.finditer(sample)}
    return len(unique_matches) >= _MIN_BIKE_TERMS
