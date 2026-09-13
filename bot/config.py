"""ArchiveStream Otonom Bot - config ve yol yonetimi."""
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"
PLUGIN_DIR = OUTPUT_DIR / "cloudstream-plugin"
DATA_DIR = OUTPUT_DIR / "data"

PAT_FILE = BASE_DIR / ".git-pat"
SETTINGS_FILE = BASE_DIR / "settings.json"
HEAL_FILE = DATA_DIR / "healed_selectors.json"

DEFAULT_SETTINGS = {
    "git_user": "",
    "git_repo": "",
    "auto_push": True,
    "rows_per_collection": 40,
}


def ensure_dirs():
    for d in (OUTPUT_DIR, PLUGIN_DIR, DATA_DIR):
        d.mkdir(parents=True, exist_ok=True)


def load_settings() -> dict:
    if SETTINGS_FILE.exists():
        try:
            return {**DEFAULT_SETTINGS, **json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))}
        except Exception:
            pass
    return dict(DEFAULT_SETTINGS)


def save_settings(s: dict):
    SETTINGS_FILE.write_text(json.dumps(s, indent=2, ensure_ascii=False), encoding="utf-8")


def load_heal_memory() -> dict:
    if HEAL_FILE.exists():
        try:
            return json.loads(HEAL_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_heal_memory(mem: dict):
    HEAL_FILE.write_text(json.dumps(mem, indent=2, ensure_ascii=False), encoding="utf-8")


def get_pat() -> str:
    """GitHub PAT'i ilk calistirmada ister, .git-pat dosyasinda saklar (gitignore'lu)."""
    if PAT_FILE.exists():
        p = PAT_FILE.read_text(encoding="utf-8").strip()
        if p:
            return p
    import getpass

    print()
    print("[GITHUB] GitHub Personal Access Token (PAT) gerekiyor.")
    print("         https://github.com/settings/tokens -> 'Generate new token (classic)'")
    print("         'repo' yetkisi yeterli. Token ekranda gorunmez, .git-pat dosyasinda saklanir.")
    pat = getpass.getpass("PAT: ").strip()
    if not pat:
        raise RuntimeError("PAT bos birakildi.")
    PAT_FILE.write_text(pat, encoding="utf-8")
    return pat
