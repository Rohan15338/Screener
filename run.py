import sys
import argparse
from screener.config import Config
from screener.storage import Storage
from screener.notifier import Notifier
from screener.instance import SingleInstance
from screener.ui.app import ScreenerApp
from screener.cli import run_cli_mode

def main():
    parser = argparse.ArgumentParser(
        description="Screener - Active Screen Time Tracker & 5-Minute Break Reminder"
    )
    parser.add_argument(
        "--cli", "--headless",
        action="store_true",
        help="Run in headless / command line terminal mode"
    )
    parser.add_argument(
        "--background", "--minimized",
        action="store_true",
        help="Start immediately in the background without opening the main window"
    )
    parser.add_argument(
        "--work-mins",
        type=int,
        default=None,
        help="Override active work minutes before break (default: 35)"
    )
    parser.add_argument(
        "--break-mins",
        type=int,
        default=None,
        help="Override break duration in minutes away from screen (default: 5)"
    )
    parser.add_argument(
        "--daily-limit",
        type=float,
        default=None,
        help="Set total daily screen time limit in hours (e.g. 4.0)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run a quick 5-second test verification"
    )

    args = parser.parse_args()

    config = Config.load()
    if args.work_mins:
        config.work_duration_minutes = args.work_mins
    if args.break_mins:
        config.break_duration_minutes = args.break_mins
    if args.daily_limit is not None:
        config.daily_limit_hours = args.daily_limit

    if args.test:
        print("[*] Running Screener diagnostic test...")
        notifier = Notifier(sound_enabled=True, notification_enabled=True)
        print("[*] Testing sound alert...")
        notifier.play_break_alert_sound()
        print("[*] Testing Windows toast notification...")
        notifier.show_toast("Screener Test", "This is a test notification from Screener.")
        print("[+] Diagnostic test completed successfully!")
        return

    if args.cli:
        run_cli_mode()
        return

    # Single-instance enforcement:
    # If already running in the background, this will unhide the background instance and exit.
    single_inst = SingleInstance()
    app = None

    def on_show_request():
        if app:
            app.after(0, app.show_from_background)

    is_primary = single_inst.check_or_register(on_show_requested=on_show_request)
    if not is_primary:
        print("[*] Screener is already running in the background. Brought window to front.")
        sys.exit(0)

    try:
        app = ScreenerApp(config=config, start_hidden=args.background)
        app.mainloop()
    finally:
        single_inst.close()

if __name__ == "__main__":
    main()
