# ✦ GentleTime ✦

A cozy, kawaii-aesthetic activity timer to track your day with gentle reminders. 💜

## What is GentleTime?

GentleTime is a soft, pastel-colored timer application built with Python's `tkinter`. It helps you:
- ⏱️ Set and track time blocks for different activities
- 📝 Log your activities throughout the day with timestamps
- 💾 Save your name and activity history (automatically!)
- 🎨 Choose from multiple beautiful themes (Pookie, Light, Dark, Devil)
- 🌿 Feel supported by animated flowers, clouds, sparkles, and cute animals
- 🔊 Get voice announcements when your timer completes (with text-to-speech)
- ⏸️ Pause, resume, and stop timers as needed
- 📊 View weekly summaries of your activities

## Aesthetic Features

- **Multiple themes**: Pookie (purple/lavender), Light (pastel), Dark (cozy dark), Devil (red/dark)
- **Animated scenery**: Flowers, clouds, sparkles, and cute animals 🌸✨
- **Kawaii-friendly**: Designed to make productivity feel cozy, not stressful
- **Responsive UI**: Buttons change colors with theme selection

## Getting Started

### Requirements
- Python 3.7+
- `tkinter` (usually included with Python)
- `pyttsx3` (for voice announcements, optional but recommended)

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python gentletime.py
```

When you first run it, GentleTime will ask for your name. It remembers! 💫

## Files Created

GentleTime will automatically create:
- `gentletime_user.txt` — Saves your name
- `gentletime_history.txt` — Logs your activities with timestamps
- `gentletime_tasks.txt` — Stores your custom tasks

## Features

### Built-in Timers
- 📚 **Study Timer** — Custom duration, enter minutes in the input field
- 👁 **Eye Rest** — 20 seconds of rest for your eyes
- 🌙 **Nap Timer** — 20 minutes of power nap
- 🌸 **Exercise** — 30 minutes of workout time

### Custom Features
- ✨ **Custom Timer Button** — Quick access button on the left of the time input field
- ➕ **Create Custom Tasks** — Save your own timed activities (menu → Create Task)
- ⏸️ **Pause/Resume** — Pause your timer and come back to it later
- 🛑 **Stop** — Cancel any running timer
- 📊 **History** — View all your logged activities
- 📈 **Weekly Summary** — See your activity patterns

### Theme Switching
- 🎨 **Change Theme** — Menu button allows you to switch between themes
- Themes update instantly across the entire interface

## UI Layout

```
[☰ Menu] [Custom Name] [change name]
         
         00:00
         (Timer Display)
         
[✨] [Enter minutes...]
(Custom Timer Button) (Time Input Field)

[📚 Study] [👁 Eye Rest] [🌙 Nap] [🌸 Exercise]
[⭐ Custom Tasks...]

[Stop] [Pause] [History] [Summary]
```

## Controls

| Button | Action |
|--------|--------|
| **☰ Menu** | Open dropdown for theme switching and task creation |
| **✨** | Start custom timer with minutes from input field |
| **[Stop]** | Stop the currently running timer |
| **[Pause]** | Pause/resume the timer |
| **[History]** | View activity log |
| **[Summary]** | View weekly activity summary |

## Tips

1. **Study Timer** — Enter minutes in the input field, then click ✨ or use Study Timer button
2. **Voice Announcements** — Install `pyttsx3` for audio feedback when timers complete
3. **Custom Tasks** — Create reusable tasks via Menu → Create Task to save time
4. **Theme Switching** — Change themes anytime via Menu → Change Theme
5. **Activity Tracking** — All activities are automatically logged with timestamps

---

*Made with 💜 for gentle productivity*

