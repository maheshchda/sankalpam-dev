"""
ElevenLabs Text-to-Speech service for custom voice cloning
This allows using a cloned voice for Sankalpam audio generation
"""
import os
import httpx
from typing import Optional
from pathlib import Path
from app.config import settings

# ElevenLabs API endpoints
ELEVENLABS_API_BASE = "https://api.elevenlabs.io/v1"

async def text_to_speech_elevenlabs(
    text: str,
    voice_id: str,
    output_path: Optional[str] = None,
    language: str = "sanskrit",
    stability: float = 0.5,
    similarity_boost: float = 0.75,
    style: float = 0.0,
    use_speaker_boost: bool = True
) -> str:
    """
    Convert text to speech using ElevenLabs custom voice.
    
    Args:
        text: Text to convert to speech
        voice_id: ElevenLabs voice ID (custom cloned voice)
        output_path: Path where audio file should be saved
        language: Language code (not used by ElevenLabs, but kept for compatibility)
        stability: Voice stability (0.0 to 1.0) - lower = more variation
        similarity_boost: How similar to original voice (0.0 to 1.0)
        style: Voice style (0.0 to 1.0)
        use_speaker_boost: Enhance speaker clarity
    
    Returns:
        Path to the generated audio file
    """
    
    if not hasattr(settings, 'elevenlabs_api_key') or not settings.elevenlabs_api_key:
        raise Exception("ElevenLabs API key not configured. Set ELEVENLABS_API_KEY in .env file.")
    
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
    
    # ElevenLabs API endpoint
    url = f"{ELEVENLABS_API_BASE}/text-to-speech/{voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": settings.elevenlabs_api_key
    }
    
    # Model selection based on language
    # Use "eleven_multilingual_v2" for Sanskrit/Telugu/Hindi
    model_id = "eleven_multilingual_v2"
    
    data = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {
            "stability": stability,
            "similarity_boost": similarity_boost,
            "style": style,
            "use_speaker_boost": use_speaker_boost
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                # Save audio file
                with open(output_path, "wb") as f:
                    f.write(response.content)
                
                print(f"✅ Generated audio with ElevenLabs custom voice: {voice_id}")
                return output_path
            else:
                error_msg = f"ElevenLabs API error: {response.status_code} - {response.text}"
                print(f"❌ {error_msg}")
                raise Exception(error_msg)
                
    except httpx.TimeoutException:
        raise Exception("ElevenLabs API request timed out")
    except Exception as e:
        raise Exception(f"Error calling ElevenLabs API: {str(e)}")


async def create_voice_clone(
    name: str,
    audio_file_path: str,
    description: Optional[str] = None
) -> str:
    """
    Create a voice clone from an audio file.
    
    Args:
        name: Name for the voice
        audio_file_path: Path to audio file (MP3, WAV, etc.)
        description: Optional description
    
    Returns:
        Voice ID of the created clone
    """
    
    if not hasattr(settings, 'elevenlabs_api_key') or not settings.elevenlabs_api_key:
        raise Exception("ElevenLabs API key not configured. Set ELEVENLABS_API_KEY in .env file.")
    
    url = f"{ELEVENLABS_API_BASE}/voices/add"
    
    headers = {
        "xi-api-key": settings.elevenlabs_api_key
    }
    
    # Read audio file
    with open(audio_file_path, "rb") as audio_file:
        files = {
            "files": (os.path.basename(audio_file_path), audio_file, "audio/mpeg")
        }
        
        data = {
            "name": name,
            "description": description or f"Custom voice for Sankalpam"
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, headers=headers, files=files, data=data)
                
                if response.status_code == 200:
                    result = response.json()
                    voice_id = result.get("voice_id")
                    print(f"✅ Created voice clone: {name} (ID: {voice_id})")
                    return voice_id
                else:
                    error_msg = f"ElevenLabs voice creation error: {response.status_code} - {response.text}"
                    print(f"❌ {error_msg}")
                    raise Exception(error_msg)
                    
        except httpx.TimeoutException:
            raise Exception("ElevenLabs voice creation request timed out")
        except Exception as e:
            raise Exception(f"Error creating voice clone: {str(e)}")


async def list_voices() -> list:
    """
    List all available voices (including cloned voices).
    
    Returns:
        List of voice dictionaries
    """
    
    if not hasattr(settings, 'elevenlabs_api_key') or not settings.elevenlabs_api_key:
        raise Exception("ElevenLabs API key not configured.")
    
    url = f"{ELEVENLABS_API_BASE}/voices"
    
    headers = {
        "xi-api-key": settings.elevenlabs_api_key
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                return result.get("voices", [])
            else:
                raise Exception(f"Error listing voices: {response.status_code} - {response.text}")
                
    except Exception as e:
        raise Exception(f"Error calling ElevenLabs API: {str(e)}")

