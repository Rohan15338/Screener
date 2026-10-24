import time
import sys
from .config import Config
from .storage import Storage
from .notifier import Notifier
from .tracker import ScreenTimeTracker, TrackerState

def format_seconds(seconds: float) -> str:
    s = int(seconds)
    hours = s // 3600
    minutes = (s % 3600) // 60
    secs = s % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"

def run_cli_mode():
    config = Config.load()
    storage = Storage()
    notifier = Notifier(
        sound_enabled=config.sound_enabled,
        notification_enabled=config.notification_enabled
    )
    tracker = ScreenTimeTracker(config, storage, notifier)

    print("=" * 60)
    print("   Screener - Terminal Background Monitor")
    print(f"   * Active Work Interval : {config.work_duration_minutes} minutes")
    print(f"   * Break Duration       : {config.break_duration_minutes} minutes")
    print(f"   * Idle Timeout         : {config.idle_threshold_seconds} seconds")
    print(f"   * Audio Alerts         : {'Enabled' if config.sound_enabled else 'Disabled'}")
    print(f"   * Windows Toast        : {'Enabled' if config.notification_enabled else 'Disabled'}")
    print("=" * 60)
    print("Press Ctrl+C to stop monitoring.\n")

    def on_break_triggered():
        print(f"\n[!] ALERT: Active screen time limit reached ({config.work_duration_minutes}m)!")
        print(f"[!] Please step away from the screen for {config.break_duration_minutes} minutes.")

    def on_break_completed():
        print(f"\n[*] Break finished! Welcome back. Screen time tracker reset.")

    tracker.on_break_trigger = on_break_triggered
    tracker.on_break_completed = on_break_completed

    try:
        while True:
            tracker.update()
            state_str = tracker.state.value
            active_str = format_seconds(tracker.session_active_seconds)
            left_str = format_seconds(tracker.get_seconds_until_break())
            idle_str = f"{int(tracker.current_idle_duration)}s"

            sys.stdout.write(
                f"\r[{state_str:^12}] Active: {active_str} | Next Break in: {left_str} | Idle: {idle_str}   "
            )
            sys.stdout.flush()
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\n\nStopped Screener monitor. Have a great day!")
