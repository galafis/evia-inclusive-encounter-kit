"""Validated, reproducible evidence bundles / Pacotes de evidências reproduzíveis."""

import hashlib
import json
import math
import os
import shutil
import tempfile
from importlib.resources import files
from pathlib import Path

from jsonschema import Draft202012Validator

MAX_BYTES = 1_048_576


def loads(raw):
    if len(raw.encode("utf-8")) > MAX_BYTES:
        raise ValueError("Input exceeds 1 MiB / Entrada excede 1 MiB")

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate key / Chave duplicada: " + key)
            result[key] = value
        return result

    def constant(value):
        raise ValueError("Non-finite number / Número não finito: " + value)

    try:
        decoded = json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
        bounded(decoded)
        return decoded
    except RecursionError as error:
        raise ValueError(
            "Input nesting is too deep / Entrada com profundidade excessiva"
        ) from error


def bounded(data):
    stack = [(data, 0)]
    while stack:
        value, depth = stack.pop()
        if depth > 32:
            raise ValueError("Input nesting is too deep / Entrada com profundidade excessiva")
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("Non-finite number / Número não finito")
        if isinstance(value, dict):
            stack.extend((item, depth + 1) for item in value.values())
        elif isinstance(value, list):
            stack.extend((item, depth + 1) for item in value)


def validate(data):
    bounded(data)
    schema = json.loads(files(__package__).joinpath("scenario.schema.json").read_text("utf-8"))
    error = next(Draft202012Validator(schema).iter_errors(data), None)
    if error:
        path = ".".join(map(str, error.absolute_path)) or "$"
        raise ValueError(f"Invalid input / Entrada inválida ({path}): {error.message}")
    return data


def canonical(data):
    return json.dumps(
        data, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
    )


def fingerprint(data):
    return hashlib.sha256(canonical(data).encode()).hexdigest()


def bi(en, pt):
    return {"en": en, "pt": pt}


def section(title, columns, rows):
    return {"title": title, "columns": columns, "rows": rows}


def metric(label, value):
    return {"label": label, "value": value}


def unique(items, key="id"):
    ids = [item[key] for item in items]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate identifiers / Identificadores duplicados")


def envelope(data, **kwargs):
    return {
        "schemaVersion": 1,
        "engineVersion": "1.0.0",
        "project": __package__,
        "scenarioId": data["scenarioId"],
        "source": data["source"],
        "title": data["title"],
        "inputSha256": fingerprint(data),
        **kwargs,
    }


def html_page(cases, live=False):
    template = files(__package__).joinpath("web.html").read_text("utf-8")
    # JSON is embedded in inert script text. Escape HTML and Unicode line boundaries.
    payload = json.dumps({"cases": cases, "live": live}, ensure_ascii=False, allow_nan=False)
    payload = payload.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")
    payload = payload.replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    return template.replace("__PAYLOAD__", payload)


def write_bundle(data, report, destination, artifacts=None):
    """All-or-nothing directory publication; existing evidence is never overwritten."""
    target = Path(destination).resolve()
    if target.exists():
        raise ValueError(
            "Output already exists; choose a new folder / Saída já existe; escolha outra pasta"
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".bundle-", dir=target.parent))
    try:
        content = {"scenario.json": data, "report.json": report, **(artifacts or {})}
        for name, value in content.items():
            if Path(name).name != name:
                raise ValueError("Invalid artifact name / Nome de artefato inválido")
            (temporary / name).write_text(
                json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                encoding="utf-8",
            )
        (temporary / "report.html").write_text(
            html_page([{"input": data, "report": report}]), encoding="utf-8"
        )
        manifest = {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(temporary.iterdir())
        }
        (temporary / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
        os.rename(temporary, target)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return target
