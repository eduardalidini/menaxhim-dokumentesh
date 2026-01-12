from __future__ import annotations

import base64

import httpx


def generate_summary(*, api_key: str, title: str, category: str, description: str | None, tags: str | None, mime_type: str, file_bytes: bytes) -> str:
    # Keep prompt minimal and Albanian-friendly.
    prompt = (
        "Gjenero një përmbledhje të shkurtër (5-8 fjali) në shqip për dokumentin. "
        "Përfshi qëllimin kryesor dhe pikat kryesore. Mos shpik fakte. "
        f"Titulli: {title}\nKategoria: {category}\n"
        f"Përshkrimi: {description or ''}\nTags: {tags or ''}\n"
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    data_b64 = base64.b64encode(file_bytes).decode("ascii")

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": mime_type, "data": data_b64}},
                ],
            }
        ],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 400},
    }

    with httpx.Client(timeout=60) as client:
        res = client.post(url, json=payload)
        res.raise_for_status()
        out = res.json()

    candidates = out.get("candidates") or []
    if not candidates:
        raise RuntimeError("Gemini returned no candidates")

    content = candidates[0].get("content") or {}
    parts = content.get("parts") or []
    text_parts = [p.get("text") for p in parts if isinstance(p, dict) and p.get("text")]
    if not text_parts:
        raise RuntimeError("Gemini returned no text")

    return "\n".join(text_parts).strip()
