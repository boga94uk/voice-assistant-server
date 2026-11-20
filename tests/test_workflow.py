"""
End-to-end workflow test simulating ESP32 interaction.
Tests the complete flow: record → transcribe → parse → confirm → execute
"""
import requests
import os
import sys

SERVER_URL = "http://localhost:8080"
AUTH_TOKEN = "7igjK2M6S6GY13P8C3HxsHRj5uBAA"  # From .env

def test_complete_workflow():
    """Simulate complete ESP32 workflow"""
    
    print("="*70)
    print("END-TO-END WORKFLOW TEST")
    print("="*70)
    print("\nSimulating ESP32 voice assistant interaction\n")
    
    # Check if test audio exists
    audio_path = os.path.join(os.path.dirname(__file__), '..', 'audio_temp', 'test_audio.wav')
    if not os.path.exists(audio_path):
        print("❌ ERROR: test_audio.wav not found")
        print(f"Expected: {audio_path}")
        return
    
    headers = {
        'Authorization': f'Bearer {AUTH_TOKEN}'
    }
    
    # Step 1: User records command
    print("Step 1: User holds button and says 'book iPhone 11 for screen'")
    print("-" * 70)
    
    with open(audio_path, 'rb') as f:
        files = {'audio': ('command.wav', f, 'audio/wav')}
        response = requests.post(
            f"{SERVER_URL}/transcribe",
            files=files,
            headers=headers
        )
    
    if response.status_code != 200:
        print(f"❌ FAILED: {response.status_code}")
        print(response.json())
        return
    
    result = response.json()
    print(f"✓ Transcribed: '{result.get('transcription')}'")
    print(f"  Type: {result.get('type')}")
    
    if result.get('type') == 'confirmation':
        print(f"  Confirmation: {result.get('confirmation')}")
        print(f"  Audio URL: {result.get('audio_url')}")
        print(f"  Command: {result.get('command')}")
        print(f"  Params: {result.get('params')}")
        
        # Step 2: Play TTS confirmation
        print("\nStep 2: ESP32 downloads and plays confirmation audio")
        print("-" * 70)
        
        audio_url = result.get('audio_url')
        if audio_url:
            audio_response = requests.get(audio_url)
            if audio_response.status_code == 200:
                print(f"✓ Downloaded audio: {len(audio_response.content)} bytes")
                print(f"  ESP32 would play: '{result.get('confirmation')}'")
            else:
                print(f"❌ Failed to download audio: {audio_response.status_code}")
        
        # Step 3: User presses confirm button
        print("\nStep 3: User presses top button to confirm")
        print("-" * 70)
        
        execute_response = requests.post(
            f"{SERVER_URL}/execute",
            json={
                'command': result.get('command'),
                'params': result.get('params')
            },
            headers={'Content-Type': 'application/json'}
        )
        
        if execute_response.status_code == 200:
            exec_result = execute_response.json()
            print(f"✓ Command executed!")
            print(f"  Status: {exec_result.get('status')}")
            print(f"  Message: {exec_result.get('message')}")
        else:
            print(f"❌ Execution failed: {execute_response.status_code}")
    
    elif result.get('type') == 'incomplete':
        print(f"  Missing: {result.get('missing')}")
        print(f"  Prompt: {result.get('prompt')}")
        print(f"  Audio URL: {result.get('audio_url')}")
        print(f"  Conversation ID: {result.get('conversation_id')}")
        
        print("\n  (Multi-turn conversation would continue...)")
    
    elif result.get('type') == 'help':
        print(f"  Answer: {result.get('answer')}")
        print(f"  Audio URL: {result.get('audio_url')}")
    
    else:
        print(f"  Message: {result.get('message')}")
        print(f"  Audio URL: {result.get('audio_url')}")
    
    print("\n" + "="*70)
    print("WORKFLOW TEST COMPLETE")
    print("="*70)
    print("\nThis simulates what the ESP32 will do:")
    print("1. Record audio (1-60 seconds)")
    print("2. Upload to /transcribe")
    print("3. Download and play TTS response")
    print("4. Wait for button (confirm/correct/cancel)")
    print("5. Execute command or handle correction")

def test_correction_workflow():
    """Test correction workflow"""
    
    print("\n" + "="*70)
    print("CORRECTION WORKFLOW TEST")
    print("="*70)
    print("\nSimulating correction scenario\n")
    
    # This would require multiple audio files
    # For now, just demonstrate the flow
    print("Correction flow:")
    print("1. Initial command → Confirmation")
    print("2. User holds button (correction mode)")
    print("3. Say correction → POST /correct")
    print("4. New confirmation with updated params")
    print("5. Confirm or correct again (max 3 times)")
    print("\n(Requires additional test audio files)")

if __name__ == "__main__":
    # Check if server is running
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=2)
        if response.status_code != 200:
            print("❌ ERROR: Server not responding")
            print("Start server first: python src/server.py")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to server")
        print("Start server first: python src/server.py")
        sys.exit(1)
    
    test_complete_workflow()
    test_correction_workflow()
