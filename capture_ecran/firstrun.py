"""Premier lancement : où ranger les captures ? (dossier du bureau, avertissement cloud)."""
from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from PIL import Image, ImageTk

from . import storage, theme
from .theme import C, font
from .resources import resource_path

CLOUD_WARNING = ("⚠  Ce dossier est synchronisé avec un cloud (OneDrive…).\n"
                 "Vos captures seront copiées automatiquement chez le fournisseur du cloud. "
                 "Si elles peuvent montrer des noms ou des écrans d'élèves, choisissez plutôt un dossier "
                 "qui n'est pas synchronisé.")


def warn_if_cloud(master: tk.Misc, path: Path) -> None:
    """Rappel court quand on choisit à la main un dossier synchronisé."""
    if storage.is_cloud_synced(path):
        from tkinter import messagebox
        messagebox.showwarning("Dossier synchronisé", CLOUD_WARNING, parent=master)


class FirstRunDialog(tk.Toplevel):
    """Résultat dans self.result (Path) : toujours un dossier utilisable (jamais None)."""

    def __init__(self, master, legacy_exists: bool = False):
        super().__init__(master)
        self.title("Bienvenue — où ranger vos captures ?")
        theme.style_dialog(self)
        if master.state() == "normal":  # transient + fenêtre mère masquée = dialogue invisible
            self.transient(master)
        self.attributes("-topmost", True)
        self.resizable(False, False)
        self.result: Path = storage.default_base_dir()
        desktop = storage.default_base_dir()
        docs = storage.documents_dir() / storage.FOLDER_NAME
        cloud = storage.is_cloud_synced(desktop)

        body = tk.Frame(self, bg=C["bg"])
        body.pack(padx=22, pady=18)
        top = tk.Frame(body, bg=C["bg"])
        top.pack(fill="x")
        try:
            self._logo = ImageTk.PhotoImage(Image.open(resource_path("logo-ui.png")).resize((76, 76), Image.LANCZOS))
            tk.Label(top, image=self._logo, bg=C["bg"]).pack(side="left", padx=(0, 14))
        except Exception:
            pass
        heads = tk.Frame(top, bg=C["bg"])
        heads.pack(side="left")
        tk.Label(heads, text="Où ranger vos captures ?", bg=C["bg"], fg=C["text"], font=font("serif", 19)).pack(anchor="w")
        tk.Label(heads, text="Je crée un dossier sur votre bureau, avec le logo jfb4plai.", bg=C["bg"],
                 fg=C["text2"], font=font("body", 10)).pack(anchor="w")
        box = tk.Frame(body, bg=C["surface"], highlightthickness=1, highlightbackground=C["border"])
        box.pack(fill="x", pady=(14, 10))
        self.path_lbl = tk.Label(box, text=str(desktop), bg=C["surface"], fg=C["teal"], font=font("medium", 10),
                                 wraplength=470, justify="left", anchor="w", padx=12, pady=9)
        self.path_lbl.pack(fill="x")
        if cloud:
            theme.callout(body, "warn", CLOUD_WARNING.split("\n", 1)[1], label="Dossier synchronisé (cloud)",
                          wrap=470).pack(fill="x", pady=(0, 10))
        if legacy_exists:
            tk.Label(body, text="Vos séries précédentes restent dans « Images\\Captures PLAI » : retrouvez-les avec "
                                "le bouton « Rouvrir… ».", bg=C["bg"], fg=C["text3"], font=font("body", 9),
                     wraplength=490, justify="left", anchor="w").pack(fill="x", pady=(0, 10))
        btns = tk.Frame(body, bg=C["bg"])
        btns.pack(fill="x")
        self.primary = ttk.Button(btns, text="✔  Créer le dossier sur le bureau", style="Primary.TButton",
                                  command=lambda: self._done(desktop))
        self.primary.pack(fill="x", pady=2)
        if cloud and not storage.is_cloud_synced(docs):
            ttk.Button(btns, text="Plutôt dans Documents (non synchronisé)",
                       command=lambda: self._done(docs)).pack(fill="x", pady=2)
        ttk.Button(btns, text="Choisir un autre dossier…", command=self._choose).pack(fill="x", pady=2)
        self.protocol("WM_DELETE_WINDOW", lambda: self._done(desktop))  # fermer = choix par défaut
        self.grab_set()
        self.primary.focus_set()

    def _choose(self):
        d = filedialog.askdirectory(parent=self, title="Choisir le dossier des captures")
        if d:
            warn_if_cloud(self, Path(d))
            self._done(Path(d))

    def _done(self, path: Path):
        self.result = Path(path)
        self.destroy()


def ask_storage(master: tk.Misc) -> Path:
    dlg = FirstRunDialog(master, storage.legacy_base_dir().is_dir())
    master.wait_window(dlg)
    return dlg.result
