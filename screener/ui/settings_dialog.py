import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional
from ..config import Config
from ..startup import is_startup_enabled, enable_startup, disable_startup

class SettingsDialog(tk.Toplevel):
    def __init__(self, master: tk.Tk, config: Config, on_saved: Optional[Callable[[Config], None]] = None):
        super().__init__(master)
        self.config = config
        self.on_saved = on_saved

        self.title("Settings - Screener")
        self.geometry("460x610")
        self.resizable(False, False)
        self.configure(bg="#181824")
        self.attributes("-topmost", True)

        self._center_window()
        self._build_ui()

    def _center_window(self):
        self.update_idletasks()
        w = 460
        h = 570
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self):
        pad_x = 24

        # Title
        title_lbl = tk.Label(
            self,
            text="Preferences & System Background",
            font=("Segoe UI", 14, "bold"),
            fg="#f8fafc",
            bg="#181824"
        )
        title_lbl.pack(anchor="w", padx=pad_x, pady=(20, 14))

        # Card container
        card = tk.Frame(self, bg="#232336", highlightbackground="#334155", highlightthickness=1)
        card.pack(fill="x", padx=pad_x, pady=(0, 16))

        # 1. Work Duration
        row1 = tk.Frame(card, bg="#232336")
        row1.pack(fill="x", padx=16, pady=(14, 8))
        tk.Label(row1, text="Active Screen Time Limit:", font=("Segoe UI", 10), fg="#e2e8f0", bg="#232336").pack(side="left")
        self.work_var = tk.IntVar(value=self.config.work_duration_minutes)
        work_spin = ttk.Spinbox(row1, from_=5, to=180, increment=5, textvariable=self.work_var, width=5)
        work_spin.pack(side="right")
        tk.Label(row1, text="mins", font=("Segoe UI", 9), fg="#94a3b8", bg="#232336").pack(side="right", padx=(0, 6))

        # 2. Break Duration
        row2 = tk.Frame(card, bg="#232336")
        row2.pack(fill="x", padx=16, pady=8)
        tk.Label(row2, text="Break Duration Away:", font=("Segoe UI", 10), fg="#e2e8f0", bg="#232336").pack(side="left")
        self.break_var = tk.IntVar(value=self.config.break_duration_minutes)
        break_spin = ttk.Spinbox(row2, from_=1, to=30, increment=1, textvariable=self.break_var, width=5)
        break_spin.pack(side="right")
        tk.Label(row2, text="mins", font=("Segoe UI", 9), fg="#94a3b8", bg="#232336").pack(side="right", padx=(0, 6))

        # 3. Daily Screen Time Limit
        row3 = tk.Frame(card, bg="#232336")
        row3.pack(fill="x", padx=16, pady=8)
        tk.Label(row3, text="Daily Screen Limit (0 = off):", font=("Segoe UI", 10), fg="#e2e8f0", bg="#232336").pack(side="left")
        self.daily_limit_var = tk.DoubleVar(value=self.config.daily_limit_hours)
        daily_spin = ttk.Spinbox(row3, from_=0.0, to=24.0, increment=0.5, textvariable=self.daily_limit_var, width=5)
        daily_spin.pack(side="right")
        tk.Label(row3, text="hours", font=("Segoe UI", 9), fg="#94a3b8", bg="#232336").pack(side="right", padx=(0, 6))

        # 4. Idle Sensitivity
        row4 = tk.Frame(card, bg="#232336")
        row4.pack(fill="x", padx=16, pady=8)
        tk.Label(row4, text="Idle Sensitivity (inactivity timeout):", font=("Segoe UI", 10), fg="#e2e8f0", bg="#232336").pack(side="left")
        self.idle_var = tk.IntVar(value=self.config.idle_threshold_seconds)
        idle_spin = ttk.Spinbox(row4, from_=15, to=600, increment=15, textvariable=self.idle_var, width=5)
        idle_spin.pack(side="right")
        tk.Label(row4, text="secs", font=("Segoe UI", 9), fg="#94a3b8", bg="#232336").pack(side="right", padx=(0, 6))

        # Divider
        tk.Frame(card, height=1, bg="#334155").pack(fill="x", padx=16, pady=10)

        # 4. Sound alert toggle
        self.sound_var = tk.BooleanVar(value=self.config.sound_enabled)
        tk.Checkbutton(
            card,
            text="Play chime alerts for breaks",
            variable=self.sound_var,
            font=("Segoe UI", 9),
            fg="#e2e8f0",
            bg="#232336",
            activebackground="#232336",
            activeforeground="#e2e8f0",
            selectcolor="#181824"
        ).pack(anchor="w", padx=16, pady=3)

        # 5. Notification toggle
        self.notif_var = tk.BooleanVar(value=self.config.notification_enabled)
        tk.Checkbutton(
            card,
            text="Show Windows toast notifications",
            variable=self.notif_var,
            font=("Segoe UI", 9),
            fg="#e2e8f0",
            bg="#232336",
            activebackground="#232336",
            activeforeground="#e2e8f0",
            selectcolor="#181824"
        ).pack(anchor="w", padx=16, pady=3)

        # 6. Auto-complete break when idle
        self.auto_break_var = tk.BooleanVar(value=self.config.auto_complete_break)
        tk.Checkbutton(
            card,
            text="Auto-complete break if away for 5 minutes",
            variable=self.auto_break_var,
            font=("Segoe UI", 9),
            fg="#e2e8f0",
            bg="#232336",
            activebackground="#232336",
            activeforeground="#e2e8f0",
            selectcolor="#181824"
        ).pack(anchor="w", padx=16, pady=3)

        # 7. Close to background
        self.bg_var = tk.BooleanVar(value=self.config.close_to_background)
        tk.Checkbutton(
            card,
            text="Close button hides to background (keeps tracking)",
            variable=self.bg_var,
            font=("Segoe UI", 9),
            fg="#e2e8f0",
            bg="#232336",
            activebackground="#232336",
            activeforeground="#e2e8f0",
            selectcolor="#181824"
        ).pack(anchor="w", padx=16, pady=3)

        # 8. Start on Windows boot
        self.boot_var = tk.BooleanVar(value=is_startup_enabled() or self.config.start_on_boot)
        tk.Checkbutton(
            card,
            text="Start automatically on Windows boot (silent background)",
            variable=self.boot_var,
            font=("Segoe UI", 9, "bold"),
            fg="#60a5fa",
            bg="#232336",
            activebackground="#232336",
            activeforeground="#60a5fa",
            selectcolor="#181824"
        ).pack(anchor="w", padx=16, pady=(3, 14))

        # Action Buttons
        btn_box = tk.Frame(self, bg="#181824")
        btn_box.pack(fill="x", padx=pad_x, pady=4)

        save_btn = tk.Button(
            btn_box,
            text="Save Settings",
            font=("Segoe UI", 10, "bold"),
            bg="#6366f1",
            fg="#ffffff",
            activebackground="#4f46e5",
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=8,
            command=self._save
        )
        save_btn.pack(side="right", padx=(8, 0))

        cancel_btn = tk.Button(
            btn_box,
            text="Cancel",
            font=("Segoe UI", 10),
            bg="#27273a",
            fg="#cbd5e1",
            activebackground="#33334d",
            activeforeground="#f8fafc",
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=8,
            command=self.destroy
        )
        cancel_btn.pack(side="right")

    def _save(self):
        try:
            self.config.work_duration_minutes = max(1, self.work_var.get())
            self.config.break_duration_minutes = max(1, self.break_var.get())
            self.config.daily_limit_hours = max(0.0, round(self.daily_limit_var.get(), 1))
            self.config.idle_threshold_seconds = max(5, self.idle_var.get())
            self.config.sound_enabled = self.sound_var.get()
            self.config.notification_enabled = self.notif_var.get()
            self.config.auto_complete_break = self.auto_break_var.get()
            self.config.close_to_background = self.bg_var.get()
            self.config.start_on_boot = self.boot_var.get()

            # Handle Windows Startup
            if self.config.start_on_boot:
                enable_startup(self.config.work_duration_minutes, self.config.break_duration_minutes)
            else:
                disable_startup()

            self.config.save()

            if self.on_saved:
                self.on_saved(self.config)
        except Exception as e:
            print(f"Error saving settings: {e}")

        self.destroy()
