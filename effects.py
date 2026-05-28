import cv2
import numpy as np


FONT        = cv2.FONT_HERSHEY_SIMPLEX
COL_WHITE   = (255, 255, 255)
COL_GREEN   = (80,  200, 80)
COL_RED     = (60,  60,  220)
COL_YELLOW  = (0,   220, 220)
COL_CYAN    = (220, 220, 0)
COL_ORANGE  = (0,   165, 255)
COL_DARK_BG = (20,  20,  20)


def _put_text(frame, text, pos, scale=0.55, color=COL_WHITE, thickness=1):
    x, y = pos
    cv2.putText(frame, text, (x + 1, y + 1), FONT, scale, (0, 0, 0), thickness + 1, cv2.LINE_AA)
    cv2.putText(frame, text, (x, y),         FONT, scale, color,      thickness,     cv2.LINE_AA)


def _put_text_centered(frame, text, cy, scale=0.6, color=COL_WHITE, thickness=1):
    (tw, _), _ = cv2.getTextSize(text, FONT, scale, thickness)
    x = (frame.shape[1] - tw) // 2
    _put_text(frame, text, (x, cy), scale=scale, color=color, thickness=thickness)


def _translucent_rect(frame, x1, y1, x2, y2, color=COL_DARK_BG, alpha=0.55):
    overlay = frame.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)


def _dark_overlay(frame, alpha=0.65):
    cv2.addWeighted(np.zeros_like(frame), alpha, frame, 1 - alpha, 0, frame)


