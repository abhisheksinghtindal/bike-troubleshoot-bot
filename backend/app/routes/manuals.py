"""Manual upload + listing endpoints."""
from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from ..config import settings
from ..services.pdf import extract_pages, is_bike_manual, sparse_page_ratio
from ..store import store

router = APIRouter(prefix="/api/manuals", tags=["manuals"])

_CONTEXT_WARN_TOKENS = 150_000
_SPARSE_THRESHOLD = 0.5


@router.post("")
async def upload_manual(file: UploadFile = File(...)) -> dict:
    # Validate content type / extension
    if file.content_type not in ("application/pdf", "application/x-pdf"):
        if not (file.filename or "").lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    data = await file.read()

    if len(data) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Magic-bytes check — defends against renamed non-PDF files
    if not data.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="File is not a valid PDF (bad magic bytes).")

    if len(data) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {settings.max_upload_bytes // (1024 * 1024)} MB limit.",
        )

    try:
        pages = extract_pages(data)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {exc}") from exc

    if not any(p.strip() for p in pages):
        raise HTTPException(
            status_code=400,
            detail="No text could be extracted from this PDF. It may be a scanned image — OCR is not supported.",
        )

    if not is_bike_manual(pages):
        raise HTTPException(
            status_code=422,
            detail="This doesn't look like a bike or motorcycle manual. Please upload an owner's manual or service manual for your bike.",
        )

    manual = store.add(filename=file.filename or "manual.pdf", pages=pages)

    warnings: list[str] = []
    if sparse_page_ratio(pages) >= _SPARSE_THRESHOLD:
        warnings.append(
            "More than half the pages appear to be scanned images. "
            "Answers may be incomplete for those sections."
        )
    if manual.approx_tokens > _CONTEXT_WARN_TOKENS:
        warnings.append(
            f"This manual is very large (~{manual.approx_tokens:,} tokens). "
            "Content near the end may be cut off during answering."
        )

    response: dict = {
        "id": manual.id,
        "filename": manual.filename,
        "page_count": manual.page_count,
        "approx_tokens": manual.approx_tokens,
    }
    if warnings:
        response["warnings"] = warnings
    return response


@router.get("")
async def list_manuals() -> dict:
    return {"manuals": store.list_summaries()}


@router.get("/{manual_id}")
async def get_manual(manual_id: str) -> dict:
    manual = store.get(manual_id)
    if not manual:
        raise HTTPException(status_code=404, detail="Manual not found.")
    return {
        "id": manual.id,
        "filename": manual.filename,
        "page_count": manual.page_count,
        "approx_tokens": manual.approx_tokens,
    }
