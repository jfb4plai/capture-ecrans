"""Assemble le rapport d'analyse de sécurité publié avec chaque version.

Entrées : fichiers texte dont la 1re ligne est « STATUT: PROPRE | MENACE | A_VERIFIER | NON_CONCLUANT ».
Sortie : SECURITY-REPORT.md ; code de sortie 1 si Defender ou ClamAV signalent une menace (la version
n'est alors PAS publiée). VirusTotal n'est jamais bloquant : un ou deux moteurs obscurs signalent souvent
à tort les programmes empaquetés (faux positifs) ; on affiche les chiffres et le lien pour juger.
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

PROPRE, MENACE, A_VERIFIER, NON_CONCLUANT = "PROPRE", "MENACE", "A_VERIFIER", "NON_CONCLUANT"
ICONS = {PROPRE: "✅", MENACE: "❌", A_VERIFIER: "⚠️", NON_CONCLUANT: "❔"}
LABELS = {PROPRE: "aucune menace détectée", MENACE: "MENACE DÉTECTÉE", A_VERIFIER: "à examiner",
          NON_CONCLUANT: "analyse non concluante"}
BLOCKING = {"Microsoft Defender", "ClamAV"}


def parse_status(text: str | None) -> str:
    if not text:
        return NON_CONCLUANT
    m = re.search(r"^STATUT:\s*([A-Z_]+)", text, re.M)
    return m.group(1) if m and m.group(1) in ICONS else NON_CONCLUANT


def body(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"^STATUT:.*\n?", "", text, count=1, flags=re.M).strip()


def section(name: str, where: str, text: str | None, missing: str) -> tuple[str, str]:
    if text is None:
        return f"### ❔ {name} ({where})\n\n{missing}\n", NON_CONCLUANT
    st = parse_status(text)
    detail = body(text)
    block = f"```\n{detail}\n```\n" if detail else ""
    return f"### {ICONS[st]} {name} ({where}) : {LABELS[st]}\n\n{block}", st


def build_report(version: str, sha_line: str | None, defender: str | None, clamav: str | None,
                 virustotal: str | None, now: datetime | None = None) -> tuple[str, bool]:
    now = now or datetime.now(timezone.utc)
    sha = (sha_line or "").strip()
    parts = [f"# Analyse de sécurité — Capture d'écran PLAI {version}\n",
             f"Date de l'analyse : {now:%Y-%m-%d %H:%M} UTC\n",
             f"Empreinte SHA-256 du fichier analysé :\n\n```\n{sha or 'inconnue'}\n```\n"]
    results = {}
    for key, name, where, text, missing in (
            ("d", "Microsoft Defender", "Windows, serveur de construction", defender, "Analyse non exécutée."),
            ("c", "ClamAV", "Linux, signatures du jour", clamav, "Analyse non exécutée."),
            ("v", "VirusTotal", "environ 70 moteurs", virustotal,
             "Non lancée : aucune clé VirusTotal n'est configurée (facultatif).")):
        md, st = section(name, where, text, missing)
        parts.append(md)
        results[name] = st
    threat = any(results[n] == MENACE for n in BLOCKING)
    parts.append("---\n\n**Ce que ce rapport prouve, et ce qu'il ne prouve pas.** Un résultat propre indique qu'aucun de ces "
                 "moteurs ne signale ce fichier à la date indiquée. Il ne garantit pas l'absence de tout risque, et il "
                 "**ne supprime pas** l'avertissement « Windows a protégé votre ordinateur » (SmartScreen), qui dépend de la "
                 "signature numérique et de la réputation du fichier, pas de la présence d'un virus.\n")
    parts.append("Code source complet : <https://github.com/jfb4plai/capture-ecrans>. Vous pouvez recalculer "
                 "l'empreinte du fichier téléchargé avec `Get-FileHash` (PowerShell) et la comparer à celle ci-dessus.\n")
    return "\n".join(parts), threat


def _read(path: str | None) -> str | None:
    if not path:
        return None
    p = Path(path)
    return p.read_text("utf-8", errors="replace") if p.is_file() else None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="")
    ap.add_argument("--sha")
    ap.add_argument("--defender")
    ap.add_argument("--clamav")
    ap.add_argument("--vt")
    ap.add_argument("--out", default="SECURITY-REPORT.md")
    a = ap.parse_args(argv)
    md, threat = build_report(a.version, _read(a.sha), _read(a.defender), _read(a.clamav), _read(a.vt))
    Path(a.out).write_text(md, "utf-8")
    print(md)
    if threat:
        print("MENACE signalée par Defender ou ClamAV : la version ne doit pas être publiée.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
