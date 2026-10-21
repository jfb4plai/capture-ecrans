"""Enregistrement vidéo d'une zone de l'écran (ffmpeg : gdigrab pour l'image, dshow pour le micro)."""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

FPS = 15
MIN_SIDE = 16  # en dessous, l'encodeur H.264 de Windows refuse l'image


class RecorderError(Exception):
    """Message destiné à l'utilisateur."""


def _even(n: int) -> int:
    return n - (n % 2)  # H.264 (yuv420p) exige une largeur et une hauteur paires


def screen_rect(box: tuple[int, int, int, int], origin: tuple[int, int]) -> tuple[int, int, int, int]:
    """Rectangle (x, y, largeur, hauteur) en coordonnées de l'écran virtuel, dimensions paires.
    `box` = (x0, y0, x1, y1) dans l'image de l'écran virtuel ; `origin` = coin haut-gauche (peut être négatif)."""
    w = _even(box[2] - box[0])
    h = _even(box[3] - box[1])
    if w < MIN_SIDE or h < MIN_SIDE:
        raise RecorderError("La zone est trop petite pour une vidéo (au moins 16 × 16 pixels).")
    return box[0] + origin[0], box[1] + origin[1], w, h


def build_command(ffmpeg: str, rect: tuple[int, int, int, int], out: Path,
                  draw_cursor: bool = True, fps: int = FPS) -> list[str]:
    """Image seule. Le son est enregistré à part puis assemblé : filmé dans la même commande, le micro perdait
    2 à 3 s sur 9 s (essai du 2026-10-21, encodeur H.264 de Windows lent au démarrage)."""
    x, y, w, h = rect
    return [ffmpeg, "-hide_banner", "-y",
            "-f", "gdigrab", "-framerate", str(fps), "-draw_mouse", "1" if draw_cursor else "0",
            "-offset_x", str(x), "-offset_y", str(y), "-video_size", f"{w}x{h}", "-i", "desktop",
            "-c:v", "h264_mf", "-b:v", "4M", "-pix_fmt", "yuv420p", "-fps_mode", "cfr", "-r", str(fps),
            str(out)]


def build_audio_command(ffmpeg: str, mic: str, out: Path) -> list[str]:
    return [ffmpeg, "-hide_banner", "-y", "-f", "dshow", "-i", f"audio={mic}", "-c:a", "pcm_s16le", str(out)]


def build_mux_command(ffmpeg: str, video: Path, audio: Path | None, audio_offset: float, out: Path) -> list[str]:
    """Image copiée telle quelle ; le son (décalé de `audio_offset` s par rapport à l'image) est encodé en AAC."""
    cmd = [ffmpeg, "-hide_banner", "-y", "-i", str(video)]
    if audio:
        cmd += ["-itsoffset", f"{audio_offset:.3f}", "-i", str(audio), "-map", "0:v", "-map", "1:a",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "128k"]  # aac natif : aac_mf coupait le son à 0,5 s
    else:
        cmd += ["-c:v", "copy"]
    return cmd + ["-movflags", "+faststart", str(out)]


def parse_duration(text: str) -> float:
    """Durée en secondes dans la sortie de `ffmpeg -i fichier` (ligne « Duration: 00:00:07.52 »), 0 si absente."""
    m = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", text)
    return int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3]) if m else 0.0


def media_duration(ffmpeg: str, path: Path) -> float:
    try:
        r = subprocess.run([ffmpeg, "-hide_banner", "-i", str(path)], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=30, creationflags=_NO_WINDOW)
    except (OSError, subprocess.SubprocessError):
        return 0.0
    return parse_duration(r.stderr or "")


def parse_microphones(text: str) -> list[str]:
    """Noms des périphériques audio dans la sortie de `ffmpeg -list_devices true -f dshow -i dummy`."""
    return re.findall(r'"([^"]+)" \(audio\)', text)


