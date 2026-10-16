"""Où ranger les captures : un dossier « Capture-ecran-jfb4plai » sur le bureau réel de l'utilisateur.

« Bureau réel » : sous Windows 11 il est souvent redirigé vers OneDrive (et se nomme « Bureau »),
on interroge donc Windows (SHGetKnownFolderPath) au lieu de deviner « ~/Desktop ».
"""
from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

FOLDER_NAME = "Capture-ecran-jfb4plai"
_FOLDERID_DESKTOP = "B4BFCC3A-DB2C-424C-B029-7FE99A87C641"
_FOLDERID_DOCUMENTS = "FDD39AD0-238F-46AF-ADB4-6C85480369C7"
_CLOUD_WORDS = ("onedrive", "dropbox", "google drive", "googledrive", "icloud", "sharepoint", "nextcloud", "owncloud")


def _known_folder(folder_id: str) -> Path | None:
    if sys.platform != "win32":
        return None
    import ctypes
    from ctypes import wintypes

    class GUID(ctypes.Structure):
        _fields_ = [("Data1", ctypes.c_ulong), ("Data2", ctypes.c_ushort), ("Data3", ctypes.c_ushort),
                    ("Data4", ctypes.c_ubyte * 8)]

    guid = GUID.from_buffer_copy(uuid.UUID(folder_id).bytes_le)
    shell32 = ctypes.WinDLL("shell32")
    ole32 = ctypes.WinDLL("ole32")
    shell32.SHGetKnownFolderPath.argtypes = [ctypes.POINTER(GUID), wintypes.DWORD, wintypes.HANDLE,
                                             ctypes.POINTER(ctypes.c_void_p)]
    shell32.SHGetKnownFolderPath.restype = ctypes.c_long
    ole32.CoTaskMemFree.argtypes = [ctypes.c_void_p]
    ptr = ctypes.c_void_p()
    try:
        if shell32.SHGetKnownFolderPath(ctypes.byref(guid), 0, None, ctypes.byref(ptr)) != 0:
            return None
        return Path(ctypes.wstring_at(ptr.value))
    finally:
        if ptr.value:
            ole32.CoTaskMemFree(ptr)


def desktop_dir() -> Path:
    p = _known_folder(_FOLDERID_DESKTOP)
    if p and p.is_dir():
        return p
    for name in ("Desktop", "Bureau"):
        cand = Path.home() / name
        if cand.is_dir():
            return cand
    return Path.home()


def documents_dir() -> Path:
    p = _known_folder(_FOLDERID_DOCUMENTS)
    if p and p.is_dir():
        return p
    for name in ("Documents",):
        cand = Path.home() / name
        if cand.is_dir():
            return cand
    return Path.home()


def default_base_dir() -> Path:
    return desktop_dir() / FOLDER_NAME


def legacy_base_dir() -> Path:
    """Emplacement des versions précédentes (1.0 – 1.1) : Images\\Captures PLAI."""
    pictures = Path.home() / "Pictures"
    return (pictures if pictures.is_dir() else Path.home()) / "Captures PLAI"


def is_cloud_synced(path: Path | str, env: dict | None = None) -> bool:
    """Vrai si le chemin est dans un dossier synchronisé avec un cloud (OneDrive, Dropbox…).
    Heuristique : variables OneDrive de Windows + mots-clés dans le chemin."""
    env = os.environ if env is None else env
    norm = os.path.normcase(os.path.normpath(str(path)))
    for var in ("OneDrive", "OneDriveConsumer", "OneDriveCommercial"):
        root = env.get(var)
        if root:
            r = os.path.normcase(os.path.normpath(root))
            if norm == r or norm.startswith(r + os.sep):
                return True
    low = norm.lower()
    return any(w in low for w in _CLOUD_WORDS)


def ensure_capture_folder(folder: Path) -> Path:
    """Crée le dossier ; s'il porte notre nom, lui donne l'icône du logo dans l'Explorateur
    (desktop.ini + attribut lecture seule sur le dossier, comme le fait Windows lui-même)."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    if folder.name == FOLDER_NAME:
        try:
            from .resources import resource_path
            icon = folder / "dossier.ico"
            ini = folder / "desktop.ini"
            if not icon.exists():
                icon.write_bytes(resource_path("icon.ico").read_bytes())
            if not ini.exists():
                ini.write_text("[.ShellClassInfo]\r\nIconResource=dossier.ico,0\r\n"
                               "InfoTip=Captures d'écran jfb4plai\r\n", "utf-8")
            _set_attrs(icon, ini, folder)
        except OSError:
            pass  # l'icône est cosmétique : ne jamais empêcher de capturer
    return folder


def _set_attrs(icon: Path, ini: Path, folder: Path) -> None:
    if sys.platform != "win32":
        return
    import ctypes
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.SetFileAttributesW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint]
    for f in (icon, ini):
        k32.SetFileAttributesW(str(f), 0x2 | 0x4)  # caché + système
    k32.SetFileAttributesW(str(folder), 0x1)       # lecture seule : Explorateur lit alors desktop.ini
