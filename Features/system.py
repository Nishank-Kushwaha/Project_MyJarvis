import os
import re
import time
import logging
import datetime
import pyautogui
import pyperclip
import pyautogui
from PIL import ImageGrab

import config

logger = logging.getLogger(__name__)

# Word-to-number map used by both set_volume and spoken_percent parsing
_WORD_TO_NUM = {
    "zero": 0, "ten": 10, "twenty": 20, "thirty": 30,
    "forty": 40, "fifty": 50, "sixty": 60,
    "seventy": 70, "eighty": 80, "ninety": 90, "hundred": 100,
}


# ─────────────────────────────────────────────────────────────────────────────
#  Volume
# ─────────────────────────────────────────────────────────────────────────────

class VolumeController:
    """
    Controls Windows system volume via pycaw.

    pycaw is imported lazily inside each method so the rest of the app
    can still run on non-Windows machines (useful for testing / CI).
    """

    def _interface(self):
        """Return the Windows EndpointVolume interface."""
        from pycaw.pycaw import AudioUtilities
        devices = AudioUtilities.GetSpeakers()
        return devices.EndpointVolume

    def get_percent(self) -> int:
        """Return current volume as an integer 0–100."""
        return int(self._interface().GetMasterVolumeLevelScalar() * 100)

    def set_percent(self, percent: int) -> int:
        """
        Set volume to the given percentage (clamped 0–100).
        Returns the actual value that was set.
        """
        percent = max(0, min(100, percent))
        self._interface().SetMasterVolumeLevelScalar(percent / 100, None)
        logger.info("Volume set to %d%%.", percent)
        return percent

    def change_by(self, delta: float) -> int:
        """
        Increase or decrease volume by delta (e.g. +0.1 or -0.1).
        Returns the new volume percentage.
        """
        vol   = self._interface()
        current = vol.GetMasterVolumeLevelScalar()
        new_val = max(0.0, min(1.0, current + delta))
        vol.SetMasterVolumeLevelScalar(new_val, None)
        result = int(new_val * 100)
        logger.info("Volume changed by %+.0f%% → %d%%.", delta * 100, result)
        return result

    def is_muted(self) -> bool:
        return bool(self._interface().GetMute())

    def mute(self) -> None:
        self._interface().SetMute(1, None)
        logger.info("Volume muted.")

    def unmute(self) -> None:
        self._interface().SetMute(0, None)
        logger.info("Volume unmuted.")

    @staticmethod
    def parse_percent(text: str):
        """
        Extract a volume percentage from a spoken string.
        Handles digits ('50', '50 percent') and words ('fifty').
        Returns an int or None.
        """
        nums = re.findall(r"\d+", text)
        if nums:
            return int(nums[0])
        for word, val in _WORD_TO_NUM.items():
            if word in text.lower().split():
                return val
        return None


# ─────────────────────────────────────────────────────────────────────────────
#  Screenshots
# ─────────────────────────────────────────────────────────────────────────────

class ScreenshotManager:
    """
    Captures full-screen or region screenshots and saves them with
    timestamped filenames inside config.SCREENSHOT_DIR.
    """

    def _make_filename(self, prefix: str) -> str:
        """Build a full output path like screenshots/screenshot_2025-01-01_12-00-00.png"""
        os.makedirs(config.SCREENSHOT_DIR, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return os.path.join(config.SCREENSHOT_DIR, f"{prefix}_{ts}.png")

    def take_fullscreen(self, delay: int = 3) -> str:
        """
        Capture the entire screen after an optional delay.

        Args:
            delay: Seconds to wait before capturing (gives time to
                   minimise the Jarvis window).
        Returns:
            Path to the saved screenshot file.
        """
        if delay:
            time.sleep(delay)

        filename = self._make_filename("screenshot")
        pyautogui.screenshot().save(filename)
        logger.info("Full-screen screenshot saved: %s", filename)
        return filename

    def take_region(self, region: tuple) -> str:
        """
        Capture a specific screen region.

        Args:
            region: (x1, y1, x2, y2) bounding box from the snip tool.
        Returns:
            Path to the saved screenshot file.
        """
        x1, y1, x2, y2 = region
        filename = self._make_filename("region")
        ImageGrab.grab(bbox=(x1, y1, x2, y2)).save(filename)
        logger.info("Region screenshot saved: %s", filename)
        return filename


# ─────────────────────────────────────────────────────────────────────────────
#  Clipboard
# ─────────────────────────────────────────────────────────────────────────────

class ClipboardManager:
    """
    Thin wrapper around pyperclip + pyautogui for clipboard operations.
    Isolated here so commands.py stays free of direct library calls.
    """

    def read(self) -> str:
        """Return current clipboard text, or '' if empty."""
        return pyperclip.paste() or ""

    def write(self, text: str) -> None:
        """Copy text to clipboard."""
        pyperclip.copy(text)
        logger.info("Copied to clipboard: '%s...'", text[:40])

    def clear(self) -> None:
        """Empty the clipboard."""
        pyperclip.copy("")
        logger.info("Clipboard cleared.")

    def paste(self) -> bool:
        """
        Trigger a Ctrl+V paste at the current cursor position.
        Returns True if clipboard had content, False if it was empty.
        """
        text = self.read()
        if text:
            pyautogui.hotkey("ctrl", "v")
            logger.info("Pasted clipboard content.")
            return True
        return False