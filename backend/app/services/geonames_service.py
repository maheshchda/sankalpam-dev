from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from app.config import settings


_GEONAMES_BASE = "http://api.geonames.org"


class GeoNamesError(RuntimeError):
    pass


def _username() -> str:
    u = (getattr(settings, "geonames_username", None) or "").strip()
    if not u:
        raise GeoNamesError("GeoNames username not configured (set GEONAMES_USERNAME in backend/.env).")
    return u


async def _get_json(path: str, params: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{_GEONAMES_BASE}{path}"
    p = dict(params)
    p["username"] = _username()
    async with httpx.AsyncClient(timeout=12.0) as client:
        r = await client.get(url, params=p)
    if r.status_code != 200:
        raise GeoNamesError(f"GeoNames HTTP {r.status_code}: {r.text[:300]}")
    try:
        payload = r.json()
    except Exception as e:
        raise GeoNamesError(f"GeoNames invalid JSON: {e}")
    # GeoNames returns {"status": {"message": "...", "value": 10}} on errors
    if isinstance(payload, dict) and payload.get("status"):
        st = payload.get("status") or {}
        msg = st.get("message") or payload.get("status")
        raise GeoNamesError(f"GeoNames error: {msg}")
    return payload if isinstance(payload, dict) else {}


async def find_nearby_place_name(lat: float, lon: float) -> Dict[str, Any]:
    """
    Reverse lookup for the nearest populated place name (city/admin/country).
    GeoNames endpoint: findNearbyPlaceNameJSON
    """
    return await _get_json("/findNearbyPlaceNameJSON", {"lat": lat, "lng": lon})


async def ocean(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    """
    Return nearby ocean name when applicable.
    GeoNames endpoint: oceanJSON
    """
    payload = await _get_json("/oceanJSON", {"lat": lat, "lng": lon})
    oc = payload.get("ocean")
    return oc if isinstance(oc, dict) else None


async def find_nearby_features(
    lat: float,
    lon: float,
    radius_km: float = 30.0,
    max_rows: int = 20,
) -> Dict[str, Any]:
    """
    Nearby GeoNames features (raw). We filter later by featureClass/featureCode.
    GeoNames endpoint: findNearbyJSON
    """
    return await _get_json(
        "/findNearbyJSON",
        {"lat": lat, "lng": lon, "radius": radius_km, "maxRows": max_rows},
    )

