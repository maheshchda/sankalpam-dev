"""
Ganesha Sankalpam Template Generator (Telugu)
Generates the full Ganesha sankalpam text with variables from the logged-in user
and Divine API (panchang). Gothra, User Nakshatra, Rashi, etc. come from current user.
"""
from datetime import datetime
from typing import Dict, Optional
import httpx
import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_BACKEND_DIR))

try:
    from app.config import settings
except ImportError:
    class Settings:
        divine_api_key = None
        divine_access_token = None
    settings = Settings()


def _to_telugu_birth_nakshatra(raw: str) -> str:
    if not raw or not raw.strip():
        return raw or ""
    try:
        from app.services.divineapi_service import _nakshatra_to_telugu
        return _nakshatra_to_telugu(raw.strip())
    except Exception:
        return raw.strip()


def _to_telugu_birth_rashi(raw: str) -> str:
    if not raw or not raw.strip():
        return raw or ""
    try:
        from app.services.divineapi_service import _english_to_telugu, _TE_RASHI
        return _english_to_telugu(raw.strip(), _TE_RASHI) or raw.strip()
    except Exception:
        return raw.strip()


async def _get_panchang_from_divine_api(data: Dict) -> Dict[str, str]:
    """Fetch panchang (rithou, mAsE, pakshE, thithou, vAsara, nakshatra, yoga, karaNa, ayanam) in Telugu."""
    try:
        from app.services.divineapi_service import (
            _english_to_telugu, _tithi_to_telugu, _nakshatra_to_telugu,
            _TE_PAKSHA, _TE_YOGA, _TE_KARANA, _TE_RITU, _TE_WEEKDAYS
        )
    except ImportError:
        def _english_to_telugu(text, mapping):
            return mapping.get(text.lower(), text) if text else ""
        def _tithi_to_telugu(text):
            return text or ""
        def _nakshatra_to_telugu(text):
            return text or ""
        _TE_PAKSHA = _TE_YOGA = _TE_KARANA = _TE_RITU = _TE_WEEKDAYS = {}

    result = {
        "rithou": "", "mAsE": "", "pakshE": "", "thithou": "", "vAsara": "",
        "nakshatra": "", "yoga": "", "karaNa": "", "ayanam": "",
    }
    if not settings.divine_api_key or not settings.divine_access_token:
        return _get_fallback_panchang(data)

    now = datetime.now()
    place = data.get("location_city") or data.get("location_state") or data.get("location_country") or "Unknown"
    lat = data.get("latitude")
    lon = data.get("longitude")
    tz = data.get("timezone_offset_hours", 0.0)
    try:
        lat_num = float(lat) if lat not in (None, "") else 0.0
        lon_num = float(lon) if lon not in (None, "") else 0.0
    except (TypeError, ValueError):
        lat_num = lon_num = 0.0

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = "https://astroapi-1.divineapi.com/indian-api/v2/find-panchang"
            headers = {"Authorization": f"Bearer {settings.divine_access_token}"}
            body = {
                "api_key": settings.divine_api_key,
                "day": str(now.day), "month": str(now.month), "year": str(now.year),
                "place": place, "Place": place, "lat": str(lat_num), "lon": str(lon_num),
                "tzone": str(tz), "lan": "tl",
            }
            r = await client.post(url, headers=headers, data=body)
            if r.status_code == 200 and r.json().get("success"):
                pdata = r.json().get("data") or {}
                tithis = pdata.get("tithis") or []
                t0 = tithis[0] if tithis and isinstance(tithis[0], dict) else {}
                paksha_name = t0.get("paksha") or pdata.get("paksha") or ""
                tithi_name = (t0.get("tithi") or pdata.get("tithi") or pdata.get("tithi_name") or "")
                if paksha_name and tithi_name:
                    tithi_name = f"{paksha_name} {tithi_name}".strip()
                nak_block = pdata.get("nakshatras") or {}
                nak_list = nak_block.get("nakshatra_list") if isinstance(nak_block, dict) else (pdata.get("nakshatra_list") or [])
                nakshatra_name = None
                if nak_list and isinstance(nak_list, list) and len(nak_list) > 0:
                    first = nak_list[0]
                    nakshatra_name = first.get("nak_name") or first.get("nakshatra_name") or first.get("name") if isinstance(first, dict) else first
                if not nakshatra_name:
                    nakshatra_name = pdata.get("nakshatra_name")
                yogas = pdata.get("yogas") or []
                y0 = yogas[0] if yogas and isinstance(yogas[0], dict) else {}
                yoga_name = y0.get("yoga_name") or y0.get("yoga") or y0.get("name") if isinstance(y0, dict) else pdata.get("yoga_name")
                karnas = pdata.get("karnas") or []
                k0 = karnas[0] if karnas and isinstance(karnas[0], dict) else {}
                karana_name = k0.get("karana_name") or k0.get("karana") or k0.get("name") if isinstance(k0, dict) else pdata.get("karana_name")

                result["pakshE"] = _english_to_telugu(paksha_name, _TE_PAKSHA) or paksha_name
                tithi_parts = (tithi_name or "").split(maxsplit=1)
                tithi_only = tithi_parts[1] if len(tithi_parts) > 1 else (tithi_parts[0] if tithi_parts else "")
                result["thithou"] = _tithi_to_telugu(tithi_only) if tithi_only else ""
                result["nakshatra"] = _nakshatra_to_telugu(nakshatra_name or "")
                result["yoga"] = _english_to_telugu((yoga_name or "").strip(), _TE_YOGA) or (yoga_name or "")
                result["karaNa"] = _english_to_telugu((karana_name or "").strip(), _TE_KARANA) or (karana_name or "")

            curl = "https://astroapi-3.divineapi.com/indian-api/v2/chandramasa"
            cbody = {
                "api_key": settings.divine_api_key,
                "day": str(now.day), "month": str(now.month), "year": str(now.year),
                "Place": place, "lat": str(lat_num), "lon": str(lon_num), "tzone": str(tz), "lan": "tl",
            }
            cr = await client.post(curl, headers=headers, data=cbody)
            if cr.status_code == 200 and cr.json().get("success"):
                cdata = cr.json().get("data") or {}
                if cdata.get("chandramasa"):
                    result["mAsE"] = str(cdata["chandramasa"]).strip()

            result["rithou"] = _TE_RITU.get(now.month, "")
            result["vAsara"] = _english_to_telugu(now.strftime("%A"), _TE_WEEKDAYS) or now.strftime("%A")
            result["ayanam"] = "ఉత్తరాయణే" if 1 <= now.month <= 6 else "దక్షిణాయణే"
    except Exception as e:
        print(f"[Ganesha Sankalpam Template] Panchang error: {e}")
        return _get_fallback_panchang(data)
    return result


