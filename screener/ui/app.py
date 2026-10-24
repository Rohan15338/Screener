import tkinter as tk
from tkinter import ttk, messagebox
import ctypes
from typing import Optional
from ..config import Config
from ..storage import Storage
from ..notifier import Notifier
from ..tracker import ScreenTimeTracker, TrackerState
from .break_window import BreakWindow
from .settings_dialog import SettingsDialog

def enable_windows_dpi_awareness():
    """Enables crisp per-monitor DPI rendering on Windows."""
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except Exception:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

def format_seconds(seconds: float) -> str:
    s = int(seconds)
    hours = s // 3600
    minutes = (s % 3600) // 60
    secs = s % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"

def format_human_duration(seconds: float) -> str:
    s = int(seconds)
    hours = s // 3600
    minutes = (s % 3600) // 60
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"

class ScreenerApp(tk.Tk):
    def __init__(self, config: Optional[Config] = None, storage: Optional[Storage] = None, start_hidden: bool = False):
        enable_windows_dpi_awareness()
        super().__init__()

        self.config = config or Config.load()
        self.storage = storage or Storage()
        self.notifier = Notifier(
            sound_enabled=self.config.sound_enabled,
            notification_enabled=self.config.notification_enabled
        )
        self.tracker = ScreenTimeTracker(self.config, self.storage, self.notifier)

        self.break_window: Optional[BreakWindow] = None
        self.settings_window: Optional[SettingsDialog] = None
        self.is_hidden_in_background = False

        self.title("Screener - Screen Time & Break Reminder")
        self.geometry("560x530")
        self.minsize(520, 480)
        self.configure(bg="#11111b")

        # Set taskbar/window icon
        from pathlib import Path
        ico = Path(__file__).resolve().parent.parent.parent / "screener.ico"
        if ico.exists():
            try:
                self.iconbitmap(str(ico))
            except Exception:
                pass

        self.protocol("WM_DELETE_WINDOW", self.on_close_requested)

        self._hook_tracker_events()
        self._build_ui()
        self._schedule_tick()

        if start_hidden:
            self.withdraw()
            self.is_hidden_in_background = True
            self.notifier.show_toast(
                "Screener Running in Background",
                f"Monitoring active screen time. We will alert you when it's time for a {self.config.break_duration_minutes}-minute break!"
            )

    def _hook_tracker_events(self):
        self.tracker.on_break_trigger = self._on_break_triggered
        self.tracker.on_break_completed = self._on_break_finished

    def _on_break_triggered(self):
        # Always bring up the break window even if main window is in background
        if not self.break_window or not self.break_window.winfo_exists():
            self.break_window = BreakWindow(self, self.tracker, on_closed=self._on_break_window_closed)
            self.break_window.lift()

    def _on_break_finished(self):
        pass

    def _on_break_window_closed(self):
        self.break_window = None

    def _build_ui(self):
        pad_x = 28

        # 1. Top Navbar / Header
        nav_frame = tk.Frame(self, bg="#11111b")
        nav_frame.pack(fill="x", padx=pad_x, pady=(18, 8))

        brand_frame = tk.Frame(nav_frame, bg="#11111b")
        brand_frame.pack(side="left")

        app_icon = tk.Label(brand_frame, text="🛡️", font=("Segoe UI Emoji", 18), bg="#11111b")
        app_icon.pack(side="left", padx=(0, 8))

        brand_title = tk.Label(brand_frame, text="Screener", font=("Segoe UI", 16, "bold"), fg="#ffffff", bg="#11111b")
        brand_title.pack(side="left")

        right_nav = tk.Frame(nav_frame, bg="#11111b")
        right_nav.pack(side="right")

        # Status badge (Active / Idle / On Break / Paused)
        self.status_badge = tk.Label(
            right_nav,
            text="● Active",
            font=("Segoe UI", 9, "bold"),
            fg="#10b981",
            bg="#1e1e2e",
            padx=12,
            pady=4
        )
        self.status_badge.pack(side="right")

        # Idle countdown text
        self.idle_label = tk.Label(
            self,
            text="Input active: monitoring mouse & keyboard",
            font=("Segoe UI", 8),
            fg="#64748b",
            bg="#11111b"
        )
        self.idle_label.pack(anchor="w", padx=pad_x, pady=(0, 10))

        # 2. Main Active Screen Time Card
        timer_card = tk.Frame(self, bg="#181825", highlightbackground="#313244", highlightthickness=1)
        timer_card.pack(fill="x", padx=pad_x, pady=6)

        timer_card_content = tk.Frame(timer_card, bg="#181825")
        timer_card_content.pack(fill="x", padx=20, pady=16)

        # Upper row: Target & Remaining
        meta_row = tk.Frame(timer_card_content, bg="#181825")
        meta_row.pack(fill="x")

        tk.Label(
            meta_row,
            text="ACTIVE SCREEN TIME",
            font=("Segoe UI", 9, "bold"),
            fg="#9399b2",
            bg="#181825"
        ).pack(side="left")

        self.next_break_label = tk.Label(
            meta_row,
            text=f"Next {self.config.break_duration_minutes}-min break in: {self.config.work_duration_minutes}:00",
            font=("Segoe UI", 9),
            fg="#a6adc8",
            bg="#181825"
        )
        self.next_break_label.pack(side="right")

        # Huge Active Screen Time Digits
        self.active_time_digits = tk.Label(
            timer_card_content,
            text="00:00:00",
            font=("Consolas", 42, "bold"),
            fg="#cdd6f4",
            bg="#181825"
        )
        self.active_time_digits.pack(pady=(8, 6))

        # Progress bar toward 5-minute break
        self.progress_canvas = tk.Canvas(timer_card_content, height=10, bg="#11111b", highlightthickness=0)
        self.progress_canvas.pack(fill="x", pady=(4, 6))

        # Progress percent text
        self.progress_text = tk.Label(
            timer_card_content,
            text="0% of current work interval",
            font=("Segoe UI", 8),
            fg="#6c7086",
            bg="#181825"
        )
        self.progress_text.pack()

        # 3. Today's Statistics Row
        stats_frame = tk.Frame(self, bg="#11111b")
        stats_frame.pack(fill="x", padx=pad_x, pady=(12, 14))

        self.card1 = self._create_stat_card(stats_frame, "🕒 Today's Active", "0m", "#89b4fa")
        self.card1.pack(side="left", expand=True, fill="both", padx=(0, 6))

        self.card2 = self._create_stat_card(stats_frame, "🌿 5m Breaks", "0", "#a6e3a1")
        self.card2.pack(side="left", expand=True, fill="both", padx=3)

        self.card3 = self._create_stat_card(stats_frame, "⏸ Away Time", "0m", "#fab387")
        self.card3.pack(side="left", expand=True, fill="both", padx=(6, 0))

        # 4. Action Buttons Toolbar
        action_bar = tk.Frame(self, bg="#11111b")
        action_bar.pack(fill="x", padx=pad_x, pady=6)

        # Break Now Button
        self.btn_break = tk.Button(
            action_bar,
            text="☕ Take 5m Break",
            font=("Segoe UI", 10, "bold"),
            bg="#10b981",
            fg="#ffffff",
            activebackground="#059669",
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=8,
            command=self.on_take_break_now
        )
        self.btn_break.pack(side="left", padx=(0, 6))

        # Pause / Resume Button
        self.btn_pause = tk.Button(
            action_bar,
            text="⏸ Pause",
            font=("Segoe UI", 10),
            bg="#313244",
            fg="#cdd6f4",
            activebackground="#45475a",
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=8,
            command=self.on_toggle_pause
        )
        self.btn_pause.pack(side="left", padx=(0, 6))

        # Send to Background Button
        self.btn_bg = tk.Button(
            action_bar,
            text="🗕 Background",
            font=("Segoe UI", 10),
            bg="#1e1e2e",
            fg="#38bdf8",
            activebackground="#313244",
            activeforeground="#38bdf8",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=8,
            command=self.hide_to_background
        )
        self.btn_bg.pack(side="left", padx=(0, 6))

        # Reset Session Button
        self.btn_reset = tk.Button(
            action_bar,
            text="🔄 Reset",
            font=("Segoe UI", 10),
            bg="#1e1e2e",
            fg="#a6adc8",
            activebackground="#313244",
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=8,
            pady=8,
            command=self.on_reset_session
        )
        self.btn_reset.pack(side="left")

        # Settings Button
        self.btn_settings = tk.Button(
            action_bar,
            text="⚙️ Settings",
            font=("Segoe UI", 10),
            bg="#1e1e2e",
            fg="#a6adc8",
            activebackground="#313244",
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=8,
            command=self.on_open_settings
        )
        self.btn_settings.pack(side="right")

        # 5. Bottom status & Quit option
        bottom_bar = tk.Frame(self, bg="#11111b")
        bottom_bar.pack(side="bottom", fill="x", padx=pad_x, pady=(0, 10))

        footer = tk.Label(
            bottom_bar,
            text="Runs in background • Auto-detects 5 min away to complete breaks",
            font=("Segoe UI", 8),
            fg="#585b70",
            bg="#11111b"
        )
        footer.pack(side="left")

        quit_btn = tk.Button(
            bottom_bar,
            text="Quit Screener",
            font=("Segoe UI", 8),
            fg="#f87171",
            bg="#11111b",
            activeforeground="#ef4444",
            activebackground="#11111b",
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self.quit_app
        )
        quit_btn.pack(side="right")

    def _create_stat_card(self, parent, title: str, default_val: str, color: str):
        card = tk.Frame(parent, bg="#181825", highlightbackground="#313244", highlightthickness=1)
        tk.Label(
            card,
            text=title,
            font=("Segoe UI", 8, "bold"),
            fg="#9399b2",
            bg="#181825"
        ).pack(anchor="w", padx=12, pady=(10, 2))

        val_label = tk.Label(
            card,
            text=default_val,
            font=("Segoe UI", 16, "bold"),
            fg=color,
            bg="#181825"
        )
        val_label.pack(anchor="w", padx=12, pady=(0, 10))
        card.val_label = val_label
        return card

    def _draw_progress(self, fraction: float):
        w = self.progress_canvas.winfo_width()
        if w <= 1:
            w = 460
        h = 10
        self.progress_canvas.delete("all")
        self.progress_canvas.create_rectangle(0, 0, w, h, fill="#1e1e2e", width=0)
        fill_w = max(0, min(w, int(w * fraction)))
        if fill_w > 0:
            if fraction >= 1.0:
                color = "#ef4444"
            elif fraction >= 0.8:
                color = "#f59e0b"
            else:
                color = "#6366f1"
            self.progress_canvas.create_rectangle(0, 0, fill_w, h, fill=color, width=0)

    def _schedule_tick(self):
        self.tracker.update()
        if not self.is_hidden_in_background:
            self._refresh_ui()
        self.after(1000, self._schedule_tick)

    def _refresh_ui(self):
        self.active_time_digits.config(text=format_seconds(self.tracker.session_active_seconds))

        seconds_left = self.tracker.get_seconds_until_break()
        self.next_break_label.config(
            text=f"Next {self.config.break_duration_minutes}-min break in: {format_seconds(seconds_left)}"
        )

        target = self.tracker.get_work_target_seconds()
        fraction = min(1.0, max(0.0, self.tracker.session_active_seconds / target)) if target > 0 else 0.0
        self._draw_progress(fraction)
        self.progress_text.config(text=f"{int(fraction * 100)}% of {self.config.work_duration_minutes}-minute work interval")

        if self.tracker.state == TrackerState.ACTIVE:
            self.status_badge.config(text="● Active", fg="#10b981", bg="#142e2b")
            idle_sec = int(self.tracker.current_idle_duration)
            if idle_sec > 5:
                idle_left = max(0, self.config.idle_threshold_seconds - idle_sec)
                self.idle_label.config(text=f"Last input {idle_sec}s ago (Pauses tracking in {idle_left}s)")
            else:
                self.idle_label.config(text="Active screen time tracking running")
            self.btn_pause.config(text="⏸ Pause")

        elif self.tracker.state == TrackerState.IDLE:
            self.status_badge.config(text="⏸ Idle / Away", fg="#f59e0b", bg="#3b2b18")
            idle_sec = int(self.tracker.current_idle_duration)
            break_target = int(self.tracker.get_break_target_seconds())
            away_left = max(0, break_target - idle_sec)
            self.idle_label.config(text=f"Away for {format_seconds(idle_sec)} (Auto-resets break in {format_seconds(away_left)})")

        elif self.tracker.state == TrackerState.ON_BREAK:
            self.status_badge.config(text="☕ On Break", fg="#38bdf8", bg="#152b3c")
            rem = int(self.tracker.break_remaining_seconds)
            self.idle_label.config(text=f"Break in progress: {format_seconds(rem)} remaining")

        elif self.tracker.state == TrackerState.BREAK_DUE:
            self.status_badge.config(text="⚠️ Break Due", fg="#ef4444", bg="#3c151c")
            self.idle_label.config(text=f"Please take your {self.config.break_duration_minutes}-minute break away from screen!")

        elif self.tracker.state == TrackerState.PAUSED:
            self.status_badge.config(text="⏹ Paused", fg="#94a3b8", bg="#262837")
            self.idle_label.config(text="Screen time tracker is paused")
            self.btn_pause.config(text="▶ Resume")

        today_stats = self.storage.get_today_stats()
        self.card1.val_label.config(text=format_human_duration(today_stats.get("active_seconds", 0)))
        self.card2.val_label.config(text=str(today_stats.get("breaks_completed", 0)))
        self.card3.val_label.config(text=format_human_duration(today_stats.get("idle_seconds", 0)))

    def hide_to_background(self):
        """Hides the main window to run completely in the background."""
        self.withdraw()
        self.is_hidden_in_background = True
        self.notifier.show_toast(
            "Screener is in Background",
            f"Active tracking continues. You'll be alerted when it's time for your {self.config.break_duration_minutes}-min break!"
        )

    def show_from_background(self):
        """Restores window from background."""
        self.deiconify()
        self.is_hidden_in_background = False
        self.lift()
        self.attributes("-topmost", True)
        self.after_idle(self.attributes, "-topmost", False)
        self.focus_force()
        self._refresh_ui()

    def on_close_requested(self):
        if self.config.close_to_background:
            self.hide_to_background()
        else:
            self.quit_app()

    def quit_app(self):
        self.destroy()

    def on_take_break_now(self):
        self.tracker.start_break()
        if not self.break_window or not self.break_window.winfo_exists():
            self.break_window = BreakWindow(self, self.tracker, on_closed=self._on_break_window_closed)
            self.break_window.lift()

    def on_toggle_pause(self):
        if self.tracker.state == TrackerState.PAUSED:
            self.tracker.resume_tracking()
        else:
            self.tracker.pause_tracking()

    def on_reset_session(self):
        if messagebox.askyesno("Reset Session", "Do you want to reset the current active screen time session?"):
            self.tracker.reset_session()

    def on_open_settings(self):
        if not self.settings_window or not self.settings_window.winfo_exists():
            self.settings_window = SettingsDialog(self, self.config, on_saved=self._on_settings_saved)

    def _on_settings_saved(self, updated_config: Config):
        self.config = updated_config
        self.notifier.sound_enabled = self.config.sound_enabled
        self.notifier.notification_enabled = self.config.notification_enabled
        self._refresh_ui()
