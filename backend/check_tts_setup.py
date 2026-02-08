#!/usr/bin/env python3
"""
Quick diagnostic script to check TTS setup
Run this to verify Google Cloud TTS configuration
"""
import sys
from pathlib import Path

print("=" * 60)
print("TTS Setup Diagnostic")
print("=" * 60)

# Check 1: Google Cloud TTS library
print("\n1. Checking Google Cloud TTS library installation...")
try:
    from google.cloud import texttospeech
    print("   ✅ google-cloud-texttospeech is installed")
    GOOGLE_CLOUD_TTS_AVAILABLE = True
except ImportError as e:
    print(f"   ❌ google-cloud-texttospeech is NOT installed: {e}")
    print("   Install it with: pip install google-cloud-texttospeech")
    GOOGLE_CLOUD_TTS_AVAILABLE = False

# Check 2: Configuration
print("\n2. Checking configuration...")
try:
    from app.config import settings
    creds_path_str = getattr(settings, 'google_cloud_tts_credentials_path', '')
    print(f"   Credentials path from settings: '{creds_path_str}'")
    
    if not creds_path_str:
        print("   ❌ GOOGLE_CLOUD_TTS_CREDENTIALS_PATH is not set in .env")
        print("   Set it in your .env file: GOOGLE_CLOUD_TTS_CREDENTIALS_PATH=./app/credentials.json")
    else:
        print(f"   ✅ GOOGLE_CLOUD_TTS_CREDENTIALS_PATH is set: '{creds_path_str}'")
        
        # Resolve path
        BACKEND_DIR = Path(__file__).parent
        creds_path_str_clean = creds_path_str.strip()
        if creds_path_str_clean.startswith("./"):
            creds_path_str_clean = creds_path_str_clean[2:]
        
        if not Path(creds_path_str_clean).is_absolute():
            creds_path = (BACKEND_DIR / creds_path_str_clean).resolve()
        else:
            creds_path = Path(creds_path_str_clean).resolve()
        
        print(f"   Resolved path: {creds_path}")
        
        # Check 3: Credentials file
        print("\n3. Checking credentials file...")
        if creds_path.exists():
            print(f"   ✅ Credentials file exists: {creds_path}")
            print(f"   File size: {creds_path.stat().st_size} bytes")
            
            # Try to validate it's valid JSON
            try:
                import json
                with open(creds_path, 'r') as f:
                    creds_data = json.load(f)
                    if 'type' in creds_data and 'private_key' in creds_data:
                        print("   ✅ Credentials file appears to be valid JSON with service account data")
                    else:
                        print("   ⚠️  Credentials file is JSON but may not be a valid service account key")
            except json.JSONDecodeError:
                print("   ❌ Credentials file is not valid JSON")
            except Exception as e:
                print(f"   ⚠️  Could not validate credentials file: {e}")
        else:
            print(f"   ❌ Credentials file NOT found at: {creds_path}")
            print(f"   Expected location: {BACKEND_DIR / 'app' / 'credentials.json'}")
            if (BACKEND_DIR / 'app' / 'credentials.json').exists():
                print(f"   ✅ But file exists at: {BACKEND_DIR / 'app' / 'credentials.json'}")
                print(f"   Try using absolute path or: app/credentials.json (without ./)")
        
except Exception as e:
    print(f"   ❌ Error loading configuration: {e}")
    import traceback
    traceback.print_exc()

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

if not GOOGLE_CLOUD_TTS_AVAILABLE:
    print("❌ Google Cloud TTS library is not installed")
    print("   Action: pip install google-cloud-texttospeech")
    sys.exit(1)

if not creds_path_str:
    print("❌ Credentials path is not configured")
    print("   Action: Set GOOGLE_CLOUD_TTS_CREDENTIALS_PATH in .env file")
    sys.exit(1)

if not creds_path.exists():
    print("❌ Credentials file not found")
    print(f"   Action: Ensure credentials.json exists at: {creds_path}")
    sys.exit(1)

print("✅ All checks passed! Google Cloud TTS should work.")
print("\nNext steps:")
print("1. Restart your backend server")
print("2. Generate a Sankalpam and check backend logs")
print("3. You should see: '✅ Using Google Cloud TTS with credentials'")
print("4. The voice should be MALE (deep, authoritative)")

