# -*- coding: utf-8 -*-
"""
Telugu sankalpam output helpers: place names and Latin→Telugu for words only.
Numbers stay as ordinary digits (0–9); we do not force Telugu numerals.
"""
from __future__ import annotations

import re
from datetime import date, datetime
from typing import Union

from app.services.translation_service import translate_geographical_name

DateLike = Union[date, datetime, None]


def format_birth_date_telugu(d: DateLike) -> str:
    """Birth date: Telugu month name + ASCII year and day (no English month words)."""
    if d is None:
        return ""
    if isinstance(d, datetime):
        day = d.day
        month_key = d.strftime("%B").lower()
        year = d.year
    else:
        day = d.day
        month_key = datetime(d.year, d.month, d.day).strftime("%B").lower()
        year = d.year
    from app.services.divineapi_service import _TE_MONTHS

    month_te = _TE_MONTHS.get(month_key) or ""
    if not month_te:
        from app.services.divineapi_service import _latin_name_to_telugu

        month_te = _latin_name_to_telugu(month_key)
    return f"{year} {month_te} {day}"


def format_birth_time_telugu(tstr: str) -> str:
    """Birth time as HH:MM with ordinary digits (no AM/PM English)."""
    if not tstr or not str(tstr).strip():
        return ""
    raw = str(tstr).strip()
    m = re.match(r"^\s*(\d{1,2})\s*:\s*(\d{1,2})", raw)
    if m:
        return f"{m.group(1)}:{m.group(2)}"
    digits = re.sub(r"\D", "", raw)
    return digits if digits else raw


def force_telugu_place_segment(raw: str) -> str:
    """Known geography → Telugu; any remaining Latin → transliteration."""
    if not raw or not str(raw).strip():
        return ""
    t = translate_geographical_name(raw.strip(), "telugu")
    if re.search(r"[A-Za-z]", t):
        from app.services.divineapi_service import _latin_name_to_telugu

        t = _latin_name_to_telugu(t)
    return t.strip()


def finalize_telugu_sankalpam_text(text: str) -> str:
    """
    Post-process generated sankalpam: transliterate remaining Latin letters to Telugu.
    Numbers and punctuation are left as-is (ordinary digits 0–9).
    """
    if not text:
        return text
    from app.services.divineapi_service import _latin_name_to_telugu

    def _latin_token(m: re.Match) -> str:
        w = m.group(0)
        if not w.strip():
            return w
        return _latin_name_to_telugu(w)

    return re.sub(r"[A-Za-z][A-Za-z0-9'\-]*", _latin_token, text)
