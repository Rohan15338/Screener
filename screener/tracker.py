import time
import sys
import os
import subprocess
import ctypes
from enum import Enum
from typing import Callable, Optional
from .config import Config
from .storage import Storage
from .notifier import Notifier

if sys.platform == "win32":
    from ctypes import wintypes

    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.UINT),
            ("dwTime", wintypes.DWORD),
        ]

def get_idle_time_seconds() -> float:
    """Returns the seconds since the last user input across Windows, macOS, and Linux."""
    if sys.platform == "win32":
        try:
            lii = LASTINPUTINFO()
            lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
            if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
                tick_count = ctypes.windll.kernel32.GetTickCount64()
                return max(0.0, (tick_count - lii.dwTime) / 1000.0)
        except Exception:
            return 0.0
    elif sys.platform == "darwin":
        # macOS native idle time via ioreg (in seconds)
        try:
            cmd = "ioreg -c IOHIDSystem | awk '/HIDIdleTime/ {print $NF/1000000000; exit}'"
            out = subprocess.check_output(cmd, shell=True, text=True).strip()
            return float(out) if out else 0.0
        except Exception:
            return 0.0
    elif sys.platform.startswith("linux"):
        # Linux X11 idle time via xprintidle (in milliseconds)
        try:
            out = subprocess.check_output(["xprintidle"], text=True).strip()
            return float(out) / 1000.0
        except Exception:
            return 0.0
    return 0.0

class TrackerState(Enum):
    ACTIVE = "Active"
    IDLE = "Idle / Away"
    BREAK_DUE = "Break Due"
    ON_BREAK = "On Break"
    PAUSED = "Paused"

