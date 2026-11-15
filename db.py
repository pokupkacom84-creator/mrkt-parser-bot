import json
import os

DB_FILE = "db.json"

class Database:
    def __init__(self):
        if not os.path.exists(DB_FILE):
            self._save({"users": {}})

    def _load(self) -> dict:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, data: dict):
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _get_user(self, user_id: int) -> dict:
        data = self._load()
        uid = str(user_id)
        if uid not in data["users"]:
            data["users"][uid] = {
                "notifications": False,
                "filter": {},
                "tracked": []
            }
            self._save(data)
        return data["users"][uid]

    # ─── Уведомления ──────────────────────────────────────
    def set_notifications(self, user_id: int, state: bool):
        data = self._load()
        uid = str(user_id)
        self._get_user(user_id)  # создать если нет
        data = self._load()
        data["users"][uid]["notifications"] = state
        self._save(data)

    def get_subscribed_users(self) -> list[tuple[int, dict]]:
        data = self._load()
        result = []
        for uid, udata in data["users"].items():
            if udata.get("notifications"):
                result.append((int(uid), udata.get("filter", {})))
        return result

    # ─── Фильтры ──────────────────────────────────────────
    def get_filter(self, user_id: int) -> dict:
        return self._get_user(user_id).get("filter", {})

    def set_filter(self, user_id: int, key: str, value):
        data = self._load()
        uid = str(user_id)
        self._get_user(user_id)
        data = self._load()
        data["users"][uid]["filter"][key] = value
        self._save(data)

    def reset_filter(self, user_id: int):
        data = self._load()
        uid = str(user_id)
        self._get_user(user_id)
        data = self._load()
        data["users"][uid]["filter"] = {}
        self._save(data)

    # ─── Трекер ───────────────────────────────────────────
    def add_tracked(self, user_id: int, collection: str, number: str):
        data = self._load()
        uid = str(user_id)
        self._get_user(user_id)
        data = self._load()
        entry = {"collection": collection, "number": number, "price": "—"}
        tracked = data["users"][uid]["tracked"]
        # не дублировать
        for t in tracked:
            if t["collection"] == collection and t["number"] == number:
                return
        tracked.append(entry)
        self._save(data)

    def get_tracked(self, user_id: int) -> list:
        return self._get_user(user_id).get("tracked", [])