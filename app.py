
import os
import sqlite3
from pathlib import Path
from functools import wraps

from flask import Flask, request, jsonify, session
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change-this-secret")

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
ADMIN_PASSWORD = os.environ.get(
    "ADMIN_PASSWORD", "AURA-ADMIN-2026"
)

# هەردوو فایلەکە لە هەمان شوێن بن
DB_PATH = Path(__file__).resolve().parent / "anime.db"

# لە Railway، FRONTEND_ORIGIN دابنێ بۆ ناونیشانی ڕاستەقینەی ئەپی GitHub Pages
FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "").strip()

CORS(
    app,
    resources={r"/api/*": {"origins": [FRONTEND_ORIGIN]}}
    if FRONTEND_ORIGIN else {r"/api/*": {"origins": "*"}}
)


def db_connect():
    db = sqlite3.connect(str(DB_PATH), timeout=15)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    with db_connect() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS animes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                anime_name TEXT NOT NULL,
                japanese_name TEXT NOT NULL DEFAULT '',
                season INTEGER NOT NULL DEFAULT 1,
                episodes INTEGER NOT NULL DEFAULT 1,
                post_link TEXT NOT NULL DEFAULT ''
            )
        """)
        db.commit()


def require_admin(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        password = request.headers.get("X-Admin-Code", "")
        if password != ADMIN_PASSWORD:
            return jsonify({"error": "ڕێگەپێدراو نییت"}), 403
        return fn(*args, **kwargs)
    return wrapper


@app.get("/api/health")
def health():
    return jsonify({"ok": True, "service": "Aura Anime"})


@app.get("/api/animes")
def get_animes():
    with db_connect() as db:
        rows = db.execute(
            "SELECT * FROM animes ORDER BY id DESC"
        ).fetchall()
    return jsonify([dict(row) for row in rows])


@app.post("/api/animes")
@require_admin
def add_anime():
    data = request.get_json(silent=True) or {}

    name = str(data.get("anime_name", "")).strip()
    japanese = str(data.get("japanese_name", "")).strip()
    link = str(data.get("post_link", "")).strip()

    try:
        season = int(data.get("season", 1))
        episodes = int(data.get("episodes", 1))
    except (TypeError, ValueError):
        return jsonify({"error": "ژمارەکان دروست نین"}), 400

    if not name or len(name) > 200:
        return jsonify({"error": "ناوی ئەنیمە دروست نییە"}), 400

    if not 1 <= season <= 100 or not 1 <= episodes <= 10000:
        return jsonify({"error": "ژمارەی وەرز یان ئەڵقە هەڵەیە"}), 400

    with db_connect() as db:
        cursor = db.execute("""
            INSERT INTO animes
            (anime_name, japanese_name, season, episodes, post_link)
            VALUES (?, ?, ?, ?, ?)
        """, (name, japanese, season, episodes, link))
        db.commit()
        anime_id = cursor.lastrowid

    # ئەنیمەکە ئێستا لە هەمان داتابەیسدا پاشەکەوت کراوە.
    # بۆ ئەوەی لە بۆتدا دەرکەوێت، main.py دەبێت هەمان anime.db بخوێنێتەوە.
    return jsonify({"ok": True, "id": anime_id}), 201


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
