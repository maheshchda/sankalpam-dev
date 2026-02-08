"""
Edge-TTS service for text-to-speech (Free, works with Python 3.13+)
Uses Microsoft Edge voices - free, high quality, no API keys needed
Supports Hindi and Telugu voices suitable for Sanskrit
"""
import os
import sys
from typing import Optional
from pathlib import Path
from app.config import settings

# Set UTF-8 encoding for Windows to handle Unicode characters (Telugu, Sanskrit, etc.)
if sys.platform == 'win32':
    # Set environment variable for UTF-8
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    # Reconfigure stdout/stderr to use UTF-8
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

# Try to import edge_tts
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False


# Voice mapping for Indian languages
VOICE_MAPPING = {
    "sanskrit": "hi-IN-MadhurNeural",  # Male Hindi voice (best for Sanskrit)
    "hindi": "hi-IN-MadhurNeural",     # Male Hindi voice
    "telugu": "te-IN-MohanNeural",     # Male Telugu voice
    "tamil": "ta-IN-ValluvarNeural",   # Male Tamil voice
    "kannada": "kn-IN-GaganNeural",    # Male Kannada voice
    "malayalam": "ml-IN-MidhunNeural", # Male Malayalam voice
    "english": "en-US-DavisNeural",    # Male English voice
    "default": "hi-IN-MadhurNeural",   # Default to Hindi male voice
}


async def list_edge_voices() -> list:
    """
    List all available Edge-TTS voices.
    Useful for finding the perfect voice.
    """
    if not EDGE_TTS_AVAILABLE:
        raise Exception("edge-tts not installed. Install with: pip install edge-tts")
    
    voices = await edge_tts.list_voices()
    return voices


async def text_to_speech_edge(
    text: str,
    language: str = "sanskrit",
    output_path: Optional[str] = None,
    voice: Optional[str] = None,
    rate: str = "+0%",  # Speech rate: -50% to +100%
    pitch: str = "+0Hz",  # Pitch: -50Hz to +50Hz
    volume: str = "+0%"  # Volume: -50% to +100%
) -> str:
    """
    Convert text to speech using Edge-TTS (free Microsoft voices).
    
    Args:
        text: Text to convert to speech
        language: Language code (sanskrit, hindi, telugu, etc.)
        output_path: Path where audio file should be saved
        voice: Optional specific voice ID (overrides language mapping)
        rate: Speech rate adjustment (e.g., "-10%", "+0%", "+10%")
        pitch: Pitch adjustment (e.g., "-5Hz", "+0Hz", "+5Hz")
        volume: Volume adjustment (e.g., "-10%", "+0%", "+10%")
    
    Returns:
        Path to the generated audio file
    """
    
    if not EDGE_TTS_AVAILABLE:
        raise Exception(
            "edge-tts not installed. Install with: pip install edge-tts\n"
            "Edge-TTS is free and works with Python 3.13+"
        )
    
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
    
    # Select voice
    if voice:
        selected_voice = voice
    else:
        selected_voice = VOICE_MAPPING.get(language.lower(), VOICE_MAPPING["default"])
    
    try:
        print(f"🎙️ Generating speech with Edge-TTS voice: {selected_voice}")
        
        # Ensure output path is a string and uses forward slashes (Windows compatibility)
        output_path_str = str(output_path).replace('\\', '/')
        
        # Create SSML for better control (rate, pitch, volume)
        # Ensure text is properly encoded as UTF-8
        ssml_text = f"""
<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{language[:2]}">
    <voice name="{selected_voice}">
        <prosody rate="{rate}" pitch="{pitch}" volume="{volume}">
            {text}
        </prosody>
    </voice>
</speak>
        """.strip()
        
        # Generate audio
        communicate = edge_tts.Communicate(ssml_text, selected_voice)
        
        # Save to file - edge_tts handles binary file writing internally
        # Ensure path is absolute and uses forward slashes for cross-platform compatibility
        abs_output_path = os.path.abspath(output_path_str)
        await communicate.save(abs_output_path)
        
        print(f"✅ Generated audio with Edge-TTS: {output_path_str}")
        return output_path_str
        
    except Exception as e:
        error_msg = f"Error with Edge-TTS: {str(e)}"
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
        
        # Fallback: try without SSML
        try:
            print("🔄 Trying Edge-TTS without SSML (fallback)...")
            output_path_str = str(output_path).replace('\\', '/')
            communicate = edge_tts.Communicate(text, selected_voice)
            
            # Save to absolute path
            abs_output_path = os.path.abspath(output_path_str)
            await communicate.save(abs_output_path)
            print(f"✅ Generated audio with Edge-TTS (fallback): {abs_output_path}")
            return abs_output_path
        except Exception as e2:
            raise Exception(f"Edge-TTS error (with and without SSML): {str(e2)}")


async def find_best_male_voice_for_language(language: str) -> str:
    """
    Find the best male voice for a given language.
    
    Args:
        language: Language code
    
    Returns:
        Voice ID
    """
    if not EDGE_TTS_AVAILABLE:
        return VOICE_MAPPING.get(language.lower(), VOICE_MAPPING["default"])
    
    try:
        voices = await edge_tts.list_voices()
        
        # Filter for the language and male voices
        lang_code = language[:2].lower()
        matching_voices = [
            v for v in voices
            if lang_code in v["Locale"].lower() and 
            ("Male" in v["Gender"] or "male" in v["Name"] or "Neural" in v["Name"])
        ]
        
        if matching_voices:
            # Prefer voices with "Neural" (better quality)
            neural_voices = [v for v in matching_voices if "Neural" in v["Name"]]
            if neural_voices:
                return neural_voices[0]["Name"]
            return matching_voices[0]["Name"]
    except Exception as e:
        print(f"Error finding voice: {e}")
    
    # Fallback to mapping
    return VOICE_MAPPING.get(language.lower(), VOICE_MAPPING["default"])

