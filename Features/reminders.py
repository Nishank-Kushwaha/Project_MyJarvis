import threading
import datetime
import logging
from typing import Callable

logger = logging.getLogger(__name__)


class ReminderManager:
    """
    Manages all active reminders for the session.

    Each reminder runs its own lightweight daemon thread that sleeps
    in 10-second intervals and fires when the target time is reached.

    Usage:
        mgr = ReminderManager(speak_func=assistant.speak)
        mgr.add("drink water", datetime.datetime.now() + timedelta(minutes=5))
    """

    def __init__(self, speak_func: Callable[[str], None]):
        """
        Args:
            speak_func: The callable used to announce a reminder when it fires.
                        Typically assistant.speak — passed in so this module
                        has zero knowledge of the GUI or speech engine.
        """
        self._speak    = speak_func
        self._reminders: list[dict] = []
        self._lock     = threading.Lock()

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def add(self, message: str, remind_time: datetime.datetime) -> dict:
        """
        Schedule a new reminder.

        Args:
            message:     What to say when the reminder fires.
            remind_time: Exact datetime at which to fire.

        Returns:
            The reminder dict (useful for testing / confirmation).
        """
        reminder = {
            "message": message,
            "time":    remind_time,
            "active":  True,
        }

        with self._lock:
            self._reminders.append(reminder)

        thread = threading.Thread(
            target=self._worker,
            args=(reminder,),
            daemon=True,
            name=f"reminder-{remind_time:%H%M%S}",
        )
        thread.start()

        logger.info("Reminder set: '%s' at %s.", message, remind_time.strftime("%H:%M"))
        return reminder

    def list_active(self) -> list[dict]:
        """Return all reminders that have not yet fired or been cancelled."""
        with self._lock:
            return [r for r in self._reminders if r["active"]]

    def cancel(self, index: int) -> bool:
        """
        Cancel a reminder by its position in the active list (0-based).

        Returns True if cancelled successfully, False if index is invalid.
        """
        active = self.list_active()
        if 0 <= index < len(active):
            active[index]["active"] = False
            logger.info("Reminder %d cancelled.", index + 1)
            return True
        logger.warning("cancel() called with invalid index %d.", index)
        return False

    def clear_all(self) -> None:
        """Cancel every active reminder. Useful on shutdown."""
        with self._lock:
            for r in self._reminders:
                r["active"] = False
        logger.info("All reminders cleared.")

    # ------------------------------------------------------------------ #
    #  Internal                                                            #
    # ------------------------------------------------------------------ #

    def _worker(self, reminder: dict) -> None:
        """
        Background thread: polls every 10 seconds until the reminder
        time is reached, then speaks the message and marks it inactive.
        """
        import time
        while reminder["active"]:
            if datetime.datetime.now() >= reminder["time"]:
                if reminder["active"]:          # re-check after acquiring
                    logger.info("Firing reminder: '%s'.", reminder["message"])
                    self._speak(f"Reminder: {reminder['message']}")
                    reminder["active"] = False
                break
            time.sleep(10)