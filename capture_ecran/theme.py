"""Style de l'application, repris du guide « Claude Code · PLAI » : fond crème, cartes blanches à bordure
fine, titres en DM Serif Display, texte en DM Sans, étiquettes en petites capitales, encadrés colorés.

Les polices sont embarquées (licence SIL OFL, voir assets/fonts) et chargées pour ce programme seulement.
Si elles manquent, on retombe sur Georgia / Segoe UI : l'application reste lisible.
"""
from __future__ import annotations

import sys
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

from .resources import resource_path

C = dict(
    bg="#faf9f7", surface="#ffffff", surface2="#f4f2ee", border="#e8e4dd", border2="#d4cfc6",
    text="#1a1814", text2="#5a564f", text3="#9a958c", dark="#1a1814", dark2="#2e2b26", dark_text="#e8e5de",
    teal="#0f6e56", teal_bg="#e1f5ee", teal_mid="#1d9e75",
    blue="#185fa5", blue_bg="#e6f1fb", blue_mid="#378add",
    amber="#854f0b", amber_bg="#faeeda", amber_mid="#ef9f27",
    green="#3b6d11", green_bg="#eaf3de", green_mid="#639922",
    red="#a32d2d", red_bg="#fcebeb", red_mid="#e24b4a",
)
CALLOUTS = {  # nom -> (fond, trait, texte)
    "info": (C["blue_bg"], C["blue_mid"], C["blue"]),
    "warn": (C["amber_bg"], C["amber_mid"], C["amber"]),
    "ok": (C["green_bg"], C["green_mid"], C["green"]),
    "danger": (C["red_bg"], C["red_mid"], C["red"]),
    "teal": (C["teal_bg"], C["teal_mid"], C["teal"]),
}
_FILES = ("DMSans-Regular.ttf", "DMSans-Italic.ttf", "DMSans-Medium.ttf", "DMSans-Bold.ttf",
          "DMSerifDisplay-Regular.ttf", "DMSerifDisplay-Italic.ttf")
_fonts: dict[str, tkfont.Font] = {}
_family: dict[str, str] = {}


def load_bundled_fonts() -> None:
    """Rend les polices du dossier assets/fonts utilisables par CE processus (Windows : FR_PRIVATE)."""
    if sys.platform != "win32":
        return
    import ctypes
    for name in _FILES:
        p = resource_path("fonts/" + name)
        if p.is_file():
            try:
                ctypes.windll.gdi32.AddFontResourceExW(str(p), 0x10, 0)
            except Exception:
                pass


def _pick(root: tk.Misc, wanted: list[str]) -> str:
    have = {f.lower() for f in tkfont.families(root)}
    for w in wanted:
        if w.lower() in have:
            return w
    return wanted[-1]


def init_fonts(root: tk.Misc) -> None:
    load_bundled_fonts()
    _family["sans"] = _pick(root, ["DM Sans 9pt", "DM Sans", "Segoe UI", "Helvetica"])
    _family["medium"] = _pick(root, ["DM Sans 9pt Medium", "DM Sans Medium"] + [_family["sans"]])
    _family["serif"] = _pick(root, ["DM Serif Display", "Georgia", "Times New Roman"])
    _family["mono"] = _pick(root, ["Cascadia Mono", "Consolas", "Courier New"])
    _fonts.clear()


def font(role: str = "body", size: int = 10) -> tkfont.Font:
    """role : body | medium | bold | italic | serif | serif_italic | mono. Un objet Font par couple (rôle, taille)."""
    key = f"{role}{size}"
    if key not in _fonts:
        fam = {"body": "sans", "bold": "sans", "italic": "sans", "medium": "medium",
               "serif": "serif", "serif_italic": "serif", "mono": "mono"}[role]
        _fonts[key] = tkfont.Font(family=_family.get(fam, "Helvetica"), size=size,
                                  weight="bold" if role == "bold" else "normal",
                                  slant="italic" if role in ("italic", "serif_italic") else "roman")
    return _fonts[key]


