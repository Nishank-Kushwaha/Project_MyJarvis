import speech_recognition as sr
import webbrowser
import pyttsx3
import requests
from google import genai
from gtts import gTTS
import pygame
import os
import dotenv
import datetime
import wikipedia
import pyjokes
import pywhatkit
import threading
from gui import JarvisGUI
import pyperclip
import pyautogui
from snip import take_snip
from PIL import ImageGrab
from pycaw.pycaw import AudioUtilities
from comtypes import CLSCTX_ALL
from reminders import set_reminder, list_reminders, cancel_reminder
import re

dotenv.load_dotenv()

gui = JarvisGUI()
recognizer = sr.Recognizer()
engine = pyttsx3.init()
running = True

news_apikey=os.getenv("NEWS_API_KEY")

gemini_apikey=os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=gemini_apikey)

# Greeting
def wish_me():
    hour = int(datetime.datetime.now().hour)

    if hour < 12:
        speak("Good Morning")
    elif hour < 18:
        speak("Good Afternoon")
    else:
        speak("Good Evening")

    speak("Initializing Jarvis. Ready for your commands.")

# Using pyttsx3 module
def speak_old(text):
    print("Jarvis:", text)
    engine.say(text)
    engine.runAndWait()

# Using gtts module
def speak(text):
    gui.update_status("Speaking ...",state="speaking")

    tts = gTTS(text)
    tts.save('temp.mp3') 

    # Initialize Pygame mixer
    pygame.mixer.init()

    # Load the MP3 file
    pygame.mixer.music.load('temp.mp3')

    # Play the MP3 file
    pygame.mixer.music.play()

    # Keep the program running until the music stops playing
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    
    pygame.mixer.music.unload()
    os.remove("temp.mp3") 

    gui.update_status("Idle",state="idle")

# ai process using gemini
def aiProcess(command):
    # -------------------- Using google gemini ---------------
   
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=[
            "You are Jarvis, a smart AI assistant like Alexa. Keep answers short.",
            command
        ]
    )

    return response.text

# Gives devices functionality
def get_volume_interface():
    devices = AudioUtilities.GetSpeakers()
    return devices.EndpointVolume

# ------------------ helpers -----------------------
def listen_once(recognizer, gui, prompt=None):
    if prompt:
        speak(prompt)
    with sr.Microphone() as source:
        gui.update_status("Listening ...", state="listening")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)  # was 1s — halved
        audio = recognizer.listen(source, timeout=6, phrase_time_limit=8)
    try:
        return recognizer.recognize_google(audio).lower()
    except sr.UnknownValueError:
        return ""

def parse_remind_time(time_text: str):
    """
    Parse a spoken time string into a datetime.
    Supports:
      'in X minutes / hours'
      'X AM/PM', 'X Y AM/PM'  (e.g. '5 30 pm', '2 pm', '14 30')
    Returns datetime or None.
    """
    now = datetime.datetime.now()
    nums = list(map(int, re.findall(r'\d+', time_text)))

    # ── relative: "in X minutes / hours" ─────────────────────────────────────
    if "minute" in time_text:
        if nums:
            return now + datetime.timedelta(minutes=nums[0])

    elif "hour" in time_text:
        if nums:
            return now + datetime.timedelta(hours=nums[0])

    # ── absolute: "5 30 PM", "14 30", "2 PM" ─────────────────────────────────
    else:
        if not nums:
            return None

        hour   = nums[0]
        minute = nums[1] if len(nums) >= 2 else 0

        # 12-hour correction
        if "pm" in time_text and hour != 12:
            hour += 12
        elif "am" in time_text and hour == 12:
            hour = 0

        # Clamp to valid range before replace()
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            return None

        remind_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if remind_time <= now:                          # already passed → tomorrow
            remind_time += datetime.timedelta(days=1)
        return remind_time

    return None

