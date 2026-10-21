import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from capture_ecran import recorder


def test_rect_even_and_origin_offset():
    # écran secondaire à gauche : l'origine de l'écran virtuel est négative
    assert recorder.screen_rect((100, 50, 741, 411), (-1920, 0)) == (-1820, 50, 640, 360)


@pytest.mark.parametrize("box", [(0, 0, 10, 300), (0, 0, 300, 15)])
def test_rect_too_small(box):
    with pytest.raises(recorder.RecorderError):
        recorder.screen_rect(box, (0, 0))


def test_video_command_has_no_audio():
    cmd = recorder.build_command("ffmpeg", (10, 20, 640, 360), Path("v.mp4"))
    assert cmd[cmd.index("-offset_x") + 1] == "10"
    assert cmd[cmd.index("-video_size") + 1] == "640x360"
    assert "h264_mf" in cmd and "libx264" not in cmd
    assert "dshow" not in cmd and "-c:a" not in cmd
    assert cmd[-1] == "v.mp4"


def test_audio_command_records_wav():
    cmd = recorder.build_audio_command("ffmpeg", "Micro (Test)", Path("m.wav"))
    assert "audio=Micro (Test)" in cmd and cmd[-1] == "m.wav"


def test_mux_uses_native_aac_and_offset():
    cmd = recorder.build_mux_command("ffmpeg", Path("v.mp4"), Path("m.wav"), 0.25, Path("o.mp4"))
    assert cmd[cmd.index("-c:a") + 1] == "aac"  # pas aac_mf : coupe le son
    assert cmd[cmd.index("-itsoffset") + 1] == "0.250"
    assert cmd[cmd.index("-c:v") + 1] == "copy"


def test_mux_without_audio_copies_video():
    cmd = recorder.build_mux_command("ffmpeg", Path("v.mp4"), None, 0, Path("o.mp4"))
    assert "-itsoffset" not in cmd and "-c:a" not in cmd


def test_parse_microphones():
    txt = ('[in#0] "HP Camera" (video)\n[in#0]   Alternative name "@device_pnp_x"\n'
           '[in#0] "Microphone Array (AMD Audio Device)" (audio)\n[in#0]   Alternative name "@device_cm_y"\n')
    assert recorder.parse_microphones(txt) == ["Microphone Array (AMD Audio Device)"]


def test_parse_duration():
    assert recorder.parse_duration("  Duration: 00:01:02.50, start: 0.000000, bitrate: 1411 kb/s") == 62.5
    assert recorder.parse_duration("rien") == 0.0


@pytest.mark.parametrize("text,seconds", [("", 0), ("  ", 0), ("10", 600), (" 1 ", 60), ("600", 36000)])
def test_parse_limit_ok(text, seconds):
    assert recorder.parse_limit(text) == seconds


@pytest.mark.parametrize("text", ["0", "601", "-5", "1,5", "dix", "10 min"])
def test_parse_limit_invalid(text):
    with pytest.raises(ValueError):
        recorder.parse_limit(text)
