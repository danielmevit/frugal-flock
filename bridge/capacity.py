import json
import os
import fcntl
import math
import re
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

MAX_FILE_SIZE = 1024 * 1024  # 1MB limit for readings file

def is_valid_label(label: str) -> bool:
    if not isinstance(label, str) or not label:
        return False
    if len(label) > 64:
        return False
    return bool(re.match(r'^[\w\-]+$', label))

def validate_percent(p: Any) -> float:
    if isinstance(p, bool):
        raise ValueError("percent cannot be boolean")
    if not isinstance(p, (int, float)):
        raise ValueError("percent must be a number")
    if math.isnan(p) or math.isinf(p):
        raise ValueError("percent must be finite")
    if not (0 <= p <= 100):
        raise ValueError("percent must be between 0 and 100")
    return float(p)

def validate_timestamp(ts_str: str) -> str:
    try:
        dt = datetime.fromisoformat(ts_str)
        if dt.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")
        now = datetime.now(timezone.utc)
        if dt > now + timedelta(days=365):
            raise ValueError("timestamp unreasonably far in future")
        return dt.isoformat()
    except Exception as e:
        raise ValueError(f"invalid timestamp {ts_str}: {e}")

class CapacityStore:
    def __init__(self, project_path: str):
        self.project_path = os.path.abspath(project_path)
        self.readings_dir = os.path.join(self.project_path, "coord", "capacity")
        self.readings_path = os.path.join(self.readings_dir, "readings.json")
        
        # Prevent path escapes
        if not self.readings_path.startswith(os.path.abspath(os.path.join(self.project_path, "coord"))):
            raise ValueError("Invalid project path")

    def _ensure_dir(self):
        os.makedirs(self.readings_dir, exist_ok=True)

    def record(self, group: str, window: str, window_minutes: int, remaining_percent: float, observed_at: str, reset_at: Optional[str] = None):
        if not is_valid_label(group):
            raise ValueError("invalid group label")
        if not is_valid_label(window):
            raise ValueError("invalid window label")
        if isinstance(window_minutes, bool) or not isinstance(window_minutes, int) or window_minutes <= 0:
            raise ValueError("window_minutes must be positive integer")
        
        remaining_percent = validate_percent(remaining_percent)
        observed_at = validate_timestamp(observed_at)
        if reset_at is not None:
            reset_at = validate_timestamp(reset_at)
        
        self._ensure_dir()
        lock_file = self.readings_path + ".lock"
        with open(lock_file, 'a+') as f_lock:
            fcntl.flock(f_lock, fcntl.LOCK_EX)
            try:
                data = {"schema_version": 1, "groups": {}}
                if os.path.exists(self.readings_path):
                    with open(self.readings_path, 'r') as f_read:
                        try:
                            content = f_read.read()
                            if len(content) <= MAX_FILE_SIZE:
                                parsed = json.loads(content)
                                if parsed.get("schema_version") == 1:
                                    data = parsed
                        except Exception:
                            pass

                if "groups" not in data or not isinstance(data["groups"], dict):
                    data["groups"] = {}

                if group not in data["groups"] or not isinstance(data["groups"][group], dict):
                    data["groups"][group] = {}

                record_data = {
                    "source": "manual",
                    "window_minutes": window_minutes,
                    "remaining_percent": remaining_percent,
                    "observed_at": observed_at
                }
                if reset_at:
                    record_data["reset_at"] = reset_at

                existing = data["groups"][group].get(window)
                if existing and existing.get("observed_at") == observed_at:
                    raise ValueError("duplicate record for same observation time")

                data["groups"][group][window] = record_data

                tmp_path = self.readings_path + ".tmp"
                with open(tmp_path, 'w') as f_tmp:
                    json.dump(data, f_tmp)
                os.replace(tmp_path, self.readings_path)
            finally:
                fcntl.flock(f_lock, fcntl.LOCK_UN)

    def show(self, group: Optional[str] = None, max_age_seconds: int = 900) -> Dict[str, Any]:
        data = {"schema_version": 1, "groups": {}}
        if os.path.exists(self.readings_path):
            try:
                with open(self.readings_path, 'r') as f:
                    content = f.read()
                    if len(content) <= MAX_FILE_SIZE:
                        parsed = json.loads(content)
                        if parsed.get("schema_version") == 1:
                            data = parsed
            except Exception:
                pass
        
        now = datetime.now(timezone.utc)
        result = {}
        groups_to_check = [group] if group else data.get("groups", {}).keys()

        for g in groups_to_check:
            if not is_valid_label(g):
                result[g] = {"status": "Unknown"}
                continue
                
            group_data = data.get("groups", {}).get(g, {})
            result[g] = {}
            for w, w_data in group_data.items():
                status = "unknown"
                age = 0.0
                try:
                    obs_time = datetime.fromisoformat(w_data["observed_at"])
                    age = (now - obs_time).total_seconds()
                    
                    if age < 0:
                        status = "invalid"
                        age = 0.0
                    elif age <= max_age_seconds:
                        status = "fresh"
                    else:
                        status = "stale"
                    
                    if w_data.get("reset_at"):
                        reset_time = datetime.fromisoformat(w_data["reset_at"])
                        if now >= reset_time:
                            status = "expired"
                except Exception:
                    status = "invalid"

                res_window = {
                    "source": w_data.get("source", "manual"),
                    "window_minutes": w_data.get("window_minutes"),
                    "observed_at": w_data.get("observed_at"),
                    "age_seconds": max(0, float(age)),
                    "status": status
                }
                
                if "reset_at" in w_data:
                    res_window["reset_at"] = w_data["reset_at"]

                if status == "fresh":
                    res_window["usable_remaining_percent"] = w_data.get("remaining_percent")
                else:
                    res_window["last_remaining_percent"] = w_data.get("remaining_percent")
                
                result[g][w] = res_window
            
            if not result[g]:
                result[g] = {"status": "Unknown"}

        return result