class ScreenTimeTracker:
    def __init__(self, config: Config, storage: Storage, notifier: Notifier):
        self.config = config
        self.storage = storage
        self.notifier = notifier

        self.state = TrackerState.ACTIVE
        self.session_active_seconds: float = 0.0
        self.session_idle_seconds: float = 0.0
        self.current_idle_duration: float = 0.0

        # Break timer state
        self.break_remaining_seconds: float = 0.0
        self.pre_warned: bool = False
        self.daily_limit_warned: bool = False
        self.postpone_count: int = 0

        # Callbacks for UI updates
        self.on_tick: Optional[Callable[["ScreenTimeTracker"], None]] = None
        self.on_state_change: Optional[Callable[[TrackerState], None]] = None
        self.on_break_trigger: Optional[Callable[[], None]] = None
        self.on_break_completed: Optional[Callable[[], None]] = None

        self._last_update_time: float = time.time()
        self._is_running: bool = False

    def get_work_target_seconds(self) -> float:
        return self.config.work_duration_minutes * 60.0

    def get_break_target_seconds(self) -> float:
        return self.config.break_duration_minutes * 60.0

    def get_seconds_until_break(self) -> float:
        target = self.get_work_target_seconds()
        return max(0.0, target - self.session_active_seconds)

    def set_state(self, new_state: TrackerState):
        if self.state != new_state:
            self.state = new_state
            if self.on_state_change:
                self.on_state_change(new_state)

    def update(self):
        """Called every second by the UI / event loop."""
        now = time.time()
        dt = min(2.0, max(0.0, now - self._last_update_time))
        self._last_update_time = now

        if self.state == TrackerState.PAUSED:
            if self.on_tick:
                self.on_tick(self)
            return

        self.current_idle_duration = get_idle_time_seconds()
        is_user_idle = self.current_idle_duration >= self.config.idle_threshold_seconds

        # --- Handling Break State ---
        if self.state == TrackerState.ON_BREAK:
            self.break_remaining_seconds = max(0.0, self.break_remaining_seconds - dt)

            # Auto-detect if user fulfilled 5 minutes away from screen
            if self.config.auto_complete_break and self.current_idle_duration >= self.get_break_target_seconds():
                self.finish_break(auto_detected=True)
                return

            if self.break_remaining_seconds <= 0:
                self.finish_break(auto_detected=False)
                return

            if self.on_tick:
                self.on_tick(self)
            return

        # --- Handling Break Due State ---
        if self.state == TrackerState.BREAK_DUE:
            # If user genuinely stepped away during warning for the full break duration
            if self.config.auto_complete_break and self.current_idle_duration >= self.get_break_target_seconds():
                self.finish_break(auto_detected=True)
                return

            if self.on_tick:
                self.on_tick(self)
            return

        # --- Normal Active / Idle Tracking ---
        if is_user_idle:
            self.set_state(TrackerState.IDLE)
            self.session_idle_seconds += dt
            self.storage.add_idle_time(dt)

            # Check if user was idle for a full break duration while idle
            # If so, they've naturally taken a 5-minute break away!
            if self.config.auto_complete_break and self.current_idle_duration >= self.get_break_target_seconds():
                if self.session_active_seconds > 0:
                    self.session_active_seconds = 0.0
                    self.pre_warned = False
                    self.storage.record_break_completed()
                    self.notifier.play_break_completed_sound()
                    self.notifier.show_toast(
                        "Break Detected!",
                        f"You were away for {self.config.break_duration_minutes} min. Active screen time reset."
                    )
        else:
            self.set_state(TrackerState.ACTIVE)
            self.session_active_seconds += dt
            self.storage.add_active_time(dt)

            # Pre-warning check (e.g. 1 minute before)
            work_target = self.get_work_target_seconds()
            pre_warning_sec = self.config.pre_warning_minutes * 60.0
            if (work_target - self.session_active_seconds) <= pre_warning_sec and not self.pre_warned:
                self.pre_warned = True
                self.notifier.show_toast(
                    "Upcoming Break",
                    f"1 minute remaining before your {self.config.break_duration_minutes}-minute screen break."
                )

            # Reached work target! Time for break
            if self.session_active_seconds >= work_target:
                self.trigger_break()

        # Daily limit check
        if self.config.daily_limit_hours > 0 and not self.daily_limit_warned:
            today_active = self.storage.get_today_stats().get("active_seconds", 0.0)
            if today_active >= self.config.daily_limit_hours * 3600.0:
                self.daily_limit_warned = True
                self.notifier.play_break_alert_sound()
                self.notifier.show_toast(
                    "Daily Limit Reached",
                    f"You have reached your daily screen limit of {self.config.daily_limit_hours}h today."
                )

        if self.on_tick:
            self.on_tick(self)

    def trigger_break(self):
        """Called when active screen time target is reached."""
        self.set_state(TrackerState.BREAK_DUE)
        self.notifier.play_break_alert_sound()
        self.notifier.show_toast(
            "Screen Time Alert!",
            f"You've been active for {self.config.work_duration_minutes} min. Please take a {self.config.break_duration_minutes}-minute break away from screen."
        )
        if self.on_break_trigger:
            self.on_break_trigger()

    def start_break(self):
        """User actively confirms/starts the break countdown."""
        self.set_state(TrackerState.ON_BREAK)
        self.break_remaining_seconds = self.get_break_target_seconds()
        self.notifier.show_toast(
            "Break Started",
            f"Take {self.config.break_duration_minutes} minutes away from the screen. Rest your eyes!"
        )

    def postpone_break(self, minutes: int = 5):
        """Postpone break by given minutes."""
        self.postpone_count += 1
        # Subtract equivalent seconds from active time to grant extra time
        extra_seconds = minutes * 60.0
        self.session_active_seconds = max(0.0, self.get_work_target_seconds() - extra_seconds)
        self.pre_warned = False
        self.storage.record_break_postponed()
        self.set_state(TrackerState.ACTIVE)

    def skip_break(self):
        """User skips current break."""
        self.session_active_seconds = 0.0
        self.pre_warned = False
        self.storage.record_break_skipped()
        self.set_state(TrackerState.ACTIVE)

    def finish_break(self, auto_detected: bool = False):
        """Break is completed."""
        self.session_active_seconds = 0.0
        self.pre_warned = False
        self.break_remaining_seconds = 0.0
        self.postpone_count = 0
        self.storage.record_break_completed()
        self.notifier.play_break_completed_sound()

        msg = "Welcome back! 5-minute break completed. Your screen time counter has been reset." if not auto_detected else \
              "Welcome back! You were away from your screen for 5 minutes. Ready to work!"
        self.notifier.show_toast("Break Complete 🎉", msg)

        self.set_state(TrackerState.ACTIVE)
        if self.on_break_completed:
            self.on_break_completed()

    def pause_tracking(self):
        self.set_state(TrackerState.PAUSED)

    def resume_tracking(self):
        self.set_state(TrackerState.ACTIVE)
        self._last_update_time = time.time()

    def reset_session(self):
        self.session_active_seconds = 0.0
        self.session_idle_seconds = 0.0
        self.break_remaining_seconds = 0.0
        self.pre_warned = False
        self.set_state(TrackerState.ACTIVE)
