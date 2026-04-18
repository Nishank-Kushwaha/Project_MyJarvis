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