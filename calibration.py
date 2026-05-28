import cv2
import numpy as np


RECT_FRACTION  = 0.15
MIN_RECT_PX    = 60
MIN_SATURATION = 40
MIN_VALUE      = 40

H_TOLERANCE_FLOOR = 12
H_TOLERANCE_CAP   = 30
H_TOLERANCE_MULT  = 2.0

S_TOLERANCE_DOWN = 80
S_TOLERANCE_UP   = 60
S_MIN_FLOOR      = 30

V_TOLERANCE_DOWN = 80
V_TOLERANCE_UP   = 60
V_MIN_FLOOR      = 30


def get_sampling_rect(frame_h, frame_w):
    side = max(MIN_RECT_PX, int(min(frame_h, frame_w) * RECT_FRACTION))
    cx, cy = frame_w // 2, frame_h // 2
    x1 = cx - side // 2
    y1 = cy - side // 2
    return x1, y1, x1 + side, y1 + side


def sample_color_from_rect(frame_bgr, rect):
    x1, y1, x2, y2 = rect
    roi_bgr = frame_bgr[y1:y2, x1:x2]

    if roi_bgr.size == 0:
        return None

    roi_hsv = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2HSV)
    pixels  = roi_hsv.reshape(-1, 3).astype(np.float32)

    valid_mask = (pixels[:, 1] >= MIN_SATURATION) & (pixels[:, 2] >= MIN_VALUE)
    valid = pixels[valid_mask]

    if len(valid) < 10:
        return None

    h = valid[:, 0]
    s = valid[:, 1]
    v = valid[:, 2]

    theta      = h * (2.0 * np.pi / 180.0)
    mean_sin   = np.mean(np.sin(theta))
    mean_cos   = np.mean(np.cos(theta))
    mean_h_rad = np.arctan2(mean_sin, mean_cos)
    if mean_h_rad < 0:
        mean_h_rad += 2.0 * np.pi
    mean_h = float(mean_h_rad * 180.0 / (2.0 * np.pi))

    R     = min(np.sqrt(mean_sin**2 + mean_cos**2), 1.0 - 1e-9)
    std_h = float(np.sqrt(-2.0 * np.log(R)) * 180.0 / (2.0 * np.pi))

    return {
        'mean_h':         mean_h,
        'mean_s':         float(np.mean(s)),
        'mean_v':         float(np.mean(v)),
        'std_h':          std_h,
        'pixel_count':    int(len(valid)),
        'raw_hsv_pixels': valid,
    }


def generate_hsv_range(stats):
    mean_h = stats['mean_h']
    mean_s = stats['mean_s']
    mean_v = stats['mean_v']
    std_h  = stats['std_h']

    h_tol = float(np.clip(std_h * H_TOLERANCE_MULT, H_TOLERANCE_FLOOR, H_TOLERANCE_CAP))
    lo_h  = mean_h - h_tol
    hi_h  = mean_h + h_tol

    lo_s = max(S_MIN_FLOOR, mean_s - S_TOLERANCE_DOWN)
    hi_s = min(255, mean_s + S_TOLERANCE_UP)
    lo_v = max(V_MIN_FLOOR, mean_v - V_TOLERANCE_DOWN)
    hi_v = min(255, mean_v + V_TOLERANCE_UP)

    if lo_h < 0 or hi_h > 179:
        if lo_h < 0:
            r1_lo = np.array([lo_h + 180, lo_s, lo_v], dtype=np.uint8)
            r1_hi = np.array([179,        hi_s, hi_v], dtype=np.uint8)
            r2_lo = np.array([0,           lo_s, lo_v], dtype=np.uint8)
            r2_hi = np.array([hi_h,        hi_s, hi_v], dtype=np.uint8)
        else:
            r1_lo = np.array([lo_h,       lo_s, lo_v], dtype=np.uint8)
            r1_hi = np.array([179,        hi_s, hi_v], dtype=np.uint8)
            r2_lo = np.array([0,          lo_s, lo_v], dtype=np.uint8)
            r2_hi = np.array([hi_h - 180, hi_s, hi_v], dtype=np.uint8)
        return [(r1_lo, r1_hi), (r2_lo, r2_hi)]

    lo = np.array([lo_h, lo_s, lo_v], dtype=np.uint8)
    hi = np.array([hi_h, hi_s, hi_v], dtype=np.uint8)
    return [(lo, hi)]


def calibrate(frame_bgr, rect):
    stats = sample_color_from_rect(frame_bgr, rect)
    if stats is None:
        return None

    return {
        'ranges':      generate_hsv_range(stats),
        'mean_hsv':    (stats['mean_h'], stats['mean_s'], stats['mean_v']),
        'pixel_count': stats['pixel_count'],
    }
