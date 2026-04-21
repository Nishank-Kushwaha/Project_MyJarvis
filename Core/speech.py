import os
import uuid
import logging
import speech_recognition as sr
import pygame
from gtts import gTTS

logger = logging.getLogger(__name__)

# Temp file stored in the OS temp dir, unique per run to avoid collisions
_TMP_AUDIO = os.path.join(os.path.dirname(__file__), f"_tts_{uuid.uuid4().hex}.mp3")


class SpeechEngine:
    """
    Handles all Text-To-Speech (TTS) and Speech-To-Text (STT) operations.

    Design decisions:
    - pygame.mixer is initialized ONCE in __init__, not on every speak() call.
    - The temp MP3 file uses a unique name so parallel processes don't collide.
    - listen_once() is the single, canonical way to capture a spoken response
      anywhere in the app — no more copy-pasted microphone blocks.
    - Both TTS engines (gTTS online, pyttsx3 offline) are supported.
      Set use_online=False to fall back to the offline engine, e.g. when
      there is no internet connection.
    """

    def __init__(self, gui, use_online: bool = True):
        """
        Args:
            gui:        JarvisGUI instance — used to update status labels.
            use_online: If True (default), use gTTS (requires internet).
                        If False, fall back to pyttsx3 (fully offline).
        """
        self.gui = gui
        self.use_online = use_online
        self.recognizer = sr.Recognizer()
        self._tmp_file = _TMP_AUDIO

        # Initialise pygame mixer once for the lifetime of the app
        pygame.mixer.init()
        logger.info("SpeechEngine ready (mode: %s).", "online/gTTS" if use_online else "offline/pyttsx3")

        # Offline engine — only imported and initialised when needed
        self._offline_engine = None

    # ------------------------------------------------------------------ #
    #  Text-To-Speech                                                      #
    # ------------------------------------------------------------------ #

    def speak(self, text: str) -> None:
        """Convert text to speech and block until playback finishes."""
        if not text or not text.strip():
            return

        logger.info("Jarvis: %s", text)
        self.gui.update_status("Speaking ...", state="speaking")

        try:
            if self.use_online:
                self._speak_online(text)
            else:
                self._speak_offline(text)
        except Exception as e:
            logger.error("TTS failed (%s). Attempting offline fallback.", e)
            self._speak_offline(text)
        finally:
            self.gui.update_status("Idle", state="idle")

    def _speak_online(self, text: str) -> None:
        """TTS via gTTS + pygame (requires internet)."""
        tts = gTTS(text)
        tts.save(self._tmp_file)

        pygame.mixer.music.load(self._tmp_file)
        pygame.mixer.music.play()

        clock = pygame.time.Clock()
        while pygame.mixer.music.get_busy():
            clock.tick(10)

        pygame.mixer.music.unload()
        self._cleanup_tmp()

    def _speak_offline(self, text: str) -> None:
        """TTS via pyttsx3 — no internet required."""
        if self._offline_engine is None:
            import pyttsx3
            self._offline_engine = pyttsx3.init()
            logger.info("pyttsx3 offline engine initialised.")

        self._offline_engine.say(text)
        self._offline_engine.runAndWait()

    def _cleanup_tmp(self) -> None:
        """Remove the temp MP3 file if it exists."""
        try:
            if os.path.exists(self._tmp_file):
                os.remove(self._tmp_file)
        except OSError as e:
            logger.warning("Could not delete temp audio file: %s", e)

    # ------------------------------------------------------------------ #
    #  Speech-To-Text                                                      #
    # ------------------------------------------------------------------ #

    def listen_once(self, prompt: str = None) -> str:
        """
        Open the microphone, optionally speak a prompt first, and return
        whatever the user says as a lowercase string.

        This is the single canonical STT method used everywhere in the app.
        Returns '' if nothing was understood or a timeout occurred.

        Args:
            prompt: Optional question/instruction to speak before listening.
        """
        if prompt:
            self.speak(prompt)

        try:
            with sr.Microphone() as source:
                self.gui.update_status("Listening ...", state="listening")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=6, phrase_time_limit=8)

            result = self.recognizer.recognize_google(audio).lower()
            logger.debug("Heard: %s", result)
            return result

        except sr.WaitTimeoutError:
            logger.debug("listen_once: timed out waiting for speech.")
            return ""

        except sr.UnknownValueError:
            logger.debug("listen_once: speech not understood.")
            return ""

        except sr.RequestError as e:
            logger.error("listen_once: STT API error — %s", e)
            self.speak("I'm having trouble with the speech service right now.")
            return ""

    # ------------------------------------------------------------------ #
    #  Lifecycle                                                           #
    # ------------------------------------------------------------------ #

    def shutdown(self) -> None:
        """
        Clean up resources. Call this when the app is closing.
        Ensures the temp file and pygame mixer are properly released.
        """
        self._cleanup_tmp()
        pygame.mixer.quit()
        logger.info("SpeechEngine shut down.")