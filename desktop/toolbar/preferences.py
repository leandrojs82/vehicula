import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile


TOOL_IDS = ("conversor", "validador", "jsoncsv", "sqlin", "sqlait", "frota", "consolidador")
DEFAULTS = {"theme": "system", "favorites": [], "on_top": False,
            "x": None, "y": None, "expanded_width": 1120, "expanded_height": 760}


def user_directory():
    return Path(os.environ.get("VEHICULA_DATA_DIR") or
                (Path(os.environ.get("LOCALAPPDATA", Path.home())) / "Vehicula"))


def clean_preferences(values):
    clean = {**DEFAULTS, "favorites": []}
    if not isinstance(values, dict):
        return clean
    if values.get("theme") in ("system", "light", "dark"):
        clean["theme"] = values["theme"]
    favorites = values.get("favorites")
    if isinstance(favorites, list):
        clean["favorites"] = list(dict.fromkeys(item for item in favorites
                                               if isinstance(item, str) and item in TOOL_IDS))
    clean["on_top"] = values.get("on_top") is True
    for key in ("x", "y"):
        value = values.get(key)
        if type(value) is int and -100_000 <= value <= 100_000:
            clean[key] = value
    for key, minimum, maximum in (("expanded_width", 760, 7680), ("expanded_height", 400, 4320)):
        value = values.get(key)
        if type(value) is int and minimum <= value <= maximum:
            clean[key] = value
    return clean


def load_preferences(path):
    try:
        return clean_preferences(json.loads(Path(path).read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return clean_preferences({})


def save_preferences(path, preferences):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                prefix="settings-", suffix=".tmp", delete=False) as output:
            temporary = Path(output.name)
            json.dump(clean_preferences(preferences), output, ensure_ascii=False, indent=2)
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
