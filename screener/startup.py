import os
import sys
from pathlib import Path

STARTUP_DIR = Path(os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"))
STARTUP_VBS = STARTUP_DIR / "Screener.vbs"

def get_pythonw_path() -> str:
    """Returns the path to pythonw.exe (windowless python runner on Windows)."""
    current_python = Path(sys.executable)
    pythonw = current_python.parent / "pythonw.exe"
    if pythonw.exists():
        return str(pythonw)
    return str(current_python)

def is_startup_enabled() -> bool:
    """Checks if Screener is scheduled to start on Windows boot."""
    return STARTUP_VBS.exists()

def enable_startup(work_mins: int = None, break_mins: int = None) -> bool:
    """Creates a silent VBS launcher in the Windows Startup folder."""
    try:
        STARTUP_DIR.mkdir(parents=True, exist_ok=True)
        pythonw = get_pythonw_path()
        run_py = Path(__file__).resolve().parent.parent / "run.py"

        extra_args = "--background"
        if work_mins:
            extra_args += f" --work-mins {work_mins}"
        if break_mins:
            extra_args += f" --break-mins {break_mins}"

        if getattr(sys, "frozen", False):
            target_cmd = f'"{sys.executable}" {extra_args}'
        else:
            dist_exe = Path(__file__).resolve().parent.parent / "dist" / "Screener.exe"
            if dist_exe.exists():
                target_cmd = f'"{dist_exe}" {extra_args}'
            else:
                pythonw = get_pythonw_path()
                run_py = Path(__file__).resolve().parent.parent / "run.py"
                target_cmd = f'"{pythonw}" "{run_py}" {extra_args}'

        # VBScript to launch completely hidden without any console window
        vbs_content = (
            'Set WshShell = CreateObject("WScript.Shell")\n'
            f'WshShell.Run """{target_cmd}""", 0, False\n'
        )

        with open(STARTUP_VBS, "w", encoding="utf-8") as f:
            f.write(vbs_content)
        return True
    except Exception as e:
        print(f"Failed to enable startup: {e}")
        return False

def disable_startup() -> bool:
    """Removes the launcher from the Windows Startup folder."""
    try:
        if STARTUP_VBS.exists():
            STARTUP_VBS.unlink()
        return True
    except Exception as e:
        print(f"Failed to disable startup: {e}")
        return False
