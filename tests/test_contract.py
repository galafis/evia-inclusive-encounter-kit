import hashlib
import json
import re
import subprocess
import sys
import tempfile
import threading
import unittest
from copy import deepcopy
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from encounter_kit.__main__ import make_server
from encounter_kit.common import fingerprint, html_page, loads, write_bundle
from encounter_kit.core import analyze, artifacts

ROOT = Path(__file__).resolve().parents[1]


def sample(name="baseline"):
    return json.loads((ROOT / "examples" / f"{name}.json").read_text("utf-8"))


class ContractTests(unittest.TestCase):
    def test_examples_are_deterministic_and_do_not_mutate_input(self):
        for path in (ROOT / "examples").glob("*.json"):
            data = json.loads(path.read_text("utf-8"))
            before = deepcopy(data)
            with self.subTest(example=path.name):
                self.assertEqual(analyze(data), analyze(data))
                self.assertEqual(data, before)

    def test_unknown_fields_rejected(self):
        data = sample()
        data["participantName"] = "Example"
        with self.assertRaises(ValueError):
            analyze(data)

    def test_only_synthetic_input(self):
        data = sample()
        data["source"] = "manual"
        with self.assertRaises(ValueError):
            analyze(data)

    def test_both_languages_required(self):
        data = sample()
        del data["title"]["pt"]
        with self.assertRaises(ValueError):
            analyze(data)

    def test_whitespace_title_rejected(self):
        data = sample()
        data["title"]["pt"] = "   "
        with self.assertRaises(ValueError):
            analyze(data)

    def test_duplicate_json_keys_rejected(self):
        with self.assertRaises(ValueError):
            loads('{"schemaVersion":1,"schemaVersion":2}')

    def test_nonfinite_and_oversize_rejected(self):
        for raw in ('{"number": NaN}', '{"number": Infinity}', " " * (1048576 + 1)):
            with self.subTest(raw=raw[:30]), self.assertRaises(ValueError):
                loads(raw)
        data = sample()
        data["title"]["en"] = float("inf")
        with self.assertRaises(ValueError):
            analyze(data)

    def test_deeply_nested_input_is_rejected(self):
        with self.assertRaises(ValueError):
            loads("[" * 2000 + "0" + "]" * 2000)
        data = sample()
        nested = []
        data["extra"] = nested
        for _ in range(50):
            child = []
            nested.append(child)
            nested = child
        with self.assertRaises(ValueError):
            analyze(data)

    def test_fingerprint_changes_with_input_not_key_order(self):
        data = sample()
        reordered = dict(reversed(list(data.items())))
        self.assertEqual(fingerprint(data), fingerprint(reordered))
        changed = deepcopy(data)
        changed["scenarioId"] = "different"
        self.assertNotEqual(fingerprint(data), fingerprint(changed))

    def test_html_payload_roundtrip_and_script_safety(self):
        data = sample()
        data["title"]["en"] = '</script><script>alert("x")</script>&\u2028'
        report = analyze(data)
        cases = [{"input": data, "report": report}]
        page = html_page(cases)
        payload = re.search(
            r'<script type="application/json" id="payload">(.*?)</script>', page, re.DOTALL
        ).group(1)
        self.assertNotIn("<script>", payload)
        self.assertEqual(json.loads(payload)["cases"], cases)

    def test_bundle_hashes_and_refusal_to_overwrite(self):
        data = sample()
        report = analyze(data)
        with tempfile.TemporaryDirectory() as tmp:
            folder = write_bundle(data, report, Path(tmp) / "result", artifacts(data, report))
            manifest = json.loads((folder / "manifest.json").read_text())
            self.assertIn("report.html", manifest)
            self.assertIn("scenario.json", manifest)
            for name, digest in manifest.items():
                self.assertEqual(hashlib.sha256((folder / name).read_bytes()).hexdigest(), digest)
            with self.assertRaises(ValueError):
                write_bundle(data, report, folder)
            self.assertEqual(json.loads((folder / "report.json").read_text("utf-8")), report)

    def test_cli_creates_a_complete_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "new"
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "encounter_kit",
                    "analyze",
                    str(ROOT / "examples/baseline.json"),
                    "--output",
                    str(destination),
                ],
                capture_output=True,
                check=False,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((destination / "manifest.json").is_file())

    def test_cli_invalid_input_never_publishes_a_partial_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "invalid.json"
            source.write_text("{}")
            destination = Path(tmp) / "out"
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "encounter_kit",
                    "analyze",
                    str(source),
                    "--output",
                    str(destination),
                ],
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 1)
            self.assertFalse(destination.exists())


class LocalWorkbenchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = make_server(sample(), 0)
        cls.port = cls.server.server_port
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(3)

    def request(self, path="/", body=None, headers=None):
        return urlopen(
            Request(f"http://127.0.0.1:{self.port}" + path, data=body, headers=headers or {}),
            timeout=30,
        )

    def test_page_and_analysis_agree(self):
        with self.request() as response:
            self.assertIn(b"Local workbench", response.read())
        with self.request(
            "/api/analyze", json.dumps(sample()).encode(), {"Content-Type": "application/json"}
        ) as response:
            self.assertEqual(json.load(response)["report"], analyze(sample()))

    def test_invalid_input_is_explained(self):
        with self.assertRaises(HTTPError) as caught:
            self.request("/api/analyze", b"{}", {"Content-Type": "application/json"})
        self.assertEqual(caught.exception.code, 400)
        self.assertIn("error", json.load(caught.exception))

    def test_foreign_origin_and_host_are_rejected(self):
        for headers in ({"Origin": "https://example.com"}, {"Host": "example.com"}):
            with self.subTest(headers=headers), self.assertRaises(HTTPError) as caught:
                self.request(headers=headers)
            self.assertEqual(caught.exception.code, 403)

    def test_form_posts_rejected(self):
        with self.assertRaises(HTTPError) as caught:
            self.request(
                "/api/analyze", b"x=y", {"Content-Type": "application/x-www-form-urlencoded"}
            )
        self.assertEqual(caught.exception.code, 415)


if __name__ == "__main__":
    unittest.main()
