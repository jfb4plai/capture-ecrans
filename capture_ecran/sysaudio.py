"""Son de l'ordinateur (ce qu'on entend dans les haut-parleurs) : capture WASAPI « loopback » (Windows), écrite en WAV.

Windows n'envoie AUCUNE donnée quand rien ne joue : le fichier est donc reconstruit sur l'horloge, avec des silences
insérés là où il n'y a pas eu de son, pour que la piste ait exactement la durée de l'enregistrement."""
from __future__ import annotations

import threading
import time
import wave
from pathlib import Path


class SystemAudioError(Exception):
    """Message destiné à l'utilisateur."""


def available() -> bool:
    """Une capture du son de l'ordinateur est-elle possible sur cette machine ?"""
    try:
        import pyaudiowpatch as pa
    except ImportError:
        return False
    p = pa.PyAudio()
    try:
        p.get_default_wasapi_loopback()
        return True
    except Exception:
        return False
    finally:
        p.terminate()


def fill_gap(expected_frames: int, got_frames: int, threshold: int) -> int:
    """Nombre d'images (échantillons) de silence à insérer avant un nouveau bloc : l'écart entre ce que l'horloge
    annonce et ce qui a été reçu, s'il dépasse `threshold` (sinon 0 : simple gigue de livraison)."""
    gap = expected_frames - got_frames
    return gap if gap > threshold else 0


class SystemAudioRecorder:
    def __init__(self):
        self._pa = None
        self._stream = None
        self._wav = None
        self._t0 = 0.0
        self._frames = 0          # images (échantillons par canal) écrites
        self._rate = 0
        self._width = 2
        self._channels = 2
        self._lock = threading.Lock()
        self.started_at = 0.0     # horloge monotonic du début réel

    def start(self, path: Path) -> None:
        try:
            import pyaudiowpatch as pa
        except ImportError as e:
            raise SystemAudioError("Le son de l'ordinateur n'est pas disponible dans cette version du programme.") from e
        self._pa = pa.PyAudio()
        try:
            dev = self._pa.get_default_wasapi_loopback()
        except Exception as e:
            self._pa.terminate()
            self._pa = None
            raise SystemAudioError("Aucune sortie audio Windows détectée : le son de l'ordinateur ne peut pas être "
                                   "enregistré.") from e
        self._rate = int(dev["defaultSampleRate"])
        self._channels = max(1, int(dev["maxInputChannels"]))
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._wav = wave.open(str(path), "wb")
        self._wav.setnchannels(self._channels)
        self._wav.setsampwidth(self._width)
        self._wav.setframerate(self._rate)
        self._frames = 0
        threshold = max(1, int(self._rate * 0.05))
        silence_unit = b"\x00" * (self._width * self._channels)

        def callback(in_data, frame_count, time_info, status):
            with self._lock:
                if self._wav is None:
                    return (None, pa.paContinue)
                expected = int((time.monotonic() - self._t0) * self._rate) - frame_count
                gap = fill_gap(expected, self._frames, threshold)
                while gap > 0:  # par blocs, sans allouer un énorme silence d'un coup
                    n = min(gap, self._rate)
                    self._wav.writeframes(silence_unit * n)
                    self._frames += n
                    gap -= n
                self._wav.writeframes(in_data)
                self._frames += frame_count
            return (None, pa.paContinue)

        try:
            self._t0 = time.monotonic()
            self.started_at = self._t0
            self._stream = self._pa.open(format=pa.paInt16, channels=self._channels, rate=self._rate, input=True,
                                         input_device_index=dev["index"], frames_per_buffer=1024,
                                         stream_callback=callback)
        except Exception as e:
            self._close()
            raise SystemAudioError(f"Impossible d'ouvrir la capture du son de l'ordinateur ({e}).") from e

    def stop(self) -> float:
        """Termine le fichier avec le silence final jusqu'à maintenant ; retourne sa durée en secondes."""
        with self._lock:
            if self._wav is not None:
                total = int((time.monotonic() - self._t0) * self._rate)
                tail = total - self._frames
                if tail > 0:
                    self._wav.writeframes(b"\x00" * (self._width * self._channels) * tail)
                    self._frames += tail
        dur = self._frames / self._rate if self._rate else 0.0
        self._close()
        return dur

    def _close(self) -> None:
        stream, self._stream = self._stream, None
        if stream is not None:
            try:
                stream.stop_stream()
                stream.close()
            except Exception:
                pass
        with self._lock:
            wav, self._wav = self._wav, None
        if wav is not None:
            wav.close()
        if self._pa is not None:
            try:
                self._pa.terminate()
            except Exception:
                pass
            self._pa = None
