"""Offline command line and loopback workbench / Comando offline e bancada local."""

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from .common import MAX_BYTES, html_page, loads, write_bundle
from .core import analyze, artifacts


def make_server(data, port=8765):
    initial = analyze(data)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def reply(self, code, body, kind="application/json; charset=utf-8"):
            raw = body.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(raw)
            self.wfile.flush()
            self.close_connection = True

        def trusted(self):
            host = f"127.0.0.1:{self.server.server_port}"
            return (
                self.headers.get("Host") == host
                and self.headers.get("Origin", f"http://{host}") == f"http://{host}"
            )

        def do_GET(self):
            if not self.trusted():
                return self.reply(403, "{}")
            if urlsplit(self.path).path != "/":
                return self.reply(404, "{}")
            self.reply(
                200,
                html_page([{"input": data, "report": initial}], live=True),
                "text/html; charset=utf-8",
            )

        def do_POST(self):
            if not self.trusted():
                return self.reply(403, "{}")
            if self.path != "/api/analyze":
                return self.reply(404, "{}")
            try:
                length = int(self.headers.get("Content-Length", "-1"))
                if not 0 < length <= MAX_BYTES:
                    return self.reply(
                        413, json.dumps({"error": "Input exceeds limit / Entrada fora do limite"})
                    )
                self.connection.settimeout(5)
                raw = self.rfile.read(length)
                if len(raw) != length:
                    raise ValueError("Incomplete input / Entrada incompleta")
                if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                    return self.reply(415, "{}")
                scenario = loads(raw.decode("utf-8"))
                result = analyze(scenario)
                self.reply(
                    200,
                    json.dumps(
                        {"input": scenario, "report": result}, ensure_ascii=False, allow_nan=False
                    ),
                )
            except (ValueError, TypeError, UnicodeError, TimeoutError) as error:
                self.reply(400, json.dumps({"error": str(error)}, ensure_ascii=False))

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.daemon_threads = True
    return server


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Offline social research workbench / Bancada offline de pesquisa social"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("analyze", "serve"):
        p = sub.add_parser(command)
        p.add_argument("input", type=Path)
        if command == "analyze":
            p.add_argument("--output", required=True, type=Path)
        else:
            p.add_argument("--port", default=8765, type=int)
    args = parser.parse_args(argv)
    try:
        if args.input.stat().st_size > MAX_BYTES:
            raise ValueError("Input exceeds 1 MiB / Entrada excede 1 MiB")
        data = loads(args.input.read_text("utf-8"))
        if args.command == "analyze":
            report = analyze(data)
            folder = write_bundle(data, report, args.output, artifacts(data, report))
            print(str(folder))
            return 0
        with make_server(data, args.port) as server:
            print(f"http://127.0.0.1:{server.server_port}", flush=True)
            server.serve_forever()
    except KeyboardInterrupt:
        return 0
    except (ValueError, OSError, TypeError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