def _animation_tick(steps, hz=4.0):
    freq = cv2.getTickFrequency()
    return int(cv2.getTickCount() // (freq / hz)) % steps


def draw_setup_screen_calibration(frame):
    h, w = frame.shape[:2]

    _translucent_rect(frame, 0, 0, w, 90, alpha=0.72)
    _put_text_centered(frame, "CLOAK CALIBRATION",
                       cy=28, scale=0.80, color=COL_ORANGE, thickness=2)
    _put_text_centered(frame, "Hold the colored cloak INSIDE the sampling rectangle",
                       cy=54, scale=0.52, color=COL_WHITE)
    _put_text_centered(frame, "Press  [C]  when the cloak fills the box",
                       cy=76, scale=0.50, color=COL_CYAN)

    _translucent_rect(frame, 0, h - 32, w, h, alpha=0.65)
    _put_text_centered(frame, "[R] Reset   [Q] Quit", cy=h - 12, scale=0.40, color=COL_WHITE)


def draw_calibration_overlay(frame, rect, waiting_for_confirm=True):
    h, w = frame.shape[:2]
    x1, y1, x2, y2 = rect

    tick       = _animation_tick(4, hz=4.0)
    bright     = [255, 200, 160, 200][tick]
    border_col = (0, bright, bright)

    cv2.rectangle(frame, (x1 - 3, y1 - 3), (x2 + 3, y2 + 3),
                  (0, bright // 3, bright // 3), 2)
    cv2.rectangle(frame, (x1, y1), (x2, y2), border_col, 2)

    corner_len = 12
    for cx, cy, dx, dy in [(x1, y1, 1, 1), (x2, y1, -1, 1), (x1, y2, 1, -1), (x2, y2, -1, -1)]:
        cv2.line(frame, (cx, cy), (cx + dx * corner_len, cy), border_col, 3)
        cv2.line(frame, (cx, cy), (cx, cy + dy * corner_len), border_col, 3)

    if waiting_for_confirm:
        banner_h = 60
        _translucent_rect(frame, 0, h - banner_h, w, h)
        _put_text_centered(frame, "RECALIBRATION — place cloak in box",
                           cy=h - banner_h + 20, scale=0.55, color=COL_ORANGE)
        _put_text_centered(frame, "Press [C] to capture  |  [R] to cancel",
                           cy=h - banner_h + 44, scale=0.46, color=COL_CYAN)


def draw_setup_screen_bg_prep(frame, mean_hsv):
    h, w = frame.shape[:2]
    _dark_overlay(frame, alpha=0.55)

    card_w = min(560, w - 40)
    cx, cy = w // 2, h // 2
    x1, y1 = cx - card_w // 2, cy - 115
    x2, y2 = x1 + card_w, cy + 115
    _translucent_rect(frame, x1, y1, x2, y2, color=(10, 40, 10), alpha=0.80)
    cv2.rectangle(frame, (x1, y1), (x2, y2), COL_GREEN, 2)

    line_y = y1 + 38
    _put_text_centered(frame, "CLOAK COLOR LOCKED  \u2713",
                       cy=line_y, scale=0.80, color=COL_GREEN, thickness=2)

    if mean_hsv is not None:
        h_val, s_val, v_val = mean_hsv
        _put_text_centered(frame, f"Target HSV: ({h_val:.0f}, {s_val:.0f}, {v_val:.0f})",
                           cy=line_y + 34, scale=0.50, color=COL_YELLOW)
    else:
        line_y -= 17

    _put_text_centered(frame, "Put the cloak DOWN and step",         cy=line_y + 72,  scale=0.58)
    _put_text_centered(frame, "COMPLETELY OUT OF FRAME",              cy=line_y + 100, scale=0.65, color=COL_ORANGE, thickness=2)
    _put_text_centered(frame, "Background capture begins shortly...", cy=line_y + 138, scale=0.46, color=COL_CYAN)


def draw_setup_screen_countdown(frame, remaining):
    h, w = frame.shape[:2]
    _dark_overlay(frame, alpha=0.50)

    digit = str(max(1, int(remaining) + 1))

    _translucent_rect(frame, 0, 0, w, 80, alpha=0.70)
    _put_text_centered(frame, "Stay out of frame — capturing background",
                       cy=30, scale=0.60)
    _put_text_centered(frame, "Clean empty scene needed for the illusion to work",
                       cy=58, scale=0.44, color=COL_CYAN)

    digit_scale = 5.0
    (dw, dh), _ = cv2.getTextSize(digit, FONT, digit_scale, 8)
    dx = (w - dw) // 2
    dy = h // 2 + dh // 2

    col = COL_GREEN if remaining > 2.0 else COL_YELLOW if remaining > 1.0 else COL_ORANGE
    cv2.putText(frame, digit, (dx + 4, dy + 4), FONT, digit_scale, (0, 0, 0), 14, cv2.LINE_AA)
    cv2.putText(frame, digit, (dx, dy),          FONT, digit_scale, col,       8,  cv2.LINE_AA)

    bar_y1 = h - 20
    bar_y2 = h - 8
    fill_w = int(w * (1.0 - remaining / 3.0))
    cv2.rectangle(frame, (0, bar_y1), (w,      bar_y2), (40, 40, 40), -1)
    cv2.rectangle(frame, (0, bar_y1), (fill_w, bar_y2), col,          -1)


def draw_bg_locked_screen(frame, progress):
    alpha = max(0.0, 1.0 - progress * 1.2)
    if alpha < 0.02:
        return

    h, w   = frame.shape[:2]
    cx, cy = w // 2, h // 2
    card_w = min(500, w - 40)
    x1, y1 = cx - card_w // 2, cy - 105
    x2, y2 = x1 + card_w, cy + 105

    overlay = frame.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), (10, 10, 10), -1)
    cv2.addWeighted(overlay, 0.78 * alpha, frame, 1 - 0.78 * alpha, 0, frame)
    cv2.rectangle(frame, (x1, y1), (x2, y2), tuple(int(c * alpha) for c in COL_GREEN), 2)

    def faded(col):
        return tuple(int(c * alpha) for c in col)

    _put_text_centered(frame, "BACKGROUND LOCKED  \u2713",             cy=cy - 60, scale=0.80, color=faded(COL_GREEN), thickness=2)
    _put_text_centered(frame, "Return to frame and pick up your cloak", cy=cy - 16, scale=0.56, color=faded(COL_WHITE))
    _put_text_centered(frame, "INVISIBILITY READY",                    cy=cy + 28, scale=0.90, color=faded(COL_CYAN),  thickness=2)
    _put_text_centered(frame, "The cloak will now appear transparent",  cy=cy + 66, scale=0.46, color=faded(COL_WHITE))


def draw_hud(frame, bg_ready, calibrated, mean_hsv, fps, effect_active):
    px1, py1, px2, py2 = 10, 10, 320, 195
    _translucent_rect(frame, px1, py1, px2, py2)

    title_col = COL_CYAN if effect_active else COL_ORANGE
    _put_text(frame, "ADAPTIVE INVISIBILITY CLOAK", (px1 + 8, py1 + 22), scale=0.52, color=title_col)
    cv2.line(frame, (px1 + 8, py1 + 28), (px2 - 8, py1 + 28), COL_WHITE, 1)

    bg_text = "READY"      if bg_ready   else "NOT CAPTURED"
    bg_col  = COL_GREEN    if bg_ready   else COL_RED
    c_text  = "CALIBRATED" if calibrated else "NOT CALIBRATED"
    c_col   = COL_GREEN    if calibrated else COL_RED

    _put_text(frame, f"Background : {bg_text}", (px1 + 8, py1 + 50),  color=bg_col)
    _put_text(frame, f"Cloak      : {c_text}",  (px1 + 8, py1 + 72),  color=c_col)

    if mean_hsv is not None:
        h_val, s_val, v_val = mean_hsv
        _put_text(frame, f"Target HSV : ({h_val:.0f}, {s_val:.0f}, {v_val:.0f})",
                  (px1 + 8, py1 + 94), color=COL_YELLOW)
    else:
        _put_text(frame, "Target HSV : ---", (px1 + 8, py1 + 94))

    fps_col = COL_GREEN if fps >= 20 else COL_YELLOW if fps >= 10 else COL_RED
    _put_text(frame, f"FPS        : {fps:.1f}", (px1 + 8, py1 + 116), color=fps_col)
    cv2.line(frame, (px1 + 8, py1 + 126), (px2 - 8, py1 + 126), COL_WHITE, 1)

    for i, (key, desc) in enumerate([("[B]", "Recapture Background"),
                                      ("[C]", "Recalibrate Cloak"),
                                      ("[R]", "Full Reset"),
                                      ("[Q]", "Quit")]):
        y = py1 + 144 + i * 14
        _put_text(frame, key,  (px1 + 8,  y), scale=0.42, color=COL_CYAN)
        _put_text(frame, desc, (px1 + 42, y), scale=0.42)


def draw_capture_flash(frame, progress):
    alpha = max(0.0, 0.6 * (1.0 - progress))
    if alpha < 0.01:
        return
    cv2.addWeighted(np.full_like(frame, 255), alpha, frame, 1 - alpha, 0, frame)


def draw_notification(frame, message, progress, color=COL_GREEN):
    alpha = max(0.0, 1.0 - progress)
    if alpha < 0.01:
        return

    h, w = frame.shape[:2]
    scale, thickness = 0.65, 1
    (tw, th), _ = cv2.getTextSize(message, FONT, scale, thickness)
    tx = (w - tw) // 2
    ty = h - 55

    pad = 14
    _translucent_rect(frame, tx - pad, ty - th - pad, tx + tw + pad, ty + pad,
                      color=(0, 0, 0), alpha=0.6 * alpha)
    cv2.rectangle(frame,
                  (tx - pad, ty - th - pad), (tx + tw + pad, ty + pad),
                  tuple(int(c * alpha) for c in color), 1)

    faded_col = tuple(int(c * alpha) for c in color)
    cv2.putText(frame, message, (tx + 1, ty + 1), FONT, scale, (0, 0, 0), thickness + 1, cv2.LINE_AA)
    cv2.putText(frame, message, (tx, ty),          FONT, scale, faded_col, thickness,     cv2.LINE_AA)


def draw_effect_indicator(frame, active):
    h, w = frame.shape[:2]
    cx, cy = w - 30, 30

    if active:
        tick   = _animation_tick(2, hz=2.0)
        radius = 8 if tick == 0 else 6
        color  = COL_GREEN
        label  = "ACTIVE"
    else:
        radius = 6
        color  = (80, 80, 80)
        label  = "STANDBY"

    cv2.circle(frame, (cx, cy), radius + 3, (0, 0, 0), -1)
    cv2.circle(frame, (cx, cy), radius, color, -1)
    _put_text(frame, label, (cx - 45, cy + 5), scale=0.38, color=color)
