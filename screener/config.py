import json
from pathlib import Path
from dataclasses import dataclass, asdict

CONFIG_FILE = Path(__file__).resolve().parent.parent / "screener_config.json"

@dataclass
class Config:
    work_duration_minutes: int = 35       # Active screen time before break prompt (35 mins)
    break_duration_minutes: int = 5       # 5 min break away from the screen
    idle_threshold_seconds: int = 60      # Seconds of inactivity before considered idle
    pre_warning_minutes: int = 1          # Warning before break
    sound_enabled: bool = True            # Play sound alerts
    notification_enabled: bool = True     # Windows toast notifications
    auto_complete_break: bool = True      # Auto-complete break when idle for full break duration
    strict_mode: bool = False             # If true, reminder stays on top and dims background
    close_to_background: bool = True      # Minimizing or closing hides to background
    start_on_boot: bool = False           # Automatically launch when Windows starts
    daily_limit_hours: float = 0.0        # Daily total screen time limit (0.0 = disabled)

    @classmethod
    def load(cls) -> "Config":
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})
            except Exception:
                return cls()
        return cls()

    def save(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(asdict(self), f, indent=4)
        except Exception as e:
            print(f"Failed to save config: {e}")
