# Jarvis Assistant
A Python-based voice assistant with a custom animated GUI.  
Jarvis listens for the wake word **"Jarvis"**, accepts voice commands, and performs tasks such as opening websites, fetching news, playing songs on YouTube, telling jokes, and answering general prompts through Gemini.

## Features
- Wake-word activation (`jarvis`)
- Voice command recognition via microphone
- Spoken responses using text-to-speech
- Animated desktop GUI status panel (`idle`, `listening`, `speaking`, etc.)
- Built-in commands:
  - Open Google, Facebook, YouTube, LinkedIn, Instagram
  - Play songs on YouTube
  - Fetch latest news headlines
  - Tell jokes
  - Speak current time/date
  - Wikipedia search
  - Google search
- Fallback AI replies using Gemini API for general prompts

## Tech Stack
- Python
- `speech_recognition` for speech-to-text
- `gTTS` + `pygame` for audio playback
- `tkinter` for GUI
- `requests` for API calls
- `python-dotenv` for environment variables
- `google-genai` for Gemini integration
- `wikipedia`, `pyjokes`, `pywhatkit` for utility features

## Project Structure
- `main.py` - core assistant logic, voice loop, command processing
- `gui.py` - animated Jarvis GUI
- `.env.sample` - template for required API keys
- `.gitignore` - ignores env files, virtual envs, cache, temp audio

## Prerequisites
- Python 3.10+ (3.11 recommended)
- Working microphone
- Internet connection
- API keys:
  - `NEWS_API_KEY` (newsdata.io)
  - `GEMINI_API_KEY` (Google Gemini)

## Setup
1. Clone the repository:
   ```powershell
   git clone <your-repo-url>
   cd <your-repo-folder>
   ```
2. Create and activate a virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   ```
3. Install dependencies:
   ```powershell
   pip install speechrecognition pyttsx3 requests google-genai gtts pygame python-dotenv wikipedia pyjokes pywhatkit pyaudio
   ```
4. Configure environment variables:
   - Copy `.env.sample` to `.env`
   - Fill in your keys:
     ```env
     NEWS_API_KEY=
     GEMINI_API_KEY=
     ```

## Run
```powershell
python main.py
```

## Usage Flow
1. Start the app.
2. Jarvis greets you and begins listening for wake word.
3. Say **"Jarvis"**.
4. Speak a command (example: "open youtube", "current time", "news").
5. To quit, say **"exit"** or **"stop"** (or press `Esc` in the GUI window).

## Supported Voice Commands
- `open google`
- `open facebook`
- `open youtube`
- `open linkedin`
- `open instagram`
- `play song` / `play music on youtube`
- `news`
- `joke`
- `current time`
- `current date`
- `wikipedia search`
- `google search`
- `exit` / `stop`

Any unrecognized command is sent to Gemini for a short AI-generated response.

## Notes
- `main.py` currently uses `gTTS` for speech output (`speak()`), while a legacy `pyttsx3` function (`speak_old()`) is still present but unused.
- News headlines are currently fetched for country `in` and language `en`.

## Troubleshooting
- **Microphone not detected / recognition fails**
  - Check microphone permissions and default input device.
  - Ensure `pyaudio` is installed correctly.
- **No Gemini response**
  - Verify `GEMINI_API_KEY` in `.env`.
  - Check internet connectivity.
- **No news output**
  - Verify `NEWS_API_KEY`.
  - Confirm API quota/limits on your provider account.
- **Audio playback issues**
  - Ensure `pygame` is installed and no other app is blocking audio output.