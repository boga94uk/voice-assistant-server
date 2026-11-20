"""
Test client to simulate ESP32 requests to the server.
"""
import requests
import os

SERVER_URL = "http://localhost:8080"
AUTH_TOKEN = "test-token-123"  # Match this with your .env SERVER_AUTH_TOKEN

def test_health():
    """Test health endpoint"""
    response = requests.get(f"{SERVER_URL}/health")
    print(f"Health Check: {response.json()}")
    return response.status_code == 200

def test_status():
    """Test status endpoint"""
    response = requests.get(f"{SERVER_URL}/status")
    print(f"Status: {response.json()}")
    return response.status_code == 200

def test_transcribe_with_text(text):
    """
    Test transcription endpoint by simulating audio upload.
    For now, we'll just test the command parsing logic.
    """
    # Create a dummy audio file
    audio_path = "test_audio.wav"
    with open(audio_path, 'wb') as f:
        f.write(b'RIFF' + b'\x00' * 100)  # Minimal WAV header
    
    try:
        headers = {
            'Authorization': f'Bearer {AUTH_TOKEN}'
        }
        
        with open(audio_path, 'rb') as f:
            files = {'audio': ('test.wav', f, 'audio/wav')}
            response = requests.post(
                f"{SERVER_URL}/transcribe",
                files=files,
                headers=headers
            )
        
        print(f"\nTranscribe Response ({response.status_code}):")
        print(response.json())
        return response
    
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)

def test_command_parsing():
    """Test command parsing with various inputs"""
    test_cases = [
        "book iPhone 15 for screen",
        "sell Samsung S24 256GB black 600",
        "status 123",
        "volume up",
        "how do I book a repair?",
        "book for screen",  # Incomplete command
    ]
    
    print("\n" + "="*60)
    print("COMMAND PARSING TESTS")
    print("="*60)
    
    for test_text in test_cases:
        print(f"\nTest: '{test_text}'")
        print("-" * 60)
        # We'll need to actually send audio, but for now this shows the structure

if __name__ == "__main__":
    print("Voice Assistant Server - Test Client")
    print("=" * 60)
    
    # Test basic endpoints
    print("\n1. Testing Health Endpoint...")
    test_health()
    
    print("\n2. Testing Status Endpoint...")
    test_status()
    
    print("\n3. Command Parsing Tests...")
    test_command_parsing()
    
    print("\n" + "="*60)
    print("Note: Full audio transcription tests require:")
    print("- Valid OpenAI API key in .env")
    print("- Real audio file or text-to-speech")
    print("="*60)
