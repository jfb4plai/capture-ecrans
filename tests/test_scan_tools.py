import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import scan_report as R  # noqa: E402
import virustotal as V  # noqa: E402

NOW = datetime(2026, 10, 16, 12, 0, tzinfo=timezone.utc)


def test_parse_status():
    assert R.parse_status("STATUT: PROPRE\nx") == R.PROPRE
    assert R.parse_status("STATUT: MENACE\n") == R.MENACE
    assert R.parse_status("n'importe quoi") == R.NON_CONCLUANT
    assert R.parse_status(None) == R.NON_CONCLUANT
    assert R.parse_status("STATUT: INVENTE") == R.NON_CONCLUANT


def test_clean_report_is_not_a_threat_and_is_honest():
    md, threat = R.build_report("v1.1.0", "abc  f.zip", "STATUT: PROPRE\nsignatures 1.2", "STATUT: PROPRE\nClamAV 1.4", None, NOW)
    assert not threat
    assert "2026-10-16 12:00 UTC" in md and "abc  f.zip" in md
    assert "✅ Microsoft Defender" in md and "✅ ClamAV" in md
    assert "Non lancée" in md                                   # VirusTotal facultatif absent : dit clairement
    assert "ne supprime pas" in md and "SmartScreen" in md     # ne promet pas ce qu'on ne peut pas tenir


@pytest.mark.parametrize("d,c", [("STATUT: MENACE\nTrojan", "STATUT: PROPRE"), ("STATUT: PROPRE", "STATUT: MENACE\nx")])
def test_defender_or_clamav_threat_blocks(d, c):
    md, threat = R.build_report("v", None, d, c, None, NOW)
    assert threat and "❌" in md


def test_unconclusive_scan_does_not_block_but_is_shown():
    md, threat = R.build_report("v", None, None, "STATUT: NON_CONCLUANT\nx", None, NOW)
    assert not threat and md.count("❔") >= 2


def test_virustotal_alert_never_blocks_but_warns():
    vt = V.summarize({"status": "completed", "stats": {"malicious": 2, "suspicious": 0, "undetected": 60, "harmless": 0}}, "ff")
    assert vt.startswith("STATUT: A_VERIFIER") and "faux" in vt and "virustotal.com/gui/file/ff" in vt
    md, threat = R.build_report("v", None, "STATUT: PROPRE", "STATUT: PROPRE", vt, NOW)
    assert not threat and "⚠️ VirusTotal" in md


def test_virustotal_summaries():
    ok = V.summarize({"status": "completed", "stats": {"malicious": 0, "suspicious": 0, "undetected": 70}}, "aa")
    assert ok.startswith("STATUT: PROPRE") and "sur 70" in ok
    assert V.summarize({"status": "queued", "stats": {}}, "aa").startswith("STATUT: NON_CONCLUANT")


class FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_virustotal_submit_and_wait_with_fake_api(tmp_path):
    f = tmp_path / "x.zip"
    f.write_bytes(b"PK\x03\x04data")
    calls = []

    def fake_urlopen(req, timeout=0):
        calls.append((req.get_method(), req.full_url, req.headers.get("X-apikey")))
        if req.get_method() == "POST":
            assert b'filename="x.zip"' in req.data and b"PK\x03\x04data" in req.data
            return FakeResp(json.dumps({"data": {"id": "AN1"}}).encode())
        state = "queued" if len([c for c in calls if c[0] == "GET"]) < 2 else "completed"
        return FakeResp(json.dumps({"data": {"attributes": {"status": state, "stats": {"malicious": 0, "undetected": 5}}}}).encode())

    aid = V.submit(f, "KEY", fake_urlopen)
    attrs = V.wait(aid, "KEY", timeout=60, urlopen=fake_urlopen, sleep=lambda s: None)
    assert aid == "AN1" and attrs["status"] == "completed"
    assert all(c[2] == "KEY" for c in calls)


def test_virustotal_main_without_key_is_a_noop(tmp_path, monkeypatch):
    monkeypatch.delenv("VT_API_KEY", raising=False)
    out = tmp_path / "o.txt"
    assert V.main([str(tmp_path / "f"), str(out)]) == 0 and not out.exists()


def test_cli_exit_code(tmp_path):
    d, c = tmp_path / "d.txt", tmp_path / "c.txt"
    d.write_text("STATUT: PROPRE\nok")
    c.write_text("STATUT: MENACE\nEicar")
    assert R.main(["--version", "v1", "--defender", str(d), "--clamav", str(c), "--out", str(tmp_path / "r.md")]) == 1
    c.write_text("STATUT: PROPRE\nok")
    assert R.main(["--version", "v1", "--defender", str(d), "--clamav", str(c), "--out", str(tmp_path / "r.md")]) == 0
    assert "Analyse de sécurité" in (tmp_path / "r.md").read_text("utf-8")
