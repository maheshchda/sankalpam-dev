"""
Script to upload the Sankalpam template to the system
Usage: python upload_template.py
"""
import requests
import json
import sys
import os
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:8000"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Admin@123"
TEMPLATE_FILE = "sample_sankalpam_template.txt"

def login_as_admin():
    """Login and get access token"""
    print("🔐 Logging in as admin...")
    
    response = requests.post(
        f"{API_BASE_URL}/api/auth/login",
        data={
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
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

def upload_template_from_file(token, template_file_path):
    """Upload template from text file"""
    print(f"\n📄 Reading template file: {template_file_path}...")
    
    if not os.path.exists(template_file_path):
        print(f"❌ Template file not found: {template_file_path}")
        sys.exit(1)
    
    with open(template_file_path, 'r', encoding='utf-8') as f:
        template_text = f.read()
    
    print(f"✅ Template text loaded ({len(template_text)} characters)")
    
    # Upload as file
    print("\n📤 Uploading template file...")
    with open(template_file_path, 'rb') as f:
        files = {'file': (os.path.basename(template_file_path), f, 'text/plain')}
        data = {
            'name': 'Standard Sankalpam Template',
            'description': 'Complete Sankalpam template with all variables for daily pooja',
            'language': 'sanskrit'
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/admin/templates/upload-file",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
            data=data
        )
    
    if response.status_code == 201:
        template = response.json()
        print("✅ Template uploaded successfully!")
        print(f"\n📋 Template Details:")
        print(f"   ID: {template['id']}")
        print(f"   Name: {template['name']}")
        print(f"   Language: {template['language']}")
        print(f"   Variables found: {template.get('variables', 'N/A')}")
        return template
    else:
        print(f"❌ Upload failed: {response.status_code}")
        print(f"   Response: {response.text}")
        sys.exit(1)

def upload_template_from_text(token, template_text):
    """Upload template directly from text"""
    print("\n📤 Uploading template directly...")
    
    data = {
        'template_text': template_text,
        'name': 'Standard Sankalpam Template',
        'description': 'Complete Sankalpam template with all variables for daily pooja',
        'language': 'sanskrit'
    }
    
    response = requests.post(
        f"{API_BASE_URL}/api/admin/templates",
        headers={"Authorization": f"Bearer {token}"},
        data=data
    )
    
    if response.status_code == 201:
        template = response.json()
        print("✅ Template uploaded successfully!")
        print(f"\n📋 Template Details:")
        print(f"   ID: {template['id']}")
        print(f"   Name: {template['name']}")
        print(f"   Language: {template['language']}")
        print(f"   Variables found: {template.get('variables', 'N/A')}")
        return template
    else:
        print(f"❌ Upload failed: {response.status_code}")
        print(f"   Response: {response.text}")
        sys.exit(1)

def list_templates(token):
    """List all templates"""
    print("\n📚 Listing all templates...")
    
    response = requests.get(
        f"{API_BASE_URL}/api/admin/templates",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        templates = response.json()
        print(f"✅ Found {len(templates)} template(s):")
        for t in templates:
            print(f"   - {t['name']} (ID: {t['id']}, Language: {t['language']})")
        return templates
    else:
        print(f"❌ Failed to list templates: {response.status_code}")
        return []

def main():
    """Main function"""
    print("=" * 60)
    print("🚀 Sankalpam Template Upload Script")
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
    token = login_as_admin()
    
    # Find template file
    script_dir = Path(__file__).parent
    template_file = script_dir / TEMPLATE_FILE
    
    # Upload template (try file upload first, fallback to text)
    try:
        template = upload_template_from_file(token, str(template_file))
    except Exception as e:
        print(f"\n⚠️  File upload failed, trying direct text upload...")
        print(f"   Error: {e}")
        with open(template_file, 'r', encoding='utf-8') as f:
            template_text = f.read()
        template = upload_template_from_text(token, template_text)
    
    # List templates
    list_templates(token)
    
    print("\n" + "=" * 60)
    print("✅ Template upload complete!")
    print("=" * 60)
    print(f"\n📝 Next Steps:")
    print(f"   1. The template is ready to use (ID: {template['id']})")
    print(f"   2. Users can now generate Sankalpam audio from this template")
    print(f"   3. Test by calling: POST /api/templates/generate with template_id={template['id']}")
    print()

if __name__ == "__main__":
    main()

