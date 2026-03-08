"""
Text-to-Speech service for generating audio from Sankalpam text
Supports multiple Indian languages with professional priest-like voice
Supports custom voice cloning via ElevenLabs
"""
import os
from typing import Optional
from pathlib import Path
from app.config import settings

# Try to import ElevenLabs service
try:
    from app.services.elevenlabs_tts import text_to_speech_elevenlabs
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False
    print("ElevenLabs TTS service not available")

# Try to import XTTS-v2 service (Open Source)
try:
    from app.services.xtts_tts import text_to_speech_xtts
    XTTS_AVAILABLE = True
except ImportError:
    XTTS_AVAILABLE = False
    # Coqui TTS (XTTS) requires Python <3.12; Edge-TTS/gTTS used as fallback

# Try to import Edge-TTS service (Free, works with Python 3.13+)
try:
    from app.services.edge_tts_service import text_to_speech_edge
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    print("Edge-TTS service not available (install with: pip install edge-tts)")

# Get the backend directory (parent of app directory)
# From backend/app/services/tts_service.py: parent.parent.parent = backend
BACKEND_DIR = Path(__file__).parent.parent.parent

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

try:
    from google.cloud import texttospeech
    GOOGLE_CLOUD_TTS_AVAILABLE = True
except ImportError:
    GOOGLE_CLOUD_TTS_AVAILABLE = False

# Language code mapping for TTS
LANGUAGE_CODES = {
    "sanskrit": "sa",  # Note: gTTS may not support Sanskrit well
    "hindi": "hi",
    "telugu": "te",
    "tamil": "ta",
    "kannada": "kn",
    "malayalam": "ml",
    "english": "en",
    "marathi": "mr",
    "gujarati": "gu",
    "bengali": "bn",
    "oriya": "or",
    "punjabi": "pa",
}

