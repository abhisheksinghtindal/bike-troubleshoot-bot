"""Chat endpoint."""
from __future__ import annotations

import json
import re
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ..config import settings
from ..services.claude import ask
from ..store import store

router = APIRouter(prefix="/api/chat", tags=["chat"])

_ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}

_INJECTION = re.compile(
    r"ignore\s+(previous|prior|all)\s+instructions?"
    r"|forget\s+(your|all)\s+"
    r"|you\s+are\s+now\s+"
    r"|new\s+instructions?\s*:"
    r"|disregard\s+(all|previous|prior)"
    r"|pretend\s+(you\s+are|to\s+be)"
    r"|act\s+as\s+(a|an)\s+",
    re.IGNORECASE,
)


@router.post("")
async def chat(
    manual_id: str = Form(...),
    question: str = Form(...),
    history: str = Form("[]"),
    image: Optional[UploadFile] = File(None),
) -> dict:
    manual = store.get(manual_id)
    if not manual:
        raise HTTPException(status_code=404, detail="Manual not found. Upload one first.")

    question = question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    if len(question) > settings.max_question_length:
        raise HTTPException(
            status_code=400,
            detail=f"Question too long (max {settings.max_question_length} characters).",
        )
    if _INJECTION.search(question):
        raise HTTPException(
            status_code=400,
            detail="Question contains disallowed content.",
        )

    image_bytes: Optional[bytes] = None
    image_media_type: Optional[str] = None
    if image is not None:
        if image.content_type not in _ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported image type {image.content_type}. Use JPEG, PNG, GIF, or WebP.",
            )
        image_bytes = await image.read()
        if len(image_bytes) > 5 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Image must be under 5 MB.")
        image_media_type = image.content_type

    try:
        parsed_history = json.loads(history)
    except (json.JSONDecodeError, ValueError):
        parsed_history = []

    try:
        result = ask(
            manual=manual,
            question=question,
            image_bytes=image_bytes,
            image_media_type=image_media_type,
            history=parsed_history,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Claude call failed: {exc}") from exc

    response: dict = {
        "manual_id": manual.id,
        "question": question,
        "answer": result["answer"],
        "model": result["model"],
        "usage": result["usage"],
    }
    if result["invalid_citations"]:
        response["warning"] = (
            f"The response cited page(s) {result['invalid_citations']} "
            f"which don't exist in this {manual.page_count}-page manual."
        )
    return response
