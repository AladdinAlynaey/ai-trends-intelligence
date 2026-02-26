"""
Thread-safe JSON file data store with encryption support.
All data persistence is via JSON files — no database.
"""
import json
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from cryptography.fernet import Fernet

_locks: dict[str, threading.RLock] = {}
_global_lock = threading.Lock()


def _get_lock(filepath: str) -> threading.RLock:
    with _global_lock:
        if filepath not in _locks:
            _locks[filepath] = threading.RLock()
        return _locks[filepath]


def _ensure_dir(filepath: str) -> None:
    dirpath = os.path.dirname(filepath)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)


# ── Core Read / Write ─────────────────────────────

def read_json(filepath: str, default=None):
    """Read a JSON file, returning *default* if it does not exist."""
    lock = _get_lock(filepath)
    with lock:
        if not os.path.exists(filepath):
            return default if default is not None else []
        try:
            with open(filepath, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except (json.JSONDecodeError, IOError):
            return default if default is not None else []


def write_json(filepath: str, data) -> None:
    """Atomically write data to a JSON file."""
    lock = _get_lock(filepath)
    with lock:
        _ensure_dir(filepath)
        tmp = filepath + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False, default=str)
        os.replace(tmp, filepath)


# ── Encrypted Read / Write ────────────────────────

def read_encrypted_json(filepath: str, key: str, default=None):
    """Read and decrypt a Fernet-encrypted JSON file."""
    lock = _get_lock(filepath)
    with lock:
        if not os.path.exists(filepath):
            return default if default is not None else []
        try:
            f = Fernet(key.encode() if isinstance(key, str) else key)
            with open(filepath, "rb") as fh:
                decrypted = f.decrypt(fh.read())
            return json.loads(decrypted)
        except Exception:
            return default if default is not None else []


def write_encrypted_json(filepath: str, key: str, data) -> None:
    """Encrypt and write data to a file."""
    lock = _get_lock(filepath)
    with lock:
        _ensure_dir(filepath)
        f = Fernet(key.encode() if isinstance(key, str) else key)
        raw = json.dumps(data, indent=2, ensure_ascii=False, default=str).encode()
        tmp = filepath + ".tmp"
        with open(tmp, "wb") as fh:
            fh.write(f.encrypt(raw))
        os.replace(tmp, filepath)


# ── CRUD Helpers ──────────────────────────────────

def generate_id() -> str:
    return uuid.uuid4().hex


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_item(filepath: str, item: dict) -> dict:
    """Append an item (with auto id + timestamps) to a JSON list file."""
    items = read_json(filepath, [])
    item.setdefault("id", generate_id())
    item.setdefault("created_at", utcnow())
    item.setdefault("updated_at", utcnow())
    items.append(item)
    write_json(filepath, items)
    return item


def update_item(filepath: str, item_id: str, updates: dict) -> dict | None:
    """Update an item by id in a JSON list file."""
    items = read_json(filepath, [])
    for i, item in enumerate(items):
        if item.get("id") == item_id:
            items[i].update(updates)
            items[i]["updated_at"] = utcnow()
            write_json(filepath, items)
            return items[i]
    return None


def delete_item(filepath: str, item_id: str) -> bool:
    """Delete an item by id from a JSON list file."""
    items = read_json(filepath, [])
    filtered = [it for it in items if it.get("id") != item_id]
    if len(filtered) == len(items):
        return False
    write_json(filepath, filtered)
    return True


def find_item(filepath: str, key: str, value) -> dict | None:
    """Find the first item where item[key] == value."""
    for item in read_json(filepath, []):
        if item.get(key) == value:
            return item
    return None


def find_items(filepath: str, key: str, value) -> list:
    """Find all items where item[key] == value."""
    return [it for it in read_json(filepath, []) if it.get(key) == value]


# ── Audit Log ─────────────────────────────────────

def append_audit_log(audit_dir: str, event: str, user_id: str = "",
                     details: str = "", ip: str = "") -> None:
    """Append-only audit log. One file per day."""
    os.makedirs(audit_dir, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filepath = os.path.join(audit_dir, f"audit_{today}.json")
    entry = {
        "timestamp": utcnow(),
        "event": event,
        "user_id": user_id,
        "details": details,
        "ip": ip,
    }
    lock = _get_lock(filepath)
    with lock:
        entries = []
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as fh:
                    entries = json.load(fh)
            except (json.JSONDecodeError, IOError):
                entries = []
        entries.append(entry)
        with open(filepath, "w", encoding="utf-8") as fh:
            json.dump(entries, fh, indent=2, ensure_ascii=False, default=str)
