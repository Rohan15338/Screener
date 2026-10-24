import sys
import os
import threading
import subprocess
import time
from typing import Optional

try:
    import winsound
except ImportError:
    winsound = None

class Notifier:
    def __init__(self, sound_enabled: bool = True, notification_enabled: bool = True):
        self.sound_enabled = sound_enabled
        self.notification_enabled = notification_enabled

    def play_break_alert_sound(self):
        """Plays a gentle chime reminding the user it's break time."""
        if not self.sound_enabled:
            return

        def _play():
            if sys.platform == "win32" and winsound:
                try:
                    winsound.Beep(587, 180)
                    time.sleep(0.05)
                    winsound.Beep(740, 200)
                    time.sleep(0.05)
                    winsound.Beep(880, 350)
                except Exception:
                    try:
                        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                    except Exception:
                        pass
            elif sys.platform == "darwin":
                # macOS system sounds
                for sound in ["/System/Library/Sounds/Ping.aiff", "/System/Library/Sounds/Hero.aiff"]:
                    if os.path.exists(sound):
                        subprocess.run(["afplay", sound], capture_output=True)
                        break
            elif sys.platform.startswith("linux"):
                # Linux system sounds or bell
                for sound in ["/usr/share/sounds/freedesktop/stereo/bell.oga", "/usr/share/sounds/freedesktop/stereo/complete.oga"]:
                    if os.path.exists(sound):
                        subprocess.run(["paplay", sound], capture_output=True)
                        break
                else:
                    sys.stdout.write("\a")
                    sys.stdout.flush()

        threading.Thread(target=_play, daemon=True).start()

    def play_break_completed_sound(self):
        """Plays a celebratory chime when the break is finished."""
        if not self.sound_enabled:
            return

        def _play():
            if sys.platform == "win32" and winsound:
                try:
                    winsound.Beep(523, 150)
                    winsound.Beep(659, 150)
                    winsound.Beep(784, 180)
                    winsound.Beep(1046, 350)
                except Exception:
                    try:
                        winsound.MessageBeep(winsound.MB_ICONASTERISK)
                    except Exception:
                        pass
            elif sys.platform == "darwin":
                for sound in ["/System/Library/Sounds/Glass.aiff", "/System/Library/Sounds/Purr.aiff"]:
                    if os.path.exists(sound):
                        subprocess.run(["afplay", sound], capture_output=True)
                        break
            elif sys.platform.startswith("linux"):
                sys.stdout.write("\a")
                sys.stdout.flush()

        threading.Thread(target=_play, daemon=True).start()

    def show_toast(self, title: str, message: str):
        """Displays native system notification across Windows, macOS, and Linux."""
        if not self.notification_enabled:
            return

        def _send():
            if sys.platform == "win32":
                safe_title = title.replace("'", "''")
                safe_msg = message.replace("'", "''")
                ps_script = f"""
                try {{
                    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
                    [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
                    $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
                    $textNodes = $template.GetElementsByTagName('text')
                    $textNodes.Item(0).AppendChild($template.CreateTextNode('{safe_title}')) | Out-Null
                    $textNodes.Item(1).AppendChild($template.CreateTextNode('{safe_msg}')) | Out-Null
                    $toast = [Windows.UI.Notifications.ToastNotification]::new($template)
                    $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Screener')
                    $notifier.Show($toast)
                }} catch {{}}
                """
                try:
                    subprocess.run(
                        ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_script],
                        capture_output=True,
                        timeout=5,
                        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
                    )
                except Exception:
                    pass
            elif sys.platform == "darwin":
                # macOS AppleScript notification
                safe_title = title.replace('"', '\\"')
                safe_msg = message.replace('"', '\\"')
                cmd = f'display notification "{safe_msg}" with title "{safe_title}"'
                try:
                    subprocess.run(["osascript", "-e", cmd], capture_output=True, timeout=5)
                except Exception:
                    pass
            elif sys.platform.startswith("linux"):
                # Linux notify-send
                try:
                    subprocess.run(["notify-send", title, message], capture_output=True, timeout=5)
                except Exception:
                    pass

        threading.Thread(target=_send, daemon=True).start()
