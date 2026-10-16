"""Accès aux fichiers embarqués (logo, icône), en développement comme dans l'exécutable PyInstaller."""
from __future__ import annotations

import sys
from pathlib import Path


def resource_path(name: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    p = base / "assets" / name
    if not p.exists():  # exécutable --onedir : les données sont sous _internal/capture_ecran/assets
        p = base / "capture_ecran" / "assets" / name
    return p
