"""
File: camera_test.py
Create this file in your ROOP folder and run it to test camera
Run: python camera_test.py
"""
import cv2
import time

def test_camera():
    print("=" * 50)
    print("CAMERA DIAGNOSTIC TEST")
    print("=" * 50)
    
    # Test 1: Basic open
    print("\n[TEST 1] Opening camera first time...")
    cap = cv2.VideoCapture(0)
    time.sleep(0.5)
    
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print("✓ SUCCESS: Camera opened and read frame")
        else:
            print("✗ FAIL: Camera opened but cannot read frame")
        cap.release()
        print("  Released camera")
    else:
        print("✗ FAIL: Cannot open camera")
        print("\n  POSSIBLE CAUSES:")
        print("  - Camera is used by another app (Zoom, Teams, Browser)")
        print("  - Camera driver issue")
        print("  - No camera connected")
        return
    
    # Test 2: Re-open after release
    print("\n[TEST 2] Re-opening camera after release...")
    time.sleep(1)  # Wait 1 second
    
    cap = cv2.VideoCapture(0)
    time.sleep(0.5)
    
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print("✓ SUCCESS: Camera re-opened successfully")
        else:
            print("✗ FAIL: Camera opened but cannot read")
        cap.release()
    else:
        print("✗ FAIL: Cannot re-open camera")
        print("\n  THIS IS YOUR PROBLEM!")
        print("  Your camera needs more time to release.")
    
    # Test 3: Multiple open/close cycles
    print("\n[TEST 3] Testing 5 open/close cycles...")
    success_count = 0
    
    for i in range(5):
        time.sleep(0.5)
        cap = cv2.VideoCapture(0)
        time.sleep(0.3)
        
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                success_count += 1
                print(f"  Cycle {i+1}: ✓ OK")
            else:
                print(f"  Cycle {i+1}: ✗ Read failed")
        else:
            print(f"  Cycle {i+1}: ✗ Open failed")
        
        cap.release()
        time.sleep(0.5)
    
    print(f"\n  Result: {success_count}/5 cycles successful")
    
    # Test 4: DirectShow (Windows)
    print("\n[TEST 4] Testing DirectShow backend (Windows)...")
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    time.sleep(0.5)
    
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print("✓ SUCCESS: DirectShow works")
        else:
            print("✗ DirectShow opened but read failed")
        cap.release()
    else:
        print("- DirectShow not available (normal on Mac/Linux)")
    
    # Test 5: Check available backends
    print("\n[TEST 5] Checking camera properties...")
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        fps = cap.get(cv2.CAP_PROP_FPS)
        print(f"  Resolution: {int(w)}x{int(h)}")
        print(f"  FPS: {fps}")
        cap.release()
    
    print("\n" + "=" * 50)
    print("DIAGNOSIS COMPLETE")
    print("=" * 50)
    
    if success_count < 5:
        print("\n⚠ YOUR CAMERA HAS RELEASE ISSUES")
        print("\nSOLUTIONS TO TRY:")
        print("1. Close ALL other apps using camera")
        print("2. Update camera drivers")
        print("3. Try: Settings > Privacy > Camera > Allow apps")
        print("4. Restart your laptop")
        print("5. Use longer delay (we'll fix in code)")
    else:
        print("\n✓ Camera works fine! Issue might be in UI code.")

if __name__ == "__main__":
    test_camera()