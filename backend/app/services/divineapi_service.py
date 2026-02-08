import httpx
from typing import List
from app.models import User, FamilyMember
from app.config import settings

async def generate_sankalpam(
    user: User,
    family_members: List[FamilyMember],
    location_city: str,
    location_state: str,
    location_country: str,
    nearby_river: str,
    language: str = "sanskrit"
) -> str:
    """
    Generate sankalpam using DivineAPI or generate a standard template
    """
    
    # Prepare sankalpam data
    sankalpam_data = {
        "user_name": f"{user.first_name} {user.last_name}",
        "gotram": user.gotram,
        "birth_place": f"{user.birth_city}, {user.birth_state}, {user.birth_country}",
        "birth_time": user.birth_time,
        "birth_date": user.birth_date.strftime("%Y-%m-%d"),
        "current_location": f"{location_city}, {location_state}, {location_country}",
        "nearby_river": nearby_river,
        "language": language,
        "family_members": [
            {
                "name": member.name,
                "relation": member.relation,
                "gotram": user.gotram  # Usually same gotram
            }
            for member in family_members
        ]
    }
    
    # Try to use DivineAPI if configured
    if settings.divineapi_key:
        try:
            async with httpx.AsyncClient() as client:
                # Note: Check DivineAPI documentation for exact endpoint
                # This is a placeholder based on typical API patterns
                url = f"{settings.divineapi_base_url}/v1/sankalpam/generate"
                headers = {
                    "Authorization": f"Bearer {settings.divineapi_key}",
                    "Content-Type": "application/json"
                }
                
                response = await client.post(url, json=sankalpam_data, headers=headers, timeout=30.0)
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("sankalpam_text", generate_standard_sankalpam(sankalpam_data))
                else:
                    print(f"DivineAPI error: {response.status_code} - {response.text}")
                    # Fall back to standard template
        except Exception as e:
            print(f"Error calling DivineAPI: {e}")
            # Fall back to standard template
    
    # Generate standard sankalpam template
    return generate_standard_sankalpam(sankalpam_data)

def generate_standard_sankalpam(data: dict) -> str:
    """
    Generate a standard sankalpam text with all the provided information
    This is a template that should be customized based on actual requirements
    """
    
    # Standard sankalpam template (Sanskrit with transliteration)
    sankalpam = f"""
श्री गणेशाय नमः

ॐ विष्णुर्विष्णुर्विष्णुः

अद्य श्रीमद्भगवतो महापुरुषस्य विष्णोराज्ञया प्रवर्तमानस्य
अद्य ब्रह्मणो द्वितीयपरार्धे श्री श्वेतवाराहकल्पे
वैवस्वतमन्वन्तरे अष्टाविंशतितमे कलियुगे
प्रथमचरणे

भारतवर्षे भरतखण्डे जम्बूद्वीपे
{data['current_location']} नगरे
{data['nearby_river']} नदी तटे

अस्मिन् वर्तमाने व्यावहारिके
{data['birth_date']} सम्वत्सरे
मासे
तिथौ
वासरे
नक्षत्रे
योगे
करणे

शुभे मुहूर्ते
अहं {data['user_name']}
गोत्र {data['gotram']}
शर्मा/वर्मा/दास/देव (अपना उपनाम)
जन्मस्थान: {data['birth_place']}
जन्मसमय: {data['birth_time']}

मम पारिवारिक सदस्याः:
"""
    
    for member in data.get('family_members', []):
        sankalpam += f"- {member['name']} ({member['relation']})\n"
    
    sankalpam += f"""
इत्यादि सकलपापक्षयपूर्वकं
अखण्डमण्डलाकारं व्याप्तं येन चराचरं
तत्परमेश्वरं प्रणम्य

अस्यां शुभतिथौ
[पूजा का नाम यहाँ]
पूजनं करिष्यामि

तत्सिद्धयर्थं
संकल्पं करोमि ॥
"""
    
    return sankalpam.strip()

