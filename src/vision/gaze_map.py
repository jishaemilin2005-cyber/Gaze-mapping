# src/vision/gaze_map.py
import numpy as np


class GazeMapper:
    def __init__(self):
        self.A = None  # 3x3 affine

    def fit(self, pupil_pts, screen_pts):
        """
        Fit an affine transformation from pupil space to screen space.
        pupil_pts: Nx2 array of pupil coordinates
        screen_pts: Nx2 array of corresponding screen coordinates
        Returns: 3x3 affine transformation matrix
        """
        P = np.hstack([pupil_pts, np.ones((len(pupil_pts), 1))])  # Nx3
        S = screen_pts  # Nx2
        # Solve P * W = S  => W = (P^+)*S, then make A as 3x3
        W, _, _, _ = np.linalg.lstsq(P, S, rcond=None)  # 3x2
        self.A = np.vstack([W.T, [0, 0, 1]])              # 3x3
        return self.A

    def map(self, center_xy):
        """
        Map a pupil coordinate to screen space.
        center_xy: (x, y) tuple or None
        Returns: (sx, sy) tuple or None
        """
        if self.A is None or center_xy is None:
            return None
        x, y = center_xy
        v = np.array([x, y, 1.0])
        result = self.A @ v
        sx, sy = result[0], result[1]
        return (float(sx), float(sy))
