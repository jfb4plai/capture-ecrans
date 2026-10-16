"""Fenêtre principale : déclenche les captures, liste la série, lance les exports."""
from __future__ import annotations

import os
import queue
import subprocess
import sys
import time
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

from PIL import Image, ImageTk

from . import APP_NAME, __version__, config, exporter, firstrun, grabber, shortcuts, steps, storage, theme, winapi
from .resources import resource_path
from .theme import C, font
from .editor import Editor, launch_paint
from .hotkeys import HotkeyListener, parse_hotkey, pretty
from .selector import select_region
from .session import Session

MODES = {"full": "Écran entier", "region": "Zone", "window": "Fenêtre active", "steps": "Série de clics"}


class App(tk.Tk):
    def __init__(self, minimized: bool = False):
        winapi.set_dpi_aware()
        winapi.set_app_id()
        super().__init__()
        theme.apply(self)
        self.title(f"{APP_NAME} {__version__}")
        self.cfg = config.load()
        self._set_icon()
        self.session: Session | None = None
        self.busy = False
        self.events: queue.Queue[str] = queue.Queue()
        self.listener: HotkeyListener | None = None
        self.recorder: steps.StepRecorder | None = None
        self.frames: steps.FrameBuffer | None = None
        self.hook: winapi.MouseHook | None = None
        self.clicks: queue.Queue = queue.Queue()
        self._thumb = None
        self.v_cursor = tk.BooleanVar(value=self.cfg["draw_cursor"])
        self.v_halo = tk.BooleanVar(value=self.cfg["click_halo"])
        self.v_clip = tk.BooleanVar(value=self.cfg["copy_clipboard"])
        self.v_after = tk.StringVar(value=self.cfg["after_capture"])
        self._build_ui()
        self._start_hotkeys()
        self._update_folder_label()
        self._fit_window()
        self.after(150, self._fit_window)  # 2e passe : les polices et retours à la ligne ont alors leur taille réelle
        self.after(100, self._poll)
        self._minimized = minimized
        self.after(400, self._startup_flow)
        self.protocol("WM_DELETE_WINDOW", self._quit)

    # ------------------------------------------------------------------ interface
    def _fit_window(self):
        """Taille = contenu (jamais plus que l'écran). Au 2e passage on ne fait que grandir : l'utilisateur
        garde ainsi la main s'il a déjà redimensionné la fenêtre."""
        self.update_idletasks()
        w, h = self.winfo_reqwidth(), min(self.winfo_reqheight(), self.winfo_screenheight() - 90)
        if getattr(self, "_fit_done", False):
            w, h = max(w, self.winfo_width()), max(h, self.winfo_height())
        self._fit_done = True
        self.geometry(f"{w}x{h}+{max(0, (self.winfo_screenwidth() - w) // 2)}+20")
        self.minsize(min(w, 900), min(h, 560))

    def _base(self) -> Path:
        """Dossier de base des séries ; recréé (avec son icône) s'il a été supprimé."""
        return storage.ensure_capture_folder(Path(self.cfg["base_dir"]))

    def _startup_flow(self):
        self._first_run()
        if self._minimized and self.cfg.get("storage_confirmed"):
            self.iconify()   # lancé au démarrage de Windows : discret, dans la barre des tâches
            return
        self._offer_shortcuts()

    def _apply_shortcuts(self, parent, desktop: bool, menu: bool, startup: bool) -> bool:
        """Crée / retire les raccourcis demandés. Affiche l'erreur (avec la marche à suivre manuelle) si besoin."""
        plan = ((shortcuts.desktop_lnk(), desktop, False), (shortcuts.start_menu_lnk(), menu, False),
                (shortcuts.startup_lnk(), startup, True))
        ok = True
        for lnk, want, minimized in plan:
            try:
                if want:
                    shortcuts.create(lnk, minimized=minimized)
                elif lnk.exists():
                    shortcuts.remove(lnk)
            except OSError as e:
                ok = False
                messagebox.showerror(APP_NAME, str(e), parent=parent)
        return ok

    def _offer_shortcuts(self):
        """Une seule fois : proposer un raccourci sur le bureau (et le lancement automatique)."""
        if sys.platform != "win32" or self.cfg.get("shortcut_offered"):
            return
        self.cfg["shortcut_offered"] = True
        config.save(self.cfg)
        dlg = tk.Toplevel(self)
        dlg.title("Ouvrir facilement le programme")
        theme.style_dialog(dlg)
        if self.state() == "normal":
            dlg.transient(self)
        dlg.resizable(False, False)
        body = tk.Frame(dlg, bg=C["bg"])
        body.pack(padx=22, pady=18)
        tk.Label(body, text="Toujours sous la main", bg=C["bg"], fg=C["text"], font=font("serif", 19)).pack(anchor="w")
        tk.Label(body, text="Mes raccourcis clavier ne fonctionnent que si le programme est ouvert. "
                            "Pour le retrouver en un clic, comme l'outil de capture de Windows :",
                 bg=C["bg"], fg=C["text2"], font=font("body", 10), wraplength=480, justify="left").pack(anchor="w", pady=(4, 10))
        warn = shortcuts.location_warning()
        if warn:
            theme.callout(body, "warn", warn, label="Attention", wrap=480).pack(fill="x", pady=(0, 10))
        v_desk, v_auto = tk.BooleanVar(value=not warn), tk.BooleanVar(value=False)
        card = theme.card(body)
        ttk.Checkbutton(card, text="Un raccourci « Capture d'écran PLAI » sur le bureau", variable=v_desk,
                        style="Card.TCheckbutton").pack(anchor="w", pady=2)
        ttk.Checkbutton(card, text="Lancer automatiquement à l'ouverture de Windows (réduit dans la barre des tâches)",
                        variable=v_auto, style="Card.TCheckbutton").pack(anchor="w", pady=2)
        row = tk.Frame(body, bg=C["bg"])
        row.pack(fill="x", pady=(14, 0))

        def valider():
            self._apply_shortcuts(dlg, v_desk.get(), False, v_auto.get())
            dlg.destroy()

        ttk.Button(row, text="✔  Valider", style="Primary.TButton", command=valider).pack(side="right")
        ttk.Button(row, text="Plus tard", command=dlg.destroy).pack(side="right", padx=8)
        dlg.update_idletasks()
        dlg.grab_set()
        self.wait_window(dlg)

    def _first_run(self):
        if self.cfg.get("storage_confirmed"):
            return
        chosen = firstrun.ask_storage(self)
        self.cfg["base_dir"] = str(chosen)
        self.cfg["storage_confirmed"] = True
        config.save(self.cfg)
        try:
            self._base()
        except OSError as e:
            messagebox.showerror(APP_NAME, f"Impossible de créer le dossier :\n{chosen}\n\n{e}")
        self._update_folder_label()
        self.say(f"Vos captures seront rangées dans : {chosen}")
        self.open_folder()

    def _update_folder_label(self):
        p = self.cfg["base_dir"]
        self.folder_lbl.config(text=p)
        if storage.is_cloud_synced(p):
            self.cloud_pill.pack(side="left")
        else:
            self.cloud_pill.pack_forget()

    def open_manual(self, anchor: str = ""):
        """Mode d'emploi installé avec le programme (aucune connexion Internet nécessaire)."""
        path = resource_path("mode-emploi.html")
        if path.is_file():
            webbrowser.open(path.as_uri() + anchor)
        else:
            webbrowser.open("https://jfb4plai.com/capture-ecran/mode-emploi.html" + anchor)

    def _set_icon(self):
        try:
            if sys.platform == "win32":
                self.iconbitmap(str(resource_path("icon.ico")))
            else:
                self._icon = ImageTk.PhotoImage(Image.open(resource_path("logo-small.png")))
                self.iconphoto(True, self._icon)
        except Exception:
            pass  # l'icône est un confort : jamais bloquant

    def _build_ui(self):
        # ---- en-tête (comme la barre de navigation du guide)
        head = tk.Frame(self, bg=C["bg"], highlightthickness=0)
        head.pack(fill="x")
        inner = tk.Frame(head, bg=C["bg"])
        inner.pack(fill="x", padx=16, pady=6)
        try:
            self._logo = ImageTk.PhotoImage(Image.open(resource_path("logo-ui.png")).resize((76, 76), Image.LANCZOS))
            tk.Label(inner, image=self._logo, bg=C["bg"]).pack(side="left", padx=(0, 12))
        except Exception:
            pass
        titles = tk.Frame(inner, bg=C["bg"])
        titles.pack(side="left")
        tk.Label(titles, text=APP_NAME, bg=C["bg"], fg=C["text"], font=font("serif", 19)).pack(anchor="w")
        tk.Label(titles, text=f"Outil pour les enseignants · jfb4plai.com · version {__version__}", bg=C["bg"],
                 fg=C["text3"], font=font("body", 9)).pack(anchor="w")
        ttk.Button(inner, text="⚙ Réglages", style="Small.TButton", command=self.settings).pack(side="right", padx=(6, 0))
        ttk.Button(inner, text="❓ Mode d'emploi", style="Small.TButton", command=self.open_manual).pack(side="right")
        tk.Frame(self, bg=C["border"], height=1).pack(fill="x")

        # ---- dossier des captures (lien) + pastille cloud
        frow = tk.Frame(self, bg=C["bg"])
        frow.pack(fill="x", padx=16, pady=(6, 0))
        tk.Label(frow, text="📁 Mes captures :", bg=C["bg"], fg=C["text3"], font=font("body", 9)).pack(side="left")
        self.folder_lbl = ttk.Label(frow, text="", style="Link.TLabel", cursor="hand2")
        self.folder_lbl.pack(side="left", padx=(6, 8))
        self.folder_lbl.bind("<Button-1>", lambda e: self.open_folder())
        self.cloud_pill = theme.pill(frow, "☁ dossier synchronisé (cloud)", "warn")

        # ---- bandeau sombre : les raccourcis (comme .leitmotiv du guide)
        dark = tk.Frame(self, bg=C["dark"])
        dark.pack(fill="x", padx=16, pady=(8, 0))
        tk.Label(dark, text="« Ouvrez votre menu déroulant, puis appuyez sur le raccourci. »", bg=C["dark"],
                 fg=C["dark_text"], font=font("serif_italic", 13), anchor="w").pack(fill="x", padx=16, pady=(9, 6))
        keys = tk.Frame(dark, bg=C["dark"])
        keys.pack(fill="x", padx=16, pady=(0, 10))
        self._hint = {}
        for col, (name, desc) in enumerate((("full", "écran entier"), ("region", "choisir une zone"),
                                            ("window", "fenêtre active"), ("steps", "série de clics"))):
            cell = tk.Frame(keys, bg=C["dark"])
            cell.grid(row=0, column=col, sticky="w", padx=(0, 22))
            cap = tk.Label(cell, text="", bg=C["dark2"], fg="#ffffff", font=font("medium", 9), padx=9, pady=3)
            cap.pack(anchor="w")
            tk.Label(cell, text=desc, bg=C["dark"], fg=C["dark_text"], font=font("italic", 9)).pack(anchor="w", pady=(3, 0))
            self._hint[name] = cap
        tk.Label(dark, text="Laissez le programme ouvert (réduisez la fenêtre, ne la fermez pas) : les raccourcis ne "
                            "fonctionnent que s'il tourne.", bg=C["dark"], fg=C["dark_text"], font=font("body", 9),
                 anchor="w").pack(fill="x", padx=16, pady=(0, 10))
        keys.columnconfigure(4, weight=1)
        tk.Label(keys, text="Portable : + touche Fn", bg=C["dark"], fg=C["text3"], font=font("body", 9),
                 anchor="e").grid(row=0, column=4, sticky="ne")

        # ---- deux colonnes
        body = tk.Frame(self, bg=C["bg"])
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)
        left = tk.Frame(body, bg=C["bg"])
        left.grid(row=0, column=0, sticky="nsew")
        right = tk.Frame(body, bg=C["bg"])
        right.grid(row=0, column=1, sticky="nsew")

        # -- gauche : prendre une capture
        btns = theme.section(left, "Prendre une capture")
        grid = ttk.Frame(btns, style="Card.TFrame")
        grid.pack(fill="x")
        for i, (text, cmd) in enumerate([("📷  Écran entier", lambda: self.request("full")),
                                         ("✂  Zone", lambda: self.request("region")),
                                         ("🪟  Fenêtre active", lambda: self.request("window")),
                                         ("⏱  Dans 3 secondes", lambda: self.request("full", delay=3))]):
            ttk.Button(grid, text=text, style="Big.TButton", command=cmd).grid(
                row=i // 2, column=i % 2, padx=3, pady=3, sticky="ew")
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)
        self.steps_btn = ttk.Button(btns, text="●  Enregistrer mes clics", style="Primary.TButton",
                                    command=lambda: self.request("steps"))
        self.steps_btn.pack(fill="x", padx=3, pady=(6, 2))
        ttk.Label(btns, text="Une capture numérotée à chaque clic.", style="CardMuted.TLabel").pack(anchor="w", padx=3)
        self.v_moment = tk.StringVar(value=self.cfg["steps_moment"])
        mrow = ttk.Frame(btns, style="Card.TFrame")
        mrow.pack(fill="x", padx=3, pady=(4, 0))
        ttk.Label(mrow, text="Image prise :", style="CardMuted.TLabel").pack(side="left")
        for val, txt in (("avant", "avant le clic (conseillé)"), ("apres", "0,5 s après")):
            ttk.Radiobutton(mrow, text=txt, value=val, variable=self.v_moment, style="Card.TRadiobutton",
                            command=self._save_opts).pack(side="left", padx=(8, 0))

        # -- gauche : exports
        out = theme.section(left, "Créer à partir de la série")
        orow = ttk.Frame(out, style="Card.TFrame")
        orow.pack(fill="x")
        for i, (text, cmd) in enumerate((("🎬  Vidéo", self.export_video), ("📝  Document Word", self.export_word),
                                         ("📄  Fiche HTML/PDF", self.export_html))):
            ttk.Button(orow, text=text, command=cmd).grid(row=0, column=i, padx=3, sticky="ew")
            orow.columnconfigure(i, weight=1)

        # -- droite : la série
        serie = theme.section(right, "Ma série de captures", expand=True)
        self.title_lbl = ttk.Label(serie, text="(aucune série pour l'instant)", style="Card.TLabel",
                                   font=font("serif", 14))
        self.title_lbl.pack(anchor="w")
        mid = ttk.Frame(serie, style="Card.TFrame")
        mid.pack(fill="both", expand=True, pady=6)
        self.listbox = tk.Listbox(mid, height=7, width=26, exportselection=False)
        theme.style_listbox(self.listbox)
        self.listbox.pack(side="left", fill="both", expand=True)
        self.listbox.bind("<Double-Button-1>", lambda e: self.edit_selected())
        self.listbox.bind("<<ListboxSelect>>", lambda e: self._show_thumb())
        thumb_box = tk.Frame(mid, bg=C["surface2"], highlightthickness=1, highlightbackground=C["border"],
                             width=212, height=118)
        thumb_box.pack(side="left", padx=(8, 0))
        thumb_box.pack_propagate(False)
        self.thumb_lbl = tk.Label(thumb_box, text="Aperçu", bg=C["surface2"], fg=C["text3"], font=font("body", 9))
        self.thumb_lbl.pack(fill="both", expand=True)
        acts = ttk.Frame(serie, style="Card.TFrame")
        acts.pack(fill="x")
        rows = [[("✎ Modifier", self.edit_selected), ("▲", lambda: self.move(-1)), ("▼", lambda: self.move(1)),
                 ("🗑 Supprimer", self.delete_selected), ("↻ Renuméroter", self.renumber)],
                [("📁 Dossier", self.open_folder), ("Nouvelle série", self.new_session),
                 ("Rouvrir…", self.open_session)]]
        for r, row in enumerate(rows):
            for c, (text, cmd) in enumerate(row):
                ttk.Button(acts, text=text, style="Small.TButton", command=cmd).grid(
                    row=r, column=c, padx=2, pady=2, sticky="w")

        # ---- barre d'état
        tk.Frame(self, bg=C["border"], height=1).pack(fill="x", side="bottom")
        bar = tk.Frame(self, bg=C["surface2"])
        bar.pack(fill="x", side="bottom")
        self.status = tk.Label(bar, text="Prêt.", bg=C["surface2"], fg=C["text2"], font=font("body", 9), anchor="w",
                               justify="left", wraplength=940)
        self.status.pack(fill="x", padx=16, pady=4)

    def _refresh_hint(self):
        k = self.cfg
        for name in ("full", "region", "window", "steps"):
            self._hint[name].config(text=pretty(k[f"hotkey_{name}"]))

    def _save_opts(self):
        self.cfg.update(draw_cursor=self.v_cursor.get(), click_halo=self.v_halo.get(),
                        copy_clipboard=self.v_clip.get(), after_capture=self.v_after.get(),
                        steps_moment=self.v_moment.get())
        config.save(self.cfg)

    def say(self, text: str):
        self.status.config(text=text)

    # ------------------------------------------------------------------ raccourcis
    def _start_hotkeys(self):
        if self.listener:
            self.listener.stop()
        self.listener = HotkeyListener(
            {"full": self.cfg["hotkey_full"], "region": self.cfg["hotkey_region"],
             "window": self.cfg["hotkey_window"], "steps": self.cfg["hotkey_steps"]}, self.events.put)
        self.listener.start()
        self.listener.ready.wait(2)
        self._refresh_hint()
        if self.listener.errors:
            self.say("⚠ " + " ; ".join(f"{MODES[k]} : {v}" for k, v in self.listener.errors.items()))

    def _poll(self):
        self._drain_clicks()
        try:
            while True:
                self.request(self.events.get_nowait())
        except queue.Empty:
            pass
        self.after(100, self._poll)

    # ------------------------------------------------------------------ série de clics
    def toggle_steps(self):
        if self.recorder:
            self.stop_steps()
        elif not self.busy:
            self.start_steps()

    def start_steps(self):
        if self.session and self.session.captures:
            ans = messagebox.askyesnocancel(
                APP_NAME, "Ajouter les clics à la série en cours ?\n\nOui = à la suite\nNon = nouvelle série", parent=self)
            if ans is None:
                return
            if not ans:
                self.session = None
        if self.session is None:
            self.session = Session.new(self._base())
            self.title_lbl.config(text=self.session.title)
        self.hook = winapi.MouseHook(self._hook_click)
        if not self.hook.start():
            messagebox.showerror(APP_NAME, self.hook.error)
            self.hook = None
            return
        vs = winapi.virtual_screen()
        self.recorder = steps.StepRecorder(self.session, (vs[0], vs[1]) if vs else (0, 0), self.v_cursor.get())
        self.frames = None
        if self.v_moment.get() == "avant":
            self.frames = steps.FrameBuffer()
            self.frames.start()
        self._was_visible = self.state() == "normal"
        self.iconify()
        self.title(f"● Enregistrement des clics — {pretty(self.cfg['hotkey_steps'])} pour arrêter")
        winapi.beep()

    def _hook_click(self, button: str, x: int, y: int):
        """Thread du hook, avant que l'application ne reçoive le clic : rester ultra rapide."""
        if winapi.foreground_is_own_process():
            return
        frame = self.frames.latest if self.frames else None
        self.clicks.put((button, (x, y), frame, time.monotonic()))

    def _drain_clicks(self):
        while True:
            try:
                button, pos, frame, t = self.clicks.get_nowait()
            except queue.Empty:
                return
            if not self.recorder or self.busy:
                continue
            if frame is None:  # mode « après » : on attend le résultat du clic
                self.after(500, lambda b=button, p=pos, tt=t: self._click_after(b, p, tt))
            else:
                self._record_click(button, pos, frame, t)

    def _click_after(self, button, pos, t):
        if self.recorder:
            frame, _ = grabber.grab_screen(draw_cursor=False)
            self._record_click(button, pos, frame, t)

    def _record_click(self, button, pos, frame, t):
        try:
            self.recorder.on_click(button, pos, frame, t)
            winapi.beep()
            self.title(f"● {self.recorder.count} clic(s) — {pretty(self.cfg['hotkey_steps'])} pour arrêter")
        except Exception as e:
            self.say("Erreur pendant l'enregistrement d'un clic : " + str(e))

    def stop_steps(self):
        rec, self.recorder = self.recorder, None
        if self.hook:
            self.hook.stop()
            self.hook = None
        if self.frames:
            self.frames.stop()
            self.frames = None
        while not self.clicks.empty():
            self.clicks.get_nowait()
        self.title(f"{APP_NAME} {__version__}")
        self.deiconify()
        self._fill_list(select=len(self.session.captures) - 1 if self.session and self.session.captures else None)
        n = rec.count if rec else 0
        self.say(f"{n} étape(s) enregistrée(s). Double-cliquez une ligne pour l'améliorer (légende, flèches, voix).")
        winapi.beep()

    def renumber(self):
        if not (self.session and self.session.captures):
            return
        n = steps.renumber_steps(self.session)
        self._fill_list(keep=True)
        self.say(f"{n} pastille(s) renumérotée(s)." if n else "Les numéros sont déjà dans le bon ordre.")

    # ------------------------------------------------------------------ capture
    def request(self, mode: str, delay: int = 0):
        if mode == "steps":
            self.toggle_steps()
            return
        if self.recorder:
            self.say("Une série de clics est en cours : arrêtez-la d'abord.")
            return
        if self.busy:
            self.say("Terminez d'abord l'action en cours (éditeur ou sélection ouvert).")
            return
        self.busy = True
        self._was_visible = self.state() == "normal"
        if delay:
            self.iconify()
            self._countdown(mode, delay)
        else:
            if self._was_visible:
                self.withdraw()  # pour que notre fenêtre n'apparaisse pas dans la capture
            self.after(250 if self._was_visible else 30, lambda: self._capture(mode))

    def _countdown(self, mode: str, n: int):
        if n == 0:
            self.title(f"{APP_NAME} {__version__}")
            self.after(150, lambda: self._capture(mode))
            return
        self.title(f"Capture dans {n}…")
        self.bell()
        self.after(1000, lambda: self._countdown(mode, n - 1))

    def _capture(self, mode: str):
        try:
            img, _ = grabber.grab_screen(self.v_cursor.get(), self.v_halo.get())
            if mode == "window":
                img = self._crop_window(img)
            elif mode == "region":
                img = select_region(self, img)
            if img is None:
                self._finish("Capture annulée.")
                return
            winapi.beep()
            if self.v_clip.get():
                winapi.copy_image_to_clipboard(img)
            if self.session is None:
                self.session = Session.new(self._base())
                self.title_lbl.config(text=self.session.title)
            cap = self.session.add(img)
            self._fill_list(select=len(self.session.captures) - 1)
            after = self.v_after.get()
            if after == "editor":
                Editor(self, self.session, cap, on_close=lambda: self._finish(f"Capture {cap.id} enregistrée."))
                return
            if after == "paint":
                launch_paint(str(self.session.final_path(cap)))
            self._finish(f"Capture {cap.id} enregistrée dans {self.session.folder}")
        except Exception as e:  # une capture ratée ne doit jamais fermer le programme
            self._finish("Erreur : " + str(e))
            messagebox.showerror(APP_NAME, f"La capture a échoué :\n{e}")

    def _crop_window(self, img):
        vs = winapi.virtual_screen()
        return grabber.crop_active_window(img, (vs[0], vs[1]) if vs else (0, 0))

    def _finish(self, msg: str):
        self.busy = False
        if getattr(self, "_was_visible", True):
            self.deiconify()
        self._fill_list(keep=True)
        self.say(msg)

    # ------------------------------------------------------------------ série
    def _fill_list(self, select: int | None = None, keep: bool = False):
        cur = self.listbox.curselection()
        self.listbox.delete(0, "end")
        if not self.session:
            return
        for i, c in enumerate(self.session.captures, start=1):
            self.listbox.insert("end", f"{i}.  {c.caption or '(sans légende)'}")
        idx = select if select is not None else (cur[0] if keep and cur else None)
        if idx is not None and idx < self.listbox.size():
            self.listbox.selection_set(idx)
            self.listbox.see(idx)
        self._show_thumb()

    def _selected(self):
        sel = self.listbox.curselection()
        if not (self.session and sel):
            self.say("Sélectionnez d'abord une capture dans la liste.")
            return None
        return self.session.captures[sel[0]]

    def _show_thumb(self):
        sel = self.listbox.curselection()
        if not (self.session and sel):
            self.thumb_lbl.config(image="", text="Aperçu")
            return
        try:
            im = self.session.load_final(self.session.captures[sel[0]])
            im.thumbnail((240, 150))
            self._thumb = ImageTk.PhotoImage(im)
            self.thumb_lbl.config(image=self._thumb, text="")
        except OSError:
            self.thumb_lbl.config(image="", text="(image introuvable)")

    def edit_selected(self):
        cap = self._selected()
        if cap and not self.busy:
            self.busy, self._was_visible = True, True
            Editor(self, self.session, cap, on_close=lambda: self._finish("Modification enregistrée."))

    def delete_selected(self):
        cap = self._selected()
        if cap and messagebox.askyesno(APP_NAME, "Supprimer cette capture définitivement ?"):
            self.session.remove(cap)
            self._fill_list()

    def move(self, delta: int):
        cap = self._selected()
        if cap:
            i = self.session.captures.index(cap)
            self.session.move(cap, delta)
            self._fill_list(select=max(0, min(len(self.session.captures) - 1, i + delta)))

    def new_session(self):
        title = simpledialog.askstring(APP_NAME, "Titre de la nouvelle série (ex. : Créer un compte ENT) :", parent=self)
        if title is None:
            return
        self.session = Session.new(self._base(), title.strip())
        self.session.title = title.strip() or "Ma série de captures"
        self.session.save()
        self.title_lbl.config(text=self.session.title)
        self._fill_list()
        self.say(f"Nouvelle série : {self.session.folder}")

    def open_session(self):
        d = filedialog.askdirectory(initialdir=self.cfg["base_dir"], title="Choisir le dossier d'une série")
        if not d:
            return
        try:
            self.session = Session.open(Path(d))
        except (OSError, ValueError):
            messagebox.showerror(APP_NAME, "Ce dossier ne contient pas de série (fichier session.json manquant).")
            return
        self.title_lbl.config(text=self.session.title)
        self._fill_list()

    def open_folder(self):
        folder = self.session.folder if self.session else self._base()
        folder.mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(folder)  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", str(folder)])

    # ------------------------------------------------------------------ exports
    def _need_session(self) -> bool:
        if self.session and self.session.captures:
            return True
        messagebox.showinfo(APP_NAME, "Prenez d'abord au moins une capture.")
        return False

    def export_video(self):
        if not self._need_session():
            return
        missing = [i for i, c in enumerate(self.session.captures, 1) if not c.caption.strip()]
        if missing and not messagebox.askyesno(
                APP_NAME, f"{len(missing)} capture(s) n'ont pas de légende (sous-titre) : {', '.join(map(str, missing))}.\n"
                          "Les écrans sans légende seront montrés sans sous-titre.\nContinuer ?"):
            return
        out = self.session.folder / "video"
        self.say("Création de la vidéo en cours…")
        self.update_idletasks()
        try:
            res = exporter.export_video_pack(self.session, out, ffmpeg_hint=self.cfg["ffmpeg_path"])
        except Exception as e:
            messagebox.showerror(APP_NAME, f"Échec de l'export : {e}")
            return
        self.say(res.message)
        detail = (f"Dossier : {out}\n• {len(res.frames)} images 1920×1080 avec sous-titres incrustés\n"
                  "• soustitres.srt\n" + ("• voixoff.wav (votre voix)\n" if res.voice else "")
                  + ("• video.mp4\n" if res.mp4 else ""))
        if res.ffmpeg_missing:
            if messagebox.askyesno(APP_NAME, f"{res.message}\n\n{detail}\nOuvrir le mode d'emploi vidéo maintenant ?"):
                self.open_manual("#video")
        else:
            messagebox.showinfo(APP_NAME, f"{res.message}\n\n{detail}")
        self._open(out)

    def export_word(self):
        if not self._need_session():
            return
        try:
            path = exporter.export_docx(self.session, self.session.folder / "document.docx", logo=self.cfg["logo_in_exports"])
        except Exception as e:
            messagebox.showerror(APP_NAME, f"Échec de l'export Word : {e}")
            return
        self.say(f"Document créé : {path}")
        self._open(path)

    def export_html(self):
        if not self._need_session():
            return
        path = exporter.export_html_guide(self.session, self.session.folder / "fiche_pas_a_pas.html", logo=self.cfg["logo_in_exports"])
        self.say(f"Fiche créée : {path}")
        self._open(path)

    @staticmethod
    def _open(path):
        try:
            if sys.platform == "win32":
                os.startfile(path)  # type: ignore[attr-defined]
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except OSError:
            pass

    # ------------------------------------------------------------------ réglages
    def settings(self):
        dlg = tk.Toplevel(self)
        dlg.title("Réglages")
        theme.style_dialog(dlg)
        dlg.transient(self)
        dlg.resizable(False, False)
        wrap = tk.Frame(dlg, bg=C["bg"])
        wrap.pack(fill="both", expand=True, padx=0, pady=(0, 12))

        # -- Capture
        cap = theme.section(wrap, "Capture")
        for text, var in (("Montrer le pointeur de la souris", self.v_cursor),
                          ("Entourer le pointeur d'un halo jaune", self.v_halo),
                          ("Copier aussi dans le presse-papiers (Ctrl+V)", self.v_clip)):
            ttk.Checkbutton(cap, text=text, variable=var, style="Card.TCheckbutton",
                            command=self._save_opts).pack(anchor="w", pady=1)
        ttk.Label(cap, text="Après la capture :", style="CardMuted.TLabel").pack(anchor="w", pady=(8, 0))
        fr = ttk.Frame(cap, style="Card.TFrame")
        fr.pack(anchor="w")
        for val, txt in (("editor", "Ouvrir l'éditeur"), ("paint", "Ouvrir Paint"), ("none", "Rien (juste enregistrer)")):
            ttk.Radiobutton(fr, text=txt, value=val, variable=self.v_after, style="Card.TRadiobutton",
                            command=self._save_opts).pack(side="left", padx=(0, 14), pady=2)

        # -- Raccourcis
        sc = theme.section(wrap, "Raccourcis clavier")
        fields = {}
        rows = [("hotkey_full", "Écran entier"), ("hotkey_region", "Zone"), ("hotkey_window", "Fenêtre active"),
                ("hotkey_steps", "Série de clics (début / fin)")]
        for i, (key, label) in enumerate(rows):
            ttk.Label(sc, text=label, style="Card.TLabel").grid(row=i, column=0, sticky="w", padx=(0, 16), pady=3)
            v = tk.StringVar(value=self.cfg[key].replace("shift", "maj"))
            ttk.Entry(sc, textvariable=v, width=22).grid(row=i, column=1, sticky="w")
            fields[key] = v
        ttk.Label(sc, text="Format : ctrl+maj+f9. Évitez Ctrl+Alt : sur un clavier belge, c'est la touche AltGr.",
                  style="CardMuted.TLabel").grid(row=len(rows), column=0, columnspan=2, sticky="w", pady=(6, 0))

        # -- Ouvrir facilement (Windows)
        if sys.platform == "win32":
            ow = theme.section(wrap, "Ouvrir facilement")
            v_desk = tk.BooleanVar(value=shortcuts.desktop_lnk().exists())
            v_menu = tk.BooleanVar(value=shortcuts.start_menu_lnk().exists())
            v_auto = tk.BooleanVar(value=shortcuts.startup_lnk().exists())
            for text, var in (("Raccourci sur le bureau", v_desk), ("Raccourci dans le menu Démarrer", v_menu),
                              ("Lancer automatiquement à l'ouverture de Windows (réduit dans la barre des tâches)", v_auto)):
                ttk.Checkbutton(ow, text=text, variable=var, style="Card.TCheckbutton").pack(anchor="w", pady=1)
            warn = shortcuts.location_warning()
            if warn:
                theme.callout(ow, "warn", warn, label="Attention", wrap=520).pack(fill="x", pady=(8, 0))
            ttk.Label(ow, text="Astuce : pour l'épingler à la barre des tâches, clic droit sur le raccourci › Épingler à la barre des tâches.",
                      style="CardMuted.TLabel").pack(anchor="w", pady=(6, 0))
        else:
            v_desk = v_menu = v_auto = None

        # -- Dossier et exports
        ex = theme.section(wrap, "Dossier et exports")
        ex.columnconfigure(1, weight=1)
        ttk.Label(ex, text="Dossier des captures", style="Card.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 16), pady=3)
        vdir = tk.StringVar(value=self.cfg["base_dir"])
        ttk.Entry(ex, textvariable=vdir, width=46).grid(row=0, column=1, sticky="ew")
        ttk.Button(ex, text="Parcourir…", style="Small.TButton",
                   command=lambda: vdir.set(filedialog.askdirectory(initialdir=vdir.get()) or vdir.get())
                   ).grid(row=0, column=2, padx=(6, 0))
        ttk.Label(ex, text="ffmpeg.exe (vidéo MP4)", style="Card.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 16), pady=3)
        vff = tk.StringVar(value=self.cfg["ffmpeg_path"])
        ttk.Entry(ex, textvariable=vff, width=46).grid(row=1, column=1, sticky="ew")
        ttk.Button(ex, text="Parcourir…", style="Small.TButton", command=lambda: vff.set(
            filedialog.askopenfilename(parent=dlg, title="Choisir ffmpeg.exe", filetypes=[("ffmpeg", "ffmpeg.exe")])
            or vff.get())).grid(row=1, column=2, padx=(6, 0))
        found = exporter.find_ffmpeg(self.cfg["ffmpeg_path"])
        tk.Label(ex, text=("✓ ffmpeg trouvé : " + found) if found else "ffmpeg non trouvé automatiquement (facultatif)",
                 bg=C["surface"], fg=C["green"] if found else C["amber"], font=font("body", 9), anchor="w",
                 wraplength=560, justify="left").grid(row=2, column=0, columnspan=3, sticky="w", pady=(2, 6))
        vlogo = tk.BooleanVar(value=self.cfg["logo_in_exports"])
        ttk.Checkbutton(ex, text="Ajouter le logo jfb4plai en haut des fiches HTML et documents Word",
                        variable=vlogo, style="Card.TCheckbutton").grid(row=3, column=0, columnspan=3, sticky="w")

        def apply():
            self.cfg["logo_in_exports"] = vlogo.get()
            self.cfg["ffmpeg_path"] = vff.get().strip()
            for key, v in fields.items():
                try:
                    parse_hotkey(v.get())
                except ValueError as e:
                    messagebox.showerror(APP_NAME, f"{dict(rows)[key]} : {e}", parent=dlg)
                    return
            for key, v in fields.items():
                self.cfg[key] = v.get().lower().replace(" ", "").replace("maj", "shift")
            if vdir.get() != self.cfg["base_dir"]:
                firstrun.warn_if_cloud(dlg, Path(vdir.get()))
            self.cfg["base_dir"] = vdir.get()
            self.cfg["storage_confirmed"] = True
            self._save_opts()
            config.save(self.cfg)
            if v_desk is not None:
                self._apply_shortcuts(dlg, v_desk.get(), v_menu.get(), v_auto.get())
            self._update_folder_label()
            dlg.destroy()
            self._start_hotkeys()
            if not (self.listener and self.listener.errors):
                self.say("Réglages enregistrés.")

        btns = tk.Frame(wrap, bg=C["bg"])
        btns.pack(fill="x", padx=16, pady=(12, 0))
        ttk.Button(btns, text="✔  Enregistrer", style="Primary.TButton", command=apply).pack(side="right")
        ttk.Button(btns, text="Annuler", command=dlg.destroy).pack(side="right", padx=8)
        dlg.update_idletasks()
        dlg.grab_set()

    def _quit(self):
        if self.listener:
            self.listener.stop()
        self.destroy()


def main(minimized: bool = False):
    App(minimized).mainloop()
