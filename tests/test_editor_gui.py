import os
import sys
import tkinter as tk
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from capture_ecran import editor as E
from capture_ecran.session import Session

pytestmark = pytest.mark.skipif(sys.platform != "win32" and not os.environ.get("DISPLAY"), reason="pas d'écran")


class Ev:
    def __init__(self, x, y, state=0):
        self.x, self.y, self.state = x, y, state


@pytest.fixture
def ed(tmp_path):
    root = tk.Tk()
    root.withdraw()
    s = Session.new(tmp_path, "t")
    img = Image.new("RGB", (800, 500), "white")
    cap = s.add(img)
    e = E.Editor(root, s, cap, recorder=None)
    e.geometry("1000x700+0+0")
    e.update()
    e._fit()
    e.update()
    yield e
    try:
        e.destroy()
        root.destroy()
    except tk.TclError:
        pass


def at(ed, x, y):
    return Ev(ed.offset[0] + x * ed.scale, ed.offset[1] + y * ed.scale)


def test_text_can_be_corrected_by_double_click_and_text_tool(ed, monkeypatch):
    answers = iter(["Bonjour", "Bonsoir", "Salut"])
    monkeypatch.setattr(E, "ask_text", lambda parent, title, initial="": next(answers))
    ed.tool.set("text")
    ed._press(at(ed, 100, 100))                       # crée « Bonjour »
    assert [i["text"] for i in ed.items] == ["Bonjour"] and ed.selected == 0
    ed._double_click(at(ed, 110, 110))                # double-clic dessus : corrige
    assert [i["text"] for i in ed.items] == ["Bonsoir"]
    ed._press(at(ed, 110, 110))                       # outil Texte sur un texte existant : corrige, ne superpose pas
    assert [i["text"] for i in ed.items] == ["Salut"] and len(ed.items) == 1
    ed.undo()
    assert ed.items[0]["text"] == "Bonsoir"           # chaque correction est annulable
    ed.undo(); ed.undo()
    assert ed.items == []


def test_edit_keeps_position_and_style_and_ignores_cancel(ed, monkeypatch):
    seen = {}
    def fake(parent, title, initial=""):
        seen["initial"] = initial
        return seen.get("reply")
    monkeypatch.setattr(E, "ask_text", fake)
    ed.items.append({"type": "text", "pos": (50, 60), "text": "Ancien", "size": 32, "color": "#E53935"})
    ed.selected = 0
    seen["reply"] = None                               # Annuler
    ed.edit_text()
    assert ed.items[0]["text"] == "Ancien" and seen["initial"] == "Ancien"   # le dialogue est pré-rempli
    seen["reply"] = "Nouveau"
    ed.edit_text()
    assert ed.items[0] == {"type": "text", "pos": (50, 60), "text": "Nouveau", "size": 32, "color": "#E53935"}


def test_edit_text_without_text_selected_explains(ed):
    ed.items.append({"type": "rect", "p1": (0, 0), "p2": (50, 50), "width": 6, "color": "#E53935"})
    ed.selected = 0
    ed.edit_text()
    assert "double-cliquez" in ed.status.cget("text")


def test_color_and_size_apply_to_selected_object(ed):
    ed.items.append({"type": "text", "pos": (50, 60), "text": "T", "size": 32, "color": "#E53935"})
    ed.items.append({"type": "arrow", "p1": (0, 0), "p2": (90, 90), "width": 6, "color": "#E53935"})
    ed.selected = 0
    ed._set_color("#1E88E5")
    assert ed.items[0]["color"] == "#1E88E5" and ed.items[1]["color"] == "#E53935"
    ed.width_name.set("Épais")
    ed._restyle_selected(size=True)
    assert ed.items[0]["size"] == 46                   # texte : taille de police
    ed.selected = 1
    ed._restyle_selected(size=True)
    assert ed.items[1]["width"] == 10                  # flèche : épaisseur
    ed.undo()
    assert ed.items[1]["width"] == 6
    ed.selected = None
    ed._set_color("#43A047")                           # rien de sélectionné : aucun objet modifié
    assert ed.items[0]["color"] == "#1E88E5"


def _walk(w):
    for c in w.winfo_children():
        yield c
        yield from _walk(c)


def _ask_with_keys(steps_fn):
    """Ouvre ask_text et pilote le clavier. La fenêtre mère doit être VISIBLE (sinon la boîte reste
    démappée et ne reçoit aucune touche : un test vide). Toute erreur ferme la boîte (pas de blocage)."""
    root = tk.Tk()
    root.geometry("200x100+0+0")
    root.update()
    errors = []

    def go():
        dlg = [w for w in root.winfo_children() if isinstance(w, tk.Toplevel)][-1]
        try:
            box = next(w for w in _walk(dlg) if isinstance(w, tk.Text))
            dlg.update()
            box.focus_force()
            dlg.update()
            assert dlg.focus_get() is box, "la zone de texte n'a pas le focus"
            steps_fn(dlg, box)
        except Exception as e:  # noqa: BLE001
            errors.append(e)
            if dlg.winfo_exists():
                dlg.destroy()

    root.after(250, go)
    try:
        result = E.ask_text(root, "Texte", "")
    finally:
        root.destroy()
    if errors:
        raise errors[0]
    return result


def test_shift_enter_makes_a_new_line_and_enter_validates():
    def steps(dlg, box):
        box.insert("end", "Ligne 1")
        box.event_generate("<Return>", state=1)       # Maj+Entrée : ne doit PAS fermer la boîte
        dlg.update()
        assert dlg.winfo_exists(), "Maj+Entrée a fermé la boîte"
        box.insert("end", "Ligne 2")
        box.event_generate("<Return>", state=0)       # Entrée seule : valide

    assert _ask_with_keys(steps) == "Ligne 1\nLigne 2"


def test_enter_alone_still_validates_single_line():
    def steps(dlg, box):
        box.insert("end", "Un seul")
        box.event_generate("<Return>", state=0)

    assert _ask_with_keys(steps) == "Un seul"
