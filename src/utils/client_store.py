import os
import json
from datetime import datetime
from typing import Dict, List

BASE_DIR = "data/clients"

def _client_dir(client_id: str) -> str:
    return os.path.join(BASE_DIR, client_id)

def ensure_client_dirs(client_id: str) -> Dict[str, str]:
    base = _client_dir(client_id)
    paths = {
        "base": base,
        "profile": os.path.join(base, "profile"),
        "portfolios": os.path.join(base, "portfolios"),
        "reports": os.path.join(base, "reports"),
    }
    for p in paths.values():
        os.makedirs(p, exist_ok=True)
    return paths

def list_clients() -> List[Dict]:
    if not os.path.exists(BASE_DIR):
        return []
    out = []
    for cid in sorted(os.listdir(BASE_DIR)):
        meta_path = os.path.join(_client_dir(cid), "client.json")
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    out.append(json.load(f))
            except:
                out.append({"client_id": cid, "name": cid})
        else:
            out.append({"client_id": cid, "name": cid})
    return out

def save_client_meta(client_id: str, name: str, email: str = "", notes: str = "") -> Dict:
    ensure_client_dirs(client_id)
    meta = {
        "client_id": client_id,
        "name": name,
        "email": email,
        "notes": notes,
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }
    meta_path = os.path.join(_client_dir(client_id), "client.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    return meta

def append_history(client_id: str, event: Dict) -> None:
    ensure_client_dirs(client_id)
    row = {"ts": datetime.utcnow().isoformat() + "Z", **event}
    hist_path = os.path.join(_client_dir(client_id), "history.jsonl")
    with open(hist_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

def read_history(client_id: str, limit: int = 50) -> List[Dict]:
    hist_path = os.path.join(_client_dir(client_id), "history.jsonl")
    if not os.path.exists(hist_path):
        return []
    rows = []
    with open(hist_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except:
                    pass
    return rows[-limit:]

def save_uploaded_bytes(dst_path: str, b: bytes) -> None:
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    with open(dst_path, "wb") as f:
        f.write(b)
