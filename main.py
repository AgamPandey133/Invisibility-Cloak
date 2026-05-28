import sys
import time
import argparse
from enum import Enum, auto

import cv2
import numpy as np

import calibration as cal
import cloak
import effects


def parse_args():
    parser = argparse.ArgumentParser(description="Adaptive Real-Time Invisibility Cloak — OpenCV")
    parser.add_argument("--camera",  type=int, default=0,    help="Camera index (default: 0)")
    parser.add_argument("--width",   type=int, default=1280, help="Capture width  (default: 1280)")
    parser.add_argument("--height",  type=int, default=720,  help="Capture height (default: 720)")
    return parser.parse_args()


class Stage(Enum):
    CALIBRATION  = auto()
    BG_PREP      = auto()
    BG_COUNTDOWN = auto()
    READY        = auto()


_BG_LOCKED_DISPLAY_SECS = 3.0
_COUNTDOWN_SECS         = 3
_BG_PREP_DISPLAY_SECS   = 2.5


class AppState:

    def __init__(self):
        self.stage: Stage = Stage.CALIBRATION

        self.background  = None
        self.calibration = None

        self.prep_start      = 0.0
        self.countdown_start = 0.0
        self._burst_buffer   = []

        self.recal_mode = False

        self.flash_start    = 0.0
        self.flash_duration = 0.5
        self.notif_message  = ""
        self.notif_start    = 0.0
        self.notif_duration = 2.0

        self.bg_locked_start   = 0.0
        self.showing_bg_locked = False

    @property
    def bg_ready(self):
        return self.background is not None

    @property
    def calibrated(self):
        return self.calibration is not None

    @property
    def effect_active(self):
        return self.stage == Stage.READY and self.bg_ready and self.calibrated

    def show_notification(self, message, duration=2.0):
        self.notif_message  = message
        self.notif_start    = time.monotonic()
        self.notif_duration = duration

    def confirm_calibration(self, calib_result):
        self.calibration = calib_result
        self.recal_mode  = False
        self.stage       = Stage.BG_PREP
        self.prep_start  = time.monotonic()

    def begin_countdown(self):
        self.stage           = Stage.BG_COUNTDOWN
        self.countdown_start = time.monotonic()
        self._burst_buffer   = []

    def add_burst_frame(self, frame):
        self._burst_buffer.append(frame.astype(np.float32))

    def finalize_background(self):
        if not self._burst_buffer:
            return
        stack = np.stack(self._burst_buffer, axis=0)
        self.background = np.median(stack, axis=0).astype(np.uint8)

        self.flash_start       = time.monotonic()
        self.showing_bg_locked = True
        self.bg_locked_start   = time.monotonic()
        self.stage             = Stage.READY

    def manual_capture_background(self, frame):
        self.background  = frame.copy()
        self.flash_start = time.monotonic()
        self.show_notification("Background Re-captured!", duration=1.5)

    def apply_recalibration(self, calib_result):
        self.calibration = calib_result
        self.recal_mode  = False
        h, s, v = calib_result['mean_hsv']
        self.show_notification(f"Re-calibrated! HSV({h:.0f}, {s:.0f}, {v:.0f})")

    def reset(self):
        self.calibration       = None
        self.background        = None
        self.recal_mode        = False
        self.showing_bg_locked = False
        self._burst_buffer     = []
        self.stage             = Stage.CALIBRATION
        self.show_notification("Reset — hold cloak and press C", duration=2.5)


def open_camera(index, width, height):
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        raise RuntimeError(
            f"Cannot open camera {index}. "
            "Check the webcam is connected and not used by something else."
        )

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"[Camera {index}] opened at {actual_w}×{actual_h}")
    return cap


class FPSMeter:

    def __init__(self, window=30):
        self._times  = []
        self._window = window

    def tick(self):
        now = time.monotonic()
        self._times.append(now)
        if len(self._times) > self._window:
            self._times.pop(0)
        if len(self._times) < 2:
            return 0.0
        elapsed = self._times[-1] - self._times[0]
        return (len(self._times) - 1) / elapsed if elapsed > 0 else 0.0


ESC = 27