async def text_to_speech(
    text: str,
    language: str = "sanskrit",
    output_path: Optional[str] = None,
    slow: bool = False
) -> str:
    """
    Convert text to speech audio file with professional male priest voice.
    
    Args:
        text: Text to convert to speech
        language: Language code (e.g., "sanskrit", "hindi", "tamil")
        output_path: Path where audio file should be saved
        slow: Whether to speak slowly (for gTTS)
    
    Returns:
        Path to the generated audio file
    """
    
    lang_code = LANGUAGE_CODES.get(language.lower(), "en")
    
    # Create output directory if it doesn't exist
    if not output_path:
        audio_dir = Path(settings.audio_storage_path) if hasattr(settings, 'audio_storage_path') else Path("uploads/audio")
        audio_dir.mkdir(parents=True, exist_ok=True)
        
        import uuid
        filename = f"{uuid.uuid4()}.mp3"
        output_path = str(audio_dir / filename)
    else:
        # Ensure directory exists
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # Try XTTS-v2 first if configured (FREE open-source voice cloning)
    if (hasattr(settings, 'use_xtts') and settings.use_xtts and 
        hasattr(settings, 'xtts_reference_audio_path') and settings.xtts_reference_audio_path):
        if XTTS_AVAILABLE:
            try:
                # Resolve reference audio path
                ref_audio_path = settings.xtts_reference_audio_path
                if not os.path.isabs(ref_audio_path):
                    ref_audio_path = str(BACKEND_DIR / ref_audio_path)
                
                if os.path.exists(ref_audio_path):
                    xtts_lang = getattr(settings, 'xtts_language', 'hi')  # Default to Hindi
                    print(f"✅ Using XTTS-v2 open-source voice cloning with reference: {ref_audio_path}")
                    result = await text_to_speech_xtts(
                        text=text,
                        voice_reference_audio=ref_audio_path,
                        output_path=output_path,
                        language=xtts_lang
                    )
                    print("✅ XTTS-v2 voice generation successful")
                    return result
                else:
                    print(f"⚠️ XTTS reference audio file not found: {ref_audio_path}")
                    print(f"Falling back to other TTS services")
            except Exception as e:
                print(f"❌ Error with XTTS-v2: {e}")
                print(f"Falling back to other TTS services")
        else:
            print("⚠️ XTTS-v2 enabled but library not available. Install with: pip install TTS")
    
    # Try ElevenLabs if configured (custom cloned voice - paid service)
    if ELEVENLABS_AVAILABLE and hasattr(settings, 'elevenlabs_api_key') and settings.elevenlabs_api_key:
        if hasattr(settings, 'elevenlabs_voice_id') and settings.elevenlabs_voice_id:
            try:
                print(f"✅ Using ElevenLabs custom cloned voice: {settings.elevenlabs_voice_id}")
                result = await text_to_speech_elevenlabs(
                    text=text,
                    voice_id=settings.elevenlabs_voice_id,
                    output_path=output_path,
                    language=language
                )
                print("✅ ElevenLabs voice generation successful")
                return result
            except Exception as e:
                print(f"❌ Error with ElevenLabs: {e}")
                print(f"Falling back to other TTS services")
        else:
            print("⚠️ ElevenLabs API key found but voice_id not configured. Set ELEVENLABS_VOICE_ID in .env")
    
    # Try Edge-TTS (Free Microsoft voices, works with Python 3.13+, good quality, no API keys)
    if EDGE_TTS_AVAILABLE:
        try:
            print(f"✅ Using Edge-TTS (free Microsoft voices, works with Python 3.13+)")
            result = await text_to_speech_edge(
                text=text,
                language=language,
                output_path=output_path,
                rate="-10%",  # Slightly slower for more reverent chanting
                pitch="-5Hz",  # Slightly lower pitch for more masculine/deep voice
                volume="+0%"
            )
            print("✅ Edge-TTS generation successful")
            return result
        except Exception as e:
            print(f"❌ Error with Edge-TTS: {e}")
            print(f"Falling back to gTTS")
    
    # Try Google Cloud TTS (best quality, professional voices, requires credentials)
    print(f"DEBUG: GOOGLE_CLOUD_TTS_AVAILABLE = {GOOGLE_CLOUD_TTS_AVAILABLE}")
    
    if GOOGLE_CLOUD_TTS_AVAILABLE:
        print(f"DEBUG: Checking for credentials path...")
        print(f"DEBUG: settings.google_cloud_tts_credentials_path = {getattr(settings, 'google_cloud_tts_credentials_path', 'NOT SET')}")
        
        creds_path = None
        if (hasattr(settings, 'google_cloud_tts_credentials_path') and 
            settings.google_cloud_tts_credentials_path):
            
            # Resolve relative paths relative to backend directory
            creds_path_str = settings.google_cloud_tts_credentials_path.strip()
            print(f"DEBUG: Original credentials path string: '{creds_path_str}'")
            print(f"DEBUG: BACKEND_DIR = {BACKEND_DIR}")
            
            # Remove leading "./" if present for cleaner path handling
            if creds_path_str.startswith("./"):
                creds_path_str = creds_path_str[2:]
                print(f"DEBUG: After removing './': '{creds_path_str}'")
            
            if not os.path.isabs(creds_path_str):
                # If relative, resolve from backend directory
                creds_path = (BACKEND_DIR / creds_path_str).resolve()
                print(f"DEBUG: Resolved relative path: {creds_path}")
            else:
                creds_path = Path(creds_path_str).resolve()
                print(f"DEBUG: Resolved absolute path: {creds_path}")
            
            # Check if file exists
            print(f"DEBUG: Checking if file exists: {creds_path.exists()}")
            if creds_path.exists():
                try:
                    # Set credentials path as environment variable for Google Cloud client
                    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(creds_path)
                    print(f"✅ Using Google Cloud TTS with credentials: {creds_path}")
                    result = await _google_cloud_tts(text, language, output_path)
                    print("✅ Google Cloud TTS generation successful")
                    return result
                except Exception as e:
                    print(f"❌ Error with Google Cloud TTS: {e}")
                    import traceback
                    traceback.print_exc()
                    print(f"Falling back to gTTS (which may have feminine voice)")
            else:
                print(f"❌ Google Cloud TTS credentials file not found: {creds_path}")
                print(f"   BACKEND_DIR = {BACKEND_DIR}")
                print(f"   Expected location: {BACKEND_DIR / 'app' / 'credentials.json'}")
                print(f"Falling back to gTTS (which may have feminine voice)")
        else:
            print("❌ Google Cloud TTS credentials path not configured in settings")
            print(f"   hasattr check: {hasattr(settings, 'google_cloud_tts_credentials_path')}")
            if hasattr(settings, 'google_cloud_tts_credentials_path'):
                print(f"   Value: '{settings.google_cloud_tts_credentials_path}'")
            print("Falling back to gTTS (which may have feminine voice)")
    else:
        print("❌ Google Cloud TTS library not available. Install: pip install google-cloud-texttospeech")
    
    # Try gTTS (WARNING: This uses FEMALE voice - not recommended for priest voice)
    # Only use if Google Cloud TTS is not available
    if GTTS_AVAILABLE:
        print("WARNING: Using gTTS which has FEMALE voice. For male priest voice, use Google Cloud TTS.")
        try:
            # Note: gTTS doesn't support Sanskrit natively
            # For Sanskrit, use Hindi which is closest phonetically
            if language.lower() == "sanskrit":
                lang_code = "hi"  # Hindi voice for Sanskrit text
            
            # WARNING: gTTS uses female voices by default - not suitable for priest voice
            # Use slow=True for more priest-like, deliberate speech
            tts = gTTS(text=text, lang=lang_code, slow=True)
            tts.save(output_path)
            print("Generated audio with gTTS (FEMALE voice - not ideal for priest)")
            return output_path
        except Exception as e:
            print(f"Error with gTTS: {e}, falling back to pyttsx3")
    
    # Fallback to pyttsx3 (offline, lower quality)
    if PYTTSX3_AVAILABLE:
        try:
            engine = pyttsx3.init()
            
            # Set properties for priest-like voice
            engine.setProperty('rate', 130)  # Slower rate for more deliberate speech
            engine.setProperty('volume', 0.9)  # Volume
            
            # Try to find a male voice (OS-dependent)
            voices = engine.getProperty('voices')
            for voice in voices:
                # Prefer male voices for priest-like sound
                if 'male' in voice.name.lower() or 'david' in voice.name.lower() or 'zira' not in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    break
            
            engine.save_to_file(text, output_path)
            engine.runAndWait()
            return output_path
        except Exception as e:
            print(f"Error with pyttsx3: {e}")
    
    # If all fail, raise an error
    raise Exception(
        "TTS service not available. Install gtts or pyttsx3. "
        "For professional priest-like Sanskrit voice, consider using Google Cloud TTS "
        "(set GOOGLE_CLOUD_TTS_CREDENTIALS_PATH in config)."
    )


