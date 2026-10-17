import os
import sys
import time
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from capture_ecran import app as A
from capture_ecran import config, steps, winapi
from capture_ecran.session import Session

pytestmark = pytest.mark.skipif(sys.platform != "win32" and not os.environ.get("DISPLAY"), reason="pas d'écran")


@pytest.fixture(scope="module")
def app(tmp_path_factory):
    base = tmp_path_factory.mktemp("base")
    orig_load, orig_save = config.load, config.save
    config.load = lambda path=None: {**orig_load(Path(os.devnull)), "base_dir": str(base),
                                     "storage_confirmed": True, "shortcut_offered": True}
    config.save = lambda cfg, path=None: None
    winapi.beep = lambda *a, **k: None
    a = A.App()
    a.geometry("1000x700+0+0")
    a.update()
    yield a
    config.load, config.save = orig_load, orig_save
    try:
        a.destroy()
    except Exception:
        pass


def fake_recording(app, tmp_path):
    app.session = Session.new(tmp_path, "série")
    app.recorder = steps.StepRecorder(app.session)
    app._rec_start = 0
    app.hook = app.frames = None
    app._recording_ui()


def click(app, i):
    frame = Image.new("RGB", (400, 300), "white")
    app._record_click("left", (50 + 90 * i, 60 + 70 * i), frame, time.monotonic() + 10 * i)  # clics bien espacés


def test_recording_gives_visible_feedback_then_restores(app, tmp_path):
    fake_recording(app, tmp_path)
    for i in range(3):
        click(app, i)
        assert app.listbox.size() == i + 1                                    # la liste se remplit EN DIRECT
        assert f"{i + 1} clic" in app.title()
        assert "Arrêter" in app.steps_btn.cget("text") and f"({i + 1} clic" in app.steps_btn.cget("text")
        assert f"{i + 1} clic(s)" in app.status.cget("text") and "en cours" in app.status.cget("text")
    app.stop_steps()
    assert app.title() == f"{A.APP_NAME} {A.__version__}"
    assert app.steps_btn.cget("text") == "●  Enregistrer mes clics"
    assert app.status.cget("text").startswith("3 étape(s) enregistrée(s)")      # compteur = ce qui est dans la liste
    assert app.listbox.size() == 3


def test_final_count_matches_list_even_when_recorder_count_differs(app, tmp_path):
    """Régression : « 0 étape(s) » affiché alors que la liste en comptait 16."""
    fake_recording(app, tmp_path)
    for i in range(4):
        click(app, i)
    app.recorder.count = 0                      # un compteur interne périmé ne doit plus fausser le message
    app.stop_steps()
    assert app.status.cget("text").startswith("4 étape(s)")


def test_double_click_counts_once(app, tmp_path):
    fake_recording(app, tmp_path)
    frame = Image.new("RGB", (400, 300), "white")
    t = time.monotonic()
    app._record_click("left", (100, 100), frame, t)
    app._record_click("left", (101, 100), frame, t + 0.1)
    assert app.listbox.size() == 1 and "1 clic" in app.title()
    app.stop_steps()
    assert app.status.cget("text").startswith("1 étape(s)")


def make_series(app, tmp_path, n=5):
    fake_recording(app, tmp_path)
    for i in range(n):
        click(app, i)
    app.stop_steps()


def test_select_all_checkbox_and_ctrl_selection(app, tmp_path):
    make_series(app, tmp_path)
    app._select_all(True)
    assert len(app.listbox.curselection()) == 5 and app.v_all.get() is True
    assert "5 sélectionnée(s) sur 5" in app.sel_lbl.cget("text")
    app._select_all(False)
    assert app.listbox.curselection() == () and app.v_all.get() is False
    app.listbox.selection_set(0)
    app.listbox.selection_set(2)                 # ce que fait Ctrl+clic avec selectmode « extended »
    app._on_select()
    assert app.listbox.curselection() == (0, 2) and "2 sélectionnée(s) sur 5" in app.sel_lbl.cget("text")
    assert app.v_all.get() is False


def test_delete_several_selected(app, tmp_path, monkeypatch):
    make_series(app, tmp_path)
    monkeypatch.setattr(A.messagebox, "askyesno", lambda *a, **k: True)
    kept = [app.session.captures[i].id for i in (1, 3)]
    app._select_all(False)
    for i in (0, 2, 4):
        app.listbox.selection_set(i)
    app.delete_selected()
    assert [c.id for c in app.session.captures] == kept and app.listbox.size() == 2
    assert not (app.session.folder / "capture_001.png").exists()


