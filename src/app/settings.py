"""应用设置持久化——最近文件、主题等"""

import json, os

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".editpdfpro")
CONFIG_FILE = os.path.join(CONFIG_DIR, "settings.json")


def _ensure_dir():
    os.makedirs(CONFIG_DIR, exist_ok=True)


def load() -> dict:
    """加载设置"""
    defaults = {"recent_files": [], "theme": "light", "last_zoom": 100}
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return {**defaults, **json.load(f)}
    except:
        pass
    return defaults


def save(data: dict):
    """保存设置"""
    _ensure_dir()
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except:
        pass


def add_recent(filepath: str):
    """添加最近文件"""
    cfg = load()
    recent = cfg.get("recent_files", [])
    if filepath in recent:
        recent.remove(filepath)
    recent.insert(0, filepath)
    cfg["recent_files"] = recent[:10]  # 最多10个
    save(cfg)


def get_recent() -> list[str]:
    return load().get("recent_files", [])


def save_theme(theme: str):
    cfg = load()
    cfg["theme"] = theme
    save(cfg)


def get_theme() -> str:
    return load().get("theme", "light")
