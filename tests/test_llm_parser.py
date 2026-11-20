"""
Test LLM-powered parameter extraction.
Requires valid OpenAI API key in .env
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from llm_parser import LLMParser
from utils import load_config, load_env

def test_llm_extraction():
    """Test LLM extraction with real-world examples"""
    
    load_env()
    config = load_config()
    llm_parser = LLMParser(config, os.getenv('OPENAI_API_KEY'))
    
    test_cases = [
        # Your actual usage patterns
        {
            'input': 'S24 for screen',
            'expected': {'brand': 'Samsung', 'model': 'Galaxy S24', 'problem': 'screen'}
        },
        {
            'input': 'iPhone 15 battery',
            'expected': {'brand': 'Apple', 'model': 'iPhone 15', 'problem': 'battery'}
        },
        {
            'input': 'Pixel 7 charging port',
            'expected': {'brand': 'Google', 'model': 'Pixel 7', 'problem': 'charging port'}
        },
        {
            'input': 'A12 screen replacement',
            'expected': {'brand': 'Samsung', 'model': 'Galaxy A12', 'problem': 'screen replacement'}
        },
        {
            'input': 'OPPO screen',
            'expected': {'brand': 'OPPO', 'model': 'Unknown', 'problem': 'screen'}
        },
        {
            'input': 'MacBook Air keyboard',
            'expected': {'brand': 'Apple', 'model': 'MacBook Air', 'problem': 'keyboard'}
        }
    ]
    
    print("="*70)
    print("LLM PARAMETER EXTRACTION TESTS")
    print("="*70)
    print("\nNote: This uses OpenAI API and costs ~$0.000015 per test\n")
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: '{test['input']}'")
        print("-" * 70)
        
        result = llm_parser.extract_book_params(test['input'])
        
        print(f"Expected: {test['expected']}")
        print(f"Got:      {result}")
        
        # Check if results match (allowing some flexibility)
        brand_match = result.get('brand') == test['expected']['brand']
        model_match = result.get('model') == test['expected']['model'] or \
                     (result.get('model') and test['expected']['model'] in result.get('model', ''))
        problem_match = result.get('problem') and test['expected']['problem'] in result.get('problem', '')
        
        if brand_match and model_match and problem_match:
            print("✓ PASS")
            passed += 1
        else:
            print("✗ FAIL")
            if not brand_match:
                print(f"  Brand mismatch: expected '{test['expected']['brand']}', got '{result.get('brand')}'")
            if not model_match:
                print(f"  Model mismatch: expected '{test['expected']['model']}', got '{result.get('model')}'")
            if not problem_match:
                print(f"  Problem mismatch: expected '{test['expected']['problem']}', got '{result.get('problem')}'")
            failed += 1
    
    print("\n" + "="*70)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("="*70)
    print(f"\nEstimated cost: ${len(test_cases) * 0.000015:.6f}")

if __name__ == "__main__":
    # Load .env first before checking
    load_env()
    
    if not os.getenv('OPENAI_API_KEY'):
        print("ERROR: OPENAI_API_KEY not found in environment")
        print("Make sure config/.env has your API key")
        sys.exit(1)
    
    test_llm_extraction()
