# src/vision/eye_only_tracker.py
from collections import deque
import cv2
import numpy as np


class EyeOnlyTracker:
    def __init__(self,
                 use_clahe=True,
                 clahe_clip=2.0,
                 clahe_tile=(8, 8),
                 morph_open_iter=1,
                 morph_close_iter=1,
                 thresh_block=15,   # must be odd
                 thresh_c=7,
                 min_pupil_area=80,
                 smooth_window=5,
                 roi_half_size=90):
        self.use_clahe = use_clahe
        self.clahe_clip = clahe_clip
        self.clahe_tile = clahe_tile
        self.morph_open_iter = morph_open_iter
        self.morph_close_iter = morph_close_iter
        self.thresh_block = max(3, thresh_block | 1)
        self.thresh_c = int(thresh_c)
        self.min_pupil_area = int(min_pupil_area)
        self.smooth_buf = deque(maxlen=max(1, int(smooth_window)))
        self.roi_half = int(roi_half_size)
        self._last_center = None

    def _pre(self, gray):
        gray = cv2.GaussianBlur(gray, (7, 7), 0)
        if self.use_clahe:
            clahe = cv2.createCLAHE(clipLimit=self.clahe_clip, tileGridSize=self.clahe_tile)
            gray = clahe.apply(gray)
        return gray

    def _th(self, gray):
        th = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_MEAN_C,
            cv2.THRESH_BINARY_INV,
            self.thresh_block, self.thresh_c
        )
        if self.morph_open_iter > 0:
            th = cv2.morphologyEx(th, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8), iterations=self.morph_open_iter)
        if self.morph_close_iter > 0:
            th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8), iterations=self.morph_close_iter)
        return th

    def _find_pupil(self, th, roi=None):
        if roi is not None:
            x1, y1, x2, y2 = roi
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(th.shape[1] - 1, x2), min(th.shape[0] - 1, y2)
            sub = th[y1:y2, x1:x2]
            contours, _ = cv2.findContours(sub, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            base_x, base_y = x1, y1
        else:
            contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            base_x = base_y = 0

        if not contours:
            return None
        c = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(c)
        if area < self.min_pupil_area:
            return None
        M = cv2.moments(c)
        if M["m00"] == 0:
            return None
        cx = int(M["m10"] / M["m00"]) + base_x
        cy = int(M["m01"] / M["m00"]) + base_y
        return (cx, cy, area)

    def reset(self):
        self.smooth_buf.clear()
        self._last_center = None

    def step(self, frame_bgr):
        """Return (center_xy, confidence [0..1], debug_dict). center_xy is (x,y) or None."""
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        gray = self._pre(gray)
        th = self._th(gray)

        roi = None
        if self._last_center is not None and self.roi_half > 0:
            cx, cy = self._last_center
            roi = (cx - self.roi_half, cy - self.roi_half, cx + self.roi_half, cy + self.roi_half)

        found = self._find_pupil(th, roi=roi) or self._find_pupil(th, roi=None)
        center = None
        conf = 0.0

        if found:
            cx, cy, area = found
            self.smooth_buf.append((cx, cy))
            sx = int(sum(p[0] for p in self.smooth_buf) / len(self.smooth_buf))
            sy = int(sum(p[1] for p in self.smooth_buf) / len(self.smooth_buf))
            center = (sx, sy)
            self._last_center = center
            # crude confidence: normalized area & presence
            conf = min(1.0, max(0.1, area / max(self.min_pupil_area * 8, 1)))
        else:
            self._last_center = None
            self.smooth_buf.clear()

        dbg = {"th": th, "roi": roi}
        return center, conf, dbg