def apply(root: tk.Tk) -> None:
    """Applique le thème à toute l'application (à appeler juste après la création de la fenêtre)."""
    init_fonts(root)
    root.configure(bg=C["bg"])
    root.option_add("*Font", font("body", 10))
    root.option_add("*Text.Font", font("body", 11))
    s = ttk.Style(root)
    s.theme_use("clam")
    base = dict(background=C["bg"], foreground=C["text"], fieldbackground=C["surface"], bordercolor=C["border"],
                darkcolor=C["bg"], lightcolor=C["bg"], troughcolor=C["surface2"], focuscolor=C["bg"],
                selectbackground=C["teal_bg"], selectforeground=C["teal"], insertcolor=C["text"])
    s.configure(".", font=font("body", 10), **base)
    s.configure("TFrame", background=C["bg"])
    s.configure("Card.TFrame", background=C["surface"])
    for name, bg in (("TLabel", C["bg"]), ("Card.TLabel", C["surface"])):
        s.configure(name, background=bg, foreground=C["text"], font=font("body", 10))
    s.configure("Muted.TLabel", foreground=C["text3"], font=font("body", 9))
    s.configure("CardMuted.TLabel", background=C["surface"], foreground=C["text3"], font=font("body", 9))
    s.configure("Title.TLabel", font=font("serif", 18))
    s.configure("Link.TLabel", foreground=C["teal"], font=font("medium", 9))
    s.configure("CardLink.TLabel", background=C["surface"], foreground=C["teal"], font=font("medium", 9))
    # boutons : « fantôme » (blanc, bordure fine) ; Primary = sombre comme l'onglet actif du guide
    s.configure("TButton", background=C["surface"], foreground=C["text"], bordercolor=C["border2"],
                darkcolor=C["surface"], lightcolor=C["surface"], focuscolor=C["surface"],
                relief="raised", borderwidth=1,  # « flat » = aucune bordure dessinée avec le thème clam
                padding=(12, 6), font=font("medium", 10), anchor="center")
    s.map("TButton", background=[("pressed", C["surface2"]), ("active", C["surface2"]), ("disabled", C["bg"])],
          darkcolor=[("pressed", C["surface2"]), ("active", C["surface2"])],
          lightcolor=[("pressed", C["surface2"]), ("active", C["surface2"])],
          foreground=[("disabled", C["text3"])], bordercolor=[("focus", C["teal_mid"]), ("active", C["text3"])])
    s.configure("Primary.TButton", background=C["dark"], foreground="#ffffff", bordercolor=C["dark"],
                darkcolor=C["dark"], lightcolor=C["dark"], focuscolor=C["dark"], padding=(14, 8))
    s.map("Primary.TButton", background=[("pressed", C["dark2"]), ("active", C["dark2"])],
          darkcolor=[("active", C["dark2"])], lightcolor=[("active", C["dark2"])],
          foreground=[("disabled", C["text3"])], bordercolor=[("active", C["dark2"]), ("focus", C["teal_mid"])])
    s.configure("Big.TButton", padding=(8, 8))
    s.configure("Small.TButton", padding=(8, 4), font=font("medium", 9))
    for kind, bg in (("TCheckbutton", C["bg"]), ("TRadiobutton", C["bg"]),
                     ("Card.TCheckbutton", C["surface"]), ("Card.TRadiobutton", C["surface"])):
        s.configure(kind, background=bg, foreground=C["text2"], font=font("body", 10), focuscolor=bg,
                    indicatorbackground=C["surface"], indicatorforeground=C["teal"], indicatorcolor=C["surface"],
                    upperbordercolor=C["border2"], lowerbordercolor=C["border2"])
        s.map(kind, indicatorcolor=[("selected", C["teal_mid"]), ("!selected", C["surface"])],
              background=[("active", bg)], foreground=[("selected", C["text"])])
    s.configure("TEntry", fieldbackground=C["surface"], bordercolor=C["border2"], padding=5)
    s.map("TEntry", bordercolor=[("focus", C["teal_mid"])])
    s.configure("TSeparator", background=C["border"])
    s.configure("Vertical.TScrollbar", background=C["surface2"], troughcolor=C["bg"], bordercolor=C["bg"])


# ---------------------------------------------------------------- composants
def card(parent: tk.Misc, padding: int = 10, **pack) -> ttk.Frame:
    """Carte blanche à bordure fine (comme .card du guide). Retourne le cadre intérieur."""
    outer = tk.Frame(parent, bg=C["surface"], highlightthickness=1, highlightbackground=C["border"],
                     highlightcolor=C["border"])
    outer.pack(fill="x", **pack)
    inner = ttk.Frame(outer, style="Card.TFrame", padding=padding)
    inner.pack(fill="both", expand=True)
    return inner


def eyebrow(parent: tk.Misc, text: str, on_card: bool = False) -> tk.Frame:
    """Étiquette en petites capitales suivie d'un filet (comme .eyebrow du guide)."""
    bg = C["surface"] if on_card else C["bg"]
    row = tk.Frame(parent, bg=bg)
    tk.Label(row, text=text.upper(), bg=bg, fg=C["text3"], font=font("medium", 8)).pack(side="left")
    tk.Frame(row, bg=C["border"], height=1).pack(side="left", fill="x", expand=True, padx=(10, 0), pady=(2, 0))
    return row


def section(parent: tk.Misc, title: str, padding: int = 10, expand: bool = False) -> ttk.Frame:
    """Étiquette + carte. Retourne le cadre intérieur de la carte."""
    eyebrow(parent, title).pack(fill="x", padx=16, pady=(8, 3))
    inner = card(parent, padding)
    holder = inner.master
    holder.pack_configure(padx=16, fill="both" if expand else "x", expand=expand)
    return inner


def callout(parent: tk.Misc, kind: str, text: str, label: str | None = None, wrap: int = 440) -> tk.Frame:
    """Encadré coloré à trait gauche (.callout / .warn / .ok / .danger du guide)."""
    bg, bar, fg = CALLOUTS[kind]
    box = tk.Frame(parent, bg=bg)
    tk.Frame(box, bg=bar, width=3).pack(side="left", fill="y")
    body = tk.Frame(box, bg=bg)
    body.pack(side="left", fill="both", expand=True, padx=12, pady=9)
    if label:
        tk.Label(body, text=label.upper(), bg=bg, fg=fg, font=font("medium", 8), anchor="w").pack(fill="x")
    tk.Label(body, text=text, bg=bg, fg=fg, font=font("body", 10), justify="left", anchor="w",
             wraplength=wrap).pack(fill="x")
    return box


def pill(parent: tk.Misc, text: str, kind: str = "teal") -> tk.Label:
    bg, _, fg = CALLOUTS[kind]
    return tk.Label(parent, text=text, bg=bg, fg=fg, font=font("medium", 9), padx=9, pady=2)


def style_listbox(lb: tk.Listbox) -> None:
    lb.configure(bg=C["surface"], fg=C["text"], selectbackground=C["teal_bg"], selectforeground=C["teal"],
                 highlightthickness=1, highlightbackground=C["border"], highlightcolor=C["teal_mid"],
                 relief="flat", bd=0, activestyle="none", font=font("body", 10))


def style_dialog(win: tk.Misc) -> None:
    win.configure(bg=C["bg"])
