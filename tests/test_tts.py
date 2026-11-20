"""
Test TTS generation with OpenAI.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tts_service import TTSService
from utils import load_config, load_env, get_audio_temp_dir

def test_tts():
    """Test TTS generation with sample text"""
    
    load_env()
    config = load_config()
    audio_temp_dir = get_audio_temp_dir()
    
    # Initialize TTS service
    tts_service = TTSService(config, os.getenv('OPENAI_API_KEY'), audio_temp_dir)
    
    test_cases = [
        "Confirm: Book Samsung Galaxy S24 for screen?",
        "Sure, please tell me the make and model.",
        "Command executed successfully!",
        "Too many corrections. Please start over.",
        "What would you like to do?"
    ]
    
    print("="*70)
    print("TTS GENERATION TEST")
    print("="*70)
    print("\nThis will use OpenAI TTS API (costs ~$0.015 per 1M characters)")
    print(f"Testing {len(test_cases)} phrases\n")
    
    passed = 0
    failed = 0
    
    for i, text in enumerate(test_cases, 1):
        print(f"\nTest {i}: '{text}'")
        print("-" * 70)
        
        try:
            audio_path = tts_service.generate(text)
            
            if audio_path and os.path.exists(audio_path):
                file_size = os.path.getsize(audio_path)
                print(f"✓ SUCCESS!")
                print(f"  File: {os.path.basename(audio_path)}")
                print(f"  Size: {file_size:,} bytes")
                print(f"  URL: http://localhost:8080/audio/{os.path.basename(audio_path)}")
                passed += 1
            else:
                print(f"✗ FAILED - No file generated")
                failed += 1
        
        except Exception as e:
            print(f"✗ ERROR: {e}")
            failed += 1
    
    print("\n" + "="*70)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("="*70)
    
    # Calculate total characters
    total_chars = sum(len(text) for text in test_cases)
    estimated_cost = (total_chars / 1_000_000) * 15
    print(f"\nTotal characters: {total_chars}")
    print(f"Estimated cost: ${estimated_cost:.6f}")
    
    if passed > 0:
        print("\n" + "="*70)
        print("To test audio playback:")
        print("1. Make sure server is running: python src/server.py")
        print("2. Open browser to: http://localhost:8080/audio/tts_<hash>.mp3")
        print("3. Or use the URLs printed above")
        print("="*70)

if __name__ == "__main__":
    test_tts()
