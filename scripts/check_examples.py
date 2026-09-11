"""Reproduce committed reports exactly / Reproduzir relatórios publicados exatamente."""

import json
from pathlib import Path

from encounter_kit.common import html_page
from encounter_kit.core import analyze

ROOT = Path(__file__).resolve().parents[1]
cases = []
for source in sorted((ROOT / "examples").glob("*.json")):
    data = json.loads(source.read_text("utf-8"))
    report = analyze(data)
    expected = json.loads((ROOT / "examples/expected" / source.name).read_text("utf-8"))
    if report != expected:
        raise SystemExit("Example drift / Exemplo divergente: " + source.name)
    cases.append({"input": data, "report": report})
page = html_page(cases)
if (ROOT / "docs/index.html").read_text("utf-8") != page:
    raise SystemExit("Rebuild demo / Reconstrua a demonstração")
print(
    f"{len(cases)} reproducible cases and complete demo / casos reproduzíveis e demonstração completa"
)
