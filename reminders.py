import threading
import datetime
import time

reminders = []  # list of active reminders

def add_reminder(message, remind_time):
    """remind_time is a datetime object"""
    reminder = {
        "message": message,
        "time": remind_time,
        "active": True
    }
    reminders.append(reminder)
    print(f"Reminder set: '{message}' at {remind_time.strftime('%H:%M')}")
    return reminder

def reminder_worker(reminder, speak_func):
    """Runs in background, waits until reminder time"""
    while True:
        now = datetime.datetime.now()
        if now >= reminder["time"] and reminder["active"]:
            speak_func(f"Reminder: {reminder['message']}")
            reminder["active"] = False
            break
        time.sleep(10)  # check every 10 seconds

def set_reminder(message, remind_time, speak_func):
    reminder = add_reminder(message, remind_time)
    t = threading.Thread(
        target=reminder_worker,
        args=(reminder, speak_func),
        daemon=True
    )
    t.start()

def list_reminders():
    active = [r for r in reminders if r["active"]]
    return active

def cancel_reminder(index):
    active = list_reminders()
    if 0 <= index < len(active):
        active[index]["active"] = False
        return True
    return False