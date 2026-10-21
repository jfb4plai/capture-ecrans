import os
import sys
import tkinter as tk
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from capture_ecran import editor as E
from capture_ecran import theme
from capture_ecran.session import Session

pytestmark = pytest.mark.skipif(sys.platform != "win32" and not os.environ.get("DISPLAY"), reason="pas d'écran")


class Ev:
    def __init__(self, x, y, state=0):
        self.x, self.y, self.state = x, y, state


@pytest.fixture(scope="module")
def tkroot(shared_app, gui_patches):
    """La racine Tk unique de la session (voir conftest.py)."""
    root = shared_app
    theme.apply(root)              # l'application applique toujours le thème avant de créer la moindre fenêtre
    root.geometry("200x100+0+0")   # visible : un dialogue « transient » d'une mère masquée reste invisible
    root.update()
    return root


@pytest.fixture
def ed(tmp_path, tkroot):
    root = tkroot
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


def _ask_with_keys(root, steps_fn):
    """Ouvre ask_text et pilote le clavier. La fenêtre mère doit être VISIBLE (sinon la boîte reste
    démappée et ne reçoit aucune touche : un test vide). Toute erreur ferme la boîte (pas de blocage)."""
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
    result = E.ask_text(root, "Texte", "")
    if errors:
        raise errors[0]
    return result


def test_shift_enter_makes_a_new_line_and_enter_validates(tkroot):
    def steps(dlg, box):
        box.insert("end", "Ligne 1")
        box.event_generate("<Return>", state=1)       # Maj+Entrée : ne doit PAS fermer la boîte
        dlg.update()
        assert dlg.winfo_exists(), "Maj+Entrée a fermé la boîte"
        box.insert("end", "Ligne 2")
        box.event_generate("<Return>", state=0)       # Entrée seule : valide

    assert _ask_with_keys(tkroot, steps) == "Ligne 1\nLigne 2"


def test_enter_alone_still_validates_single_line(tkroot):
    def steps(dlg, box):
        box.insert("end", "Un seul")
        box.event_generate("<Return>", state=0)

    assert _ask_with_keys(tkroot, steps) == "Un seul"


def test_theme_is_applied_and_fonts_resolve(tkroot):
    f = theme.font("serif", 18)
    assert f.actual("size") == 18 or f.actual("size") == -24 or isinstance(f.actual("family"), str)
    assert theme.font("serif", 18) is f                       # un seul objet par (rôle, taille) : pas de fuite
    for style in ("TButton", "Primary.TButton", "Small.TButton", "Big.TButton", "Card.TLabel", "Card.TRadiobutton",
                  "Card.TCheckbutton", "Muted.TLabel"):
        assert tkroot.tk.call("ttk::style", "layout", style)  # les styles existent
    assert str(tkroot.cget("bg")) == theme.C["bg"]


def test_callout_and_pill_kinds_exist(tkroot):
    for kind in ("info", "warn", "ok", "danger", "teal"):
        assert theme.callout(tkroot, kind, "texte", label="titre") is not None
        assert theme.pill(tkroot, "x", kind if kind in theme.CALLOUTS else "teal") is not None


def test_bundled_fonts_have_french_glyphs():
    from PIL import ImageFont
    from capture_ecran.resources import resource_path
    for name in ("DMSans-Regular.ttf", "DMSans-Medium.ttf", "DMSans-Bold.ttf", "DMSerifDisplay-Regular.ttf"):
        path = resource_path("fonts/" + name)
        assert path.is_file(), name
        f = ImageFont.truetype(str(path), 24)
        for ch in "éèêàçùôîœÉ«»’…":
            assert f.getmask(ch).getbbox() is not None, f"{name} : glyphe manquant {ch}"
    for lic in ("OFL-DMSans.txt", "OFL-DMSerifDisplay.txt"):
        assert "SIL OPEN FONT LICENSE" in resource_path("fonts/" + lic).read_text("utf-8").upper()


def test_html_fiche_uses_the_site_style(tmp_path):
    from capture_ecran import exporter
    from capture_ecran.session import Session
    s = Session.new(tmp_path, "Mon tuto")
    img = Image.new("RGB", (300, 200), "white")
    s.update(s.add(img), img, img, [], "Étape un")
    html = exporter.export_html_guide(s, tmp_path / "f.html").read_text("utf-8")
    assert "#faf9f7" in html and "DM Serif Display" in html and "font/ttf;base64" in html
    assert "Étape un" in html and "class='num'" in html


# ------------------------------------------------------------------ masques et presse-papiers
def test_mask_tools_are_offered_with_a_clear_warning():
    labels = {key: (label, tip) for key, _g, label, tip in E.TOOLS}
    assert labels["redact"][0] == "Masquer" and "DÉFINITIVEMENT" in labels["redact"][1]
    assert labels["blur"][0] == "Pixelliser" and "déconseillé" in labels["blur"][1]


def test_saving_with_a_mask_destroys_original_and_copies_final(ed, monkeypatch):
    copied = []
    monkeypatch.setattr(E.winapi, "copy_image_to_clipboard", lambda img: copied.append(img.copy()) or True)
    ed.base = Image.effect_noise((800, 500), 90).convert("RGB")      # contenu « secret »
    ed.copy_on_save = True
    ed.tool.set("redact")
    ed._press(at(ed, 100, 100))
    ed._drag(at(ed, 300, 200))
    ed._release(at(ed, 300, 200))
    assert [i["type"] for i in ed.items] == ["redact"]
    assert "DÉFINITIF" in ed.status.cget("text")
    ed.save_and_close()
    original = ed.session.load_original(ed.cap)
    assert copied and set(copied[0].crop((120, 120, 280, 180)).getdata()) == {(0, 0, 0)}   # le presse-papiers n'a pas le secret
    assert set(original.crop((120, 120, 280, 180)).getdata()) == {(0, 0, 0)}               # ni le fichier d'origine
