# src/vision/camera_capture.py
import cv2
import numpy as np
import time
import os
import sys
from collections import deque
import json

from eye_only_tracker import EyeOnlyTracker
from gaze_map import GazeMapper


class CameraCapture:
    """
    Main capture loop integrating EyeOnlyTracker with OBS/camera input.
    Replaces face-based calibration with pupil-only calibration.
    """

    def __init__(self, source="obs", resize_max_h=720, horizontal_flip=True):
        self.source = source
        self.resize_max_h = resize_max_h
        self.horizontal_flip = horizontal_flip

        # Initialize tracker with defaults from rough3.py
        self.tracker = EyeOnlyTracker(
            use_clahe=True,
            clahe_clip=2.0,
            clahe_tile=(8, 8),
            morph_open_iter=1,
            morph_close_iter=1,
            thresh_block=15,
            thresh_c=7,
            min_pupil_area=80,
            smooth_window=5,
            roi_half_size=90
        )

        self.mapper = GazeMapper()
        self.cap = None
        self.calibrated = False

        # Statistics
        self.frames_processed = 0
        self.frames_detected = 0
        self.last_reset_time = time.time()

        # State
        self.pupil_xy = None
        self.gaze_xy = None
        self.confidence = 0.0

    def open_capture(self):
        """Open video capture from OBS or webcam."""
        print(f"Opening capture source: {self.source}")

        if self.source == "obs":
            # Try OBS Virtual Camera
            self.cap = self._try_open_obs()
            if self.cap is None:
                print("OBS not found, falling back to webcam...")
                self.cap = cv2.VideoCapture(0)
        else:
            self.cap = cv2.VideoCapture(0)

        if not self.cap.isOpened():
            raise RuntimeError("Cannot open camera")

        print("✅ Camera opened successfully")
        return True

    def _try_open_obs(self):
        """Try to open OBS Virtual Camera."""
        candidates = [
            ("video=OBS Virtual Camera", cv2.CAP_DSHOW),
            ("video=OBS-Camera", cv2.CAP_DSHOW),
            ("/dev/video2", cv2.CAP_V4L2),
        ]

        for device, backend in candidates:
            try:
                cap = cv2.VideoCapture(device, backend)
                time.sleep(0.2)
                if cap.isOpened():
                    print(f"✅ Opened OBS: {device}")
                    return cap
                cap.release()
            except Exception as e:
                print(f"Failed to open {device}: {e}")

        return None

    def process_frame(self, frame_bgr):
        """Process a single frame through the tracker."""
        # Apply preprocessing
        if self.horizontal_flip:
            frame_bgr = cv2.flip(frame_bgr, 1)

        if self.resize_max_h and frame_bgr.shape[0] > self.resize_max_h:
            scale = self.resize_max_h / frame_bgr.shape[0]
            frame_bgr = cv2.resize(frame_bgr,
                                   (int(frame_bgr.shape[1] * scale), self.resize_max_h))

        # Track pupil
        center, conf, dbg = self.tracker.step(frame_bgr)

        self.frames_processed += 1
        if center is not None:
            self.frames_detected += 1
            self.pupil_xy = center
            self.confidence = conf

            # Map to screen coordinates if calibrated
            if self.calibrated:
                self.gaze_xy = self.mapper.map(center)
        else:
            self.pupil_xy = None
            self.gaze_xy = None
            self.confidence = 0.0

        # Auto-reset if no detection for 1 second
        if center is None:
            if time.time() - self.last_reset_time > 1.0:
                self.tracker.reset()
                self.last_reset_time = time.time()
        else:
            self.last_reset_time = time.time()

        return frame_bgr, dbg

    def calibrate_pupil_only(self, screen_width=1920, screen_height=1080):
        """
        Pupil-only calibration: collect samples at 5 target points.
        No face/landmark detection required.
        """
        print("\n=== Starting Pupil-Only Calibration ===")
        print("Look at each target dot for 2 seconds.\n")

        # Define 5 calibration points
        cx, cy = screen_width // 2, screen_height // 2
        margin = 200

        targets = [
            ("Center", cx, cy),
            ("Left", margin, cy),
            ("Right", screen_width - margin, cy),
            ("Top", cx, margin),
            ("Bottom", cx, screen_height - margin),
        ]

        pupil_samples = []
        screen_samples = []

        for name, sx, sy in targets:
            print(f"Look at: {name} ({sx}, {sy})")
            samples = []

            # Show visual target (would be rendered in actual UI)
            start_time = time.time()
            while time.time() - start_time < 2.0:
                ret, frame = self.cap.read()
                if not ret:
                    continue

                frame, dbg = self.process_frame(frame)

                if self.pupil_xy is not None:
                    samples.append(self.pupil_xy)

                # Visualize calibration target
                vis = frame.copy()
                cv2.circle(vis, (int(sx * frame.shape[1] / screen_width),
                                 int(sy * frame.shape[0] / screen_height)),
                           20, (0, 255, 0), 2)
                cv2.putText(vis, f"{name} - {len(samples)} samples",
                           (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.imshow("Calibration", vis)
                cv2.waitKey(1)

            if len(samples) < 10:
                print(f"⚠️ Warning: Only {len(samples)} samples for {name}")

            # Average samples
            if samples:
                mean_px = int(np.mean([s[0] for s in samples]))
                mean_py = int(np.mean([s[1] for s in samples]))
                pupil_samples.append([mean_px, mean_py])
                screen_samples.append([sx, sy])
                print(f"  Collected: pupil=({mean_px}, {mean_py}) -> screen=({sx}, {sy})")
                print(f"  Variance: x={np.std([s[0] for s in samples]):.1f}, y={np.std([s[1] for s in samples]):.1f}")

        if len(pupil_samples) < 3:
            print("❌ Calibration failed: not enough samples")
            return False

        # Fit affine transformation
        pupil_pts = np.array(pupil_samples, dtype=np.float32)
        screen_pts = np.array(screen_samples, dtype=np.float32)

        self.mapper.fit(pupil_pts, screen_pts)
        self.calibrated = True

        print("\n✅ Calibration complete!")
        print(f"Transformation matrix:\n{self.mapper.A}")

        cv2.destroyWindow("Calibration")
        return True

    def get_detection_rate(self):
        """Return pupil detection rate."""
        if self.frames_processed == 0:
            return 0.0
        return self.frames_detected / self.frames_processed

    def run_loop(self, window_name="Eye Tracker", show_debug=True):
        """Main capture loop."""
        print("\n=== Starting Capture Loop ===")
        print("Press 'q' to quit, 'r' to reset tracker, 'c' to recalibrate")

        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Failed to read frame")
                break

            frame, dbg = self.process_frame(frame)

            # Visualize
            vis = frame.copy()

            if self.pupil_xy is not None:
                cv2.circle(vis, self.pupil_xy, 6, (0, 255, 0), -1)
                cv2.putText(vis, f"Pupil: {self.pupil_xy}", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            if self.gaze_xy is not None:
                cv2.putText(vis, f"Gaze: ({int(self.gaze_xy[0])}, {int(self.gaze_xy[1])})",
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

            # Stats
            rate = self.get_detection_rate() * 100
            cv2.putText(vis, f"Detection: {rate:.1f}% | Conf: {self.confidence:.2f}",
                       (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            # Show debug threshold if requested
            if show_debug and "th" in dbg:
                th_color = cv2.cvtColor(dbg["th"], cv2.COLOR_GRAY2BGR)
                h = min(vis.shape[0], 480)
                vis_rs = cv2.resize(vis, (int(vis.shape[1] * h / vis.shape[0]), h))
                th_rs = cv2.resize(th_color, (int(th_color.shape[1] * h / th_color.shape[0]), h))
                combined = np.hstack((vis_rs, th_rs))
                cv2.imshow(window_name, combined)
            else:
                cv2.imshow(window_name, vis)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                break
            elif key == ord('r'):
                self.tracker.reset()
                print("🔁 Tracker reset")
            elif key == ord('c'):
                self.calibrate_pupil_only()

        self.cap.release()
        cv2.destroyAllWindows()

        print(f"\n✅ Session complete. Detection rate: {self.get_detection_rate()*100:.1f}%")


def main():
    """Run standalone tracker with calibration."""
    capture = CameraCapture(source="obs")

    try:
        capture.open_capture()

        # Run calibration first
        print("\nStarting calibration in 3 seconds...")
        time.sleep(3)
        capture.calibrate_pupil_only()

        # Run main loop
        capture.run_loop()

    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