def _get_fallback_panchang(data: Dict) -> Dict[str, str]:
    try:
        from app.services.divineapi_service import _fallback_panchang_for_today, _TE_RITU, _TE_WEEKDAYS
        from app.services.divineapi_service import (
            _english_to_telugu, _tithi_to_telugu, _nakshatra_to_telugu,
            _TE_PAKSHA, _TE_YOGA, _TE_KARANA
        )
    except ImportError:
        def _fallback_panchang_for_today(n):
            return {"paksha": "", "tithi": "", "nakshatra": "", "yoga": "", "karana": ""}
        _TE_RITU = _TE_WEEKDAYS = _TE_PAKSHA = _TE_YOGA = _TE_KARANA = {}
        def _english_to_telugu(t, m):
            return m.get(t.lower(), t) if t else ""
        def _tithi_to_telugu(t):
            return t or ""
        def _nakshatra_to_telugu(t):
            return t or ""

    now = datetime.now()
    fb = _fallback_panchang_for_today(now)
    paksha_te = _english_to_telugu(fb.get("paksha", ""), _TE_PAKSHA) or fb.get("paksha", "")
    tithi_raw = (fb.get("tithi") or "").split(maxsplit=1)
    tithi_only = tithi_raw[1] if len(tithi_raw) > 1 else (tithi_raw[0] if tithi_raw else "")
    return {
        "rithou": _TE_RITU.get(now.month, ""),
        "mAsE": now.strftime("%B"),
        "pakshE": paksha_te,
        "thithou": _tithi_to_telugu(tithi_only) if tithi_only else "",
        "vAsara": _english_to_telugu(now.strftime("%A"), _TE_WEEKDAYS) or now.strftime("%A"),
        "nakshatra": _nakshatra_to_telugu(fb.get("nakshatra", "")),
        "yoga": _english_to_telugu((fb.get("yoga") or "").strip(), _TE_YOGA) or fb.get("yoga", ""),
        "karaNa": _english_to_telugu((fb.get("karana") or "").strip(), _TE_KARANA) or fb.get("karana", ""),
        "ayanam": "ఉత్తరాయణే" if 1 <= now.month <= 6 else "దక్షిణాయణే",
    }


