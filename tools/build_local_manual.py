"""Fabrique capture_ecran/assets/mode-emploi.html (autonome, lisible hors connexion) à partir de la
page du site : python tools/build_local_manual.py <dossier capture-ecran du site>
(le dépôt du site contient index.html, mode-emploi.html et _style.css)."""
import base64
import re
import sys
from pathlib import Path

site = Path(sys.argv[1])
root = Path(__file__).resolve().parent.parent
html = (site / "mode-emploi.html").read_text("utf-8")
css = (site / "_style.css").read_text("utf-8")
import io
from PIL import Image
_im = Image.open(root / "capture_ecran/assets/logo-ui.png").convert("RGBA").resize((200, 200), Image.LANCZOS)
_buf = io.BytesIO()
_im.save(_buf, "PNG", optimize=True)
logo = base64.b64encode(_buf.getvalue()).decode()  # 200 px affichés à 88-100 px : net sur écrans HiDPI

html = re.sub(r'\s*<link rel="preconnect"[^>]*>', "", html)
html = re.sub(r'\s*<link href="https://fonts[^>]*>', "", html)
html = html.replace('<link rel="stylesheet" href="_style.css" />', f"<style>{css.replace('Inter', 'Segoe UI')}</style>")
html, n = re.subn(r'<img src="[^"]*logo[^"]*" alt="jfb4plai — accueil" />',
                  f'<img src="data:image/png;base64,{logo}" alt="jfb4plai" />', html)
assert n == 1, "logo de la page du site introuvable : le script doit être adapté"  # jamais de logo cassé en silence
html = html.replace('<a href="/"><img', '<a href="https://jfb4plai.com"><img')
html = html.replace('<a href="./">← Télécharger le programme</a>', '<a href="https://jfb4plai.com/capture-ecran/">jfb4plai.com/capture-ecran</a>')
html = html.replace('<a href="./">page de téléchargement</a>', '<a href="https://jfb4plai.com/capture-ecran/">page de téléchargement</a>')
html = html.replace('<a href="/">jfb4plai.com</a>', '<a href="https://jfb4plai.com">jfb4plai.com</a>')
(root / "capture_ecran/assets/mode-emploi.html").write_text(html, "utf-8")
print("écrit", len(html), "octets")