def spoken_index(text: str) -> int:
    """Convert '1' / 'one' / 'first' etc. to 0-based index. Returns -1 on failure."""
    word_map = {
        "one": 1, "first": 1,
        "two": 2, "second": 2,
        "three": 3, "third": 3,
        "four": 4, "fourth": 4,
        "five": 5, "fifth": 5,
        "six": 6, "sixth": 6,
        "seven": 7, "eighth": 7,
        "eight": 8, "eight": 8,
        "nine": 9, "ninth": 9,
        "ten": 10, "tenth": 10,
    }
    nums = re.findall(r'\d+', text)
    if nums:
        return int(nums[0]) - 1
    for word, val in word_map.items():
        if word in text.split():          # whole-word match
            return val - 1
    return -1

# process function for commmands
def processCommand(c):
    
    global running 
    c = c.lower()

    if "open google" in c:
        speak("Opening Google")
        webbrowser.open("https://google.com")

    elif "open facebook" in c:
        speak("Opening Facebook")
        webbrowser.open("https://facebook.com")

    elif "open youtube" in c:
        speak("Opening YouTube")
        webbrowser.open("https://youtube.com")

    elif "open linkedin" in c:
        speak("Opening LinkedIn")
        webbrowser.open("https://linkedin.com")

    elif "open instagram" in c:
        speak("Opening Instagram")
        webbrowser.open("https://instagram.com")

    elif "play song" in c or "play music on youtube" in c:
        speak("Which song should I play?")
        with sr.Microphone() as source:
            print("Listening ...")
            gui.update_status("Listening ...",state="listening")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source)

        song = recognizer.recognize_google(audio)

        if song != "none":
            speak(f"Playing {song}")
            pywhatkit.playonyt(song)

    elif "news" in c:
        speak("Fetching news...")
        gui.update_status("Processing ...", state="processing") 

        try:
            url = f"https://newsdata.io/api/1/latest?apikey={news_apikey}&country=in&language=en"
            response = requests.get(url)

            if response.status_code == 200:
                data = response.json()
                articles = data.get('results', [])

                if not articles:
                    speak("No news found")
                    return

                for article in articles[:5]:  # top 5
                    speak(article.get('title', 'No title'))

            else:
                speak("Failed to fetch news")

        except Exception as e:
            speak("Error fetching news")
            print(e)
    
    elif "joke" in c:
        gui.update_status("Processing ...", state="processing")
        joke = pyjokes.get_joke()
        speak(joke)

    elif "current time" in c:
        time = datetime.datetime.now().strftime("%H:%M:%S")
        speak(f"The time is {time}")

    elif "current date" in c:
        date = datetime.datetime.now().strftime("%d %B %Y")
        speak(f"Today is {date}")

    elif "wikipedia search" in c:
        speak("What should I search?")

        with sr.Microphone() as source:
            print("Listening ...")
            gui.update_status("Listening ...",state="listening")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source)

        search = recognizer.recognize_google(audio)
        print("Search:", search)
        
        result = wikipedia.summary(search, sentences=2)
        speak("According to Wikipedia")
        speak(result)

    elif "google search" in c:
        speak("What should I search?")

        with sr.Microphone() as source:
            print("Listening ...")
            gui.update_status("Listening ...",state="listening")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source)

        search = recognizer.recognize_google(audio)
        print("Search:", search)

        webbrowser.open(f"https://www.google.com/search?q={search}")

    elif "copy this" in c or "copy that" in c:
        # Asks what to copy, then puts it in clipboard
        speak("What should I copy?")
        with sr.Microphone() as source:
            gui.update_status("Listening ...", state="listening")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source)
        text_to_copy = recognizer.recognize_google(audio)
        pyperclip.copy(text_to_copy)
        speak(f"Copied: {text_to_copy}")

    elif "copy" in c:
        text = pyperclip.paste()
        if text:
            speak(f"Clipboard has: {text[:50]}")
        else:
            speak("Clipboard is empty")

    elif "paste" in c:
        text = pyperclip.paste()
        if text:
            speak(f"Pasting: {text[:50]}")
            pyautogui.hotkey('ctrl', 'v')
        else:
            speak("Nothing in clipboard to paste")

    elif "clear clipboard" in c:
        pyperclip.copy("")
        speak("Clipboard cleared")

    elif "take screenshot region" in c:
        speak("Select the region on screen. Press Escape to cancel.")
        import time
        time.sleep(1)  # small delay so Jarvis window fades

        region = take_snip()  # opens snipping overlay

        if region:
            x1, y1, x2, y2 = region
            folder = "screenshots"
            os.makedirs(folder, exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"{folder}/region_{timestamp}.png"

            screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            screenshot.save(filename)
            speak("Region screenshot saved")
            print(f"Saved: {filename}")
        else:
            speak("Screenshot cancelled")

    elif "take screenshot" in c:
        gui.update_status("Processing ...", state="processing")

        # Create screenshots folder if it doesn't exist
        folder = "screenshots"
        os.makedirs(folder, exist_ok=True)

        # Filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{folder}/screenshot_{timestamp}.png"

        # Small delay so Jarvis window doesn't block the screen
        speak("Taking screenshot in 3 seconds")
        import time
        time.sleep(3)

        screenshot = pyautogui.screenshot()
        screenshot.save(filename)

        speak(f"Screenshot saved as screenshot_{timestamp}")
        print(f"Saved: {filename}")

    elif "volume up" in c:
        volume = get_volume_interface()
        current = volume.GetMasterVolumeLevelScalar()
        new_vol = min(1.0, current + 0.1)   # increase by 10%, max 100%
        volume.SetMasterVolumeLevelScalar(new_vol, None)
        speak(f"Volume increased to {int(new_vol * 100)} percent")

    elif "volume down" in c:
        volume = get_volume_interface()
        current = volume.GetMasterVolumeLevelScalar()
        new_vol = max(0.0, current - 0.1)   # decrease by 10%, min 0%
        volume.SetMasterVolumeLevelScalar(new_vol, None)
        speak(f"Volume decreased to {int(new_vol * 100)} percent")

    elif "unmute" in c:
        volume = get_volume_interface()
        volume.SetMute(0, None)
        speak("Unmuted")

    elif "mute" in c:
        volume = get_volume_interface()
        volume.SetMute(1, None)
        speak("Muted")

    elif "set volume" in c:
        speak("What percentage?")
        with sr.Microphone() as source:
            gui.update_status("Listening ...", state="listening")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source)

        try:
            percent_text = recognizer.recognize_google(audio)
            # Extract number from speech like "fifty" or "50 percent"
            import re
            numbers = re.findall(r'\d+', percent_text)
            
            if numbers:
                percent = int(numbers[0])
            else:
                # Handle spoken numbers
                word_to_num = {
                    "ten": 10, "twenty": 20, "thirty": 30,
                    "forty": 40, "fifty": 50, "sixty": 60,
                    "seventy": 70, "eighty": 80, "ninety": 90,
                    "hundred": 100, "zero": 0
                }
                percent = word_to_num.get(percent_text.lower().split()[0], None)

            if percent is not None and 0 <= percent <= 100:
                volume = get_volume_interface()
                volume.SetMasterVolumeLevelScalar(percent / 100, None)
                speak(f"Volume set to {percent} percent")
            else:
                speak("Please say a number between 0 and 100")

        except Exception as e:
            speak("Sorry I couldn't understand the volume level")
            print(e)

    elif "current volume" in c or "what is the volume" in c:
        volume = get_volume_interface()
        current = int(volume.GetMasterVolumeLevelScalar() * 100)
        muted = volume.GetMute()
        if muted:
            speak("Volume is currently muted")
        else:
            speak(f"Current volume is {current} percent")

    elif "set reminder" in c or "remind me" in c:
        gui.update_status("Processing ...", state="processing")

        speak("What should I remind you about?")
        with sr.Microphone() as source:
            gui.update_status("Listening ...", state="listening")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)  # was 1s — halved
            audio = recognizer.listen(source, timeout=6, phrase_time_limit=8)
        try:
            reminder_msg = recognizer.recognize_google(audio).lower()
        except sr.UnknownValueError:
            speak("Sorry, I didn't catch that.")
            return
        
        speak("At what time? Say something like: in 5 minutes, 2 PM, or 5 30 AM.")
        with sr.Microphone() as source:
            gui.update_status("Listening ...", state="listening")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)  # was 1s — halved
            audio = recognizer.listen(source, timeout=6, phrase_time_limit=8)
        try:
            time_text = recognizer.recognize_google(audio).lower()
        except sr.UnknownValueError:
            speak("Sorry, I didn't catch the time.")
            return

        remind_time = parse_remind_time(time_text)
        if remind_time:
            set_reminder(reminder_msg, remind_time, speak)
            speak(f"Reminder set for {remind_time:%I:%M %p}. I'll remind you to {reminder_msg}.")
        else:
            speak("Sorry, I couldn't understand that time. Try saying 'in 10 minutes' or '3 PM'.")

    elif "list reminders" in c or "my reminders" in c:
        active = list_reminders()
        if not active:
            speak("You have no active reminders.")
            return
        speak(f"You have {len(active)} reminder{'s' if len(active) != 1 else ''}.")
        for i, r in enumerate(active, start=1):
            speak(f"Reminder {i}: {r['message']} at {r['time']:%I:%M %p}.")

    elif "cancel reminder" in c:

        active = list_reminders()
        if not active:
            speak("You have no active reminders.")
            return
        
        speak(f"You have {len(active)} reminder{'s' if len(active) != 1 else ''}.")
        for i, r in enumerate(active, start=1):
            speak(f"Reminder {i}: {r['message']} at {r['time']:%I:%M %p}.")

        num_text = listen_once(recognizer, gui, "Which reminder should I cancel? Say the number.")

        speak("Which reminder should I cancel? Say the number.")
        with sr.Microphone() as source:
            gui.update_status("Listening ...", state="listening")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)  # was 1s — halved
            audio = recognizer.listen(source, timeout=6, phrase_time_limit=8)
        try:
            num_text = recognizer.recognize_google(audio).lower()
        except sr.UnknownValueError:
            speak("Sorry, I didn't catch that.")
            return

        index = spoken_index(num_text)

        if cancel_reminder(index):
            speak(f"Reminder {index + 1} cancelled.")
        else:
            speak("I couldn't find that reminder. Please try again.")

    elif "exit" in c or "stop" in c:
        speak("Shutting down Jarvis. Have a nice day.")
        gui.update_status("Shutting down ...",state="shutdown")

        running = False  

        def close_app():
            gui.root.destroy() 

        gui.root.after(0, close_app)

    else:
        # Let Gemini handle the request
        gui.update_status("Processing ...", state="processing")
        output = aiProcess(c)
        speak(output) 

def run_jarvis():
    global running
    wish_me()
    while True:
        if not running:
            break

        try:
            with sr.Microphone() as source:
                print("Listening for wake word ...")
                gui.update_status("Listening for wake word ...", state="listening")
                recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = recognizer.listen(source)

            word = recognizer.recognize_google(audio)
            print("You said:", word)

            if "jarvis" in word.lower():
                gui.update_status("Active ...", state="active")
                speak("Yes")

                with sr.Microphone() as source:
                    print("Active ...")
                    gui.update_status("Active ...", state="active")
                    recognizer.adjust_for_ambient_noise(source, duration=1)
                    audio = recognizer.listen(source)

                command = recognizer.recognize_google(audio)
                print("Command:", command)

                processCommand(command)

        except sr.UnknownValueError:
            print("Could not understand audio")

        except sr.RequestError as e:
            print(f"API error: {e}")

        except Exception as e:
            print(f"Error: {e}")


# Run in thread
threading.Thread(target=run_jarvis, daemon=True).start()

# Run GUI
gui.run()