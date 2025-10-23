#!/usr/bin/env python3
"""
Test script for the EyeOnlyTracker module.
Runs a quick test to verify the tracker and calibration work correctly.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'vision'))

from camera_capture import CameraCapture


def main():
    print("=== Eye Tracker Test ===")
    print("This will test the pupil-only tracker and calibration system.\n")

    capture = CameraCapture(source="obs")

    try:
        print("Opening camera...")
        capture.open_capture()

        print("\nCalibration will start in 3 seconds.")
        print("Follow the on-screen instructions and look at each target.")
        import time
        time.sleep(3)

        if capture.calibrate_pupil_only():
            print("\n✅ Calibration successful!")
            print("\nStarting tracking loop...")
            print("Press 'q' to quit, 'r' to reset, 'c' to recalibrate")
            capture.run_loop()
        else:
            print("\n❌ Calibration failed")

    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    print("\n=== Test Complete ===")


if __name__ == "__main__":
    main()
