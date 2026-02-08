#!/usr/bin/env python3
"""Check which TTS services are available"""
import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

print("=== CHECKING TTS SERVICES ===\n")

# Check Google Cloud TTS
try:
    from google.cloud import texttospeech
    print("[OK] Google Cloud TTS: INSTALLED")
    GOOGLE_AVAILABLE = True
except Exception as e:
    print(f"[X] Google Cloud TTS: NOT INSTALLED - {e}")
    GOOGLE_AVAILABLE = False

# Check Edge-TTS
try:
    import edge_tts
    print("[OK] Edge-TTS: INSTALLED")
    EDGE_AVAILABLE = True
except Exception as e:
    print(f"[X] Edge-TTS: NOT INSTALLED - {e}")
    EDGE_AVAILABLE = False

# Check gTTS
try:
    from gtts import gTTS
    print("[OK] gTTS: INSTALLED")
    GTTS_AVAILABLE = True
except Exception as e:
    print(f"[X] gTTS: NOT INSTALLED - {e}")
    GTTS_AVAILABLE = False

# Check credentials file
import os
from pathlib import Path

backend_dir = Path(__file__).parent
creds_path = backend_dir / "app" / "credentials.json"

print(f"\n=== CHECKING CREDENTIALS ===")
print(f"Expected path: {creds_path}")
if creds_path.exists():
    print(f"[OK] Credentials file EXISTS ({creds_path.stat().st_size} bytes)")
    
    # Check if Google Cloud TTS can use it
    if GOOGLE_AVAILABLE:
        try:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(creds_path)
            client = texttospeech.TextToSpeechClient()
            print("[OK] Google Cloud TTS client initialized successfully!")
            print("  -> Google Cloud TTS is READY TO USE")
        except Exception as e:
            print(f"[X] Google Cloud TTS client failed: {e}")
            print("  -> Check if credentials are valid")
else:
    print(f"[X] Credentials file NOT FOUND")
    print("  -> Google Cloud TTS will not work")

# Summary
print(f"\n=== SUMMARY ===")
if GOOGLE_AVAILABLE and creds_path.exists():
    print("[OK] Google Cloud TTS: READY (will be used first)")
elif EDGE_AVAILABLE:
    print("[OK] Edge-TTS: AVAILABLE (will be used as fallback)")
elif GTTS_AVAILABLE:
    print("[WARN] gTTS: AVAILABLE (female voice, not ideal for priest)")
    print("  -> Consider installing Google Cloud TTS for better quality")
else:
    print("[X] NO TTS SERVICE AVAILABLE")
    print("  -> Install at least one: pip install gtts")

