import tkinter as tk
from tkinter import ttk
import random
from typing import Optional, Callable
from pathlib import Path
from ..tracker import ScreenTimeTracker, TrackerState

TIPS = [
    "👀 20-20-20 Rule: Look at an object at least 20 feet away for 20 seconds to relax your eye muscles.",
    "🚶 Step away from your desk! Take a short stroll or walk around the room.",
    "💧 Drink a glass of water. Staying hydrated reduces mental fatigue and eye strain.",
    "🙆 Roll your shoulders backwards 5 times and gently tilt your neck left and right.",
    "🪟 Gaze out of the window into the distant horizon to reduce near-focus stress.",
    "👐 Interlock your fingers and stretch your arms forward and overhead.",
    "🌬️ Take 3 slow, deep belly breaths: inhale for 4 seconds, hold for 4, exhale for 6.",
]

class BreakWindow(tk.Toplevel):
    def __init__(self, master: tk.Tk, tracker: ScreenTimeTracker, on_closed: Optional[Callable[[], None]] = None):
        super().__init__(master)
        self.tracker = tracker
        self.on_closed = on_closed
        self.tip_index = random.randint(0, len(TIPS) - 1)
        self.tip_timer = 0

        self.title("Break Reminder - Screener")
        self.geometry("520x460")
        self.resizable(False, False)
        self.configure(bg="#181824")

        ico = Path(__file__).resolve().parent.parent.parent / "screener.ico"
        if ico.exists():
            try:
                self.iconbitmap(str(ico))
            except Exception:
                pass

        # Keep on top
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self.on_close_clicked)

        self._center_window()
        self._build_ui()
        self._update_loop()

    def _center_window(self):
        self.update_idletasks()
        w = 520
        h = 460
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self):
        # Header banner
        header_frame = tk.Frame(self, bg="#181824")
        header_frame.pack(fill="x", padx=24, pady=(24, 8))

        self.icon_label = tk.Label(header_frame, text="🌿", font=("Segoe UI Emoji", 32), bg="#181824")
        self.icon_label.pack()

        self.title_label = tk.Label(
            header_frame,
            text=f"Time for a {self.tracker.config.break_duration_minutes}-Minute Screen Break",
            font=("Segoe UI", 16, "bold"),
            fg="#f8fafc",
            bg="#181824"
        )
        self.title_label.pack(pady=(4, 2))

        self.subtitle_label = tk.Label(
            header_frame,
            text="Step away from your screen, rest your eyes, and stretch.",
            font=("Segoe UI", 10),
            fg="#94a3b8",
            bg="#181824"
        )
        self.subtitle_label.pack()

        # Big Countdown Display
        timer_card = tk.Frame(self, bg="#232336", highlightbackground="#334155", highlightthickness=1)
        timer_card.pack(fill="x", padx=32, pady=12)

        self.timer_label = tk.Label(
            timer_card,
            text="05:00",
            font=("Consolas", 42, "bold"),
            fg="#38bdf8",
            bg="#232336"
        )
        self.timer_label.pack(pady=(12, 2))

        self.state_subtext = tk.Label(
            timer_card,
            text="Remaining away time",
            font=("Segoe UI", 9),
            fg="#64748b",
            bg="#232336"
        )
        self.state_subtext.pack(pady=(0, 6))

        # Progress bar
        self.progress_canvas = tk.Canvas(timer_card, height=8, bg="#1e1e2e", highlightthickness=0)
        self.progress_canvas.pack(fill="x", padx=20, pady=(0, 14))

        # Ergonomic Tip Box
        self.tip_frame = tk.Frame(self, bg="#1e1e2e", highlightbackground="#2e2e42", highlightthickness=1)
        self.tip_frame.pack(fill="x", padx=32, pady=8)

        self.tip_label = tk.Label(
            self.tip_frame,
            text=TIPS[self.tip_index],
            font=("Segoe UI", 9, "italic"),
            fg="#cbd5e1",
            bg="#1e1e2e",
            wraplength=440,
            justify="center"
        )
        self.tip_label.pack(padx=16, pady=12)

        # Buttons Row
        self.btn_frame = tk.Frame(self, bg="#181824")
        self.btn_frame.pack(fill="x", padx=32, pady=(12, 16))

        self.action_btn = tk.Button(
            self.btn_frame,
            text="☕ Start 5-Min Timer",
            font=("Segoe UI", 10, "bold"),
            bg="#10b981",
            fg="#ffffff",
            activebackground="#059669",
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=8,
            command=self.on_action_clicked
        )
        self.action_btn.pack(side="left", expand=True, fill="x", padx=(0, 4))

        self.postpone_btn = tk.Button(
            self.btn_frame,
            text="⏳ Postpone 5m",
            font=("Segoe UI", 10),
            bg="#334155",
            fg="#f8fafc",
            activebackground="#475569",
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=8,
            command=self.on_postpone_clicked
        )
        self.postpone_btn.pack(side="left", expand=True, fill="x", padx=4)

        self.skip_btn = tk.Button(
            self.btn_frame,
            text="⏭ Skip",
            font=("Segoe UI", 10),
            bg="#27273a",
            fg="#94a3b8",
            activebackground="#33334d",
            activeforeground="#cbd5e1",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=8,
            command=self.on_skip_clicked
        )
        self.skip_btn.pack(side="left", expand=True, fill="x", padx=(4, 0))

        # Bottom note about auto-detection
        self.footer_label = tk.Label(
            self,
            text="💡 Tip: Simply walk away! Screener auto-detects 5 min of inactivity and automatically closes this window.",
            font=("Segoe UI", 8),
            fg="#64748b",
            bg="#181824",
            wraplength=460,
            justify="center"
        )
        self.footer_label.pack(side="bottom", pady=(0, 12))

    def _draw_progress_bar(self, fraction: float):
        w = self.progress_canvas.winfo_width()
        if w <= 1:
            w = 400
        h = 8
        self.progress_canvas.delete("all")
        # Background bar
        self.progress_canvas.create_rectangle(0, 0, w, h, fill="#1e1e2e", width=0)
        # Filled bar
        fill_w = max(0, min(w, int(w * fraction)))
        if fill_w > 0:
            color = "#10b981" if fraction >= 1.0 else "#38bdf8"
            self.progress_canvas.create_rectangle(0, 0, fill_w, h, fill=color, width=0)

    def _update_loop(self):
        if not self.winfo_exists():
            return

        # Rotate tip every 25 seconds
        self.tip_timer += 1
        if self.tip_timer >= 25:
            self.tip_timer = 0
            self.tip_index = (self.tip_index + 1) % len(TIPS)
            self.tip_label.config(text=TIPS[self.tip_index])

        # Check tracker state
        if self.tracker.state == TrackerState.ON_BREAK:
            rem = int(self.tracker.break_remaining_seconds)
            mins = rem // 60
            secs = rem % 60
            self.timer_label.config(text=f"{mins:02d}:{secs:02d}", fg="#10b981")
            self.state_subtext.config(text="Break in progress - Enjoy your rest!")
            self.action_btn.config(text="✓ Complete Early", bg="#334155", command=self.on_complete_early)

            total_break = self.tracker.get_break_target_seconds()
            progress = 1.0 - (rem / total_break) if total_break > 0 else 1.0
            self._draw_progress_bar(progress)

        elif self.tracker.state == TrackerState.BREAK_DUE:
            rem = int(self.tracker.get_break_target_seconds())
            mins = rem // 60
            secs = rem % 60
            self.timer_label.config(text=f"{mins:02d}:{secs:02d}", fg="#f59e0b")
            self.state_subtext.config(text="Active screen time threshold reached!")
            self.action_btn.config(text="☕ Start 5-Min Timer", bg="#10b981", command=self.on_action_clicked)
            self._draw_progress_bar(0.0)

        elif self.tracker.state == TrackerState.ACTIVE and self.tracker.session_active_seconds < 10:
            # 5-minute break completed! Automatically disappear window immediately!
            self.destroy()
            if self.on_closed:
                self.on_closed()
            return

        self.after(500, self._update_loop)

    def on_action_clicked(self):
        if self.tracker.state != TrackerState.ON_BREAK:
            self.tracker.start_break()

    def on_complete_early(self):
        self.tracker.finish_break(auto_detected=False)
        self.destroy()
        if self.on_closed:
            self.on_closed()

    def on_postpone_clicked(self):
        self.tracker.postpone_break(minutes=5)
        self.destroy()
        if self.on_closed:
            self.on_closed()

    def on_skip_clicked(self):
        self.tracker.skip_break()
        self.destroy()
        if self.on_closed:
            self.on_closed()

    def on_close_clicked(self):
        self.destroy()
        if self.on_closed:
            self.on_closed()
