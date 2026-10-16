"""Premier lancement : où ranger les captures ? (dossier du bureau, avertissement cloud)."""
from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from PIL import Image, ImageTk

from . import storage
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
        if master.state() == "normal":  # transient + fenêtre mère masquée = dialogue invisible
            self.transient(master)
        self.attributes("-topmost", True)
        self.resizable(False, False)
        self.result: Path = storage.default_base_dir()
        desktop = storage.default_base_dir()
        docs = storage.documents_dir() / storage.FOLDER_NAME
        cloud = storage.is_cloud_synced(desktop)

        body = ttk.Frame(self, padding=16)
        body.pack()
        try:
            self._logo = ImageTk.PhotoImage(Image.open(resource_path("logo-small.png")).resize((56, 56), Image.LANCZOS))
            ttk.Label(body, image=self._logo).grid(row=0, column=0, rowspan=2, padx=(0, 12), sticky="n")
        except Exception:
            pass
        ttk.Label(body, text="Où ranger vos captures ?", font=("Segoe UI", 14, "bold")).grid(row=0, column=1, sticky="w")
        ttk.Label(body, text="Je crée un dossier sur votre bureau, avec le logo jfb4plai :",
                  wraplength=460).grid(row=1, column=1, sticky="w")
        self.path_lbl = ttk.Label(body, text=str(desktop), font=("Segoe UI", 10, "bold"), wraplength=460,
                                  foreground="#1565C0")
        self.path_lbl.grid(row=2, column=0, columnspan=2, pady=8, sticky="w")
        row = 3
        if cloud:
            warn = tk.Label(body, text=CLOUD_WARNING, justify="left", wraplength=460, bg="#FFF3CD", fg="#664D03",
                            relief="solid", bd=1, padx=10, pady=8)
            warn.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 8))
            row += 1
        if legacy_exists:
            ttk.Label(body, text="Vos séries précédentes restent dans « Images\\Captures PLAI » : "
                                 "retrouvez-les avec le bouton « Rouvrir… ».", wraplength=460,
                      foreground="#555").grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 8))
            row += 1
        btns = ttk.Frame(body)
        btns.grid(row=row, column=0, columnspan=2, sticky="ew")
        self.primary = ttk.Button(btns, text="✔  Créer le dossier sur le bureau", command=lambda: self._done(desktop))
        self.primary.pack(fill="x", pady=2, ipady=4)
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
