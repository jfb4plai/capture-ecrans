"""Prépare vendor/ffmpeg/ : ffmpeg.exe (build LGPL de BtbN), sa licence et le fichier des sources.

Usage : python tools/fetch_ffmpeg.py [--zip chemin_du_zip_deja_telecharge]

Refuse tout build GPL ou « nonfree » : le programme est sous licence PolyForm Noncommercial et lance ffmpeg
comme programme séparé ; seul un build LGPL a des obligations légères (texte de licence + adresse des sources).
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

URL = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-lgpl.zip"
OUT = Path(__file__).resolve().parent.parent / "vendor" / "ffmpeg"


def run(exe: Path, *args: str) -> str:
    r = subprocess.run([str(exe), "-hide_banner", *args], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=60)
    return (r.stdout or "") + (r.stderr or "")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", type=Path)
    a = ap.parse_args()
    tmp = Path(tempfile.mkdtemp(prefix="ffmpeg-lgpl-"))
    try:
        zpath = a.zip
        if not zpath:
            zpath = tmp / "ffmpeg.zip"
            print("Téléchargement :", URL)
            urllib.request.urlretrieve(URL, zpath)
        with zipfile.ZipFile(zpath) as z:
            names = {Path(n).name.lower(): n for n in z.namelist() if not n.endswith("/")}
            exe_name = next(n for n in z.namelist() if n.lower().endswith("/bin/ffmpeg.exe"))
            lic_name = next(n for n in z.namelist() if n.count("/") == 1 and n.lower().endswith("/license.txt"))
            z.extract(exe_name, tmp / "x")
            z.extract(lic_name, tmp / "x")
        exe, lic = tmp / "x" / exe_name, tmp / "x" / lic_name
        version = run(exe, "-version")
        first = version.splitlines()[0] if version else ""
        conf = next((l for l in version.splitlines() if l.startswith("configuration:")), "")
        for bad in ("--enable-gpl", "--enable-nonfree", "--enable-libx264", "--enable-libx265"):
            if bad in conf:
                print(f"REFUS : ce build contient {bad} (GPL ou non libre).", file=sys.stderr)
                return 1
        if "LESSER GENERAL PUBLIC LICENSE" not in lic.read_text("utf-8", errors="replace")[:400]:
            print("REFUS : LICENSE.txt n'est pas la LGPL.", file=sys.stderr)
            return 1
        enc = run(exe, "-encoders")
        for need in ("h264_mf", " aac "):
            if need not in enc:
                print(f"REFUS : encodeur manquant : {need.strip()}", file=sys.stderr)
                return 1
        m = re.search(r"-g([0-9a-f]{7,})", first)
        commit = m.group(1) if m else ""
        OUT.mkdir(parents=True, exist_ok=True)
        shutil.copy2(exe, OUT / "ffmpeg.exe")
        shutil.copy2(lic, OUT / "LICENSE-ffmpeg.txt")
        src = f"""FFmpeg fourni avec Capture d'écran PLAI : sources et licence
==========================================================

Le fichier ffmpeg.exe de ce dossier est FFmpeg (https://ffmpeg.org), distribué sous la licence
GNU Lesser General Public License version 3 (texte complet : LICENSE-ffmpeg.txt).
Capture d'écran PLAI le lance comme programme séparé. Vous pouvez le remplacer par un autre
ffmpeg.exe de votre choix (ou indiquer le vôtre dans les réglages).

Version : {first}
Compilation : build « lgpl » de BtbN (sans GPL, sans libx264).
{conf}

Code source correspondant (vous pouvez le demander ou le télécharger) :
  - FFmpeg, révision exacte : https://github.com/FFmpeg/FFmpeg/commit/{commit or '(voir la version ci-dessus)'}
    archive : https://github.com/FFmpeg/FFmpeg/archive/{commit or 'master'}.zip
  - Scripts de compilation du build : https://github.com/BtbN/FFmpeg-Builds
  - Téléchargement d'origine : {URL}

Capture d'écran PLAI : https://github.com/jfb4plai/capture-ecrans  (licence PolyForm Noncommercial 1.0.0, fichier LICENSE)
"""
        (OUT / "SOURCES-ffmpeg.txt").write_text(src, "utf-8")
        print("OK :", first)
        print("Dossier prêt :", OUT, f"({(OUT / 'ffmpeg.exe').stat().st_size // 1_000_000} Mo)")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
