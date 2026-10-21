"""Point d'entrée de l'exécutable (import absolu : un import relatif échoue quand PyInstaller
lance un script seul). Écrit les erreurs dans un fichier journal lisible par l'utilisateur."""
import os
import sys
import traceback
from pathlib import Path


def _log_path() -> Path:
    root = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "CaptureEcranPLAI"
    root.mkdir(parents=True, exist_ok=True)
    return root / "erreur.log"


def _selftest(out: Path) -> int:
    """Vérifie que l'exécutable démarre : crée la fenêtre, la détruit, écrit OK."""
    from capture_ecran import __version__
    from capture_ecran.app import App
    from capture_ecran.resources import resource_path
    for name in ("icon.ico", "logo-small.png"):
        assert resource_path(name).is_file(), f"ressource manquante : {name}"
    from capture_ecran import exporter
    ff = exporter.find_ffmpeg()
    if getattr(sys, "frozen", False):  # l'exécutable construit doit embarquer son ffmpeg
        assert ff and Path(ff).parent.name == "ffmpeg", f"ffmpeg fourni absent (trouvé : {ff})"
        for name in ("LICENSE-ffmpeg.txt", "SOURCES-ffmpeg.txt"):
            assert (Path(ff).parent / name).is_file(), f"fichier de licence manquant : {name}"
        assert exporter.video_encoder_args(ff)[1] == "h264_mf", "ffmpeg fourni : encodeur H.264 inattendu"
    app = App()
    app.update()
    app._quit()
    out.write_text(f"OK {__version__} ffmpeg={ff}", "utf-8")
    return 0


def run() -> int:
    try:
        if "--selftest" in sys.argv:
            return _selftest(Path(sys.argv[sys.argv.index("--selftest") + 1]))
        from capture_ecran import APP_NAME, winapi
        if not winapi.acquire_single_instance():
            if not winapi.raise_existing_window(APP_NAME):
                import tkinter
                from tkinter import messagebox
                r = tkinter.Tk()
                r.withdraw()
                messagebox.showinfo(APP_NAME, "Le programme est déjà ouvert : cherchez-le dans la barre des tâches.")
            return 0
        from capture_ecran.app import main
        main(minimized="--reduit" in sys.argv)
        return 0
    except Exception:
        text = traceback.format_exc()
        try:
            _log_path().write_text(text, "utf-8")
        except OSError:
            pass
        try:
            import tkinter
            from tkinter import messagebox
            root = tkinter.Tk()
            root.withdraw()
            messagebox.showerror("Capture d'écran PLAI",
                                 "Le programme a rencontré une erreur.\n\nDétail enregistré dans :\n"
                                 f"{_log_path()}\n\n{text[-600:]}")
        except Exception:
            pass
        return 1


if __name__ == "__main__":
    sys.exit(run())
