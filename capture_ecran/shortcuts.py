"""Raccourcis Windows : bureau, menu Démarrer, lancement automatique à l'ouverture de session.

Création via WScript.Shell (PowerShell, rien à installer). Les chemins passent par des variables d'environnement
plutôt que dans le texte du script : aucun souci de guillemets ou d'accents.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from . import storage

LNK_NAME = "Capture d'écran PLAI.lnk"
MANUAL_HELP = ("Faites-le à la main : clic droit sur « Capture-ecran-PLAI.exe » › Afficher d'autres options › "
               "Envoyer vers › Bureau (créer un raccourci).")

_PS_CREATE = r'''
$ErrorActionPreference = "Stop"
$l = (New-Object -ComObject WScript.Shell).CreateShortcut($env:CEP_LNK)
$l.TargetPath = $env:CEP_TARGET
$l.Arguments = $env:CEP_ARGS
$l.WorkingDirectory = $env:CEP_WD
$l.Description = $env:CEP_DESC
if ($env:CEP_ICON) { $l.IconLocation = $env:CEP_ICON }
$l.WindowStyle = [int]$env:CEP_STYLE
$l.Save()
'''
_PS_READ = r'''
$l = (New-Object -ComObject WScript.Shell).CreateShortcut($env:CEP_LNK)
"$($l.TargetPath)|$($l.Arguments)|$($l.WorkingDirectory)|$($l.IconLocation)|$($l.WindowStyle)"
'''


def desktop_lnk() -> Path:
    return storage.desktop_dir() / LNK_NAME


def start_menu_lnk() -> Path:
    base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    return base / "Microsoft" / "Windows" / "Start Menu" / "Programs" / LNK_NAME


def startup_lnk() -> Path:
    base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    return base / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup" / LNK_NAME


def target_command() -> tuple[str, str, str]:
    """(programme, arguments, dossier de travail) pour relancer CE programme."""
    if getattr(sys, "frozen", False):
        exe = Path(sys.executable)
        return str(exe), "", str(exe.parent)
    py = Path(sys.executable)
    pyw = py.with_name("pythonw.exe")  # sans fenêtre noire
    root = Path(__file__).resolve().parent.parent
    return str(pyw if pyw.is_file() else py), "-m capture_ecran", str(root)


def location_warning(exe: str | Path | None = None) -> str | None:
    """Avertit si le programme est lancé depuis un endroit fragile : un raccourci y casserait tôt ou tard."""
    low = str(exe or sys.executable).lower().replace("/", "\\")
    if "\\temp\\" in low or "temp1_" in low or "\\appdata\\local\\temp" in low:
        return ("Le programme tourne depuis un dossier TEMPORAIRE (probablement ouvert depuis le zip). "
                "Extrayez d'abord le zip (clic droit › Extraire tout…), déplacez le dossier extrait à un endroit durable "
                "(par exemple Documents), relancez-le, puis créez le raccourci.")
    if "\\downloads\\" in low or "\\téléchargements\\" in low or "\\telechargements\\" in low:
        return ("Le programme se trouve dans « Téléchargements ». Si vous videz ce dossier, le raccourci cessera de "
                "fonctionner : déplacez d'abord le dossier extrait à un endroit durable (par exemple Documents).")
    return None


def build_env(lnk: Path, target: str, args: str, workdir: str, icon: str | None, minimized: bool) -> dict:
    env = dict(os.environ)
    env.update({"CEP_LNK": str(lnk), "CEP_TARGET": target, "CEP_ARGS": args, "CEP_WD": workdir,
                "CEP_DESC": "Capture d'écran PLAI : menus déroulants, annotations, vidéo sous-titrée",
                "CEP_ICON": f"{icon},0" if icon else "", "CEP_STYLE": "7" if minimized else "1"})
    return env


def _run_ps(script: str, env: dict) -> subprocess.CompletedProcess:
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
                          env=env, capture_output=True, text=True, timeout=60, creationflags=flags)


def create(lnk: Path, minimized: bool = False) -> None:
    """Crée (ou remplace) le raccourci. Lève OSError avec un message utile si impossible."""
    if sys.platform != "win32":
        raise OSError("Les raccourcis ne sont disponibles que sous Windows.")
    target, args, workdir = target_command()
    if minimized:
        args = (args + " --reduit").strip()
    icon = target if getattr(sys, "frozen", False) else None
    lnk = Path(lnk)
    lnk.parent.mkdir(parents=True, exist_ok=True)
    try:
        r = _run_ps(_PS_CREATE, build_env(lnk, target, args, workdir, icon, minimized))
    except (OSError, subprocess.TimeoutExpired) as e:
        raise OSError(f"PowerShell indisponible ({e}). {MANUAL_HELP}") from e
    if r.returncode != 0 or not lnk.is_file():
        raise OSError(f"Création impossible ({(r.stderr or '').strip()[:200] or 'raison inconnue'}). {MANUAL_HELP}")


def remove(lnk: Path) -> None:
    Path(lnk).unlink(missing_ok=True)


def read(lnk: Path) -> dict:
    """Relit un raccourci (pour les tests et le diagnostic)."""
    r = _run_ps(_PS_READ, {**os.environ, "CEP_LNK": str(lnk)})
    target, args, wd, icon, style = (r.stdout.strip().split("|") + [""] * 5)[:5]
    return {"target": target, "args": args, "workdir": wd, "icon": icon, "style": style}
