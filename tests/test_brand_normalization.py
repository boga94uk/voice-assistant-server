"""
Test brand normalization logic.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from command_parser import CommandParser
from utils import load_commands

def test_brand_normalization():
    """Test brand normalization for Apple and Samsung products"""
    
    commands_config = load_commands()
    parser = CommandParser(commands_config)
    
    test_cases = [
        # Apple products
        {
            'input': 'book iPhone 15 for screen',
            'expected_brand': 'Apple',
            'expected_model': 'iPhone 15'
        },
        {
            'input': 'book iPad Pro for battery',
            'expected_brand': 'Apple',
            'expected_model': 'iPad Pro'
        },
        {
            'input': 'book MacBook Air for keyboard',
            'expected_brand': 'Apple',
            'expected_model': 'MacBook Air'
        },
        {
            'input': 'book iMac 27 for display',
            'expected_brand': 'Apple',
            'expected_model': 'iMac 27'
        },
        # Samsung products
        {
            'input': 'book Samsung S24 for screen',
            'expected_brand': 'Samsung',
            'expected_model': 'S24'
        },
        {
            'input': 'book Galaxy S24 for screen',
            'expected_brand': 'Samsung',
            'expected_model': 'Galaxy S24'
        },
        {
            'input': 'book Samsung Galaxy S24 for screen',
            'expected_brand': 'Samsung',
            'expected_model': 'Galaxy S24'
        },
        # Other brands (should stay as-is)
        {
            'input': 'book Google Pixel for screen',
            'expected_brand': 'Google',
            'expected_model': 'Pixel'
        },
        {
            'input': 'book OnePlus 12 for screen',
            'expected_brand': 'OnePlus',
            'expected_model': '12'
        }
    ]
    
    print("="*70)
    print("BRAND NORMALIZATION TESTS")
    print("="*70)
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: '{test['input']}'")
        print("-" * 70)
        
        result = parser.parse(test['input'])
        
        if result['type'] == 'command':
            actual_brand = result['params'].get('brand', '')
            actual_model = result['params'].get('model', '')
            
            print(f"Expected: brand='{test['expected_brand']}', model='{test['expected_model']}'")
            print(f"Actual:   brand='{actual_brand}', model='{actual_model}'")
            
            if actual_brand == test['expected_brand'] and actual_model == test['expected_model']:
                print("✓ PASS")
                passed += 1
            else:
                print("✗ FAIL")
                failed += 1
        else:
            print(f"✗ FAIL - Unexpected result type: {result['type']}")
            failed += 1
    
    print("\n" + "="*70)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("="*70)

if __name__ == "__main__":
    test_brand_normalization()
