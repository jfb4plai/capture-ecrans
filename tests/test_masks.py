import json
import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from capture_ecran import annotate
from capture_ecran.app import copy_raw_capture
from capture_ecran.session import Session

BOX = {"p1": (40, 30), "p2": (160, 90)}


def secret_image():
    """Image « avec du texte » : du bruit, donc chaque pixel est une information à ne pas laisser fuiter."""
    return Image.effect_noise((300, 200), 90).convert("RGB")


def region(img, pad=0):
    return img.crop((40 + pad, 30 + pad, 160 - pad, 90 - pad))


def test_redact_is_fully_opaque_and_local():
    img = secret_image()
    out = annotate.render(img, [{"type": "redact", **BOX}])
    assert set(region(out).getdata()) == {(0, 0, 0)}          # aucun pixel d'origine : ni transparence ni flou
    assert out.getpixel((5, 5)) == img.getpixel((5, 5))        # hors zone : intact
    assert out.getpixel((250, 150)) == img.getpixel((250, 150))


def test_redact_survives_preview_scaling():
    img = secret_image().resize((150, 100))
    out = annotate.render(img, [{"type": "redact", **BOX}], scale=0.5)
    assert set(out.crop((22, 17, 78, 43)).getdata()) == {(0, 0, 0)}


def test_bake_masks_returns_new_image_and_unmasked_items_only():
    img = secret_image()
    arrow = {"type": "arrow", "p1": (0, 0), "p2": (50, 50), "width": 6, "color": "#E53935"}
    items = [{"type": "redact", **BOX}, {"type": "blur", "p1": (200, 100), "p2": (280, 180)}, arrow]
    baked, kept = annotate.bake_masks(img, items)
    assert kept == [arrow]                                     # la flèche reste modifiable, pas les masques
    assert set(region(baked).getdata()) == {(0, 0, 0)}
    assert baked.crop((200, 100, 280, 180)).tobytes() != img.crop((200, 100, 280, 180)).tobytes()
    assert region(img).tobytes() != region(baked).tobytes()     # l'image passée n'est pas modifiée sur place
    again, kept2 = annotate.bake_masks(baked, kept)             # idempotent
    assert again.tobytes() == baked.tobytes() and kept2 == kept


def test_original_file_no_longer_contains_masked_data(tmp_path):
    """Le point central : le dossier « originales » ne doit plus permettre de lire ce qui a été masqué."""
    s = Session.new(tmp_path, "sécurité")
    secret = secret_image()
    cap = s.add(secret)
    assert region(s.load_original(cap)).tobytes() == region(secret).tobytes()      # avant : en clair
    items = [{"type": "redact", **BOX}]
    s.update(cap, secret, annotate.render(secret, items), items, "x")
    original = s.load_original(cap)
    assert set(region(original).getdata()) == {(0, 0, 0)}                           # après : détruit
    assert set(region(s.load_final(cap)).getdata()) == {(0, 0, 0)}
    assert s.captures[0].items == []
    text = (s.folder / "session.json").read_text("utf-8")
    assert "redact" not in text                                                     # pas de trace exploitable non plus
    # et la réouverture de la série ne ramène rien
    reopened = Session.open(s.folder)
    assert set(region(reopened.load_original(reopened.captures[0])).getdata()) == {(0, 0, 0)}


def test_pixelation_is_baked_into_original_too(tmp_path):
    s = Session.new(tmp_path, "pix")
    secret = secret_image()
    cap = s.add(secret)
    items = [{"type": "blur", **BOX}]
    s.update(cap, secret, annotate.render(secret, items), items, "")
    assert region(s.load_original(cap)).tobytes() != region(secret).tobytes()
    assert s.load_original(cap).tobytes() == s.load_final(cap).tobytes()


def test_old_series_can_be_secured(tmp_path):
    """Séries d'avant la v1.1.2 : masque présent dans session.json mais original encore en clair."""
    s = Session.new(tmp_path, "ancienne")
    secret = secret_image()
    cap = s.add(secret)
    cap.items = [{"type": "redact", **BOX}, {"type": "step", "pos": (10, 10), "number": 1, "radius": 15, "color": "#E53935"}]
    s.save()
    assert region(s.load_original(cap)).tobytes() == region(secret).tobytes()
    assert s.secure_all() == 1
    assert set(region(s.load_original(cap)).getdata()) == {(0, 0, 0)}
    assert [i["type"] for i in cap.items] == ["step"]
    assert s.secure_all() == 0                                  # rien à refaire


def test_clipboard_policy():
    assert copy_raw_capture(True, "none") and copy_raw_capture(True, "paint")
    assert not copy_raw_capture(True, "editor")                 # l'éditeur copiera l'image FINALE, masques compris
    assert not copy_raw_capture(False, "none")
