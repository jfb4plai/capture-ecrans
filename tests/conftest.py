import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture(scope="session")
def shared_app(tmp_path_factory):
    """UNE seule racine Tk (l'application elle-même) pour toute la session de tests. Créer une seconde racine Tk
    dans le même processus échoue par intermittence (« Can't find a usable tk.tcl ») : constaté sur la v1.2.2
    déjà publiée (3 échecs sur 8) comme sur la v1.3.x."""
    if sys.platform != "win32" and not os.environ.get("DISPLAY"):
        pytest.skip("pas d'écran")
    from capture_ecran import app as A
    from capture_ecran import config, winapi
    base = tmp_path_factory.mktemp("base")
    orig_load, orig_save, orig_beep = config.load, config.save, winapi.beep
    config.load = lambda path=None: {**orig_load(Path(os.devnull)), "base_dir": str(base),
                                     "storage_confirmed": True, "shortcut_offered": True}
    config.save = lambda cfg, path=None: None
    winapi.beep = lambda *a, **k: None
    try:
        a = A.App()
    finally:
        config.load, config.save, winapi.beep = orig_load, orig_save, orig_beep  # ne pas fuir vers les autres modules
    a.geometry("1000x700+0+0")
    a.update()
    yield a
    try:
        a.destroy()
    except Exception:
        pass


@pytest.fixture(scope="module")
def gui_patches():
    """Pendant un module GUI : jamais d'écriture des réglages réels ni de bip. Défait à la fin du module."""
    from capture_ecran import config, winapi
    mp = pytest.MonkeyPatch()
    mp.setattr(config, "save", lambda cfg, path=None: None)
    mp.setattr(winapi, "beep", lambda *a, **k: None)
    yield
    mp.undo()