def list_microphones(ffmpeg: str) -> list[str]:
    try:
        r = subprocess.run([ffmpeg, "-hide_banner", "-list_devices", "true", "-f", "dshow", "-i", "dummy"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15,
                           creationflags=_NO_WINDOW)
    except (OSError, subprocess.SubprocessError):
        return []
    return parse_microphones(r.stderr or "")


_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0


class ScreenRecorder:
    def __init__(self):
        self._v: subprocess.Popen | None = None
        self._a: subprocess.Popen | None = None
        self._logs: list = []
        self._t_v = self._t_a = 0.0
        self._start = 0.0
        self._ffmpeg = ""
        self.out: Path | None = None
        self.mic_failed = False

    @property
    def running(self) -> bool:
        return self._v is not None and self._v.poll() is None

    @property
    def elapsed(self) -> float:
        return time.monotonic() - self._start if self._v else 0.0

    def _spawn(self, cmd: list[str]) -> subprocess.Popen:
        log = tempfile.TemporaryFile()  # stderr dans un fichier : un tube plein bloquerait ffmpeg
        self._logs.append(log)
        return subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=log,
                                creationflags=_NO_WINDOW)

    def start(self, ffmpeg: str, rect: tuple[int, int, int, int], out: Path, mic: str | None = None,
              draw_cursor: bool = True) -> None:
        out = Path(out)
        out.parent.mkdir(parents=True, exist_ok=True)
        self._ffmpeg, self.out, self.mic_failed = ffmpeg, out, False
        self._tmp_v, self._tmp_a = out.with_suffix(".video.mp4"), out.with_suffix(".micro.wav")
        try:
            if mic:  # le micro d'abord : il met ~1,5 s à s'ouvrir (constaté) et on ne veut pas perdre le début de la voix
                self._a = self._spawn(build_audio_command(ffmpeg, mic, self._tmp_a))
                deadline = time.monotonic() + 4
                while time.monotonic() < deadline and self._a.poll() is None and "Press [q]" not in self._text(0):
                    time.sleep(0.05)
            self._t_v = time.monotonic()
            self._v = self._spawn(build_command(ffmpeg, rect, self._tmp_v, draw_cursor))
        except OSError as e:
            self._abort()
            raise RecorderError(f"ffmpeg n'a pas pu démarrer ({e}).") from e
        self._start = self._t_v
        time.sleep(0.8)  # un échec immédiat (zone hors écran) se voit tout de suite
        if self._v.poll() is not None:
            tail = self._tail(len(self._logs) - 1)
            self._abort()
            raise RecorderError("L'enregistrement n'a pas démarré." + (f" Détail : {tail}" if tail else ""))
        if self._a is not None and self._a.poll() is not None:
            self._a = None
            self.mic_failed = True  # la vidéo continue sans micro ; l'appelant prévient l'utilisateur

    @staticmethod
    def _signal_quit(proc: subprocess.Popen | None) -> None:
        if proc is None or proc.poll() is not None or not proc.stdin:
            return
        try:
            proc.stdin.write(b"q")
            proc.stdin.flush()
            proc.stdin.close()
        except (OSError, ValueError):
            pass

    @staticmethod
    def _wait(proc: subprocess.Popen | None) -> None:
        if proc is None:
            return
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()

    def stop(self) -> Path | None:
        """Arrête les enregistrements, assemble image et son ; retourne le MP4, ou None s'il est inutilisable."""
        if self._v is None:
            return None
        self._signal_quit(self._a)  # les deux d'un coup : la fin du son sert de repère pour caler l'image
        self._signal_quit(self._v)
        self._wait(self._a)
        self._wait(self._v)
        out = self.out
        has_audio = self._a is not None and self._tmp_a.exists() and self._tmp_a.stat().st_size > 1000
        ok = self._tmp_v.exists() and self._tmp_v.stat().st_size > 1000
        if ok:
            # On cale la FIN du son sur la fin de l'image.
            offset = media_duration(self._ffmpeg, self._tmp_v) - media_duration(self._ffmpeg, self._tmp_a)                 if has_audio else 0.0  # négatif si le son a commencé avant l'image : son début est alors rogné
            r = subprocess.run(build_mux_command(self._ffmpeg, self._tmp_v, self._tmp_a if has_audio else None,
                                                 offset, out),
                               capture_output=True, creationflags=_NO_WINDOW)
            ok = r.returncode == 0 and out.exists() and out.stat().st_size > 1000
        for tmp in (self._tmp_v, self._tmp_a):
            tmp.unlink(missing_ok=True)
        self._abort()
        return out if ok else None

    def _text(self, i: int) -> str:
        try:
            log = self._logs[i]
            log.seek(0)
            return log.read().decode("utf-8", "replace")
        except (OSError, ValueError, IndexError):
            return ""

    def _tail(self, i: int) -> str:
        lines = [l.strip() for l in self._text(i).splitlines() if l.strip()]
        return lines[-1] if lines else ""

    def _abort(self) -> None:
        for p in (self._v, self._a):
            if p is not None and p.poll() is None:
                p.kill()
        for log in self._logs:
            log.close()
        self._logs, self._v, self._a = [], None, None
