# J.A.R.V.I.S — Voice Assistant v2.0

A Python-based voice assistant with a custom animated GUI.  
Jarvis listens for the wake word **"Jarvis"**, accepts voice commands, and performs tasks such as opening websites, fetching news, playing songs on YouTube, controlling system volume, setting reminders, taking screenshots, and answering general prompts through Gemini AI.

> **v2.0** — complete architectural rewrite. Modular class-based design, single-responsibility modules, dispatch-table command routing, and proper error handling throughout.

---

## Features

- Wake-word activation (`jarvis`)
- Voice command recognition via microphone
- Spoken responses using gTTS + pygame (with automatic pyttsx3 offline fallback)
- Animated desktop GUI status panel (`idle`, `listening`, `speaking`, `processing`, etc.)
- **System controls** — volume up/down/mute/unmute/set, current volume query
- **Reminders** — set, list, and cancel time-based voice reminders
- **Screenshots** — full-screen capture and region snip tool
- **Clipboard** — copy, paste, read, and clear clipboard by voice
- **Web & information** — open sites, news headlines, YouTube playback, Wikipedia, Google search
- **Jokes** — via pyjokes
- **AI fallback** — any unrecognised command is answered by Gemini

---

## Project Structure

```
jarvis/
├── main.py                  # Entry point — 3 lines
├── config.py                # All constants, URLs, and API key loading
│
├── core/
│   ├── assistant.py         # JarvisAssistant — main orchestrator and wake-word loop
│   ├── speech.py            # SpeechEngine — TTS (gTTS/pyttsx3) and STT (listen_once)
│   └── commands.py          # CommandRouter — dispatch table, all command handlers
│
├── features/
│   ├── ai.py                # AIClient — Gemini API wrapper
│   ├── system.py            # VolumeController, ScreenshotManager, ClipboardManager
│   ├── web.py               # WebHandler — news, YouTube, Wikipedia, Google search
│   └── reminders.py         # ReminderManager — threaded reminder scheduling
│
├── gui/
│   ├── app.py               # JarvisGUI — animated tkinter status panel
│   └── snip.py              # take_snip() — interactive region selector overlay
│
├── screenshots/             # Auto-created on first screenshot
├── .env                     # Your API keys (never commit this)
├── .env.sample              # Safe-to-commit key template
├── .gitignore
└── requirements.txt
```

---

## Tech Stack

| Purpose                           | Library                          |
| --------------------------------- | -------------------------------- |
| Speech-to-text                    | `speech_recognition` + `pyaudio` |
| Text-to-speech (online)           | `gTTS` + `pygame`                |
| Text-to-speech (offline fallback) | `pyttsx3`                        |
| GUI                               | `tkinter`                        |
| AI responses                      | `google-genai` (Gemini)          |
| News                              | `requests` → newsdata.io         |
| YouTube playback                  | `pywhatkit`                      |
| Wikipedia                         | `wikipedia`                      |
| Jokes                             | `pyjokes`                        |
| Volume control                    | `pycaw` (Windows only)           |
| Screenshots                       | `pyautogui` + `Pillow`           |
| Clipboard                         | `pyperclip` + `pyautogui`        |
| Environment variables             | `python-dotenv`                  |

---

## Prerequisites

