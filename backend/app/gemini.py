from __future__ import annotations

import base64

import httpx


def generate_summary(*, api_key: str, title: str, category: str, description: str | None, tags: str | None, mime_type: str, file_bytes: bytes) -> str:
    # Keep prompt minimal and Albanian-friendly.
    prompt = (
        "Vepro si një përmbledhës profesionist. Krijo një përmbledhje të qartë dhe gjithëpërfshirëse të dokumentit në gjuhën shqipe, "
        "duke respektuar këto udhëzime:\n\n"
        "Udhëzime:\n"
        "- Krijo një përmbledhje të detajuar, të thelluar dhe të mirëstrukturuar, duke ruajtur qartësinë dhe përmbledhtësinë.\n"
        "- Mbulo të gjitha pikat kyçe dhe idetë kryesore të tekstit origjinal, duke e kondensuar në një format të lehtë për t'u kuptuar.\n"
        "- Përfshi detaje dhe shembuj relevantë që mbështesin idetë kryesore, pa informacion të panevojshëm ose përsëritje.\n"
        "- Mbështetu vetëm në tekstin e dhënë (dokumentin dhe metadatat); mos shto informacion nga jashtë.\n"
        "- Gjatësia duhet të jetë në përpjesëtim me gjatësinë/kompleksitetin e dokumentit: mjaftueshëm e gjatë për të kapur pikat kryesore dhe detajet, "
        "por jo tepër e gjatë.\n"
        "- Organizimi: përdor tituj dhe nën-tituj të qartë për seksionet (p.sh. 'Përmbledhje', 'Kapitulli 9', 'Kapitulli 10', 'Konceptet Kryesore'). "
        "Çdo seksion shkruaje në formë paragrafësh.\n\n"
        "Shkruaj vetëm përmbledhjen (pa shpjeguar procesin).\n\n"
        f"Titulli: {title}\nKategoria: {category}\n"
        f"Përshkrimi: {description or ''}\nTags: {tags or ''}\n"
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
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
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 4096},
    }

    try:
        with httpx.Client(timeout=60) as client:
            res = client.post(url, json=payload)
        res.raise_for_status()
        out = res.json()
    except httpx.HTTPStatusError as e:
        body = None
        try:
            body = e.response.text
        except Exception:
            body = None
        raise RuntimeError(f"Gemini request failed: HTTP {e.response.status_code} {body or ''}".strip()) from e
    except Exception as e:
        raise RuntimeError(f"Gemini request failed: {e}") from e

    candidates = out.get("candidates") or []
    if not candidates:
        raise RuntimeError("Gemini returned no candidates")

    content = candidates[0].get("content") or {}
    parts = content.get("parts") or []
    text_parts = [p.get("text") for p in parts if isinstance(p, dict) and p.get("text")]
    if not text_parts:
        raise RuntimeError("Gemini returned no text")

    return "\n".join(text_parts).strip()
