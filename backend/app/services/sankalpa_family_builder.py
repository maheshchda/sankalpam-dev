"""
Helpers for Sankalpa text: family participants, Telugu elaboration phrases, intent suffixes.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

from app.models import FamilyMember, User

# Relations (case-insensitive) used to group members for classical Sanskrit/Telugu phrasing
_SPOUSE_RELATIONS = {"wife", "husband", "spouse"}
_CHILD_RELATIONS = {"son", "daughter", "child"}


def filter_family_participants(
    members: Sequence[FamilyMember],
    participant_ids: Optional[Sequence[int]],
) -> List[FamilyMember]:
    """
    If participant_ids is None, return all members (same as legacy callers).
    If provided (possibly empty), only those IDs (exclude deceased even if wrongly selected).
    """
    if participant_ids is None:
        return list(members)
    id_set = {int(x) for x in participant_ids}
    return [m for m in members if m.id in id_set and not getattr(m, "is_deceased", False)]


def _norm_relation(rel: str) -> str:
    return (rel or "").strip().lower()


# Intent key -> Telugu phrase fragment (purpose of the sankalpa)
_SANKALPA_INTENT_TE: Dict[str, str] = {
    "general": "క్షేమ స్థైర్య ధైర్య విజయ అభయ ఆయురారోగ్య ఐశ్వర్యాభివృద్ధ్యర్థం",
    "health": "ఆయురారోగ్య ఐశ్వర్యాభివృద్ధ్యర్థం",
    "wealth": "ధన ఐశ్వర్యాభివృద్ధ్యర్థం",
    "papam": "సకల పాప నివృత్యర్థం",
    "business": "వ్యాపారాభివృద్ధ్యర్థం",
}


def sankalpa_intent_phrase_te(intent_key: Optional[str]) -> str:
    """Return Telugu purpose phrase; default to general wellbeing."""
    k = (intent_key or "general").strip().lower()
    return _SANKALPA_INTENT_TE.get(k, _SANKALPA_INTENT_TE["general"])


def build_telugu_sankalpa_extras(
    *,
    user_name_te: str,
    gotra_te: str,
    birth_nak_te: str,
    birth_rashi_te: str,
    family_members_payload: List[dict],
    intent_key: Optional[str],
) -> Tuple[Dict[str, str], List[str]]:
    """
    Build extra template variables for Telugu sankalpam from already-localized names (Telugu script).
    Use relation_raw (English) for grouping; name in Telugu script.
    """
    spouses: List[str] = []
    children: List[str] = []
    for m in family_members_payload:
        name = (m.get("name") or "").strip()
        r = _norm_relation(m.get("relation_raw") or m.get("relation") or "")
        if not name:
            continue
        if r in _SPOUSE_RELATIONS:
            spouses.append(name)
        elif r in _CHILD_RELATIONS:
            children.append(name)

    gotra_gotrodabhavasya = f"{gotra_te} గోత్రోద్భవస్య" if gotra_te else "గోత్రోద్భవస్య"

    spouse_line = ""
    if spouses:
        spouse_line = f"ధర్మపత్నీ సమేతస్య {spouses[0]} నామధేయాయాః"

    children_joined = ", ".join(children) if children else ""

    elaboration_parts: List[str] = [gotra_gotrodabhavasya, f"{user_name_te} నామధేయస్య"]
    if spouse_line:
        elaboration_parts.append(spouse_line)
    if children_joined:
        elaboration_parts.append(f"{children_joined} నామధేయానాం")
    elaboration_parts.append("మమ సహ కుటుంబానాం")
    intent_phrase = sankalpa_intent_phrase_te(intent_key)
    elaboration_parts.append(intent_phrase)
    sankalpa_family_elaboration_te = " ".join(elaboration_parts).strip() + " ।"

    all_names: List[str] = [user_name_te]
    for m in family_members_payload:
        n = (m.get("name") or "").strip()
        if n:
            all_names.append(n)
    if len(all_names) == 1:
        family_list_te = f"{all_names[0]} నామధేయస్య"
    else:
        family_list_te = ", ".join(all_names) + " నామధేయానాం"

    highlight_names: List[str] = [user_name_te]
    highlight_names.extend(spouses)
    highlight_names.extend(children)

    extras = {
        "gotra_gotrodabhavasya": gotra_gotrodabhavasya,
        "gotra_suffix": gotra_gotrodabhavasya,
        "spouse_names_telugu": spouses[0] if spouses else "",
        "children_names_list_telugu": children_joined,
        "sankalpa_family_elaboration_te": sankalpa_family_elaboration_te,
        "sankalpa_intent_phrase_te": intent_phrase,
        "family_list_te": family_list_te,
        "karta_line_te": f"{user_name_te} నామధేయస్య · {birth_nak_te} నక్షత్రే · {birth_rashi_te} రాశౌ",
    }
    return extras, highlight_names


def profile_ready_for_sankalpa(user: User) -> bool:
    """True when gotra and at least one of janma nakshatra / rashi exist for a smooth ritual line."""
    g = (getattr(user, "gotram", None) or "").strip()
    nak = (getattr(user, "birth_nakshatra", None) or "").strip()
    rashi = (getattr(user, "birth_rashi", None) or "").strip()
    return bool(g and (nak or rashi))