def handle_key(key, state, frame, rect):
    if key == ord('q') or key == ord('Q') or key == ESC:
        return True

    if key == ord('r') or key == ord('R'):
        state.reset()
        return False

    if state.stage == Stage.CALIBRATION:
        if key == ord('c') or key == ord('C'):
            result = cal.calibrate(frame, rect)
            if result is None:
                state.show_notification("Not enough color pixels — fill the box!", duration=2.5)
            else:
                state.confirm_calibration(result)
        return False

    if state.stage in (Stage.BG_PREP, Stage.BG_COUNTDOWN):
        return False

    if state.stage == Stage.READY:
        if key == ord('b') or key == ord('B'):
            state.show_notification("Step OUT of frame, then B captures background", duration=3.0)
            state.manual_capture_background(frame)
            return False

        if key == ord('c') or key == ord('C'):
            if not state.recal_mode:
                state.recal_mode = True
                state.show_notification("Place cloak in box, press C again", duration=3.0)
            else:
                result = cal.calibrate(frame, rect)
                if result is None:
                    state.show_notification("Calibration failed — fill the box!", duration=2.5)
                    state.recal_mode = False
                else:
                    state.apply_recalibration(result)
            return False

    return False


def main():
    args  = parse_args()
    state = AppState()
    fps_m = FPSMeter()

    try:
        cap = open_camera(args.camera, args.width, args.height)
    except RuntimeError as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)

    print("Warming up camera … ", end="", flush=True)
    for _ in range(30):
        cap.read()
    print("done.")
    print("Controls: [C] Calibrate  [B] Recapture BG  [R] Reset  [Q/Esc] Quit")

    window_name = "Adaptive Invisibility Cloak"
    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, actual_w, actual_h)

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                print("[WARNING] Failed to read frame — retrying …")
                time.sleep(0.05)
                continue

            h, w = frame.shape[:2]
            rect = cal.get_sampling_rect(h, w)
            fps  = fps_m.tick()
            now  = time.monotonic()

            if state.stage == Stage.BG_PREP:
                if now - state.prep_start >= _BG_PREP_DISPLAY_SECS:
                    state.begin_countdown()

            elif state.stage == Stage.BG_COUNTDOWN:
                elapsed   = now - state.countdown_start
                remaining = _COUNTDOWN_SECS - elapsed
                if remaining <= 1.0:
                    state.add_burst_frame(frame)
                if remaining <= 0.0:
                    state.finalize_background()

            if state.stage == Stage.CALIBRATION:
                output = frame.copy()
                effects.draw_calibration_overlay(output, rect)
                effects.draw_setup_screen_calibration(output)

            elif state.stage == Stage.BG_PREP:
                output   = frame.copy()
                mean_hsv = state.calibration['mean_hsv'] if state.calibrated else None
                effects.draw_setup_screen_bg_prep(output, mean_hsv)

            elif state.stage == Stage.BG_COUNTDOWN:
                output    = frame.copy()
                elapsed   = now - state.countdown_start
                remaining = max(0.0, _COUNTDOWN_SECS - elapsed)
                effects.draw_setup_screen_countdown(output, remaining)

            else:
                output, _ = cloak.process_frame(frame, state.background, state.calibration)

                if state.showing_bg_locked:
                    elapsed = now - state.bg_locked_start
                    if elapsed < _BG_LOCKED_DISPLAY_SECS:
                        effects.draw_bg_locked_screen(output, elapsed / _BG_LOCKED_DISPLAY_SECS)
                    else:
                        state.showing_bg_locked = False

                mean_hsv = state.calibration['mean_hsv'] if state.calibrated else None
                effects.draw_hud(output,
                                 bg_ready=state.bg_ready,
                                 calibrated=state.calibrated,
                                 mean_hsv=mean_hsv,
                                 fps=fps,
                                 effect_active=state.effect_active)

                effects.draw_effect_indicator(output, active=state.effect_active)

                if state.recal_mode:
                    effects.draw_calibration_overlay(output, rect)

                if now - state.flash_start < state.flash_duration:
                    progress = (now - state.flash_start) / state.flash_duration
                    effects.draw_capture_flash(output, progress)

            if state.notif_message:
                elapsed  = now - state.notif_start
                progress = elapsed / state.notif_duration
                if progress < 1.0:
                    effects.draw_notification(output, state.notif_message, progress)
                else:
                    state.notif_message = ""

            cv2.imshow(window_name, output)

            key = cv2.waitKey(1) & 0xFF
            if handle_key(key, state, frame, rect):
                break

    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user.")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("[INFO] Camera released. Bye!")


if __name__ == "__main__":
    main()
