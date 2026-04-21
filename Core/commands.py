import re
import os
import time
import datetime
import logging
import webbrowser
import requests
import wikipedia
import pyjokes
import pywhatkit
import pyperclip
import pyautogui
from PIL import ImageGrab
from google import genai

from Features.reminders import set_reminder, list_reminders, cancel_reminder
from GUI.snip import take_snip
import config

logger = logging.getLogger(__name__)


class CommandRouter:
    """
    Routes a spoken command string to the correct handler method.

    How to add a new command:
        1. Write a handler method:   def _handle_myfeature(self, command): ...
        2. Register its triggers in _build_dispatch_table() below — done.
           No other file needs to change.

    The dispatch table is a list of (triggers, handler) pairs evaluated
    in order. The first matching trigger wins, so more-specific phrases
    (e.g. "take screenshot region") must appear BEFORE broader ones
    (e.g. "take screenshot").
    """

    def __init__(self, assistant):
        """
        Args:
            assistant: JarvisAssistant instance.
                       Gives access to assistant.speak(), assistant.speech,
                       assistant.gui, and assistant.stop().
        """
        self.assistant = assistant
        self.speak     = assistant.speak
        self.listen    = assistant.speech.listen_once   # canonical STT helper
        self.gui       = assistant.gui

        self._gemini   = genai.Client(api_key=config.GEMINI_API_KEY)
        self._dispatch = self._build_dispatch_table()

    # ------------------------------------------------------------------ #
    #  Public                                                              #
    # ------------------------------------------------------------------ #

    def route(self, command: str) -> None:
        """
        Match command against the dispatch table and call the handler.
        Falls back to Gemini AI if nothing matches.
        """
        command = command.lower().strip()
        logger.debug("Routing command: '%s'", command)

        for triggers, handler in self._dispatch:
            if any(trigger in command for trigger in triggers):
                try:
                    handler(command)
                except Exception as e:
                    logger.exception("Handler %s raised: %s", handler.__name__, e)
                    self.speak("Something went wrong. Please try again.")
                return

        # Nothing matched — hand off to Gemini
        self._handle_ai_fallback(command)

    # ------------------------------------------------------------------ #
    #  Dispatch table                                                      #
    # ------------------------------------------------------------------ #

    def _build_dispatch_table(self) -> list:
        """
        Returns an ordered list of (trigger_phrases, handler) pairs.

        Order matters — put more specific phrases before general ones.
        Adding a new command = one new tuple here + one new method below.
        """
        return [
            # ── websites ──────────────────────────────────────────────
            (["open google"],      self._handle_open_google),
            (["open youtube"],     self._handle_open_youtube),
            (["open facebook"],    self._handle_open_facebook),
            (["open linkedin"],    self._handle_open_linkedin),
            (["open instagram"],   self._handle_open_instagram),

            # ── media ─────────────────────────────────────────────────
            (["play song", "play music on youtube"], self._handle_play_song),

            # ── information ───────────────────────────────────────────
            (["news"],             self._handle_news),
            (["joke"],             self._handle_joke),
            (["current time"],     self._handle_time),
            (["current date"],     self._handle_date),
            (["wikipedia search"], self._handle_wikipedia),
            (["google search"],    self._handle_google_search),

            # ── clipboard ─────────────────────────────────────────────
            (["copy this", "copy that"], self._handle_copy_text),
            (["clear clipboard"],        self._handle_clear_clipboard),
            (["paste"],                  self._handle_paste),
            (["copy"],                   self._handle_read_clipboard),

            # ── screenshots (specific before general) ─────────────────
            (["take screenshot region"], self._handle_screenshot_region),
            (["take screenshot"],        self._handle_screenshot),

            # ── volume ────────────────────────────────────────────────
            (["volume up"],                          self._handle_volume_up),
            (["volume down"],                        self._handle_volume_down),
            (["set volume"],                         self._handle_set_volume),
            (["current volume", "what is the volume"], self._handle_current_volume),
            (["unmute"],                             self._handle_unmute),
            (["mute"],                               self._handle_mute),

            # ── reminders ─────────────────────────────────────────────
            (["set reminder", "remind me"],  self._handle_set_reminder),
            (["list reminders", "my reminders"], self._handle_list_reminders),
            (["cancel reminder"],            self._handle_cancel_reminder),

            # ── lifecycle ─────────────────────────────────────────────
            (["exit", "stop", "shutdown"],   self._handle_exit),
        ]

    # ------------------------------------------------------------------ #
    #  Handlers — websites                                                 #
    # ------------------------------------------------------------------ #

    def _handle_open_google(self, _):
        self.speak("Opening Google")
        webbrowser.open(config.WEBSITES["google"])

    def _handle_open_youtube(self, _):
        self.speak("Opening YouTube")
        webbrowser.open(config.WEBSITES["youtube"])

    def _handle_open_facebook(self, _):
        self.speak("Opening Facebook")
        webbrowser.open(config.WEBSITES["facebook"])

    def _handle_open_linkedin(self, _):
        self.speak("Opening LinkedIn")
        webbrowser.open(config.WEBSITES["linkedin"])

    def _handle_open_instagram(self, _):
        self.speak("Opening Instagram")
        webbrowser.open(config.WEBSITES["instagram"])

    # ------------------------------------------------------------------ #
    #  Handlers — media                                                    #
    # ------------------------------------------------------------------ #

    def _handle_play_song(self, _):
        song = self.listen("Which song should I play?")
        if song:
            self.speak(f"Playing {song}")
            pywhatkit.playonyt(song)
        else:
            self.speak("I didn't catch the song name.")

    # ------------------------------------------------------------------ #
    #  Handlers — information                                              #
    # ------------------------------------------------------------------ #

    def _handle_news(self, _):
        self.speak("Fetching the latest news.")
        self.gui.update_status("Processing ...", state="processing")

        try:
            url = (
                f"{config.NEWS_URL}"
                f"?apikey={config.NEWS_API_KEY}"
                f"&country=in&language=en"
            )
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            articles = response.json().get("results", [])
            if not articles:
                self.speak("No news articles found right now.")
                return

            for article in articles[:5]:
                self.speak(article.get("title", "No title available"))

        except requests.RequestException as e:
            logger.error("News fetch failed: %s", e)
            self.speak("I couldn't fetch the news. Please check your connection.")

    def _handle_joke(self, _):
        self.gui.update_status("Processing ...", state="processing")
        self.speak(pyjokes.get_joke())

    def _handle_time(self, _):
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        self.speak(f"The time is {current_time}")

    def _handle_date(self, _):
        current_date = datetime.datetime.now().strftime("%d %B %Y")
        self.speak(f"Today is {current_date}")

    def _handle_wikipedia(self, _):
        query = self.listen("What should I search on Wikipedia?")
        if not query:
            return
        try:
            self.gui.update_status("Processing ...", state="processing")
            result = wikipedia.summary(query, sentences=2)
            self.speak("According to Wikipedia")
            self.speak(result)
        except wikipedia.exceptions.DisambiguationError:
            self.speak("That topic is ambiguous. Could you be more specific?")
        except wikipedia.exceptions.PageError:
            self.speak("I couldn't find a Wikipedia page for that.")

    def _handle_google_search(self, _):
        query = self.listen("What should I search on Google?")
        if query:
            webbrowser.open(f"https://www.google.com/search?q={query}")

    # ------------------------------------------------------------------ #
    #  Handlers — clipboard                                                #
    # ------------------------------------------------------------------ #

    def _handle_copy_text(self, _):
        text = self.listen("What should I copy?")
        if text:
            pyperclip.copy(text)
            self.speak(f"Copied: {text}")

    def _handle_read_clipboard(self, _):
        text = pyperclip.paste()
        self.speak(f"Clipboard has: {text[:50]}" if text else "Clipboard is empty.")

    def _handle_paste(self, _):
        text = pyperclip.paste()
        if text:
            self.speak(f"Pasting: {text[:50]}")
            pyautogui.hotkey("ctrl", "v")
        else:
            self.speak("Nothing in clipboard to paste.")

    def _handle_clear_clipboard(self, _):
        pyperclip.copy("")
        self.speak("Clipboard cleared.")

    # ------------------------------------------------------------------ #
    #  Handlers — screenshots                                              #
    # ------------------------------------------------------------------ #

    def _handle_screenshot_region(self, _):
        self.speak("Select the region on screen. Press Escape to cancel.")
        time.sleep(1)

        region = take_snip()
        if not region:
            self.speak("Screenshot cancelled.")
            return

        x1, y1, x2, y2 = region
        filename = self._save_screenshot(
            ImageGrab.grab(bbox=(x1, y1, x2, y2)),
            prefix="region"
        )
        self.speak("Region screenshot saved.")
        logger.info("Saved: %s", filename)

    def _handle_screenshot(self, _):
        self.gui.update_status("Processing ...", state="processing")
        self.speak("Taking screenshot in 3 seconds.")
        time.sleep(3)

        filename = self._save_screenshot(pyautogui.screenshot(), prefix="screenshot")
        self.speak(f"Screenshot saved.")
        logger.info("Saved: %s", filename)

    def _save_screenshot(self, image, prefix: str) -> str:
        """Save a PIL image to the screenshots folder with a timestamp filename."""
        os.makedirs(config.SCREENSHOT_DIR, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = os.path.join(config.SCREENSHOT_DIR, f"{prefix}_{timestamp}.png")
        image.save(filename)
        return filename

    # ------------------------------------------------------------------ #
    #  Handlers — volume                                                   #
    # ------------------------------------------------------------------ #

    def _get_volume_interface(self):
        from pycaw.pycaw import AudioUtilities
        devices = AudioUtilities.GetSpeakers()
        return devices.EndpointVolume

    def _handle_volume_up(self, _):
        vol = self._get_volume_interface()
        new_vol = min(1.0, vol.GetMasterVolumeLevelScalar() + 0.1)
        vol.SetMasterVolumeLevelScalar(new_vol, None)
        self.speak(f"Volume increased to {int(new_vol * 100)} percent.")

    def _handle_volume_down(self, _):
        vol = self._get_volume_interface()
        new_vol = max(0.0, vol.GetMasterVolumeLevelScalar() - 0.1)
        vol.SetMasterVolumeLevelScalar(new_vol, None)
        self.speak(f"Volume decreased to {int(new_vol * 100)} percent.")

    def _handle_mute(self, _):
        self._get_volume_interface().SetMute(1, None)
        self.speak("Muted.")

    def _handle_unmute(self, _):
        self._get_volume_interface().SetMute(0, None)
        self.speak("Unmuted.")

    def _handle_current_volume(self, _):
        vol = self._get_volume_interface()
        if vol.GetMute():
            self.speak("Volume is currently muted.")
        else:
            self.speak(f"Current volume is {int(vol.GetMasterVolumeLevelScalar() * 100)} percent.")

    def _handle_set_volume(self, _):
        percent_text = self.listen("What percentage?")
        if not percent_text:
            return

        percent = self._parse_volume_percent(percent_text)
        if percent is not None and 0 <= percent <= 100:
            self._get_volume_interface().SetMasterVolumeLevelScalar(percent / 100, None)
            self.speak(f"Volume set to {percent} percent.")
        else:
            self.speak("Please say a number between 0 and 100.")

    def _parse_volume_percent(self, text: str):
        """Extract an integer 0-100 from a spoken string, or return None."""
        nums = re.findall(r"\d+", text)
        if nums:
            return int(nums[0])

        word_to_num = {
            "zero": 0, "ten": 10, "twenty": 20, "thirty": 30,
            "forty": 40, "fifty": 50, "sixty": 60,
            "seventy": 70, "eighty": 80, "ninety": 90, "hundred": 100,
        }
        for word, val in word_to_num.items():
            if word in text.lower().split():
                return val
        return None

    # ------------------------------------------------------------------ #
    #  Handlers — reminders                                                #
    # ------------------------------------------------------------------ #

    def _handle_set_reminder(self, _):
        self.gui.update_status("Processing ...", state="processing")

        reminder_msg = self.listen("What should I remind you about?")
        if not reminder_msg:
            self.speak("I didn't catch that.")
            return

        time_text = self.listen(
            "At what time? Say something like: in 5 minutes, 2 PM, or 5 30 AM."
        )
        if not time_text:
            self.speak("I didn't catch the time.")
            return

        remind_time = _parse_remind_time(time_text)
        if remind_time:
            set_reminder(reminder_msg, remind_time, self.speak)
            self.speak(
                f"Reminder set for {remind_time:%I:%M %p}. "
                f"I'll remind you to {reminder_msg}."
            )
        else:
            self.speak(
                "Sorry, I couldn't understand that time. "
                "Try saying 'in 10 minutes' or '3 PM'."
            )

    def _handle_list_reminders(self, _):
        active = list_reminders()
        if not active:
            self.speak("You have no active reminders.")
            return
        count = len(active)
        self.speak(f"You have {count} reminder{'s' if count != 1 else ''}.")
        for i, r in enumerate(active, start=1):
            self.speak(f"Reminder {i}: {r['message']} at {r['time']:%I:%M %p}.")

    def _handle_cancel_reminder(self, _):
        active = list_reminders()
        if not active:
            self.speak("You have no active reminders.")
            return

        count = len(active)
        self.speak(f"You have {count} reminder{'s' if count != 1 else ''}.")
        for i, r in enumerate(active, start=1):
            self.speak(f"Reminder {i}: {r['message']} at {r['time']:%I:%M %p}.")

        # Fixed: listen_once called ONCE, result used directly
        num_text = self.listen("Which reminder should I cancel? Say the number.")
        if not num_text:
            self.speak("I didn't catch that.")
            return

        index = _spoken_index(num_text)
        if cancel_reminder(index):
            self.speak(f"Reminder {index + 1} cancelled.")
        else:
            self.speak("I couldn't find that reminder. Please try again.")

    # ------------------------------------------------------------------ #
    #  Handlers — AI fallback                                              #
    # ------------------------------------------------------------------ #

    def _handle_ai_fallback(self, command: str) -> None:
        self.gui.update_status("Processing ...", state="processing")
        logger.info("Falling back to Gemini for: '%s'", command)
        try:
            response = self._gemini.models.generate_content(
                model=config.GEMINI_MODEL,
                contents=[config.GEMINI_SYSTEM_PROMPT, command],
            )
            self.speak(response.text)
        except Exception as e:
            logger.error("Gemini API error: %s", e)
            self.speak("I'm having trouble reaching the AI service right now.")

    # ------------------------------------------------------------------ #
    #  Handlers — lifecycle                                                #
    # ------------------------------------------------------------------ #

    def _handle_exit(self, _):
        self.speak("Shutting down Jarvis. Have a nice day.")
        self.gui.update_status("Shutting down ...", state="shutdown")
        self.assistant.speech.shutdown()
        self.assistant.stop()


# ------------------------------------------------------------------ #
#  Module-level helpers (pure functions, no class state needed)       #
# ------------------------------------------------------------------ #

def _parse_remind_time(time_text: str):
    """
    Parse a spoken time string into a datetime object.
    Supports:
      - Relative: 'in X minutes', 'in X hours'
      - Absolute: '2 PM', '5 30 AM', '14 30'
    Returns a datetime, or None if unparseable.
    """
    now  = datetime.datetime.now()
    nums = list(map(int, re.findall(r"\d+", time_text)))

    if "minute" in time_text:
        return now + datetime.timedelta(minutes=nums[0]) if nums else None

    if "hour" in time_text:
        return now + datetime.timedelta(hours=nums[0]) if nums else None

    if not nums:
        return None

    hour   = nums[0]
    minute = nums[1] if len(nums) >= 2 else 0

    if "pm" in time_text and hour != 12:
        hour += 12
    elif "am" in time_text and hour == 12:
        hour = 0

    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return None

    remind_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if remind_time <= now:
        remind_time += datetime.timedelta(days=1)
    return remind_time


def _spoken_index(text: str) -> int:
    """
    Convert a spoken ordinal or cardinal to a 0-based index.
    e.g. 'first' → 0, 'two' → 1, '3' → 2
    Returns -1 if nothing matches.
    """
    word_map = {
        "one":   1, "first":   1,
        "two":   2, "second":  2,
        "three": 3, "third":   3,
        "four":  4, "fourth":  4,
        "five":  5, "fifth":   5,
        "six":   6, "sixth":   6,
        "seven": 7, "seventh": 7,   # fixed: was "eighth": 7
        "eight": 8, "eighth":  8,   # fixed: duplicate key removed
        "nine":  9, "ninth":   9,
        "ten":  10, "tenth":  10,
    }
    nums = re.findall(r"\d+", text)
    if nums:
        return int(nums[0]) - 1
    for word, val in word_map.items():
        if word in text.split():
            return val - 1
    return -1