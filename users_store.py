import json
import os
from datetime import datetime, timezone

USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")


def _load() -> dict:
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save(data: dict) -> None:
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def register_user(user) -> bool:
    """
    يسجل مستخدم تيليجرام (كائن telegram.User) أو يحدّث آخر ظهور له.
    يُرجع True إذا كان هذا أول تسجيل له.
    """
    data = _load()
    uid = str(user.id)
    is_new = uid not in data
    previous_joined_at = data.get(uid, {}).get("joined_at")

    data[uid] = {
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "joined_at": previous_joined_at or datetime.now(timezone.utc).isoformat(),
        "last_seen": datetime.now(timezone.utc).isoformat(),
    }
    _save(data)
    return is_new


def get_all_users() -> list:
    return list(_load().values())


def count_users() -> int:
    return len(_load())
