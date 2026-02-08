"""
Test script to verify Google Cloud TTS is using male voice
Run this to check if credentials and voice are configured correctly
"""
import asyncio
import os
from pathlib import Path
from app.services.tts_service import text_to_speech

async def test_voice():
    # Test text in Sanskrit/Hindi
    test_text = "श्री गणेशाय नमः। ॐ विष्णुर्विष्णुर्विष्णुः।"
    
    print("Testing TTS voice generation...")
    print(f"Test text: {test_text}")
    
    try:
        output_path = await text_to_speech(
            text=test_text,
            language="sanskrit",
            output_path="test_voice_output.mp3"
        )
        
        print(f"\n✅ Audio generated successfully: {output_path}")
        print("\nPlease listen to the audio and verify:")
        print("1. Is it a MALE voice? (should be deep, not feminine)")
        print("2. Does it sound professional and reverent?")
        print("3. Check backend logs above to see which TTS service was used")
        
    except Exception as e:
        print(f"\n❌ Error generating audio: {e}")
        print("\nTroubleshooting:")
        print("1. Check that GOOGLE_CLOUD_TTS_CREDENTIALS_PATH is set correctly in .env")
        print("2. Verify credentials file exists and is valid")
        print("3. Ensure Google Cloud TTS API is enabled in your Google Cloud project")
        print("4. Check backend logs for detailed error messages")

if __name__ == "__main__":
    asyncio.run(test_voice())

