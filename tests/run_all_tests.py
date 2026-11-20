"""
Master test runner for all Voice Assistant Server tests.

Runs all test suites and provides a summary report.
"""

import sys
import subprocess
import time


def run_test(test_file, description):
    """Run a single test file and return results"""
    print(f"\n{'='*70}")
    print(f"Running: {description}")
    print(f"File: {test_file}")
    print('='*70)
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        elapsed = time.time() - start_time
        
        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr and result.returncode != 0:
            print("STDERR:", result.stderr)
        
        success = result.returncode == 0
        
        return {
            'name': description,
            'file': test_file,
            'success': success,
            'elapsed': elapsed,
            'output': result.stdout
        }
        
    except subprocess.TimeoutExpired:
        return {
            'name': description,
            'file': test_file,
            'success': False,
            'elapsed': 30,
            'error': 'Timeout (30s)'
        }
    except Exception as e:
        return {
            'name': description,
            'file': test_file,
            'success': False,
            'elapsed': 0,
            'error': str(e)
        }


def print_summary(results):
    """Print test summary report"""
    print("\n" + "="*70)
    print("TEST SUMMARY REPORT")
    print("="*70)
    
    passed = sum(1 for r in results if r['success'])
    failed = len(results) - passed
    total_time = sum(r['elapsed'] for r in results)
    
    print(f"\nTotal Tests: {len(results)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⏱️  Total Time: {total_time:.2f}s")
    
    print("\nDetailed Results:")
    print("-" * 70)
    
    for i, result in enumerate(results, 1):
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{i}. {status} - {result['name']} ({result['elapsed']:.2f}s)")
        
        if not result['success'] and 'error' in result:
            print(f"   Error: {result['error']}")
    
    print("=" * 70)
    
    if failed > 0:
        print(f"\n❌ {failed} test(s) failed!")
        return False
    else:
        print("\n✅ All tests passed!")
        return True


if __name__ == '__main__':
    print("\n" + "#"*70)
    print("# VOICE ASSISTANT SERVER - COMPREHENSIVE TEST SUITE")
    print("#"*70)
    print("\nThis will run all test suites to verify:")
    print("  • TTS caching system")
    print("  • Response types (Say/Ask/Confirm)")
    print("  • LLM fallback")
    print("  • Conversation management")
    print("  • Question limits")
    
    input("\nPress Enter to start testing...")
    
    tests = [
        ('test_tts_caching.py', 'TTS Caching System'),
        ('test_response_types.py', 'Response Types & Conversations'),
        ('test_llm_fallback.py', 'LLM Fallback & Natural Language'),
    ]
    
    results = []
    
    for test_file, description in tests:
        result = run_test(test_file, description)
        results.append(result)
    
    # Print summary
    all_passed = print_summary(results)
    
    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)