async def _google_cloud_tts(text: str, language: str, output_path: str) -> str:
    """
    Use Google Cloud Text-to-Speech API for high-quality Sanskrit/Indian language TTS
    with professional male priest voice optimized for devotional chanting.
    
    Uses WaveNet or Neural2 voices for superior quality and natural sound.
    Requires GOOGLE_CLOUD_TTS_CREDENTIALS_PATH to be set in config.
    """
    client = texttospeech.TextToSpeechClient()
    
    # Map language to Google Cloud TTS language code and voice
    # Using WaveNet voices (premium quality) for professional priest-like sound
    # For Sanskrit, we use Hindi (hi-IN) as it's the closest supported language
    voice_config = {
        "sanskrit": {
            "language_code": "hi-IN",  # Hindi for Sanskrit (better support)
            # Use WaveNet/Neural2 voices first (they support pitch parameters for deep voice)
            # Note: Chirp3-HD voices don't support pitch parameters, so we use WaveNet/Neural2
            "voice_names": [
                "hi-IN-Wavenet-D",          # WaveNet male voice (premium, supports pitch, deep voice)
                "hi-IN-Neural2-D",          # Neural2 male voice (high quality, supports pitch)
                "hi-IN-Standard-D",         # Standard male voice (fallback, may not support pitch)
            ],
            "ssml_gender": texttospeech.SsmlVoiceGender.MALE,
        },
        "hindi": {
            "language_code": "hi-IN",
            "voice_names": [
                "hi-IN-Wavenet-D",
                "hi-IN-Neural2-D",
                "hi-IN-Standard-D",
            ],
            "ssml_gender": texttospeech.SsmlVoiceGender.MALE,
        },
        "tamil": {
            "language_code": "ta-IN",
            "voice_names": [
                "ta-IN-Wavenet-D",
                "ta-IN-Neural2-D",
                "ta-IN-Standard-D",
            ],
            "ssml_gender": texttospeech.SsmlVoiceGender.MALE,
        },
        "telugu": {
            "language_code": "te-IN",
            "voice_names": [
                "te-IN-Wavenet-D",
                "te-IN-Neural2-D",
                "te-IN-Standard-D",
            ],
            "ssml_gender": texttospeech.SsmlVoiceGender.MALE,
        },
    }
    
    config = voice_config.get(language.lower(), {
        "language_code": "hi-IN",
        "voice_names": ["hi-IN-Wavenet-D", "hi-IN-Neural2-D", "hi-IN-Standard-D"],
        "ssml_gender": texttospeech.SsmlVoiceGender.MALE,
    })
    
    # Process text: Add natural pauses between mantras and slokas
    processed_text = text.replace('॥', '॥<break time="1000ms"/>')  # Longer pause after ॥
    processed_text = processed_text.replace('।', '।<break time="600ms"/>')  # Medium pause after ।
    
    # Try voices in order until one works with pitch parameters
    # WaveNet and Neural2 support pitch for deep voice, Standard may not
    last_error = None
    for voice_name in config["voice_names"]:
        try:
            # Configure the voice
            voice = texttospeech.VoiceSelectionParams(
                language_code=config["language_code"],
                name=voice_name,
                ssml_gender=texttospeech.SsmlVoiceGender.MALE,
            )
            
            # Configure audio output for devotional priest-like chanting
            # Balanced settings for natural deep male priest voice
            # Moderate pitch adjustment for natural-sounding deep male voice
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=0.75,        # Moderately slow for reverent chanting (keep as user likes it)
                pitch=-5.0,                 # Moderate lower pitch for natural deep male priest voice
                volume_gain_db=0.5,         # Minimal volume adjustment for natural sound
                sample_rate_hertz=24000,    # High quality audio
            )
            
            # Use SSML only for pauses, not for pitch/rate (to avoid double modification)
            # Let audio_config handle pitch and rate for cleaner, more natural sound
            ssml_text = f"""<speak>
                {processed_text}
            </speak>"""
            
            # Use SSML input mainly for pauses between mantras
            synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)
            
            print(f"Trying voice: {voice_name} (with pitch=-5.0 for natural deep male priest voice)")
            response = client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )
            
            # Success! Write the response and return
            with open(output_path, "wb") as out:
                out.write(response.audio_content)
            
            print(f"✅ Generated audio with professional priest voice: {voice_name} (deep, male, reverent)")
            return output_path
            
        except Exception as e:
            error_msg = str(e)
            last_error = e
            print(f"Voice {voice_name} failed: {error_msg}")
            
            # If pitch is not supported, try without pitch for this voice
            if "pitch" in error_msg.lower() or "does not support" in error_msg.lower():
                print(f"  Voice {voice_name} doesn't support pitch. Trying without pitch adjustment...")
                try:
                    # Try again without pitch parameter (will use voice's natural pitch)
                    audio_config_no_pitch = texttospeech.AudioConfig(
                        audio_encoding=texttospeech.AudioEncoding.MP3,
                        speaking_rate=0.75,        # Moderately slow for reverent chanting
                        volume_gain_db=1.0,
                        sample_rate_hertz=24000,
                    )
                    # Use simpler SSML without pitch in prosody (voice's natural male pitch)
                    ssml_text_no_pitch = f"""<speak>
                        <prosody rate="slow" volume="+10%">
                            {processed_text}
                        </prosody>
                    </speak>"""
                    synthesis_input_no_pitch = texttospeech.SynthesisInput(ssml=ssml_text_no_pitch)
                    
                    response = client.synthesize_speech(
                        input=synthesis_input_no_pitch, voice=voice, audio_config=audio_config_no_pitch
                    )
                    
                    with open(output_path, "wb") as out:
                        out.write(response.audio_content)
                    
                    print(f"✅ Generated audio with voice: {voice_name} (natural pitch, slow rate)")
                    return output_path
                except Exception as e2:
                    print(f"  Voice {voice_name} also failed without pitch: {e2}")
                    continue
            else:
                # Other error, try next voice
                continue
    
    # If all voices failed, raise the last error
    if last_error:
        raise last_error
    raise Exception("All voices failed to generate audio")

# For production, you might want to use cloud-based TTS services:
# - Azure Cognitive Services (good Sanskrit support)
# - Google Cloud Text-to-Speech (excellent Indian language support)
# - AWS Polly (good language coverage)
# These services typically have Python SDKs and better quality/accuracy

