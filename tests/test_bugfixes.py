"""
Test Bug Fixes
Verify the two specific bug fixes from log analysis:
1. Ticket ID with transcription artifacts ("12.27" → "1227")
2. Book command loop prevention
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from command_parser import CommandParser
from conversation import ConversationManager
from utils import load_commands

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

print(f"{Colors.BOLD}Testing Bug Fixes{Colors.END}")
print("="*60)

# Load config
commands_config = load_commands()
command_parser = CommandParser(commands_config, None)
conversation_manager = ConversationManager()

total_tests = 0
passed_tests = 0

def test(name, func):
    """Run test and track results"""
    global total_tests, passed_tests
    total_tests += 1
    print(f"\n{Colors.BLUE}Test:{Colors.END} {name}")
    try:
        passed = func()
        if passed:
            print(f"  {Colors.GREEN}✅ PASS{Colors.END}")
            passed_tests += 1
        else:
            print(f"  {Colors.RED}❌ FAIL{Colors.END}")
        return passed
    except Exception as e:
        print(f"  {Colors.RED}❌ FAIL: {e}{Colors.END}")
        return False

# === BUG FIX 1: Ticket ID Transcription Artifacts ===

def test_ticket_complete_with_dots():
    """Test: 'Ticket 12.27 completed' should extract ticket 1227"""
    text = "Ticket 12.27 completed"
    result = command_parser.parse_with_regex(text)
    
    if result and result.get('command') == 'ticket_complete':
        ticket_id = result['params'].get('ticket_id')
        print(f"  Input: '{text}'")
        print(f"  Extracted ticket_id: '{ticket_id}'")
        return ticket_id == '1227'
    return False

def test_ticket_start_with_commas():
    """Test: 'Ticket 1,2,3,4 started' should extract ticket 1234"""
    text = "Ticket 1,2,3,4 started"
    result = command_parser.parse_with_regex(text)
    
    if result and result.get('command') == 'ticket_start':
        ticket_id = result['params'].get('ticket_id')
        print(f"  Input: '{text}'")
        print(f"  Extracted ticket_id: '{ticket_id}'")
        return ticket_id == '1234'
    return False

def test_ticket_with_spaces():
    """Test: 'Ticket 1 2 2 7 collected' should extract ticket 1227"""
    text = "Ticket 1 2 2 7 collected"
    result = command_parser.parse_with_regex(text)
    
    if result and result.get('command') == 'ticket_collected':
        ticket_id = result['params'].get('ticket_id')
        print(f"  Input: '{text}'")
        print(f"  Extracted ticket_id: '{ticket_id}'")
        return ticket_id == '1227'
    return False

def test_print_ticket_with_dots():
    """Test: 'Print ticket 12.27' should extract ticket 1227"""
    text = "Print ticket 12.27"
    result = command_parser.parse_with_regex(text)
    
    if result and result.get('command') == 'print_ticket':
        ticket_id = result['params'].get('ticket_id')
        print(f"  Input: '{text}'")
        print(f"  Extracted ticket_id: '{ticket_id}'")
        return ticket_id == '1227'
    return False

# === BUG FIX 2: Context Reset for New Commands ===

def test_context_reset_on_book():
    """Test: 'book' keyword should trigger context reset"""
    conv_id = conversation_manager.create('help', {}, [])
    
    should_reset = conversation_manager.should_reset_context("book iPhone 12", conv_id)
    print(f"  Existing conversation: 'help'")
    print(f"  New text: 'book iPhone 12'")
    print(f"  Should reset: {should_reset}")
    
    conversation_manager.complete(conv_id)
    return should_reset == True

def test_context_reset_on_sell():
    """Test: 'sell' keyword should trigger context reset"""
    conv_id = conversation_manager.create('book', {'brand': 'Apple'}, ['model'])
    
    should_reset = conversation_manager.should_reset_context("sell Samsung S21", conv_id)
    print(f"  Existing conversation: 'book' (partial)")
    print(f"  New text: 'sell Samsung S21'")
    print(f"  Should reset: {should_reset}")
    
    conversation_manager.complete(conv_id)
    return should_reset == True

def test_context_reset_on_ticket():
    """Test: 'ticket' keyword should trigger context reset"""
    conv_id = conversation_manager.create('book', {'brand': 'Apple'}, ['model'])
    
    should_reset = conversation_manager.should_reset_context("ticket 1234 completed", conv_id)
    print(f"  Existing conversation: 'book' (partial)")
    print(f"  New text: 'ticket 1234 completed'")
    print(f"  Should reset: {should_reset}")
    
    conversation_manager.complete(conv_id)
    return should_reset == True

def test_no_reset_on_answer():
    """Test: Simple answer should NOT trigger context reset"""
    conv_id = conversation_manager.create('book', {'brand': 'Apple'}, ['model'])
    
    should_reset = conversation_manager.should_reset_context("iPhone 12", conv_id)
    print(f"  Existing conversation: 'book' (partial)")
    print(f"  New text: 'iPhone 12' (answer)")
    print(f"  Should reset: {should_reset}")
    
    conversation_manager.complete(conv_id)
    return should_reset == False

def test_param_merging():
    """Test: merge_params should update params without replacing"""
    conv_id = conversation_manager.create('book', {'brand': 'Apple'}, ['model', 'problem'])
    
    conversation_manager.merge_params(conv_id, {'model': 'iPhone 12'})
    conv = conversation_manager.get(conv_id)
    
    print(f"  Initial params: {'brand': 'Apple'}")
    print(f"  Merged: {'model': 'iPhone 12'}")
    print(f"  Result params: {conv['params']}")
    print(f"  Still missing: {conv['missing']}")
    
    has_both = conv['params'].get('brand') == 'Apple' and conv['params'].get('model') == 'iPhone 12'
    correct_missing = 'problem' in conv['missing'] and 'model' not in conv['missing']
    
    conversation_manager.complete(conv_id)
    return has_both and correct_missing

# Run all tests
print(f"\n{Colors.BOLD}BUG FIX 1: Ticket ID Transcription Handling{Colors.END}")
print("-"*60)
test("Ticket 12.27 completed", test_ticket_complete_with_dots)
test("Ticket 1,2,3,4 started", test_ticket_start_with_commas)
test("Ticket 1 2 2 7 collected", test_ticket_with_spaces)
test("Print ticket 12.27", test_print_ticket_with_dots)

print(f"\n{Colors.BOLD}BUG FIX 2: Book Command Loop Prevention{Colors.END}")
print("-"*60)
test("Context reset on 'book' keyword", test_context_reset_on_book)
test("Context reset on 'sell' keyword", test_context_reset_on_sell)
test("Context reset on 'ticket' keyword", test_context_reset_on_ticket)
test("No reset on simple answer", test_no_reset_on_answer)
test("Parameter merging", test_param_merging)

# Summary
print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
print(f"{Colors.BOLD}SUMMARY{Colors.END}")
print(f"{Colors.BOLD}{'='*60}{Colors.END}")
print(f"Total Tests: {total_tests}")
print(f"{Colors.GREEN}Passed: {passed_tests}{Colors.END}")
print(f"{Colors.RED}Failed: {total_tests - passed_tests}{Colors.END}")
print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%\n")

if passed_tests == total_tests:
    print(f"{Colors.GREEN}{Colors.BOLD}🎉 ALL BUG FIXES VERIFIED! 🎉{Colors.END}\n")
    sys.exit(0)
else:
    print(f"{Colors.RED}{Colors.BOLD}❌ SOME TESTS FAILED{Colors.END}\n")
    sys.exit(1)
