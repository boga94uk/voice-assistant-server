"""
Test audio transcription with OpenAI Whisper.
This requires a real audio file to test.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from transcription import TranscriptionService
from utils import load_config, load_env

def test_transcription():
    """Test transcription with a sample audio file"""
    
    load_env()
    config = load_config()
    
    # Initialize transcription service
    transcription_service = TranscriptionService(config, os.getenv('OPENAI_API_KEY'))
    
    # Check if we have a test audio file
    test_audio_path = os.path.join(os.path.dirname(__file__), '..', 'audio_temp', 'test_audio.wav')
    
    if not os.path.exists(test_audio_path):
        print("="*70)
        print("NO TEST AUDIO FILE FOUND")
        print("="*70)
        print(f"\nExpected file: {test_audio_path}")
        print("\nTo test transcription:")
        print("1. Record a short audio file (say 'book iPhone 15 for screen')")
        print("2. Save it as: audio_temp/test_audio.wav")
        print("3. Run this test again")
        print("\nOr use an online tool to generate a test WAV file.")
        return
    
    print("="*70)
    print("TRANSCRIPTION TEST")
    print("="*70)
    print(f"\nTranscribing: {test_audio_path}")
    print("This will use OpenAI Whisper API (costs ~$0.006 per minute)")
    
    try:
        text = transcription_service.transcribe(test_audio_path)
        
        if text:
            print(f"\n✓ SUCCESS!")
            print(f"Transcribed text: '{text}'")
            print(f"\nLength: {len(text)} characters")
        else:
            print("\n✗ FAILED - No text returned")
    
    except Exception as e:
        print(f"\n✗ ERROR: {e}")

if __name__ == "__main__":
    test_transcription()