- Python 3.10+ (3.11 recommended)
- Windows OS (required for `pycaw` volume control)
- Working microphone
- Internet connection
- API keys:
  - `NEWS_API_KEY` — [newsdata.io](https://newsdata.io)
  - `GEMINI_API_KEY` — [Google AI Studio](https://aistudio.google.com)

---

## Setup

1. **Clone the repository**

   ```powershell
   git clone <your-repo-url>
   cd jarvis
   ```

2. **Create and activate a virtual environment**

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

3. **Install dependencies**

   ```powershell
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   ```powershell
   copy .env.sample .env
   ```

   Then open `.env` and fill in your keys:

   ```env
   NEWS_API_KEY=your_newsdata_key_here
   GEMINI_API_KEY=your_gemini_key_here
   ```

5. **Run**
   ```powershell
   python main.py
   ```

---

## Usage Flow

1. Start the app — Jarvis greets you and begins listening.
2. Say **"Jarvis"** to activate.
3. Speak a command (e.g. `"open youtube"`, `"set reminder"`, `"volume up"`).
4. Say **"exit"** or **"stop"** to shut down, or press `Esc` in the GUI window.

---

## Supported Voice Commands

### Websites

| Command          | Action              |
| ---------------- | ------------------- |
| `open google`    | Opens google.com    |
| `open youtube`   | Opens youtube.com   |
| `open facebook`  | Opens facebook.com  |
| `open linkedin`  | Opens linkedin.com  |
| `open instagram` | Opens instagram.com |

### Media & Information

| Command                               | Action                                       |
| ------------------------------------- | -------------------------------------------- |
| `play song` / `play music on youtube` | Asks for song name, plays on YouTube         |
| `news`                                | Reads top 5 Indian headlines                 |
| `joke`                                | Tells a random joke                          |
| `current time`                        | Speaks the current time                      |
| `current date`                        | Speaks today's date                          |
| `wikipedia search`                    | Asks for a topic, reads a 2-sentence summary |
| `google search`                       | Asks for a query, opens search results       |

### System Controls

| Command                                 | Action                            |
| --------------------------------------- | --------------------------------- |
| `volume up`                             | Increases volume by 10%           |
| `volume down`                           | Decreases volume by 10%           |
| `set volume`                            | Asks for a percentage and sets it |
| `current volume` / `what is the volume` | Speaks the current volume level   |
| `mute`                                  | Mutes system audio                |
| `unmute`                                | Unmutes system audio              |

### Screenshots & Clipboard

| Command                   | Action                                |
| ------------------------- | ------------------------------------- |
| `take screenshot`         | Full-screen capture after 3s delay    |
| `take screenshot region`  | Opens snip overlay for region capture |
| `copy this` / `copy that` | Copies spoken text to clipboard       |
| `copy`                    | Reads current clipboard content aloud |
| `paste`                   | Triggers Ctrl+V at cursor             |
| `clear clipboard`         | Empties the clipboard                 |

### Reminders

| Command                           | Action                                   |
| --------------------------------- | ---------------------------------------- |
| `set reminder` / `remind me`      | Asks what and when, schedules reminder   |
| `list reminders` / `my reminders` | Reads all active reminders               |
| `cancel reminder`                 | Lists reminders and asks which to cancel |

> Reminder times can be spoken as: `"in 5 minutes"`, `"in 2 hours"`, `"3 PM"`, `"5 30 AM"`.

### General

| Command                      | Action                                     |
| ---------------------------- | ------------------------------------------ |
| any unrecognised command     | Sent to Gemini AI for a short spoken reply |
| `exit` / `stop` / `shutdown` | Graceful shutdown                          |

---

## Adding a New Command

Thanks to the dispatch table pattern in `core/commands.py`, adding a command is a two-step process with no changes required elsewhere:

1. Write a handler method in `CommandRouter`:

   ```python
   def _handle_my_feature(self, command: str) -> None:
       self.speak("Doing the thing.")
   ```

2. Register its trigger phrases in `_build_dispatch_table()`:
   ```python
   (["my trigger phrase"], self._handle_my_feature),
   ```

That's it.

---

## Troubleshooting

**Microphone not detected / recognition fails**

- Check microphone permissions and default input device in Windows Sound settings.
- Ensure `pyaudio` is installed: `pip install pyaudio`.

**No Gemini response**

- Verify `GEMINI_API_KEY` in `.env`.
- Check internet connectivity.
- Confirm the model name in `config.py` matches an available Gemini model.

**No news output**

- Verify `NEWS_API_KEY` in `.env`.
- Check your newsdata.io quota and plan limits.

**Audio playback issues**

- Ensure `pygame` is installed and no other app is exclusively holding the audio device.
- If offline, gTTS will fail — `SpeechEngine` will automatically fall back to `pyttsx3`.

**Volume controls not working**

- `pycaw` is Windows-only. Volume commands will not work on macOS or Linux.

**`pycaw` import error on startup**

- Volume control is lazy-imported and will not crash the app — only volume commands will fail.

---

## Changelog

### v2.0

- Full architectural rewrite — class-based, modular design
- `JarvisAssistant` orchestrator class replaces global state
- `SpeechEngine` class — pygame initialised once, offline fallback via pyttsx3
- `CommandRouter` dispatch table replaces 300-line `if/elif` chain
- `AIClient`, `WebHandler`, `VolumeController`, `ScreenshotManager`, `ClipboardManager` extracted into `features/`
- `ReminderManager` class with thread-safe lock and `clear_all()` on shutdown
- `config.py` centralises all constants, URLs, and model names
- `main.py` reduced from 566 lines to 3 lines
- Fixed: `cancel_reminder` double-listen bug
- Fixed: `spoken_index` duplicate key and wrong ordinal mapping
- Added: structured `logging` throughout (replaces bare `print` statements)
- Added: proper exception types (`ConnectionError`, `ValueError`) in `web.py`
- Added: `speak_func` injected into `ReminderManager` (no circular imports)

### v1.0

- Initial release — single-file assistant with animated GUI
