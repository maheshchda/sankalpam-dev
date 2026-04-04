"""
Panchang (Hindu almanac) router.

GET /api/panchang/today
  Returns today's Tithi, Vara, Nakshatra, Yoga, Karana with per-element
  auspiciousness scores (green / yellow / red) and personalised Tarabala
  when the user has a Janma Nakshatra on their profile.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta, timezone

from app.database import get_db
from app.routers.auth import get_current_user
from app.models import User, FamilyMember
from app.services.divineapi_service import (
    _fetch_panchang_for_today,
    _fallback_panchang_for_today,
)

router = APIRouter()

# ── Durmuhurta windows (fixed by weekday, approx. standard Indian times) ──────
# Each entry: list of (start_hhmm, end_hhmm) tuples for that weekday.
# Source: classical Muhurta texts; times are approximate local time.
_DURMUHURTA: dict[str, list[tuple[str, str]]] = {
    "Monday":    [("12:24", "13:12")],
    "Tuesday":   [("08:24", "09:12"), ("23:12", "00:00")],
    "Wednesday": [("11:36", "12:24")],
    "Thursday":  [("10:00", "10:48")],
    "Friday":    [("10:48", "11:36")],
    "Saturday":  [("05:48", "06:36")],
    "Sunday":    [("16:24", "17:12")],
}

# Rahu Kala (inauspicious 90-min window each weekday, starting from sunrise ~06:00)
_RAHU_KALA: dict[str, tuple[str, str]] = {
    "Monday":    ("07:30", "09:00"),
    "Tuesday":   ("15:00", "16:30"),
    "Wednesday": ("12:00", "13:30"),
    "Thursday":  ("13:30", "15:00"),
    "Friday":    ("10:30", "12:00"),
    "Saturday":  ("09:00", "10:30"),
    "Sunday":    ("16:30", "18:00"),
}


def _hhmm_to_minutes(t: str) -> int:
    """Convert HH:MM string to minutes since midnight."""
    try:
        h, m = t.split(":")
        return int(h) * 60 + int(m)
    except Exception:
        return -1


def _durmuhurta_status(weekday: str, now: datetime) -> dict:
    """
    Returns whether we are currently in a Durmuhurta or Rahu Kala window,
    plus all windows for today so the user knows what to avoid.
    """
    current_min = now.hour * 60 + now.minute
    windows = _DURMUHURTA.get(weekday, [])
    rahu     = _RAHU_KALA.get(weekday)

    in_durmuhurta = False
    next_durmuhurta: Optional[str] = None
    for (start, end) in windows:
        s = _hhmm_to_minutes(start)
        e = _hhmm_to_minutes(end)
        if s <= current_min < e:
            in_durmuhurta = True
        elif current_min < s and next_durmuhurta is None:
            next_durmuhurta = f"{start}–{end}"

    in_rahu = False
    if rahu:
        rs = _hhmm_to_minutes(rahu[0])
        re = _hhmm_to_minutes(rahu[1])
        if rs <= current_min < re:
            in_rahu = True

    return {
        "in_durmuhurta":   in_durmuhurta,
        "in_rahu_kala":    in_rahu,
        "durmuhurta_windows": [f"{s}–{e}" for s, e in windows],
        "rahu_kala_window":   f"{rahu[0]}–{rahu[1]}" if rahu else None,
        "next_durmuhurta":    next_durmuhurta,
    }


# ── Auspiciousness tables ─────────────────────────────────────────────────────

# Tithi score: based on classical Nanda/Bhadra/Jaya/Rikta/Purna classification
_TITHI_SCORE: dict[str, tuple[str, str]] = {
    # Nanda (1, 6, 11) — social & festive
    "pratipada":   ("green",  "Nanda Tithi — Auspicious"),
    "prathama":    ("green",  "Nanda Tithi — Auspicious"),
    "shashthi":    ("green",  "Nanda Tithi — Auspicious"),
    "ekadashi":    ("green",  "Nanda Tithi — Very Auspicious"),
    # Bhadra (2, 7, 12) — learning & travel
    "dvitiya":     ("green",  "Bhadra Tithi — Auspicious"),
    "saptami":     ("green",  "Bhadra Tithi — Auspicious"),
    "dvadashi":    ("green",  "Bhadra Tithi — Auspicious"),
    # Jaya (3, 8, 13)
    "tritiya":     ("green",  "Jaya Tithi — Auspicious"),
    "ashtami":     ("yellow", "Jaya Tithi — Moderate"),
    "trayodashi":  ("yellow", "Jaya Tithi — Moderate"),
    # Rikta (4, 9, 14) — inauspicious for new beginnings
    "chaturthi":   ("red",    "Rikta Tithi — Avoid new starts"),
    "navami":      ("red",    "Rikta Tithi — Avoid new starts"),
    "chaturdashi": ("red",    "Rikta Tithi — Avoid new starts"),
    # Purna (5, 10, 15/Purnima) + Amavasya
    "panchami":    ("green",  "Purna Tithi — Auspicious"),
    "dashami":     ("green",  "Purna Tithi — Auspicious"),
    "purnima":     ("green",  "Purna Tithi — Very Auspicious"),
    "amavasya":    ("red",    "Amavasya — Inauspicious for new work"),
}

# Vara (weekday) score
_VARA_SCORE: dict[str, tuple[str, str]] = {
    "monday":    ("yellow", "Soma Vara — Moderate"),
    "tuesday":   ("red",    "Mangala Vara — Avoid new beginnings"),
    "wednesday": ("green",  "Budha Vara — Auspicious"),
    "thursday":  ("green",  "Guru Vara — Very Auspicious"),
    "friday":    ("green",  "Shukra Vara — Auspicious"),
    "saturday":  ("yellow", "Shani Vara — Moderate"),
    "sunday":    ("yellow", "Ravi Vara — Moderate"),
}

# Nakshatra score: based on classical Gana classification
_NAKSHATRA_SCORE: dict[str, tuple[str, str]] = {
    # Laghu / Kshipra (Swift) — Green
    "ashwini":            ("green",  "Kshipra — Auspicious"),
    "pushya":             ("green",  "Kshipra — Auspicious"),
    "hasta":              ("green",  "Kshipra — Auspicious"),
    # Mridu (Soft) — Green
    "mrigashira":         ("green",  "Mridu — Auspicious"),
    "chitra":             ("green",  "Mridu — Auspicious"),
    "anuradha":           ("green",  "Mridu — Auspicious"),
    "revati":             ("green",  "Mridu — Auspicious"),
    # Dhruva (Fixed) — Green
    "rohini":             ("green",  "Dhruva — Very Auspicious"),
    "uttara phalguni":    ("green",  "Dhruva — Auspicious"),
    "uttara ashadha":     ("green",  "Dhruva — Auspicious"),
    "uttara bhadrapada":  ("green",  "Dhruva — Auspicious"),
    # Chara (Movable) — Green
    "punarvasu":          ("green",  "Chara — Auspicious"),
    "swati":              ("green",  "Chara — Auspicious"),
    "shravana":           ("green",  "Chara — Auspicious"),
    "dhanishta":          ("green",  "Chara — Auspicious"),
    "shatabhisha":        ("green",  "Chara — Auspicious"),
    # Mishra (Mixed) — Yellow
    "krittika":           ("yellow", "Mishra — Moderate"),
    "vishakha":           ("yellow", "Mishra — Moderate"),
    # Ugra (Fierce) — Yellow
    "bharani":            ("yellow", "Ugra — Moderate"),
    "magha":              ("yellow", "Ugra — Moderate"),
    "purva phalguni":     ("yellow", "Ugra — Moderate"),
    "purva ashadha":      ("yellow", "Ugra — Moderate"),
    "purva bhadrapada":   ("yellow", "Ugra — Moderate"),
    # Tikshna / Daruna (Sharp) — Red
    "ardra":              ("red",    "Tikshna — Inauspicious"),
    "ashlesha":           ("red",    "Tikshna — Inauspicious"),
    "jyeshtha":           ("red",    "Tikshna — Inauspicious"),
    "mula":               ("red",    "Tikshna — Inauspicious"),
}

# Nakshatra order (1–27) for Tarabala calculation
_NAK_ORDER = [
    "ashwini", "bharani", "krittika", "rohini", "mrigashira", "ardra",
    "punarvasu", "pushya", "ashlesha", "magha", "purva phalguni", "uttara phalguni",
    "hasta", "chitra", "swati", "vishakha", "anuradha", "jyeshtha",
    "mula", "purva ashadha", "uttara ashadha", "shravana", "dhanishta",
    "shatabhisha", "purva bhadrapada", "uttara bhadrapada", "revati",
]

# Tarabala: 1–9 cycle from Janma Nakshatra
_TARABALA: dict[int, tuple[str, str]] = {
    1: ("yellow", "Janma — Proceed with caution"),
    2: ("green",  "Sampat — Very Auspicious"),
    3: ("red",    "Vipat — Avoid"),
    4: ("green",  "Kshema — Beneficial"),
    5: ("red",    "Pratyak — Avoid"),
    6: ("green",  "Sadhana — Good for effort"),
    7: ("red",    "Naidhana — Avoid"),
    8: ("green",  "Mitra — Friendly"),
    9: ("green",  "Param Mitra — Very Auspicious"),
}


# ── Nakshatra → primary Rasi mapping (Moon sign for today's nakshatra) ────────
_NAK_TO_RASI: dict[str, str] = {
    "ashwini":           "Mesha",    "bharani":           "Mesha",
    "krittika":          "Vrishabha","rohini":            "Vrishabha",
    "mrigashira":        "Mithuna",  "ardra":             "Mithuna",
    "punarvasu":         "Mithuna",  "pushya":            "Karka",
    "ashlesha":          "Karka",    "magha":             "Simha",
    "purva phalguni":    "Simha",    "uttara phalguni":   "Kanya",
    "hasta":             "Kanya",    "chitra":            "Tula",
    "swati":             "Tula",     "vishakha":          "Tula",
    "anuradha":          "Vrischika","jyeshtha":          "Vrischika",
    "mula":              "Dhanu",    "purva ashadha":     "Dhanu",
    "uttara ashadha":    "Makara",   "shravana":          "Makara",
    "dhanishta":         "Makara",   "shatabhisha":       "Kumbha",
    "purva bhadrapada":  "Kumbha",   "uttara bhadrapada": "Meena",
    "revati":            "Meena",
}

# Rasi order for Chandra Balam count
_RASI_ORDER = [
    "Mesha", "Vrishabha", "Mithuna", "Karka",
    "Simha", "Kanya",     "Tula",    "Vrischika",
    "Dhanu", "Makara",    "Kumbha",  "Meena",
]

# Chandra Balam: 1=position of moon from Janma Rasi (1-indexed, cyclic)
# 1→Janma(medium), 2→inauspicious, 3→good, 4→inauspicious, 5→medium,
# 6→good, 7→good, 8→inauspicious, 9→medium, 10→good, 11→good, 12→inauspicious
_CHANDRA_BALAM: dict[int, tuple[str, str]] = {
    1:  ("yellow", "Janma Rasi — Moon in your birth sign, proceed with caution"),
    2:  ("red",    "No Chandra Balam — Moon 2nd from Janma Rasi, avoid new starts"),
    3:  ("green",  "Chandra Balam — Moon 3rd from Janma Rasi, auspicious"),
    4:  ("red",    "No Chandra Balam — Moon 4th from Janma Rasi, inauspicious"),
    5:  ("yellow", "Moderate Chandra Balam — Moon 5th from Janma Rasi"),
    6:  ("green",  "Chandra Balam — Moon 6th from Janma Rasi, auspicious"),
    7:  ("green",  "Chandra Balam — Moon 7th from Janma Rasi, auspicious"),
    8:  ("red",    "No Chandra Balam — Moon 8th from Janma Rasi, inauspicious"),
    9:  ("yellow", "Moderate Chandra Balam — Moon 9th from Janma Rasi"),
    10: ("green",  "Chandra Balam — Moon 10th from Janma Rasi, auspicious"),
    11: ("green",  "Chandra Balam — Moon 11th from Janma Rasi, auspicious"),
    12: ("red",    "No Chandra Balam — Moon 12th from Janma Rasi, inauspicious"),
}


def _get_current_rasi(nakshatra: str) -> Optional[str]:
    """Return the Rasi the Moon is in today based on today's nakshatra."""
    return _NAK_TO_RASI.get(_norm(nakshatra))


