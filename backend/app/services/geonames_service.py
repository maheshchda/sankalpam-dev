from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

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
    # GeoNames returns status error when not near any ocean; that should be a normal "None".
    try:
        payload = await _get_json("/oceanJSON", {"lat": lat, "lng": lon})
        oc = payload.get("ocean")
        return oc if isinstance(oc, dict) else None
    except GeoNamesError as e:
        msg = str(e).lower()
        if "could not find an ocean" in msg:
            return None
        raise


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


def _bbox_from_km(lat: float, lon: float, km: float) -> Tuple[float, float, float, float]:
    """
    Rough bounding box around a point.
    1° lat ~ 111 km; 1° lon ~ 111 km * cos(lat)
    Returns (north, south, east, west).
    """
    dlat = km / 111.0
    # Avoid division by zero near poles (not relevant for our use, but keep safe)
    import math
    denom = max(0.05, math.cos(math.radians(lat)))
    dlon = km / (111.0 * denom)
    north = lat + dlat
    south = lat - dlat
    east = lon + dlon
    west = lon - dlon
    return north, south, east, west


async def search_natural_features(
    lat: float,
    lon: float,
    radius_km: float = 60.0,
    max_rows: int = 20,
) -> Dict[str, Any]:
    """
    Query GeoNames 'searchJSON' for natural features around a point.
    Returns:
      {
        "hydro": [...],     # featureClass H (rivers, lakes, streams, seas)
        "terrain": [...],   # featureClass T (mountains, hills, ranges)
      }

    We avoid findNearbyJSON because it often returns buildings (featureClass S).
    """
    north, south, east, west = _bbox_from_km(lat, lon, radius_km)

    async def _search(feature_class: str) -> List[Dict[str, Any]]:
        payload = await _get_json(
            "/searchJSON",
            {
                "featureClass": feature_class,
                "north": north,
                "south": south,
                "east": east,
                "west": west,
                "maxRows": max_rows,
                # Style influences which fields are returned; FULL gives more metadata
                "style": "FULL",
                # Order by relevance; the API doesn't guarantee distance ordering, so we post-sort later
                "orderby": "relevance",
            },
        )
        rows = payload.get("geonames") if isinstance(payload, dict) else None
        return rows if isinstance(rows, list) else []

    return {
        "hydro": await _search("H"),
        "terrain": await _search("T"),
    }


