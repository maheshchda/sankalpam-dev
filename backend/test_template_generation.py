"""
Script to test Sankalpam template generation and audio creation
Usage: python test_template_generation.py
"""
import requests
import json
import sys
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"
TEST_USERNAME = "admin"  # Change to a regular user if needed
TEST_PASSWORD = "Admin@123"

def login(username, password):
    """Login and get access token"""
    print(f"🔐 Logging in as {username}...")
    
    response = requests.post(
        f"{API_BASE_URL}/api/auth/login",
        data={
            "username": username,
            "password": password
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✅ Login successful!")
        return token
    else:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        sys.exit(1)

def get_user_info(token):
    """Get current user info"""
    response = requests.get(
        f"{API_BASE_URL}/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        return response.json()
    return None

def get_active_templates(token):
    """Get list of active templates"""
    print("\n📚 Fetching available templates...")
    
    response = requests.get(
        f"{API_BASE_URL}/api/templates/templates",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        templates = response.json()
        print(f"✅ Found {len(templates)} template(s)")
        for t in templates:
            print(f"   - {t['name']} (ID: {t['id']}, Language: {t['language']})")
            if t.get('variables'):
                import json
                vars_list = json.loads(t['variables']) if isinstance(t['variables'], str) else t['variables']
                print(f"     Variables: {', '.join(vars_list[:5])}{'...' if len(vars_list) > 5 else ''}")
        return templates
    else:
        print(f"❌ Failed to get templates: {response.status_code} - {response.text}")
        return []

def generate_audio_from_template(token, template_id, user):
    """Generate audio from template"""
    print(f"\n🎵 Generating Sankalpam audio from template {template_id}...")
    
    # Use user's birth location as current location for testing
    request_data = {
        "template_id": template_id,
        "location_city": user.get("birth_city", "Chennai"),
        "location_state": user.get("birth_state", "Tamil Nadu"),
        "location_country": user.get("birth_country", "India"),
        "latitude": None,  # Can add coordinates if available
        "longitude": None,
        "date": datetime.now().isoformat(),
        "pooja_name": "Test Pooja"
    }
    
    print(f"📋 Request data:")
    print(f"   Location: {request_data['location_city']}, {request_data['location_state']}")
    print(f"   Date: {request_data['date']}")
    print(f"   Pooja: {request_data['pooja_name']}")
    
    response = requests.post(
        f"{API_BASE_URL}/api/templates/generate",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json=request_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Sankalpam generated successfully!")
        print(f"\n📝 Generated Text (first 200 chars):")
        print(f"   {result['text'][:200]}...")
        print(f"\n🎵 Audio URL: {API_BASE_URL}{result['audio_url']}")
        print(f"\n📊 Variables used:")
        for key, value in list(result['variables_used'].items())[:10]:
            print(f"   {key}: {value}")
        if len(result['variables_used']) > 10:
            print(f"   ... and {len(result['variables_used']) - 10} more")
        return result
    else:
        print(f"❌ Generation failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

def main():
    """Main function"""
    print("=" * 60)
    print("🧪 Sankalpam Template Generation Test")
    print("=" * 60)
    
    # Check if backend is running
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"⚠️  Backend might not be running. Expected /health to return 200, got {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to backend at {API_BASE_URL}")
        print(f"   Error: {e}")
        print(f"   Make sure the backend server is running: uvicorn main:app --reload")
        sys.exit(1)
    
    # Login
    token = login(TEST_USERNAME, TEST_PASSWORD)
    
    # Get user info
    user = get_user_info(token)
    if user:
        print(f"👤 User: {user.get('first_name')} {user.get('last_name')}")
        print(f"   Gotram: {user.get('gotram')}")
        print(f"   Birth Place: {user.get('birth_city')}, {user.get('birth_state')}")
    
    # Get templates
    templates = get_active_templates(token)
    
    if not templates:
        print("\n⚠️  No templates found. Please upload a template first using upload_template.py")
        sys.exit(1)
    
    # Use first template
    template_id = templates[0]['id']
    
    # Generate audio
    result = generate_audio_from_template(token, template_id, user or {})
    
    if result:
        print("\n" + "=" * 60)
        print("✅ Test complete!")
        print("=" * 60)
        print(f"\n🎧 To play the audio:")
        print(f"   Open in browser: {API_BASE_URL}{result['audio_url']}")
        print(f"   Or visit the playback page with the audio URL")
        print()
    else:
        print("\n❌ Test failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()

