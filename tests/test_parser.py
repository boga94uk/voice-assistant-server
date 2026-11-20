"""
Unit tests for command parser - no server needed.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from command_parser import CommandParser
from utils import load_commands

def test_command_parser():
    """Test command parsing with various inputs"""
    
    # Load commands config
    commands_config = load_commands()
    parser = CommandParser(commands_config)
    
    test_cases = [
        {
            'input': 'book iPhone 15 for screen replacement',
            'expected_type': 'command',
            'expected_command': 'book'
        },
        {
            'input': 'sell Samsung S24 256GB black 600',
            'expected_type': 'command',
            'expected_command': 'sell'
        },
        {
            'input': 'status 123',
            'expected_type': 'command',
            'expected_command': 'status'
        },
        {
            'input': 'volume up',
            'expected_type': 'command',
            'expected_command': 'volume'
        },
        {
            'input': 'brightness 50',
            'expected_type': 'command',
            'expected_command': 'brightness'
        },
        {
            'input': 'book for screen',
            'expected_type': 'incomplete',
            'expected_command': 'book_simple'  # Updated to match new pattern
        },
        {
            'input': 'sell iPhone 15 256 GB Midnight Blue 750',
            'expected_type': 'command',
            'expected_command': 'sell'  # Test spacing tolerance
        },
        {
            'input': 'how do I book a repair?',
            'expected_type': 'help'
        },
        {
            'input': 'what is this device?',
            'expected_type': 'help'
        },
        {
            'input': 'random gibberish xyz',
            'expected_type': 'unknown'
        }
    ]
    
    print("="*70)
    print("COMMAND PARSER TESTS")
    print("="*70)
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: '{test['input']}'")
        print("-" * 70)
        
        result = parser.parse(test['input'])
        
        print(f"Expected Type: {test['expected_type']}")
        print(f"Actual Type:   {result['type']}")
        
        if result['type'] == test['expected_type']:
            print("✓ Type matches")
            
            if 'expected_command' in test:
                if result.get('command') == test['expected_command']:
                    print(f"✓ Command matches: {result['command']}")
                else:
                    print(f"✗ Command mismatch: expected {test['expected_command']}, got {result.get('command')}")
                    failed += 1
                    continue
            
            # Show additional details
            if result['type'] == 'command':
                print(f"  Parameters: {result.get('params', {})}")
                print(f"  Requires confirmation: {result.get('requires_confirmation', False)}")
            elif result['type'] == 'incomplete':
                print(f"  Missing: {result.get('missing', [])}")
                print(f"  Prompt: {result.get('prompt', '')}")
            
            passed += 1
        else:
            print(f"✗ Type mismatch")
            failed += 1
        
        print(f"Full result: {result}")
    
    print("\n" + "="*70)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("="*70)

if __name__ == "__main__":
    test_command_parser()
