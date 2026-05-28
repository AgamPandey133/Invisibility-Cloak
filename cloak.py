import cv2
import numpy as np


_OPEN_K   = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
_CLOSE_K  = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
_DILATE_K = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))


def build_raw_mask(frame_hsv, ranges):
    mask = np.zeros(frame_hsv.shape[:2], dtype=np.uint8)
    for lo, hi in ranges:
        mask |= cv2.inRange(frame_hsv, lo, hi)
    return mask


def clean_mask(raw_mask):
    m = cv2.morphologyEx(raw_mask, cv2.MORPH_OPEN,  _OPEN_K,  iterations=2)
    m = cv2.morphologyEx(m,        cv2.MORPH_CLOSE, _CLOSE_K, iterations=3)
    m = cv2.dilate(m, _DILATE_K, iterations=1)
    return m


def apply_cloak_effect(current_frame, background, mask):
    inv_mask    = cv2.bitwise_not(mask)
    foreground  = cv2.bitwise_and(current_frame, current_frame, mask=inv_mask)
    replacement = cv2.bitwise_and(background,    background,    mask=mask)
    return cv2.add(foreground, replacement)


def process_frame(current_frame, background, calibration):
    if background is None or calibration is None:
        return current_frame.copy(), None

    if background.shape != current_frame.shape:
        bg = cv2.resize(background, (current_frame.shape[1], current_frame.shape[0]))
    else:
        bg = background

    frame_hsv = cv2.cvtColor(current_frame, cv2.COLOR_BGR2HSV)
    raw_mask  = build_raw_mask(frame_hsv, calibration['ranges'])
    clean     = clean_mask(raw_mask)
    result    = apply_cloak_effect(current_frame, bg, clean)

    return result, clean
