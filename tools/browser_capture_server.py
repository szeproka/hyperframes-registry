"""Serve registry/blocks and save frames a browser page posts back, for previews the render
pipeline cannot make (the shader transitions draw their WebGL only in a real browser).

Usage: python3 tools/browser_capture_server.py [port]  (default 8765)
POST /save?name=<item>&i=<frame>  body: a data:image/jpeg;base64,... URL
Frames land in ~/.cache/hyperframes-registry-refresh/frames-<item>/frame-<i>.jpg.
"""

import base64
import http.server
import os
import re
import sys
from urllib.parse import parse_qs, urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOCKS = os.path.join(ROOT, "registry", "blocks")
OUT = os.path.expanduser("~/.cache/hyperframes-registry-refresh")


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BLOCKS, **kwargs)

    def do_POST(self):
        query = parse_qs(urlparse(self.path).query)
        name = query.get("name", [""])[0]
        index = query.get("i", [""])[0]
        if not re.fullmatch(r"[a-z0-9-]+", name) or not index.isdigit():
            self.send_error(400)
            return
        body = self.rfile.read(int(self.headers.get("Content-Length", 0))).decode()
        data = base64.b64decode(body.split(",", 1)[1])
        folder = os.path.join(OUT, "frames-" + name)
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, f"frame-{int(index):04d}.jpg"), "wb") as f:
            f.write(data)
        self.send_response(204)
        self.end_headers()

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
