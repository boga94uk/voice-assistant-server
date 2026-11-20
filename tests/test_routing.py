"""
Test Script for 3-Layer Routing Architecture
Tests all layers without calling real Phoneshop API
"""
import sys
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import after path setup
from utils import load_config, load_commands, load_env
from command_parser import CommandParser
from unified_command_extractor import UnifiedCommandExtractor
from conversation import ConversationManager

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_test(name, layer):
    """Print test header"""
    layer_colors = {
        1: Colors.RED,
        2: Colors.YELLOW,
        3: Colors.CYAN
    }
    color = layer_colors.get(layer, Colors.BLUE)
    print(f"\n{color}{Colors.BOLD}=== LAYER {layer} TEST: {name} ==={Colors.END}")

def print_result(passed, message):
    """Print test result"""
    if passed:
        print(f"{Colors.GREEN}✅ PASS:{Colors.END} {message}")
    else:
        print(f"{Colors.RED}❌ FAIL:{Colors.END} {message}")

def print_info(label, value):
    """Print info line"""
    print(f"{Colors.BLUE}{label}:{Colors.END} {value}")

# Load configuration
print(f"{Colors.BOLD}Loading configuration...{Colors.END}")
load_env()
config = load_config()
commands_config = load_commands()
config_dir = Path(__file__).parent.parent / 'config'

# Helper function to create properly structured mock responses
def make_mock_response(payload: dict):
    """Create a mock OpenAI response with proper structure"""
    choice = Mock()
    choice.message = Mock()
    choice.message.content = json.dumps(payload)
    
    response = Mock()
    response.choices = [choice]
    return response

# Initialize services with mocked OpenAI
print(f"{Colors.BOLD}Initializing services (with mocked OpenAI)...{Colors.END}")

# Mock LLM Parser
llm_parser = Mock()

# Initialize Command Parser (Layer 1)
command_parser = CommandParser(commands_config, llm_parser)

# Initialize Unified Command Extractor (Layer 2) with mocked OpenAI
openai_config = {
    'api_key': 'test-key',
    'model': 'gpt-4o-mini',
    'max_tokens': 500,
    'temperature': 0.7
}

# Mock the OpenAI client in unified extractor
with patch('unified_command_extractor.OpenAI'):
    unified_extractor = UnifiedCommandExtractor(openai_config, config_dir)
    
    # Mock the client's chat completion
    unified_extractor.client.chat.completions.create = Mock()

print(f"{Colors.GREEN}✅ Services initialized{Colors.END}\n")

# Test counters
total_tests = 0
passed_tests = 0

def run_test(name, layer, test_func):
    """Run a test and track results"""
    global total_tests, passed_tests
    total_tests += 1
    print_test(name, layer)
    try:
        passed = test_func()
        if passed:
            passed_tests += 1
        return passed
    except Exception as e:
        print_result(False, f"Exception: {e}")
        return False

# === LAYER 1 TESTS (Regex Matching) ===

def test_ticket_start():
    """Test: ticket 1234 started"""
    text = "ticket 1234 started"
    print_info("Input", text)
    
    result = command_parser.parse_with_regex(text)
    
    if result and result.get('type') == 'command':
        print_info("Command", result.get('command'))
        print_info("Params", result.get('params'))
        passed = result.get('command') == 'ticket_start' and result['params'].get('ticket_id') == '1234'
        print_result(passed, "Regex matched ticket_start with ID 1234")
        return passed
    else:
        print_result(False, "No regex match")
        return False

def test_ticket_complete():
    """Test: ticket 5678 completed"""
    text = "ticket 5678 completed"
    print_info("Input", text)
    
    result = command_parser.parse_with_regex(text)
    
    if result and result.get('type') == 'command':
        print_info("Command", result.get('command'))
        passed = result.get('command') == 'ticket_complete'
        print_result(passed, "Regex matched ticket_complete")
        return passed
    else:
        print_result(False, "No regex match")
        return False

def test_no_regex_match():
    """Test: book iphone for battery (should NOT match regex)"""
    text = "book iphone for battery"
    print_info("Input", text)
    
    result = command_parser.parse_with_regex(text)
    
    passed = result is None
    print_result(passed, "Correctly did NOT match regex (goes to Layer 2)")
    return passed

# === LAYER 2 TESTS (Unified Command Extractor) ===

def test_book_complete():
    """Test: Book iPhone 12 for battery, price 75"""
    text = "Book iPhone 12 for battery, price 75"
    print_info("Input", text)
    
    # Mock LLM response for complete command
    mock_payload = {
        "command": "book",
        "params": {
            "brand": "Apple",
            "model": "iPhone 12",
            "problem": "battery replacement",
            "totalPrice": 75
        },
        "missing_params": [],
        "confidence": 0.96
    }
    unified_extractor.client.chat.completions.create.return_value = make_mock_response(mock_payload)
    
    result = unified_extractor.extract_command(text)
    
    print_info("Command", result.get('command'))
    print_info("Params", result.get('params'))
    print_info("Confidence", result.get('confidence'))
    
    passed = (
        result.get('command') == 'book' and
        result.get('confidence') > 0.5 and
        len(result.get('missing_params', [])) == 0
    )
    print_result(passed, "Extracted complete book command")
    return passed

