import os
import sqlite3
import subprocess
from flask import Flask, render_template, request, redirect, url_for, session
import requests

app = Flask(__name__)
app.secret_key = "aura_anime_secret_admin_key"

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_IDS = [6450069400, 5455374693, 8535560894, 1475355789, 5242890148]
ADMIN_PASSWORD = "aura_admin_pass"

# کارپێکردنی بۆتەکە لە پشتەوە
try:
    subprocess.Popen(["python", "main.py"])
except Exception as e:
    print(f"Error starting bot: {e}")

def init_db():
    conn = sqlite3.connect("anime.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS animes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            anime_name TEXT NOT NULL,
            japanese_name TEXT,
            season TEXT,
            episodes TEXT,
            post_link TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    logged_in = session.get("logged_in", False)
    animes = []
    if logged_in:
        conn = sqlite3.connect("anime.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM animes ORDER BY id DESC")
        animes = cursor.fetchall()
        conn.close()
    return render_template("index.html", logged_in=logged_in, animes=animes)

@app.route("/login", methods=["POST"])
def login():
    if request.form.get("password") == ADMIN_PASSWORD:
        session["logged_in"] = True
    return redirect(url_for("home"))

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("home"))

@app.route("/add", methods=["POST"])
def add_anime():
    if not session.get("logged_in"):
        return redirect(url_for("home"))

    anime_name = request.form.get("anime_name")
    japanese_name = request.form.get("japanese_name")
    season = request.form.get("season")
    episodes = request.form.get("episodes")
    post_link = request.form.get("post_link")

    conn = sqlite3.connect("anime.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO animes (anime_name, japanese_name, season, episodes, post_link)
        VALUES (?, ?, ?, ?, ?)
    ''', (anime_name, japanese_name, season, episodes, post_link))
    conn.commit()
    conn.close()

    message = (
        f"✨ **ئەنیمیی نوێ زیادکرا!**\n\n"
        f"📌 **ناو:** {anime_name}\n"
        f"🇯🇵 **ژاپۆنی:** {japanese_name}\n"
        f"📂 **وەرز:** {season}\n"
        f"🎬 **ئەڵقەکان:** {episodes}\n"
        f"🔗 **لینک:** {post_link}"
    )
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    if BOT_TOKEN:
        for admin_id in ADMIN_IDS:
            requests.post(url, json={"chat_id": admin_id, "text": message, "parse_mode": "Markdown"})

    return redirect(url_for("home"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
