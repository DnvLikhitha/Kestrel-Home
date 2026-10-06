#!/usr/bin/env python3
"""
server.py - Kestrel Home Warranty Claim Review Service
Single-endpoint fraud scoring service with plain-English explanation.
Zero external dependencies required at runtime.
"""

import http.server
import json
import os
import sys
from urllib.parse import urlparse

# Ensure local kestrel module is importable
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import kestrel

PORT = int(os.environ.get("PORT", 8000))
STATIC_DIR = os.path.join(CURRENT_DIR, "static")

REQUIRED_FIELDS = [
    "partner_id",
    "sku",
    "claim_amount_inr",
    "days_since_purchase",
    "partner_inspected",
    "photo_attached"
]

class KestrelRequestHandler(http.server.BaseHTTPRequestHandler):
    def send_json(self, status_code: int, data: dict):
        response_bytes = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(response_bytes)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/health":
            self.send_json(200, {"status": "ok", "service": "kestrel-fraud-review", "version": "1.0"})
            return

        # Serve static HTML interface
        if path == "/" or path == "/index.html":
            file_path = os.path.join(STATIC_DIR, "index.html")
            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return

        self.send_json(404, {"error": "Endpoint not found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path != "/api/score":
            self.send_json(404, {"error": "Endpoint not found. Use POST /api/score"})
            return

        content_length = self.headers.get("Content-Length")
        if not content_length:
            self.send_json(400, {"error": "Bad Request: Missing Content-Length header"})
            return

        try:
            length = int(content_length)
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body)
        except Exception as e:
            self.send_json(400, {"error": f"Invalid JSON payload: {str(e)}"})
            return

        if not isinstance(data, dict):
            self.send_json(400, {"error": "Payload must be a JSON object"})
            return

        # Validate required fields
        missing = [f for f in REQUIRED_FIELDS if f not in data or data[f] is None or data[f] == ""]
        if missing:
            self.send_json(400, {
                "error": f"Missing required fields: {', '.join(missing)}",
                "required": REQUIRED_FIELDS
            })
            return

        # Validate types
        try:
            claim_amount = float(data["claim_amount_inr"])
            if claim_amount < 0:
                raise ValueError("claim_amount_inr must be positive")
        except ValueError:
            self.send_json(400, {"error": "claim_amount_inr must be a valid non-negative number"})
            return

        try:
            days = int(data["days_since_purchase"])
            if days < 0:
                raise ValueError("days_since_purchase must be non-negative")
        except ValueError:
            self.send_json(400, {"error": "days_since_purchase must be a valid non-negative integer"})
            return

        inspected = str(data["partner_inspected"]).upper()
        if inspected not in ["Y", "N"]:
            self.send_json(400, {"error": "partner_inspected must be 'Y' or 'N'"})
            return

        photo = str(data["photo_attached"]).upper()
        if photo not in ["Y", "N"]:
            self.send_json(400, {"error": "photo_attached must be 'Y' or 'N'"})
            return

        try:
            result = kestrel.score_claim(data)
            self.send_json(200, result)
        except Exception as e:
            self.send_json(500, {"error": f"Scoring error: {str(e)}"})

    def log_message(self, format, *args):
        # Clean logging
        sys.stderr.write(f"[{self.log_date_time_string()}] {format % args}\n")

def run(port=PORT):
    server_address = ("", port)
    httpd = http.server.HTTPServer(server_address, KestrelRequestHandler)
    print(f"============================================================")
    print(f" Kestrel Home Warranty Claim Review Service")
    print(f" Running at http://localhost:{port}")
    print(f" Endpoints: GET /api/health | POST /api/score")
    print(f"============================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()

if __name__ == "__main__":
    run()
