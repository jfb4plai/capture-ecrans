import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from capture_ecran import shortcuts, winapi

WIN = sys.platform == "win32"


@pytest.mark.parametrize("exe,expected", [
    (r"C:\Users\ann\AppData\Local\Temp\Temp1_Capture-ecran-PLAI-windows.zip\Capture-ecran-PLAI\Capture-ecran-PLAI.exe", "TEMPORAIRE"),
    (r"C:\Users\ann\Downloads\Capture-ecran-PLAI\Capture-ecran-PLAI.exe", "Téléchargements"),
    (r"C:\Users\ann\Téléchargements\Capture-ecran-PLAI\Capture-ecran-PLAI.exe", "Téléchargements"),
    (r"C:\Users\ann\Documents\Capture-ecran-PLAI\Capture-ecran-PLAI.exe", None),
    (r"D:\Outils\Capture-ecran-PLAI\Capture-ecran-PLAI.exe", None),
])
def test_location_warning(exe, expected):
    w = shortcuts.location_warning(exe)
    assert (w is None) if expected is None else (expected in w)


def test_lnk_locations(monkeypatch, tmp_path):
    monkeypatch.setenv("APPDATA", str(tmp_path / "Roaming"))
    assert shortcuts.startup_lnk().parts[-2:] == ("Startup", shortcuts.LNK_NAME)
    assert "Start Menu" in str(shortcuts.start_menu_lnk()) and "Startup" not in str(shortcuts.start_menu_lnk())
    assert shortcuts.desktop_lnk().name == shortcuts.LNK_NAME


def test_env_carries_unicode_paths_without_quoting_problems(tmp_path):
    lnk = tmp_path / "Dossier avec 'apostrophe' é" / shortcuts.LNK_NAME
    env = shortcuts.build_env(lnk, r"C:\Mes outils\é\x.exe", "--reduit", r"C:\Mes outils\é", r"C:\Mes outils\é\x.exe", True)
    assert env["CEP_LNK"] == str(lnk) and env["CEP_STYLE"] == "7" and env["CEP_ICON"].endswith(",0")
    assert shortcuts.build_env(lnk, "t", "", "w", None, False)["CEP_ICON"] == ""


def test_target_command_frozen_and_dev(monkeypatch, tmp_path):
    exe = tmp_path / "Capture" / "Capture-ecran-PLAI.exe"   # chemin natif de la plateforme de test
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(exe))
    target, args, wd = shortcuts.target_command()
    assert target == str(exe) and args == "" and wd == str(exe.parent)
    monkeypatch.setattr(sys, "frozen", False, raising=False)
    t2, a2, _ = shortcuts.target_command()
    assert a2 == "-m capture_ecran"


@pytest.mark.skipif(WIN, reason="test du refus hors Windows")
def test_create_refused_outside_windows(tmp_path):
    with pytest.raises(OSError):
        shortcuts.create(tmp_path / "x.lnk")


def test_single_instance_is_noop_outside_windows():
    if not WIN:
        assert winapi.acquire_single_instance() is True
        assert winapi.raise_existing_window("x") is False


@pytest.mark.skipif(not WIN, reason="WScript.Shell / mutex Windows")
def test_real_shortcut_roundtrip_on_windows(tmp_path):
    lnk = tmp_path / "Sous dossier é" / shortcuts.LNK_NAME
    shortcuts.create(lnk, minimized=True)
    info = shortcuts.read(lnk)
    assert lnk.is_file()
    assert "--reduit" in info["args"] and info["style"] == "7"
    assert info["target"] and Path(info["target"]).name.lower() in ("pythonw.exe", "python.exe", "capture-ecran-plai.exe")
    shortcuts.create(lnk, minimized=False)             # remplacement
    assert "--reduit" not in shortcuts.read(lnk)["args"]
    shortcuts.remove(lnk)
    assert not lnk.exists()


@pytest.mark.skipif(not WIN, reason="mutex Windows")
def test_second_instance_is_detected_on_windows():
    name = f"Local\\CEP-test-{uuid.uuid4().hex}"
    assert winapi.acquire_single_instance(name) is True
    assert winapi.acquire_single_instance(name) is False
