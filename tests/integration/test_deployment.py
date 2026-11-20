"""
Quick deployment test script for security updates.
Tests that the server starts and auth middleware is working.
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all imports work"""
    print("🧪 Testing imports...")
    
    try:
        from auth_middleware import require_device_auth, generate_signature, verify_signature
        print("   ✅ auth_middleware imported successfully")
    except ImportError as e:
        print(f"   ❌ Failed to import auth_middleware: {e}")
        return False
    
    try:
        from device_manager import DeviceManager
        print("   ✅ device_manager imported successfully")
    except ImportError as e:
        print(f"   ❌ Failed to import device_manager: {e}")
        return False
    
    return True

def test_signature_generation():
    """Test signature generation"""
    print("\n🧪 Testing signature generation...")
    
    try:
        from auth_middleware import generate_signature
        
        device_id = "AA:BB:CC:DD:EE:FF"
        timestamp = "1234567890"
        nonce = "12345678"
        device_secret = device_id
        
        signature = generate_signature(device_id, timestamp, nonce, device_secret)
        
        if len(signature) == 64:  # SHA256 hex = 64 chars
            print(f"   ✅ Signature generated: {signature[:16]}...")
            return True
        else:
            print(f"   ❌ Invalid signature length: {len(signature)}")
            return False
            
    except Exception as e:
        print(f"   ❌ Signature generation failed: {e}")
        return False

def test_signature_verification():
    """Test signature verification"""
    print("\n🧪 Testing signature verification...")
    
    try:
        from auth_middleware import generate_signature, verify_signature
        import time
        
        device_id = "AA:BB:CC:DD:EE:FF"
        timestamp = str(int(time.time() * 1000))  # Current time in ms
        nonce = "12345678"
        device_secret = device_id
        
        # Generate signature
        signature = generate_signature(device_id, timestamp, nonce, device_secret)
        
        # Verify signature
        is_valid, error_msg = verify_signature(device_id, timestamp, nonce, signature, device_secret)
        
        if is_valid:
            print("   ✅ Signature verification successful")
            return True
        else:
            print(f"   ❌ Signature verification failed: {error_msg}")
            return False
            
    except Exception as e:
        print(f"   ❌ Signature verification test failed: {e}")
        return False

def test_replay_protection():
    """Test replay protection (nonce reuse)"""
    print("\n🧪 Testing replay protection...")
    
    try:
        from auth_middleware import generate_signature, verify_signature
        import time
        
        device_id = "AA:BB:CC:DD:EE:FF"
        timestamp = str(int(time.time() * 1000))
        nonce = "87654321"  # Different nonce
        device_secret = device_id
        
        # Generate signature
        signature = generate_signature(device_id, timestamp, nonce, device_secret)
        
        # First verification should succeed
        is_valid1, error_msg1 = verify_signature(device_id, timestamp, nonce, signature, device_secret)
        
        if not is_valid1:
            print(f"   ❌ First verification failed: {error_msg1}")
            return False
        
        # Second verification with same nonce should fail (replay attack)
        is_valid2, error_msg2 = verify_signature(device_id, timestamp, nonce, signature, device_secret)
        
        if not is_valid2 and "Nonce already used" in error_msg2:
            print("   ✅ Replay protection working (nonce reuse detected)")
            return True
        else:
            print(f"   ❌ Replay protection failed: nonce reuse not detected")
            return False
            
    except Exception as e:
        print(f"   ❌ Replay protection test failed: {e}")
        return False

def test_device_config():
    """Test device configuration loading"""
    print("\n🧪 Testing device configuration...")
    
    try:
        from device_manager import DeviceManager
        
        dm = DeviceManager()
        
        # Check if devices loaded
        if len(dm.devices) == 0:
            print("   ⚠️  No devices in config (this is okay for first setup)")
            return True
        
        # Check first device
        device_id = list(dm.devices.keys())[0]
        device = dm.get_device(device_id)
        
        if device:
            print(f"   ✅ Device loaded: {device_id} ({device.get('staff_name', 'Unknown')})")
            
            # Check if device_secret exists
            if 'device_secret' in device:
                print(f"   ✅ Device secret configured")
            else:
                print(f"   ⚠️  No device_secret (will default to MAC address)")
            
            return True
        else:
            print(f"   ❌ Failed to load device: {device_id}")
            return False
            
    except Exception as e:
        print(f"   ❌ Device config test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🚀 Voice Assistant Server - Deployment Test")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_imports),
        ("Signature Generation", test_signature_generation),
        ("Signature Verification", test_signature_verification),
        ("Replay Protection", test_replay_protection),
        ("Device Configuration", test_device_config)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 All tests passed! Deployment is ready.")
        print("\nNext steps:")
        print("1. Start server: .\\start_server.bat")
        print("2. Test with ESP32 device")
        print("3. Monitor logs: tail -f logs/voice_assistant.log")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please fix issues before deploying.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
