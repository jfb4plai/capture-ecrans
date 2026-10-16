"""Envoie un fichier à VirusTotal (API v3, clé gratuite) et écrit un résumé : python virustotal.py FICHIER SORTIE.

Clé : variable d'environnement VT_API_KEY. ATTENTION : le fichier envoyé devient accessible aux partenaires de
VirusTotal ; à n'utiliser que pour un programme destiné à être public (c'est le cas ici : code ouvert).
Écrit d'après la documentation de l'API ; non testé en direct depuis l'environnement de développement.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import urllib.request
import uuid
from pathlib import Path

API = "https://www.virustotal.com/api/v3"


def multipart(path: Path) -> tuple[bytes, str]:
    boundary = uuid.uuid4().hex
    head = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{path.name}\"\r\n"
            "Content-Type: application/octet-stream\r\n\r\n").encode()
    return head + path.read_bytes() + f"\r\n--{boundary}--\r\n".encode(), boundary


def _call(req, urlopen=urllib.request.urlopen):
    with urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))


def submit(path: Path, key: str, urlopen=urllib.request.urlopen) -> str:
    data, boundary = multipart(path)
    req = urllib.request.Request(f"{API}/files", data=data, method="POST", headers={
        "x-apikey": key, "Content-Type": f"multipart/form-data; boundary={boundary}"})
    return _call(req, urlopen)["data"]["id"]


def wait(analysis_id: str, key: str, timeout: int = 600, urlopen=urllib.request.urlopen, sleep=time.sleep) -> dict:
    deadline = time.monotonic() + timeout
    while True:
        req = urllib.request.Request(f"{API}/analyses/{analysis_id}", headers={"x-apikey": key})
        attrs = _call(req, urlopen)["data"]["attributes"]
        if attrs.get("status") == "completed" or time.monotonic() > deadline:
            return attrs
        sleep(20)


def summarize(attrs: dict, sha256: str) -> str:
    stats = attrs.get("stats", {}) or {}
    mal, sus = stats.get("malicious", 0), stats.get("suspicious", 0)
    total = sum(v for k, v in stats.items() if isinstance(v, int))
    if attrs.get("status") != "completed":
        status, note = "NON_CONCLUANT", "L'analyse n'était pas terminée au moment du relevé."
    elif mal + sus == 0:
        status, note = "PROPRE", "Aucun moteur ne signale le fichier."
    else:
        status = "A_VERIFIER"
        note = ("Au moins un moteur le signale. Les programmes empaquetés (PyInstaller) déclenchent parfois de faux "
                "positifs chez un ou deux moteurs peu connus : consultez le détail avant de conclure.")
    return (f"STATUT: {status}\nMoteurs : {mal} malveillant(s), {sus} suspect(s), sur {total} résultats.\n{note}\n"
            f"Rapport complet : https://www.virustotal.com/gui/file/{sha256}")


def main(argv=None) -> int:
    argv = argv or sys.argv[1:]
    path, out = Path(argv[0]), Path(argv[1])
    key = os.environ.get("VT_API_KEY", "")
    if not key:
        print("VT_API_KEY absente : analyse VirusTotal ignorée.")
        return 0
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    try:
        attrs = wait(submit(path, key), key)
        out.write_text(summarize(attrs, sha), "utf-8")
    except Exception as e:  # une panne de VirusTotal ne doit jamais bloquer une version
        out.write_text(f"STATUT: NON_CONCLUANT\nVirusTotal injoignable ou erreur : {e}", "utf-8")
    print(out.read_text("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
