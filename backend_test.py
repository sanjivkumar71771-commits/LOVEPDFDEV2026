#!/usr/bin/env python3
"""
Backend API tests for LovePDF app - Remove Background and Compress Image endpoints
"""
import requests
import io
from PIL import Image
import sys

# Backend base URL from frontend/.env
BASE_URL = "https://45ca9796-e5fd-4358-a4b3-f57a860064e7.preview.emergentagent.com"

def create_test_image(width=800, height=600, color=(255, 0, 0), format='JPEG'):
    """Create a test image in memory"""
    img = Image.new('RGB', (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format=format)
    buf.seek(0)
    return buf

def create_test_text_file():
    """Create a test text file"""
    return io.BytesIO(b"This is a test text file, not an image.")

def test_remove_bg_with_image():
    """Test 1: POST /api/image/remove-bg with a real photo"""
    print("\n" + "="*80)
    print("TEST 1: Remove Background with Real Image")
    print("="*80)
    
    # Create a test JPEG image
    test_image = create_test_image(800, 600, (100, 150, 200), 'JPEG')
    
    url = f"{BASE_URL}/api/image/remove-bg"
    files = {'file': ('test_photo.jpg', test_image, 'image/jpeg')}
    
    print(f"Sending POST request to: {url}")
    print("File: test_photo.jpg (800x600 JPEG)")
    
    try:
        response = requests.post(url, files=files, timeout=120)
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"X-Bg-Engine: {response.headers.get('X-Bg-Engine', 'N/A')}")
        print(f"Content-Disposition: {response.headers.get('Content-Disposition', 'N/A')}")
        print(f"Response Size: {len(response.content)} bytes")
        
        # Check if response is a valid PNG
        if response.status_code == 200:
            png_signature = response.content[:8]
            expected_png_sig = b'\x89PNG\r\n\x1a\n'
            is_valid_png = png_signature == expected_png_sig
            print(f"Valid PNG signature: {is_valid_png}")
            print(f"PNG signature bytes: {png_signature.hex()}")
            
            # Verify required conditions
            checks = {
                "HTTP 200": response.status_code == 200,
                "Content-Type is image/png": response.headers.get('Content-Type') == 'image/png',
                "X-Bg-Engine header present": 'X-Bg-Engine' in response.headers,
                "X-Bg-Engine value valid": response.headers.get('X-Bg-Engine') in ['remove.bg', 'offline'],
                "Valid PNG bytes": is_valid_png
            }
            
            print("\n✓ Verification Checks:")
            all_passed = True
            for check, passed in checks.items():
                status = "✅ PASS" if passed else "❌ FAIL"
                print(f"  {status}: {check}")
                if not passed:
                    all_passed = False
            
            if all_passed:
                print("\n🎉 TEST 1: PASSED")
                engine = response.headers.get('X-Bg-Engine', 'unknown')
                print(f"   Engine used: {engine}")
                if engine == 'offline':
                    print("   ℹ️  Note: Fell back to offline rembg engine (remove.bg keys likely exhausted)")
                return True
            else:
                print("\n❌ TEST 1: FAILED - Some checks did not pass")
                return False
        else:
            print(f"\n❌ TEST 1: FAILED - Expected HTTP 200, got {response.status_code}")
            print(f"Response body: {response.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        print("\n⚠️  TEST 1: TIMEOUT - Request took longer than 120 seconds")
        print("   Note: First offline rembg run can take 10-40s to download model")
        return False
    except Exception as e:
        print(f"\n❌ TEST 1: ERROR - {type(e).__name__}: {e}")
        return False

def test_remove_bg_with_invalid_file():
    """Test 2: POST /api/image/remove-bg with invalid upload (text file)"""
    print("\n" + "="*80)
    print("TEST 2: Remove Background with Invalid File (Text)")
    print("="*80)
    
    test_text = create_test_text_file()
    
    url = f"{BASE_URL}/api/image/remove-bg"
    files = {'file': ('test.txt', test_text, 'text/plain')}
    
    print(f"Sending POST request to: {url}")
    print("File: test.txt (text/plain)")
    
    try:
        response = requests.post(url, files=files, timeout=30)
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        if response.status_code == 415:
            print("\n✅ TEST 2: PASSED - Correctly rejected with HTTP 415")
            print(f"   Response: {response.text[:200]}")
            return True
        else:
            print(f"\n❌ TEST 2: FAILED - Expected HTTP 415, got {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"\n❌ TEST 2: ERROR - {type(e).__name__}: {e}")
        return False

def test_compress_regression():
    """Test 3: Regression test for /api/image/compress"""
    print("\n" + "="*80)
    print("TEST 3: Compress Image Regression (quality=60, max_width=0)")
    print("="*80)
    
    # Create a test JPEG image
    test_image = create_test_image(1200, 900, (200, 100, 50), 'JPEG')
    
    url = f"{BASE_URL}/api/image/compress"
    files = {'file': ('test_image.jpg', test_image, 'image/jpeg')}
    data = {'quality': 60, 'max_width': 0}
    
    print(f"Sending POST request to: {url}")
    print("File: test_image.jpg (1200x900 JPEG)")
    print(f"Parameters: quality=60, max_width=0")
    
    try:
        response = requests.post(url, files=files, data=data, timeout=30)
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"Content-Disposition: {response.headers.get('Content-Disposition', 'N/A')}")
        print(f"Response Size: {len(response.content)} bytes")
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            content_disposition = response.headers.get('Content-Disposition', '')
            
            checks = {
                "HTTP 200": response.status_code == 200,
                "Content-Type is image": content_type.startswith('image/'),
                "Content-Disposition has filename": 'filename=' in content_disposition,
                "Response has content": len(response.content) > 0
            }
            
            print("\n✓ Verification Checks:")
            all_passed = True
            for check, passed in checks.items():
                status = "✅ PASS" if passed else "❌ FAIL"
                print(f"  {status}: {check}")
                if not passed:
                    all_passed = False
            
            if all_passed:
                print("\n🎉 TEST 3: PASSED")
                return True
            else:
                print("\n❌ TEST 3: FAILED - Some checks did not pass")
                return False
        else:
            print(f"\n❌ TEST 3: FAILED - Expected HTTP 200, got {response.status_code}")
            print(f"Response body: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"\n❌ TEST 3: ERROR - {type(e).__name__}: {e}")
        return False

def main():
    print("="*80)
    print("LovePDF Backend API Tests")
    print("Testing Remove Background and Compress Image endpoints")
    print("="*80)
    print(f"Backend URL: {BASE_URL}")
    
    results = {}
    
    # Run all tests
    results['test1_remove_bg_image'] = test_remove_bg_with_image()
    results['test2_remove_bg_invalid'] = test_remove_bg_with_invalid_file()
    results['test3_compress_regression'] = test_compress_regression()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    total = len(results)
    passed = sum(results.values())
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
