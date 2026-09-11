"""Rebuild reviewed examples / Reconstruir exemplos revisados."""

import json
from pathlib import Path

from encounter_kit.common import html_page
from encounter_kit.core import analyze

ROOT = Path(__file__).resolve().parents[1]
cases = []
for path in sorted((ROOT / "examples").glob("*.json")):
    data = json.loads(path.read_text("utf-8"))
    report = analyze(data)
    (ROOT / "examples/expected").mkdir(exist_ok=True)
    (ROOT / "examples/expected" / path.name).write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    cases.append({"input": data, "report": report})
(ROOT / "docs/index.html").write_text(html_page(cases), encoding="utf-8")
print("Rebuilt three cases / Três casos reconstruídos")
