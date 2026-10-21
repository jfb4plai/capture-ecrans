"""Barre flottante pendant l'enregistrement vidéo : durée, bouton Arrêter, rappel du raccourci.
Placée hors de la zone filmée ; en plus, exclue de la capture (Windows 10 2004 et plus) pour le cas où
aucun espace libre n'existe (zone = tout l'écran)."""
from __future__ import annotations

import tkinter as tk

from . import winapi
from .theme import C, font


def bar_position(rect: tuple[int, int, int, int], size: tuple[int, int], screen: tuple[int, int, int, int],
                 gap: int = 12) -> tuple[int, int, bool]:
    """(x, y, hors_zone) : emplacement de la barre, de préférence au-dessus, puis sous, puis à droite, puis
    à gauche de la zone filmée. `rect` = (x, y, largeur, hauteur), `screen` = (gauche, haut, largeur, hauteur).
    Sans place libre : en haut au centre de la zone, hors_zone = False."""
    x, y, w, h = rect
    bw, bh = size
    sl, st, sw, sh = screen
    cx = min(max(x + (w - bw) // 2, sl + gap), sl + sw - bw - gap)   # centrée sur la zone, sans sortir de l'écran
    cy = min(max(y + (h - bh) // 2, st + gap), st + sh - bh - gap)
    for bx, by in ((cx, y - bh - gap), (cx, y + h + gap), (x + w + gap, cy), (x - bw - gap, cy)):
        if bx >= sl and by >= st and bx + bw <= sl + sw and by + bh <= st + sh:
            return bx, by, True
    return min(max(x + (w - bw) // 2, sl), sl + sw - bw), max(y + gap, st), False


class RecordBar(tk.Toplevel):
    def __init__(self, master: tk.Misc, rect: tuple[int, int, int, int], hotkey: str, on_stop, limited: bool = False):
        super().__init__(master)
        self.withdraw()  # on mesure d'abord le contenu : la largeur dépend de la police et de l'échelle d'affichage
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(bg=C["dark"], highlightbackground=C["red_mid"], highlightthickness=2)
        tk.Label(self, text="●", bg=C["dark"], fg=C["red_mid"], font=font("bold", 14)).pack(side="left", padx=(12, 4))
        self.time_lbl = tk.Label(self, text="00:00", bg=C["dark"], fg="#ffffff", font=font("bold", 13), width=11 if limited else 5)
        self.time_lbl.pack(side="left")
        tk.Button(self, text="■  Arrêter", command=on_stop, bg=C["red_mid"], fg="#ffffff", activebackground=C["red"],
                  activeforeground="#ffffff", relief="flat", font=font("bold", 11), padx=14, pady=4,
                  cursor="hand2").pack(side="left", padx=10, pady=8)
        self.hint_lbl = tk.Label(self, text=f"ou {hotkey}", bg=C["dark"], fg=C["dark_text"], font=font("body", 11))
        self.hint_lbl.pack(side="left", padx=(0, 16))
        for w in (self, self.time_lbl):  # on peut la déplacer si elle gêne
            w.bind("<ButtonPress-1>", self._grab)
            w.bind("<B1-Motion>", self._drag)
        self.update_idletasks()
        size = (self.winfo_reqwidth(), self.winfo_reqheight())
        vs = winapi.virtual_screen() or (0, 0, self.winfo_screenwidth(), self.winfo_screenheight())
        x, y, self.outside = bar_position(rect, size, vs)
        self.geometry(f"{size[0]}x{size[1]}{x:+d}{y:+d}")
        self.deiconify()
        self.update_idletasks()
        winapi.exclude_from_capture(self.winfo_id())

    def _grab(self, e):
        self._off = (e.x_root - self.winfo_x(), e.y_root - self.winfo_y())

    def _drag(self, e):
        self.geometry(f"+{e.x_root - self._off[0]}+{e.y_root - self._off[1]}")

    def set_time(self, seconds: float, remaining: float | None = None):
        """Temps écoulé ; avec une durée programmée, le décompte « reste mm:ss » (orange sur les 10 dernières secondes)."""
        if remaining is None:
            t = int(seconds)
            self.time_lbl.config(text=f"{t // 60:02d}:{t % 60:02d}")
            return
        r = max(0, int(remaining + 0.999))
        self.time_lbl.config(text=f"reste {r // 60:02d}:{r % 60:02d}", fg=C["amber_mid"] if r <= 10 else "#ffffff")