async def _get_geographical_reference(data: Dict) -> str:
    try:
        from app.services.divineapi_service import _telugu_geographical_reference_from_country
        return _telugu_geographical_reference_from_country(data.get("location_country", ""))
    except ImportError:
        c = (data.get("location_country") or "").strip().lower()
        if not c or "india" in c:
            return "జంబూద్వీపే భారతవర్షే భారతఖండే"
        return f"{data.get('location_country', '')} దేశే"


async def _get_geographical_feature(data: Dict) -> str:
    """River/place phrase for the sankalpam (e.g. కృష్ణా గోదావర్యో మధ్యప్రదేశే or user's nearby river)."""
    try:
        from app.services.divineapi_service import _telugu_geographical_feature_from_data
        return _telugu_geographical_feature_from_data(data)
    except ImportError:
        r = data.get("nearby_river", "")
        if r:
            return f"{r} నదీ తటే"
        return "కృష్ణా గోదావర్యో మధ్యప్రదేశే"


async def generate_sankalpam_text(data: Dict) -> str:
    """
    Generate full Telugu Ganesha Sankalpam. Variables (Gothra, Nakshatra, Rashi, etc.)
    come from the current logged-in user; panchang from Divine API.
    """
    lines = []

    # ---------- Static preamble ----------
    lines.append("విఘ్నేశ్వర స్వామి పూజ")
    lines.append("")
    lines.append("పసుపుతో విఘేశ్వరుని చేసి, తమలపాకులో ఉంచాలి. తమల పాకు చివర తూర్పు ఉనకుగాని, ఉత్తరత్తము వైపునకు గాని ఉండునట్లు ఉంచాలి. ఆ తమలపాకును ఒక పళ్లెంలో పోసిన య్యం ఉంచాలి. అనంతరం అగరవత్తులు వెలిగించి దీపారాధన చేయాలి)")
    lines.append("")
    lines.append("ఓం దేవీంవాచ మజనయంత దేవాస్తాం విశ్వరూపాః పశవోవదంతి")
    lines.append("సానో మంద్రేష మూర్జం దుహానాధే నుర్వాగ స్మానుప సుష్టుతైతు")
    lines.append("అయం ముహూర్త స్సుముహూర్తోస్తు॥")
    lines.append("")
    lines.append("య శ్శివో నామరూపాభ్యాం యాదేవీ సర్వమంగళా |")
    lines.append("తయోస్సంస్మరణా త్సుంసాం సర్వతో జయమంగళం ॥")
    lines.append("")
    lines.append("శుక్లాం బరధరం విష్ణుం శశివర్ణం చతుర్భుజం |")
    lines.append("ప్రసన్న వదనం ధ్యాయేత్ సర్వ విఘ్నోప శాంతయే ||")
    lines.append("")
    lines.append("తదేవ లగ్నం సుదినం తదేవ తారాబలం చంద్ర బలం తదేవ |")
    lines.append("విద్యాబలం దైవబలం తదేవ లక్ష్మీపతే తేఘ్ర యుగం స్మరామి||")
    lines.append("")
    lines.append("యత్ర యోగేశ్వరః కృష్ణో యత్ర పార్థ ధనుర్ధరః |")
    lines.append("తత్ర శ్రీర్విజయో భూతిః ధ్రువా నీతిర్మతిర్మమ ॥")
    lines.append("")
    lines.append("స్మృతే సకల కళ్యాణ భాజనం యత్ర జాయతే|")
    lines.append("పురుషంత మజం నిత్యం ప్రజామి శరణం హరిమ్ ||")
    lines.append("")
    lines.append("సర్వదా సర్వ కార్యేషు నాస్తి తేషాం మంగళమ్ |")
    lines.append("యేషాం హృదిసో భగవాన్ మంగళాయతనం హరిః ||")
    lines.append("")
    lines.append("లాభస్తేషాం జయస్తేషాం కుత స్తేషాం పరాభవః ॥")
    lines.append("యేషా మిందీ వరశ్యామో హృదయస్థో జనార్ధనః ॥")
    lines.append("")
    lines.append("ఆపదామపహర్తారం దాతారం సర్వసంపదాం")
    lines.append("లోకాభిరామం శ్రీ రామం భూయో భూయో నమామ్యహం॥")
    lines.append("")
    lines.append("సర్వ మంగళ మాంగళ్యే శివే సర్వార్థ సాధికే |")
    lines.append("శరణ్యే త్ర్యంబకే దేవి నారాయణి నమోస్తుతే ॥")
    lines.append("")
    lines.append("(విఘేశ్వరుడిపై అక్షతలు వేసి, నమస్కరిస్తూ)")
    lines.append("")
    lines.append("శ్రీ లక్ష్మీ నారాయణాభ్యాం నమః ఉమామహేశ్వరాభ్యాం నమః")
    lines.append("వాణీ హిరణ్యగర్భాభ్యాం నమః శచీపురందరాభ్యాం నమః")
    lines.append("")
    lines.append("ఇంద్రాది అష్టదిష్టక్పాలక దేవతాభ్యో నమః అరుంధతీ వసిష్ఠాభ్యాం నమః")
    lines.append("సీతారామాభ్యాం నమః మాతాపితృభ్యాం నమః")
    lines.append("సర్వేభ్యో మహాజనేభ్యో నమః")
    lines.append("")
    lines.append("(అనంతరం ఆచమనం చేస్తూ అంటే కింది మంత్రాలు చదువుతూ కుడి అర చేతితో నీరు తీర్థంలాగ తాగాలి)")
    lines.append("")
    for mantram in [
        "ఓం కేశవాయ స్వాహా", "ఓం నారాయణ స్వాహా", "ఓం మాధవాయ స్వాహా", "ఓం గోవిందాయ నమః",
        "ఓం విష్ణవే నమః", "ఓం మధుసూదనాయ నమః", "ఓం త్రివిక్రమాయ నమః", "ఓం వామనాయ నమః",
        "ఓం శ్రీధరాయ నమః", "ఓం హృషీకేశాయ నమః", "ఓం పద్మనాభాయ నమః", "ఓం దామోదరాయ నమః",
        "ఓం సంకర్షణాయ నమః", "ఓం వాసుదేవాయ నమః", "ఓం ప్రద్యుమ్నాయ నమః", "ఓం అనిరుద్ధాయ నమః",
        "ఓం పురుషోత్తమాయ నమః", "ఓం అధోక్షజాయ నమః", "ఓం నారసింహాయ నమః", "ఓం అచ్యుతాయ నమః",
        "ఓం ఉపేంద్రాయ నమః", "ఓం హరయే నమః", "ఓం జనార్ధనాయ నమః", "ఓం శ్రీకృష్ణాయ నమః",
    ]:
        lines.append(mantram)
    lines.append("")
    lines.append("(అనంతరం నీటిని పైకి, పక్కలకు, వెనక్కివెద జల్లుతూ కింది శ్లోకం పఠించాలి)")
    lines.append("")
    lines.append("ఉత్తిష్ఠంతు భూత పిశాచాః యేతే భూమి భారకాః")
    lines.append("ఏతేషా మవిరోధేన బ్రహ్మకర్మ సమారభే")
    lines.append("")
    lines.append("(అక్షతలు కొన్ని వాసన చూసి ఎడమచేతి పక్క నుంచి వెనుక్కి వేసుకోవాలి. అనంతరం ప్రాణాయామం చేయాలి అంటే కుడి చేతి బొటన వేలు, మధ్య వేలితో రెండు ముక్కు రంధ్రాలను మూసి ఈ మంత్రాలు చదవాలి)")
    lines.append("")
    lines.append("ఓం భూః ఓం భువః ఓం సువః ఓం జనః ఓం తపః ఓం సత్యం")
    lines.append("ఓం తత్సవితుర్వరేణ్యం భర్గో దేవస్య ధీమహి ధీయోయనః ప్రచోదయాత్")
    lines.append("ఓం ఆపో జ్యోతి రసోమృతం బ్రహ్మ భూర్భువస్సువరోమ్")
    lines.append("")
    lines.append("(అని మూడు సార్లు జపించాలి)")
    lines.append("")
    lines.append("(అనంతరం అక్షతలు తీసుకుని సంకల్పం చెప్పుకోవాలి)")
    lines.append("")
    lines.append("సంకల్పము:")
    lines.append("")

    # ---------- Sankalpam paragraph with variables (user + Divine API) ----------
    geo_ref = await _get_geographical_reference(data)
    geo_feature = await _get_geographical_feature(data)
    panchang = await _get_panchang_from_divine_api(data)
    current_year = data.get("current_year", datetime.now().year)
    rithou = panchang.get("rithou", "")
    mAsE = panchang.get("mAsE", "")
    pakshE = panchang.get("pakshE", "")
    thithou = panchang.get("thithou", "")
    vAsara = panchang.get("vAsara", "")
    nakshatra = panchang.get("nakshatra", "")
    yoga = panchang.get("yoga", "")
    karaNa = panchang.get("karaNa", "")
    ayanam = panchang.get("ayanam", "")

    user_name = data.get("user_name", "")
    gotram = data.get("gotram", "")
    birth_nakshatra = _to_telugu_birth_nakshatra(data.get("birth_nakshatra") or "")
    birth_rashi = _to_telugu_birth_rashi(data.get("birth_rashi") or "")
    family_members = data.get("family_members", [])

    geo_ref_comma = ", ".join(geo_ref.split()) if geo_ref else geo_ref
    sankalpam_para = (
        "ఓం మమోపాత్త దురితక్షయ ద్వారా శ్రీ పరమేశ్వర ప్రీత్యర్థం శుభే, శోభన ముహూర్తే, శ్రీ మహావిష్ణో రాజ్ఞాయా ప్రవర్తమానస్య అద్యబ్రహ్మణః ద్వితీయ పరార్థే, శ్వేత వరాహకల్పే, వైవస్వత మన్వంతరే, కలియుగే, ప్రథమపాదే, "
        + geo_ref_comma + " మేరోర్ధక్షిణదిగ్భాగే, "
        + geo_feature + " అస్మిన్ వర్తమాన వ్యావహారిక చంద్రమాన "
        + str(current_year) + " సంవత్సరే, " + ayanam + " ఆయనే " + rithou + " ఋతౌ " + mAsE + " మాసే, " + pakshE + " పక్షే, " + thithou + " తిధౌ, " + vAsara + " వాసరే, " + nakshatra + " శుభ నక్షత్రే, " + yoga + " శుభయోగే, శుభకరణే."
    )
    lines.append(sankalpam_para)
    lines.append("")
    # User identity and family (from logged-in user: Gothra, Nakshatra, Rashi)
    lines.append("అహం " + user_name + " గోత్ర " + gotram + " " + birth_nakshatra + " నక్షత్రే " + birth_rashi + " రాశౌ.")
    if family_members:
        fam_str = ", ".join((m.get("name", "") + " (" + m.get("relation", "") + ")") for m in family_members)
        lines.append("మమ పారివారిక సదస్యులు: " + fam_str + ".")
    lines.append("")
    lines.append("ఏవం గుణ విశేషణ విషిష్ఠాయాం, శుభతిదౌ, సహకుటుంబానాం క్షేమ, స్థైర్య, ధైర్య, విజయ, ఆయురారోగ్య ఐశ్వర్యాభివృద్ధ్యర్థం శ్రీ మహా గణాధిపతి శ్రీ సుబ్రహ్మణ్య స్వామి హరిహరపుత్ర అయ్యప్ప స్వామి దేవతాపూజా కాలమందు శ్రీ మహా గణాధిపతి పూజార్థం...")
    lines.append("")
    lines.append("(అక్షతలు, నీరు కలిపి పళ్ళెంలో విడిచివేయాలి)")
    lines.append("")
    lines.append("(అనంతరం కలశపూజ చేయాలి. కలశం అంటే నీళ్ళు ఉండే పాత్రకు గంధం, కుంకుమ అలంకరించి అక్షతలు, పుష్పం వేసి ఎడమ అర చేతితో కింద పట్టుకొని కుడిఅరచేతితో పైన పట్టుకోని కింది శ్లోకాలు చదవాలి)")
    lines.append("")
    lines.append("తదంగ కలశ పూజాం కరిష్యే")
    lines.append("")
    lines.append("కలశస్య ముఖే విష్ణుః కంఠే రుద్ర స్సమాశ్రితః ।")
    lines.append("మూలే తత్ర స్థితో బ్రహ్మా మధ్యే మాతృగణాః స్మృతాః ॥")
    lines.append("కుక్షౌతు సాగరాస్సర్వే సప్త ద్వీపా వసుంధరా ।")
    lines.append("ఋగ్వేదో యజుర్వేదో స్సామవేదో అధర్వణః ॥")
    lines.append("")
    lines.append("గంగేచ యమునే చైవ గోదావరీ సరస్వతీ నర్మదా సింధు కావేరి జలేస్మిన్ సన్నిధిం కురు")
    lines.append("")
    lines.append("(కింది శ్లోకం చదువుతూ కలశంలోని నీటిని పుష్పంతో తీసుకొని పూజా ద్రవ్యాల మీద, దేవుడి మీద, మీ మీద జల్లుకోవాలి)")
    lines.append("")
    lines.append("(అనంతరం ప్రాణప్రతిష్ట చేయాలి.. అనగా పసుపు గణపతిపై కుడిచేతిని ఉంచి కింది మంత్రాలు చదవాలి)")
    lines.append("")
    lines.append("ఓం అసునీతే పునరస్మాసు చక్షుః")
    lines.append("ఓం మహాగణపతయే నమః")
    lines.append("")
    lines.append("ఓం శ్రీ స్వామియే శరణమయ్యప్ప")

    return "\n".join(lines)
