from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import urllib3
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
CORS(app)

# ─────────────────────────────────────────────
CATALOGUE_URL   = os.environ.get("CATALOGUE_URL",   "https://creds.curtin.edu.au")
CATALOGUE_TOKEN = os.environ.get("CATALOGUE_TOKEN", "d3ca3e2dd2048c80f46898a36c43f46a")
# ─────────────────────────────────────────────

HEADERS = {"Authorization": f'Token token="{CATALOGUE_TOKEN}"'}


@app.after_request
def add_cors(response):
    response.headers["Access-Control-Allow-Origin"]  = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.errorhandler(Exception)
def handle_error(e):
    return jsonify({"error": str(e)}), 500


@app.route("/health")
def health():
    token_set = bool(CATALOGUE_TOKEN)
    return jsonify({"status": "ok", "token_set": token_set})


@app.route("/enrolments")
def enrolments():
    if not CATALOGUE_TOKEN:
        return jsonify({"error": "CATALOGUE_TOKEN not set"}), 500

    results, url = [], f"{CATALOGUE_URL}/api/v1/enrollments?per_page=100"
    while url:
        r = requests.get(url, headers=HEADERS, verify=False, timeout=30)
        if r.status_code == 401:
            return jsonify({"error": "Invalid API token"}), 401
        r.raise_for_status()
        data = r.json()
        page = data if isinstance(data, list) else next(
            (v for v in data.values() if isinstance(v, list)), []
        )
        results.extend(page)
        links = {
            p.split(";")[1].strip().strip('rel="'): p.split(";")[0].strip().strip("<>")
            for p in r.headers.get("Link", "").split(",") if ";" in p
        }
        url = links.get("next")
    return jsonify({"enrollments": results})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