def test_move_a_selected_block(app, tmp_path):
    make_series(app, tmp_path)
    ids = [c.id for c in app.session.captures]
    app._select_all(False)
    app.listbox.selection_set(2)
    app.listbox.selection_set(3)
    app.move(-1)
    assert [c.id for c in app.session.captures] == [ids[0], ids[2], ids[3], ids[1], ids[4]]
    assert app.listbox.curselection() == (1, 2)
    app.move(-1)
    app.move(-1)                                   # déjà en tête : sans effet, sans erreur
    assert app.listbox.curselection() == (0, 1)


def test_edit_needs_a_single_selection(app, tmp_path):
    make_series(app, tmp_path)
    app._select_all(True)
    assert app._selected() is None and "une seule" in app.status.cget("text")


def test_export_scope_selection_or_whole(app, tmp_path, monkeypatch):
    make_series(app, tmp_path)
    app._select_all(False)
    app.listbox.selection_set(1)
    app.listbox.selection_set(3)
    answers = iter([True, False])                   # Oui = sélection, Non = toute la série
    monkeypatch.setattr(A.messagebox, "askyesnocancel", lambda *a, **k: next(answers))
    part, suffix = app._export_scope()
    assert suffix == "_selection" and [c.id for c in part.captures] == [app.session.captures[i].id for i in (1, 3)]
    assert len(app.session.captures) == 5           # la vraie série n'est pas touchée
    whole, suffix = app._export_scope()
    assert suffix == "" and whole is app.session
    monkeypatch.setattr(A.messagebox, "askyesnocancel", lambda *a, **k: None)
    assert app._export_scope() is None              # Annuler
    app._select_all(True)                           # tout sélectionné : pas de question
    monkeypatch.setattr(A.messagebox, "askyesnocancel", lambda *a, **k: pytest.fail("question inutile"))
    assert app._export_scope()[1] == ""


def test_quick_capture_goes_to_clipboard_only(app, tmp_path, monkeypatch):
    """Capture simple : zone → presse-papiers, sans pointeur ni halo, sans éditeur, sans fichier ni série."""
    calls = {}
    full = Image.new("RGB", (400, 300), "white")
    monkeypatch.setattr(A.grabber, "grab_screen", lambda *a, **k: calls.setdefault("grab", a) and (full, (0, 0)))
    monkeypatch.setattr(A, "select_region", lambda master, img: img.crop((10, 10, 110, 90)))
    monkeypatch.setattr(A.winapi, "copy_image_to_clipboard", lambda im: calls.setdefault("clip", im.size) and True)
    monkeypatch.setattr(A.Editor, "__init__", lambda *a, **k: pytest.fail("l'éditeur ne doit pas s'ouvrir"))
    app.session = None
    before = list(tmp_path.iterdir())
    app.busy = True
    app._capture("quick")
    assert calls["grab"] == (False, False)          # ni pointeur ni halo jaune
    assert calls["clip"] == (100, 80)               # seule la zone choisie est copiée
    assert app.session is None and list(tmp_path.iterdir()) == before and not app.busy
    assert "presse-papiers" in app.status.cget("text") and "Aucun fichier" in app.status.cget("text")


def test_quick_capture_cancelled(app, monkeypatch):
    monkeypatch.setattr(A.grabber, "grab_screen", lambda *a, **k: (Image.new("RGB", (50, 50)), (0, 0)))
    monkeypatch.setattr(A, "select_region", lambda master, img: None)
    monkeypatch.setattr(A.winapi, "copy_image_to_clipboard", lambda im: pytest.fail("rien à copier"))
    app.busy = True
    app._capture("quick")
    assert app.status.cget("text") == "Capture annulée." and not app.busy


def test_quick_hotkey_default_and_distinct():
    cfg = config.load(Path(os.devnull))
    keys = [cfg[k] for k in ("hotkey_full", "hotkey_region", "hotkey_window", "hotkey_steps", "hotkey_quick", "hotkey_show")]
    assert cfg["hotkey_quick"] == "ctrl+shift+f8" and len(set(keys)) == len(keys)
    from capture_ecran.hotkeys import parse_hotkey
    parse_hotkey(cfg["hotkey_quick"])
