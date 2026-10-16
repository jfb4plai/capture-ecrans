import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from capture_ecran import config, storage


@pytest.mark.parametrize("path,env,expected", [
    (r"C:\Users\ann\OneDrive\Bureau\Capture-ecran-jfb4plai", {}, True),
    (r"C:\Users\ann\OneDrive - Ecole Saint-Jean\Bureau", {}, True),
    (r"C:\Users\ann\Desktop\Capture-ecran-jfb4plai", {}, False),
    (r"D:\Dropbox\x", {}, True),
    (r"C:\Users\ann\Google Drive\x", {}, True),
    (r"C:\Users\ann\Documents", {}, False),
])
def test_cloud_detection_by_keyword(path, env, expected):
    assert storage.is_cloud_synced(path, env) is expected


def test_cloud_detection_by_env_variable(tmp_path):
    root = tmp_path / "Synchro"
    inside = root / "Bureau" / "x"
    assert storage.is_cloud_synced(inside, {"OneDrive": str(root)})
    assert not storage.is_cloud_synced(tmp_path / "Synchro2", {"OneDrive": str(root)})  # préfixe de nom, pas de dossier
    assert not storage.is_cloud_synced(inside, {})


def test_default_dir_is_named_folder_on_desktop():
    d = storage.default_base_dir()
    assert d.name == "Capture-ecran-jfb4plai"
    assert d.parent == storage.desktop_dir()
    assert storage.desktop_dir().is_dir() or storage.desktop_dir() == Path.home()


def test_known_folders_resolve_without_error():
    # Sous Windows (CI) interroge réellement l'API ; ailleurs retombe sur le dossier personnel.
    assert storage.documents_dir().exists()
    assert storage.desktop_dir().exists()


def test_ensure_folder_adds_icon_only_for_our_folder(tmp_path):
    ours = storage.ensure_capture_folder(tmp_path / storage.FOLDER_NAME)
    assert (ours / "desktop.ini").read_text("utf-8").startswith("[.ShellClassInfo]")
    assert "IconResource=dossier.ico,0" in (ours / "desktop.ini").read_text("utf-8")
    assert (ours / "dossier.ico").stat().st_size > 1000
    other = storage.ensure_capture_folder(tmp_path / "Mes captures")
    assert other.is_dir() and not (other / "desktop.ini").exists()  # on ne personnalise pas le dossier d'un autre
    assert storage.ensure_capture_folder(ours) == ours  # idempotent


def test_config_default_base_dir_and_first_run_flag(tmp_path):
    cfg = config.load(tmp_path / "nope.json")
    assert Path(cfg["base_dir"]).name == "Capture-ecran-jfb4plai"
    assert cfg["storage_confirmed"] is False
