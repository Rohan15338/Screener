import json
from pathlib import Path
from datetime import date
from typing import Dict, Any

STORAGE_FILE = Path(__file__).resolve().parent.parent / "daily_stats.json"

class Storage:
    def __init__(self, file_path: Path = STORAGE_FILE):
        self.file_path = file_path
        self._data: Dict[str, Dict[str, Any]] = self._load()

    def _load(self) -> Dict[str, Dict[str, Any]]:
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save(self):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
        except Exception as e:
            print(f"Failed to save stats: {e}")

    def _today_key(self) -> str:
        return date.today().isoformat()

    def get_today_stats(self) -> Dict[str, Any]:
        key = self._today_key()
        if key not in self._data:
            self._data[key] = {
                "active_seconds": 0.0,
                "idle_seconds": 0.0,
                "breaks_completed": 0,
                "breaks_skipped": 0,
                "breaks_postponed": 0,
            }
        return self._data[key]

    def add_active_time(self, seconds: float):
        stats = self.get_today_stats()
        stats["active_seconds"] = round(stats.get("active_seconds", 0.0) + seconds, 1)
        self._save()

    def add_idle_time(self, seconds: float):
        stats = self.get_today_stats()
        stats["idle_seconds"] = round(stats.get("idle_seconds", 0.0) + seconds, 1)
        self._save()

    def record_break_completed(self):
        stats = self.get_today_stats()
        stats["breaks_completed"] = stats.get("breaks_completed", 0) + 1
        self._save()

    def record_break_skipped(self):
        stats = self.get_today_stats()
        stats["breaks_skipped"] = stats.get("breaks_skipped", 0) + 1
        self._save()

    def record_break_postponed(self):
        stats = self.get_today_stats()
        stats["breaks_postponed"] = stats.get("breaks_postponed", 0) + 1
        self._save()