def _chandra_balam(janma_rasi: str, today_rasi: str) -> Optional[tuple[int, str, str]]:
    """
    Returns (position, score, label) for Chandra Balam, or None if either Rasi unknown.
    Position is 1-indexed count from Janma Rasi to today's Moon Rasi (cyclic over 12).
    """
    j = janma_rasi.strip().title()
    t = today_rasi.strip().title()
    # Normalise variants
    rasi_aliases = {
        "aries": "Mesha", "taurus": "Vrishabha", "gemini": "Mithuna",
        "cancer": "Karka", "leo": "Simha", "virgo": "Kanya",
        "libra": "Tula", "scorpio": "Vrischika", "sagittarius": "Dhanu",
        "capricorn": "Makara", "aquarius": "Kumbha", "pisces": "Meena",
        "karkataka": "Karka", "karkkataka": "Karka", "vrishchika": "Vrischika",
    }
    j = rasi_aliases.get(j.lower(), j)
    t = rasi_aliases.get(t.lower(), t)

    # Find indices
    j_idx = next((i for i, r in enumerate(_RASI_ORDER) if r.lower() == j.lower()), None)
    t_idx = next((i for i, r in enumerate(_RASI_ORDER) if r.lower() == t.lower()), None)
    if j_idx is None or t_idx is None:
        return None
    position = ((t_idx - j_idx) % 12) + 1
    score, label = _CHANDRA_BALAM[position]
    return (position, score, label)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _norm(s: str) -> str:
    return (s or "").strip().lower()


