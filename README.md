# Screener 🖥️🌿

> **Active Screen Time Tracker & 5-Minute Break Reminder**

**Screener** tracks your **active screen time** (detecting real mouse and keyboard engagement on Windows) and warns you to take a **5-minute break away from your screen** to protect your eyesight, posture, and mental focus.

---

## ✨ Key Features

1. **Active Screen Time Tracking (Input-Aware)**
   - Tracks only when you are actively interacting with your computer via Windows API (`GetLastInputInfo`).
   - Pauses screen time counting automatically when you step away, lock your screen, or stay idle for more than 60 seconds (customizable).

2. **5-Minute Break Warning System**
   - **Audio Chimes**: Plays a gentle, pleasant ascending harmonic chime when break time arrives.
   - **Windows Toast Notifications**: Displays native Windows notifications reminding you to step away.
   - **Interactive Break Reminder Window**: An on-screen card featuring a 5-minute live countdown timer, postpone options, and eye-strain reduction tips.

3. **Smart Inactivity Auto-Detection**
   - Simply walk away from your desk! If Screener detects 5 minutes of no input, it automatically marks your break as completed, plays a welcome-back chime, and resets your active screen time counter.

4. **Ergonomic & Eye Relief Guidance**
   - Incorporates the **20-20-20 rule** (look 20 feet away for 20 seconds).
   - Rotating tips for shoulder rolls, deep breathing, wrist stretches, and hydration.

5. **Live Dashboard & Daily History**
   - Live digital timer showing current active screen time and countdown to the next break.
   - Daily statistics: Today's active screen time, breaks completed, and idle/away time stored in `daily_stats.json`.
   - Action controls: *Take Break Now*, *Pause/Resume*, *Reset Session*, *Settings*.

6. **Zero Dependencies**
   - Built entirely on the standard Python library (`tkinter`, `ctypes`, `winsound`). No external package installation required.

---

## 📦 Standalone App Deployment (No Python Required)

Screener is compiled as a standalone Windows executable (`dist\Screener.exe`):

1. **Run Instantly**: Double-click [dist\Screener.exe](file:///c:/Users/rohan/OneDrive/Documents/Projects/Screener/dist/Screener.exe).
2. **Install Desktop & Start Menu Shortcut**: Double-click [create_desktop_shortcut.bat](file:///c:/Users/rohan/OneDrive/Documents/Projects/Screener/create_desktop_shortcut.bat).
3. **Rebuild Anytime**: Double-click [build_exe.bat](file:///c:/Users/rohan/OneDrive/Documents/Projects/Screener/build_exe.bat).
4. **Distribute**: You can copy `dist\Screener.exe` to any Windows 10/11 computer and it runs immediately without installing Python or dependencies!

---

## 🚀 Quick Start

### 1. Launch in the Background (Completely Silent)
Double-click `start_background.vbs`, or run:
```powershell
pythonw run.py --background
```
- Runs 100% silently with **no black terminal / command window**.
- Tracks keyboard/mouse input quietly in the background.
- When active screen time reaches your limit (e.g., 25 mins), it plays an alert chime, sends a Windows toast notification, and pops up the **5-minute Break Window**.
- Re-running `python run.py` or double-clicking `start_screener.bat` automatically brings the existing background window to the front without spawning duplicate processes!

### 2. Launch the Graphical Dashboard
```powershell
python run.py
```
- Click the **🗕 Background** button or close `X` to send it into the background.

### 3. Launch on Windows Startup (Automatic on PC Boot)
1. In Screener, click **⚙️ Settings**.
2. Check **"Start automatically on Windows boot (silent background)"**.
3. Click **Save Settings**. Screener will now automatically run silently whenever you log in!

### 4. Stopping Background Screener
Double-click `stop_background.bat`, or click **Quit Screener** in the bottom right corner of the dashboard.

---

## ⚙️ Configuration

Settings can be adjusted directly inside the GUI by clicking **⚙️ Settings**, or by editing `screener_config.json`:

| Setting | Default | Description |
|---|---|---|
| `work_duration_minutes` | `35` | Minutes of continuous active screen time before a break warning |
| `break_duration_minutes` | `5` | Length of the break away from screen |
| `idle_threshold_seconds` | `60` | Inactivity threshold before switching to "Idle / Away" |
| `sound_enabled` | `true` | Play audible chimes |
| `notification_enabled` | `true` | Show native Windows toast notifications |
| `auto_complete_break` | `true` | Auto-complete break when away for 5 minutes |

---

## 🧪 Running Tests

To run the unit tests:
```powershell
python -m unittest discover tests
```

---

## 📁 Project Structure

```
Screener/
├── screener/
│   ├── config.py           # User preferences and JSON persistence
│   ├── storage.py          # Daily active & break statistics
│   ├── notifier.py         # Windows toast notifications & audio chimes
│   ├── tracker.py          # Windows idle detection & active state engine
│   ├── cli.py              # Terminal-based background monitor
│   └── ui/
│       ├── app.py          # Modern dark dashboard (Tkinter, DPI-aware)
│       ├── break_window.py # 5-minute countdown reminder with ergonomic tips
│       └── settings_dialog.py # Settings configuration dialog
├── tests/
│   └── test_tracker.py     # Automated unit tests
├── run.py                  # CLI & GUI entrypoint
├── requirements.txt        # Dependencies notice
└── README.md               # Documentation
```
