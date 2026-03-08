"""
XTTS-v2 Text-to-Speech service for custom voice cloning (Open Source)
XTTS-v2 is a multilingual voice cloning model from Coqui AI
Supports 17+ languages including Hindi (works well for Sanskrit/Telugu)
"""
import os
import subprocess
import sys
from typing import Optional
from pathlib import Path
from app.config import settings
import httpx

# Try to import TTS library
try:
    from TTS.api import TTS
    XTTS_AVAILABLE = True
except ImportError:
    XTTS_AVAILABLE = False
    # Coqui TTS requires Python <3.12; Edge-TTS or gTTS will be used as fallback


async def text_to_speech_xtts(
    text: str,
    voice_reference_audio: str,  # Path to reference audio file (6+ seconds)
    output_path: Optional[str] = None,
    language: str = "hi",  # Use "hi" for Hindi (closest to Sanskrit/Telugu for XTTS)
    speaker_wav: Optional[str] = None  # Path to speaker reference audio
) -> str:
    """
    Convert text to speech using XTTS-v2 voice cloning (Open Source).
    
    Args:
        text: Text to convert to speech
        voice_reference_audio: Path to reference audio file (6+ seconds for voice cloning)
        output_path: Path where audio file should be saved
        language: Language code (hi, en, es, fr, de, it, pt, pl, tr, ru, nl, cs, ar, zh, ja, ko, hu)
        speaker_wav: Optional - path to speaker reference audio (if different from voice_reference_audio)
    
    Returns:
        Path to the generated audio file
    """
    
    if not XTTS_AVAILABLE:
        raise Exception(
            "TTS library not available. Install with: pip install TTS\n"
            "Note: XTTS-v2 requires GPU for best performance (CPU is slower but works)"
        )
    
    # Create output directory if it doesn't exist
    if not output_path:
        audio_dir = Path(settings.audio_storage_path) if hasattr(settings, 'audio_storage_path') else Path("uploads/audio")
        audio_dir.mkdir(parents=True, exist_ok=True)
        
        import uuid
        filename = f"{uuid.uuid4()}.wav"
        output_path = str(audio_dir / filename)
    else:
        # Ensure directory exists
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # Use speaker_wav if provided, otherwise use voice_reference_audio
    speaker_audio = speaker_wav if speaker_wav else voice_reference_audio
    
    if not os.path.exists(speaker_audio):
        raise Exception(f"Reference audio file not found: {speaker_audio}")
    
    try:
        # Initialize XTTS model
        # Note: First run will download the model (~1.7GB)
        print(f"🔄 Initializing XTTS-v2 model (this may take a moment on first run)...")
        tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", gpu=True)
        
        print(f"🎙️ Generating speech with cloned voice from: {speaker_audio}")
        # Generate speech
        # XTTS-v2 uses the reference audio to clone the voice
        tts.tts_to_file(
            text=text,
            speaker_wav=speaker_audio,
            language=language,
            file_path=output_path
        )
        
        print(f"✅ Generated audio with XTTS-v2 cloned voice: {output_path}")
        return output_path
        
    except Exception as e:
        error_msg = f"Error with XTTS-v2: {str(e)}"
        print(f"❌ {error_msg}")
        raise Exception(error_msg)


async def text_to_speech_xtts_api(
    text: str,
    voice_reference_audio_path: str,
    output_path: Optional[str] = None,
    language: str = "hi",
    api_url: str = "http://localhost:8001"  # XTTS API server
) -> str:
    """
    Convert text to speech using XTTS-v2 via API server (alternative approach).
    
    This is useful if you want to run XTTS in a separate service/container.
    
    Args:
        text: Text to convert to speech
        voice_reference_audio_path: Path to reference audio file
        output_path: Path where audio file should be saved
        language: Language code
        api_url: URL of XTTS API server
    
    Returns:
        Path to the generated audio file
    """
    
    # Create output directory if it doesn't exist
    if not output_path:
        audio_dir = Path(settings.audio_storage_path) if hasattr(settings, 'audio_storage_path') else Path("uploads/audio")
        audio_dir.mkdir(parents=True, exist_ok=True)
        
        import uuid
        filename = f"{uuid.uuid4()}.wav"
        output_path = str(audio_dir / filename)
    else:
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
    
    if not os.path.exists(voice_reference_audio_path):
        raise Exception(f"Reference audio file not found: {voice_reference_audio_path}")
    
    try:
        # Read audio file
        with open(voice_reference_audio_path, "rb") as audio_file:
            files = {
                "reference_audio": (os.path.basename(voice_reference_audio_path), audio_file, "audio/wav")
            }
            
            data = {
                "text": text,
                "language": language
            }
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{api_url}/tts",
                    files=files,
                    data=data
                )
                
                if response.status_code == 200:
                    with open(output_path, "wb") as f:
                        f.write(response.content)
                    print(f"✅ Generated audio via XTTS API: {output_path}")
                    return output_path
                else:
                    raise Exception(f"XTTS API error: {response.status_code} - {response.text}")
                    
    except Exception as e:
        raise Exception(f"Error calling XTTS API: {str(e)}")

