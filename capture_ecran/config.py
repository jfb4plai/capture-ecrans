"""Préférences de l'utilisateur (fichier JSON dans le profil, jamais dans le dossier du programme)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

SETTINGS_VERSION = 2   # 2 (v1.4.4) : « Capture simple » enregistrée en « editor » remise UNE fois sur « clipboard »
MIGRATION_NOTICE = ""  # texte à montrer à l'utilisateur après la migration (rempli par load())

DEFAULTS = {
    "settings_version": SETTINGS_VERSION,
    "hotkey_full": "ctrl+shift+f9",
    "hotkey_region": "ctrl+shift+f10",
    "hotkey_window": "ctrl+shift+f11",
    "hotkey_steps": "ctrl+shift+f12",
    "hotkey_quick": "ctrl+shift+f8",   # capture simple : zone → presse-papiers, sans pointeur ni halo (comme Windows+Maj+S)
    "hotkey_video": "ctrl+shift+f7",  # vidéo : démarre et arrête l'enregistrement
    "hotkey_show": "win+shift+q",   # rouvre la fenêtre du programme (s'il tourne déjà)
    "lnk_hotkey": False,            # touche de raccourci Ctrl+Alt+Q sur les raccourcis Windows (lance le programme)
    "steps_moment": "avant",     # avant | apres
    "logo_in_exports": False,
    "ffmpeg_path": "",
    "video_area": "region",      # region | full | window
    "video_limit_min": 0,        # arrêt automatique après N minutes ; 0 = pas de limite
    "video_mic": True,
    "video_system": True,        # enregistrer aussi le son de l'ordinateur (haut-parleurs / casque)           # enregistrer aussi le micro
    "shortcut_offered": False,   # la proposition de raccourci a déjà été faite
    "draw_cursor": True,
    "click_halo": True,
    "copy_clipboard": True,
    "after_capture": "editor",   # editor | paint | none
    "quick_after": "clipboard",  # capture simple : clipboard (presse-papiers seulement) | series (+ rangée dans la série) | editor (+ éditeur)
    "base_dir": "",
    "storage_confirmed": False,   # vrai une fois le choix du dossier fait au premier lancement
}


def config_path() -> Path:
    if sys.platform == "win32":
        root = Path(os.environ.get("APPDATA", Path.home()))
    else:
        root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return root / "CaptureEcranPLAI" / "config.json"


def default_base_dir() -> Path:
    from . import storage
    return storage.default_base_dir()


def load(path: Path | None = None) -> dict:
    path = path or config_path()
    global MIGRATION_NOTICE
    cfg = dict(DEFAULTS)
    raw: dict = {}
    try:
        data = json.loads(path.read_text("utf-8"))
        raw = data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        pass
    cfg.update({k: v for k, v in raw.items() if k in DEFAULTS})
    if not cfg["base_dir"]:
        cfg["base_dir"] = str(default_base_dir())
    # Un fichier existant sans numéro de version vient d'avant la v1.4.4 ; un fichier absent est une installation neuve.
    stored = raw.get("settings_version", 1) if raw else SETTINGS_VERSION
    if isinstance(stored, int) and stored < SETTINGS_VERSION:
        if cfg["quick_after"] == "editor":
            cfg["quick_after"] = "clipboard"
            MIGRATION_NOTICE = ("Capture simple remise sur « presse-papiers seulement » (nouveau réglage par défaut). "
                                "Vous pouvez la changer sous le bouton « Capture simple ».")
        cfg["settings_version"] = SETTINGS_VERSION
        save(cfg, path)  # une seule fois : ensuite le numéro de version est enregistré
    return cfg


def save(cfg: dict, path: Path | None = None) -> None:
    path = path or config_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), "utf-8")
    except OSError:
        pass