def _lookup(value: str, table: dict) -> tuple[str, str]:
    """Case-insensitive lookup with partial-match fallback."""
    v = _norm(value)
    if v in table:
        return table[v]
    for key, val in table.items():
        if key in v or v in key:
            return val
    return ("yellow", "Moderate")


def _tarabala(janma: str, today: str) -> Optional[tuple[int, str, str]]:
    """
    Returns (tara_number, score, label) or None if either nakshatra unknown.
    Tara is 1-9, cycling through the 27 nakshatras from the Janma Nakshatra.
    """
    j = _norm(janma)
    t = _norm(today)
    j_idx = next((i for i, n in enumerate(_NAK_ORDER) if j in n or n in j), None)
    t_idx = next((i for i, n in enumerate(_NAK_ORDER) if t in n or n in t), None)
    if j_idx is None or t_idx is None:
        return None
    count = ((t_idx - j_idx) % 27) + 1
    tara  = ((count - 1) % 9) + 1
    score, label = _TARABALA[tara]
    return (tara, score, label)


def _overall(scores: list[str]) -> str:
    """
    Aggregate: 2+ reds → red; 1 red → yellow; 2+ greens → green; else yellow.
    """
    reds   = scores.count("red")
    greens = scores.count("green")
    if reds >= 2:
        return "red"
    if reds == 1:
        return "yellow"
    if greens >= 2:
        return "green"
    return "yellow"


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.get("/today")
async def get_today_panchang(
    lat: Optional[float] = Query(None, description="Latitude of user's current location"),
    lon: Optional[float] = Query(None, description="Longitude of user's current location"),
    timezone_offset: float = Query(0.0, description="Browser timezone offset in hours (e.g. -5 for EST)"),
    member_id: Optional[int] = Query(None, description="Family member ID to personalise for (omit for self)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return today's Panchang with auspiciousness scoring.
    Personalises Tarabala + Chandra Balam for the logged-in user or a selected family member.
    Uses user's current location: lat/lon when provided, else profile (current_city, state, country).
    Date/weekday are computed in the user's timezone (from timezone_offset) so they match the browser.
    """
    utc_now = datetime.now(timezone.utc)
    now = utc_now + timedelta(hours=timezone_offset)

    # When lat/lon missing, use user's profile location for place-based lookup
    loc_city = ""
    loc_state = ""
    loc_country = ""
    if lat is None and lon is None:
        loc_city = (getattr(current_user, "current_city", None) or "").strip()
        loc_state = (getattr(current_user, "current_state", None) or "").strip()
        loc_country = (getattr(current_user, "current_country", None) or "").strip()

    panchang = await _fetch_panchang_for_today(
        now=now,
        location_city=loc_city,
        location_state=loc_state,
        location_country=loc_country,
        latitude=str(lat) if lat is not None else None,
        longitude=str(lon) if lon is not None else None,
        timezone_offset_hours=timezone_offset,
        language="en",
    )
    if not panchang:
        panchang = _fallback_panchang_for_today(now)

    weekday           = now.strftime("%A")
    tithi             = panchang.get("tithi", "")
    tithi_end_time    = panchang.get("tithi_end_time", "")
    nakshatra         = panchang.get("nakshatra", "")
    nakshatra_end_time = panchang.get("nakshatra_end_time", "")
    yoga              = panchang.get("yoga", "")
    karana            = panchang.get("karana", "")

    vara_score,  vara_label  = _lookup(weekday,   _VARA_SCORE)
    tithi_score, tithi_label = _lookup(tithi,     _TITHI_SCORE)
    nak_score,   nak_label   = _lookup(nakshatra, _NAKSHATRA_SCORE)

    # Durmuhurta & Rahu Kala status
    dm = _durmuhurta_status(weekday, now)

    # Override scores if currently in an inauspicious window
    if dm["in_durmuhurta"] or dm["in_rahu_kala"]:
        vara_score  = "red"
        vara_label  = f"{'Durmuhurta' if dm['in_durmuhurta'] else 'Rahu Kala'} active — avoid new starts"

    # Resolve subject: family member (if member_id given) or logged-in user
    subject_name    = f"{current_user.first_name} {current_user.last_name}".strip()
    subject_is_self = True
    if member_id:
        member = db.query(FamilyMember).filter(
            FamilyMember.id == member_id,
            FamilyMember.user_id == current_user.id,
        ).first()
        if not member:
            raise HTTPException(status_code=404, detail="Family member not found")
        janma_nak    = getattr(member, "birth_nakshatra", None) or ""
        janma_rasi   = getattr(member, "birth_rashi",     None) or ""
        subject_name = member.name
        subject_is_self = False
    else:
        janma_nak    = getattr(current_user, "birth_nakshatra", None) or ""
        janma_rasi   = getattr(current_user, "birth_rashi",     None) or ""

    # Tarabala
    tara_result  = None
    is_janma_day = False
    if janma_nak and nakshatra:
        tb = _tarabala(janma_nak, nakshatra)
        if tb:
            tara_result = {"num": tb[0], "score": tb[1], "label": tb[2]}
        if _norm(janma_nak) in _norm(nakshatra) or _norm(nakshatra) in _norm(janma_nak):
            is_janma_day = True

    # Chandra Balam
    chandra_result = None
    today_rasi = _get_current_rasi(nakshatra)
    if janma_rasi and today_rasi:
        cb = _chandra_balam(janma_rasi, today_rasi)
        if cb:
            chandra_result = {
                "position": cb[0], "score": cb[1], "label": cb[2],
                "today_rasi": today_rasi, "janma_rasi": janma_rasi,
            }

    # Build Tithi detail string (with end time + Durmuhurta windows)
    tithi_detail_parts = [tithi_label]
    if tithi_end_time:
        tithi_detail_parts.append(f"Ends at {tithi_end_time}")
    if dm["durmuhurta_windows"]:
        tithi_detail_parts.append(
            "Durmuhurta today: " + ", ".join(dm["durmuhurta_windows"])
        )
    if dm["rahu_kala_window"]:
        tithi_detail_parts.append(f"Rahu Kala: {dm['rahu_kala_window']}")
    if dm["in_durmuhurta"]:
        tithi_detail_parts.append("⚠ Durmuhurta is ACTIVE right now")
    elif dm["in_rahu_kala"]:
        tithi_detail_parts.append("⚠ Rahu Kala is ACTIVE right now")
    elif dm["next_durmuhurta"]:
        tithi_detail_parts.append(f"Next Durmuhurta: {dm['next_durmuhurta']}")

    # Build Nakshatra detail string (with end time)
    nak_detail_parts = [nak_label]
    if nakshatra_end_time:
        nak_detail_parts.append(f"Ends at {nakshatra_end_time}")

    # Aggregate scores
    base_scores = [vara_score, tithi_score, nak_score]
    if tara_result:
        base_scores.append(tara_result["score"])
    if chandra_result:
        base_scores.append(chandra_result["score"])
    if dm["in_durmuhurta"] or dm["in_rahu_kala"]:
        base_scores.append("red")
    overall = _overall(base_scores)

    # Build ticker segments
    segments = [
        {"label": "Vara",      "value": weekday,  "score": vara_score,  "detail": vara_label},
        {"label": "Tithi",     "value": tithi,    "score": tithi_score, "detail": " · ".join(tithi_detail_parts)},
        {"label": "Nakshatra", "value": nakshatra,"score": nak_score,   "detail": " · ".join(nak_detail_parts)},
        {"label": "Yoga",      "value": yoga,     "score": "yellow",    "detail": ""},
        {"label": "Karana",    "value": karana,   "score": "yellow",    "detail": ""},
    ]
    if tara_result:
        segments.append({
            "label":  "Taara Balam",
            "value":  tara_result["label"].split(" — ")[0],
            "score":  tara_result["score"],
            "detail": tara_result["label"],
        })
    if chandra_result:
        segments.append({
            "label":  "Chandra Balam",
            "value":  f"Moon in {chandra_result['today_rasi']} ({chandra_result['position']}th from {chandra_result['janma_rasi']})",
            "score":  chandra_result["score"],
            "detail": chandra_result["label"],
        })
    if is_janma_day:
        segments.append({
            "label":  "⭐ Janma Nakshatra",
            "value":  "Today is Janma Nakshatra day",
            "score":  "yellow",
            "detail": "Observe caution; good for spiritual practices",
        })

    return {
        "date":               now.strftime("%A, %d %B %Y"),
        "weekday":            weekday,
        "tithi":              tithi,
        "tithi_end_time":     tithi_end_time,
        "nakshatra":          nakshatra,
        "nakshatra_end_time": nakshatra_end_time,
        "yoga":               yoga,
        "karana":             karana,
        "overall":            overall,
        "segments":           segments,
        "durmuhurta":         dm,
        "is_janma_day":       is_janma_day,
        "personalized":       bool(tara_result or chandra_result),
        "subject_name":       subject_name,
        "subject_is_self":    subject_is_self,
        "janma_nakshatra":    janma_nak,
        "janma_rasi":         janma_rasi,
        "today_rasi":         today_rasi or "",
        "chandra_balam":      chandra_result,
    }


@router.get("/kp-chart")
async def get_kp_cuspal_chart(
    lat: float = Query(..., description="Latitude (required for Placidus cusps)"),
    lon: float = Query(..., description="Longitude (required for Placidus cusps)"),
    timezone_offset: float = Query(0.0, description="Browser TZ offset hours from UTC"),
    current_user: User = Depends(get_current_user),
):
    """
    Krishnamurti-style snapshot: sidereal Sun/Moon, Moon sub-lord, 12 Placidus cusp longitudes
    with cuspal sub-lords (Swiss Ephemeris + Krishnamurti ayanamsa on the server).
    """
    try:
        from app.services.swiss_ephemeris_engine import (
            compute_kp_chart,
            julian_day_ut_from_local,
            kp_chart_to_dict,
        )
    except ImportError:
        raise HTTPException(status_code=503, detail="Swiss Ephemeris module not available")

    utc_now = datetime.now(timezone.utc)
    now = utc_now + timedelta(hours=timezone_offset)
    try:
        jd = julian_day_ut_from_local(now.replace(tzinfo=None), timezone_offset)
        chart = compute_kp_chart(jd, float(lat), float(lon))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"KP chart failed: {e}") from e

    return kp_chart_to_dict(chart)
