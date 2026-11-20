"""
Quick test script to verify OpenAI transcription is working.
This helps diagnose why the server is returning mock responses.
"""
import os
import sys
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv('config/.env')

# Get API key
api_key = os.getenv('OPENAI_API_KEY')

print("="*60)
print("  OpenAI Transcription Service Test")
print("="*60)
print()

# Check API key
if not api_key:
    print("❌ FAIL: OPENAI_API_KEY not found in config/.env")
    print()
    print("Fix: Edit config/.env and set your OpenAI API key:")
    print("OPENAI_API_KEY=sk-proj-...")
    sys.exit(1)

if api_key == "sk-your-key-here":
    print("❌ FAIL: OPENAI_API_KEY is set to default value")
    print()
    print("Fix: Edit config/.env and set your actual OpenAI API key")
    sys.exit(1)

print(f"✓ API Key found ({len(api_key)} characters)")
print(f"  Starts with: {api_key[:7]}...")
print()

# Test API connection
print("Testing OpenAI API connection...")
try:
    client = OpenAI(api_key=api_key)
    
    # Try to list models (quick test)
    models = client.models.list()
    print("✓ Successfully connected to OpenAI API")
    print()
    
except Exception as e:
    print(f"❌ FAIL: Cannot connect to OpenAI API")
    print(f"Error: {e}")
    print()
    print("Possible causes:")
    print("  - Invalid API key")
    print("  - Network connectivity issue")
    print("  - OpenAI service temporarily down")
    print("  - Rate limit exceeded")
    print()
    print("Solutions:")
    print("  1. Verify your API key at https://platform.openai.com/api-keys")
    print("  2. Check your OpenAI account billing and usage")
    print("  3. Check your internet connection")
    sys.exit(1)

# Test Whisper API specifically
print("Testing Whisper transcription API...")
print("Note: This will use a small amount of API credits")
print()

try:
    # Create a tiny test audio file (1 second of silence as WAV)
    import wave
    import struct
    
    test_file = "test_audio.wav"
    
    # Generate 1 second of silence at 16kHz, mono
    with wave.open(test_file, 'wb') as wav:
        wav.setnchannels(1)  # Mono
        wav.setsampwidth(2)  # 16-bit
        wav.setframerate(16000)  # 16kHz
        
        # 1 second of silence
        for i in range(16000):
            wav.writeframes(struct.pack('<h', 0))
    
    print(f"Created test audio file: {test_file}")
    
    # Try transcription
    with open(test_file, 'rb') as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text"
        )
    
    print("✓ Whisper API is working!")
    print(f"  Transcription result: '{transcript.strip() if transcript else '(empty)'}'"
)
    print()
    
    # Cleanup
    if os.path.exists(test_file):
        os.remove(test_file)
        print(f"Cleaned up test file: {test_file}")
    
except Exception as e:
    print(f"❌ FAIL: Whisper transcription failed")
    print(f"Error: {e}")
    print()
    print("This could indicate:")
    print("  - Insufficient API credits/quota")
    print("  - API key lacks transcription permissions")
    print("  - Temporary API service issue")
    print()
    
    # Cleanup on error
    if os.path.exists("test_audio.wav"):
        os.remove("test_audio.wav")
    
    sys.exit(1)

print()
print("="*60)
print("  All Tests Passed! ✓")
print("="*60)
print()
print("The transcription service should be working.")
print("If the server is still returning mock responses:")
print("  1. Restart the server: start_server.bat")
print("  2. Check the server console for error messages")
print("  3. Try sending a test recording from the ESP32 device")
