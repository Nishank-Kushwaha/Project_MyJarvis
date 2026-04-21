import threading
import datetime
import logging
import speech_recognition as sr

from GUI.app import JarvisGUI

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


class JarvisAssistant:
    """
    Central orchestrator for J.A.R.V.I.S.

    Owns the main wake-word loop, coordinates the GUI, SpeechEngine,
    and CommandRouter. Nothing domain-specific lives here — this class
    only wires the pieces together and manages lifecycle state.
    """

    def __init__(self):
        self.running = False
        self.recognizer = sr.Recognizer()

        # GUI is created first so other components can call update_status
        self.gui = JarvisGUI()

        # Imported here to avoid circular imports; both receive a reference
        # to this assistant so they can call self.speak / self.gui freely.
        from Core.speech import SpeechEngine
        from Core.commands import CommandRouter

        self.speech = SpeechEngine(gui=self.gui)
        self.router = CommandRouter(assistant=self)
        
        from Features import reminders as reminder_module
        reminder_module.init(self.speak)

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def start(self):
        """
        Entry point called from main.py.
        Starts the background listener thread then hands control to the GUI.
        """
        self.running = True
        thread = threading.Thread(target=self._run_loop, daemon=True)
        thread.start()
        logger.info("Jarvis background thread started.")
        self.gui.run()          # blocks until the window is closed

    def speak(self, text: str):
        """Convenience pass-through so other modules can call assistant.speak()."""
        self.speech.speak(text)

    def stop(self):
        """Graceful shutdown — called by the 'exit' command handler."""
        self.running = False
        self.gui.root.after(0, self.gui.root.destroy)

    # ------------------------------------------------------------------ #
    #  Internal loop                                                       #
    # ------------------------------------------------------------------ #

    def _run_loop(self):
        """Background thread: greet → listen for wake word → dispatch command."""
        self._greet()

        while self.running:
            try:
                word = self._listen_for_wake_word()
                if not word:
                    continue

                if "jarvis" in word.lower():
                    self.gui.update_status("Active ...", state="active")
                    self.speak("Yes")
                    logger.info("Wake word detected.")

                    command = self._listen_for_command()
                    if command:
                        logger.info("Command received: %s", command)
                        self.router.route(command)

            except sr.UnknownValueError:
                logger.debug("Could not understand audio — ignoring.")

            except sr.RequestError as e:
                logger.error("Speech API error: %s", e)
                self.speak("I'm having trouble reaching the speech service.")

            except Exception as e:
                logger.exception("Unexpected error in main loop: %s", e)

    def _listen_for_wake_word(self) -> str:
        """Open the microphone and return whatever was said, or '' on failure."""
        try:
            with sr.Microphone() as source:
                self.gui.update_status("Listening for wake word ...", state="listening")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = self.recognizer.listen(source)

            return self.recognizer.recognize_google(audio)

        except sr.WaitTimeoutError:
            return ""

    def _listen_for_command(self) -> str:
        """
        Called after the wake word is detected.
        Returns the spoken command string, or '' on failure.
        """
        try:
            with sr.Microphone() as source:
                self.gui.update_status("Listening ...", state="listening")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=6, phrase_time_limit=8)

            return self.recognizer.recognize_google(audio).lower()

        except (sr.UnknownValueError, sr.WaitTimeoutError):
            self.speak("I didn't catch that. Please try again.")
            return ""

    def _greet(self):
        """Speak a time-appropriate greeting on startup."""
        hour = datetime.datetime.now().hour

        if hour < 12:
            greeting = "Good Morning"
        elif hour < 18:
            greeting = "Good Afternoon"
        else:
            greeting = "Good Evening"

        self.speak(greeting)
        self.speak("Initializing Jarvis. Ready for your commands.")
        self.gui.update_status("Idle", state="idle")