def test_book_incomplete():
    """Test: Book for screen (missing brand/model)"""
    text = "Book for screen"
    print_info("Input", text)
    
    # Mock LLM response for incomplete command
    mock_payload = {
        "command": "book",
        "params": {
            "problem": "screen replacement"
        },
        "missing_params": ["brand", "model"],
        "confidence": 0.6
    }
    unified_extractor.client.chat.completions.create.return_value = make_mock_response(mock_payload)
    
    result = unified_extractor.extract_command(text)
    
    print_info("Command", result.get('command'))
    print_info("Missing params", result.get('missing_params'))
    
    passed = (
        result.get('command') == 'book' and
        'brand' in result.get('missing_params', [])
    )
    print_result(passed, "Detected missing parameters")
    return passed

def test_sell_command():
    """Test: Sell Samsung S21 128GB Blue £399"""
    text = "Sell Samsung S21 128GB Blue £399"
    print_info("Input", text)
    
    # Mock LLM response
    mock_payload = {
        "command": "sell",
        "params": {
            "brand": "Samsung",
            "model": "Galaxy S21",
            "storage": "128GB",
            "color": "Blue",
            "price": 399
        },
        "missing_params": [],
        "confidence": 0.95
    }
    unified_extractor.client.chat.completions.create.return_value = make_mock_response(mock_payload)
    
    result = unified_extractor.extract_command(text)
    
    print_info("Command", result.get('command'))
    print_info("Params", result.get('params'))
    
    passed = result.get('command') == 'sell' and result.get('confidence') > 0.5
    print_result(passed, "Extracted sell command")
    return passed

def test_unknown_command():
    """Test: Random gibberish (should be unknown)"""
    text = "asdf qwerty zxcv"
    print_info("Input", text)
    
    # Mock LLM response for unknown
    mock_payload = {
        "command": "unknown",
        "params": {},
        "missing_params": [],
        "confidence": 0.1
    }
    unified_extractor.client.chat.completions.create.return_value = make_mock_response(mock_payload)
    
    result = unified_extractor.extract_command(text)
    
    print_info("Command", result.get('command'))
    print_info("Confidence", result.get('confidence'))
    
    passed = result.get('command') == 'unknown' or result.get('confidence') < 0.5
    print_result(passed, "Correctly identified as unknown (goes to Layer 3)")
    return passed

# === LAYER 3 TESTS (Agent/Conversational) ===

def test_agent_routing():
    """Test: Questions route to Layer 3"""
    test_queries = [
        "Is my Nokia repair ready?",
        "What's the status of ticket 1227?",
        "Where is my Samsung?",
        "How much does it cost?"
    ]
    
    all_passed = True
    for query in test_queries:
        print_info("Query", query)
        
        # Check it doesn't match regex
        regex_result = command_parser.parse_with_regex(query)
        
        # Mock LLM to return unknown (should route to agent)
        mock_payload = {
            "command": "unknown",
            "params": {},
            "missing_params": [],
            "confidence": 0.2
        }
        unified_extractor.client.chat.completions.create.return_value = make_mock_response(mock_payload)
        
        extract_result = unified_extractor.extract_command(query)
        
        passed = (
            regex_result is None and
            (extract_result.get('command') == 'unknown' or extract_result.get('confidence') < 0.5)
        )
        
        if passed:
            print(f"  {Colors.GREEN}✓{Colors.END} Routes to Layer 3 (Agent)")
        else:
            print(f"  {Colors.RED}✗{Colors.END} Does NOT route to Layer 3")
            all_passed = False
    
    print_result(all_passed, "All queries route to Agent layer")
    return all_passed

# === RUN ALL TESTS ===

print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
print(f"{Colors.BOLD}TESTING 3-LAYER ROUTING ARCHITECTURE{Colors.END}")
print(f"{Colors.BOLD}{'='*60}{Colors.END}")

# Layer 1 Tests
run_test("Ticket Start Command", 1, test_ticket_start)
run_test("Ticket Complete Command", 1, test_ticket_complete)
run_test("No Regex Match (passes to Layer 2)", 1, test_no_regex_match)

# Layer 2 Tests
run_test("Complete Book Command", 2, test_book_complete)
run_test("Incomplete Book Command", 2, test_book_incomplete)
run_test("Sell Command", 2, test_sell_command)
run_test("Unknown Command (passes to Layer 3)", 2, test_unknown_command)

# Layer 3 Tests
run_test("Conversational Queries Route to Agent", 3, test_agent_routing)

# Summary
print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
print(f"{Colors.BOLD}TEST SUMMARY{Colors.END}")
print(f"{Colors.BOLD}{'='*60}{Colors.END}")
print(f"Total Tests: {total_tests}")
print(f"{Colors.GREEN}Passed: {passed_tests}{Colors.END}")
print(f"{Colors.RED}Failed: {total_tests - passed_tests}{Colors.END}")
print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%\n")

if passed_tests == total_tests:
    print(f"{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED! 🎉{Colors.END}\n")
    sys.exit(0)
else:
    print(f"{Colors.RED}{Colors.BOLD}❌ SOME TESTS FAILED{Colors.END}\n")
    sys.exit(1)
