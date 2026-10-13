import os
import sqlite3
import subprocess
from flask import Flask, render_template_string, request, redirect, url_for, session
import requests

app = Flask(__name__)
app.secret_key = "aura_anime_secret_admin_key"

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_IDS = [6450069400, 5455374693, 8535560894, 1475355789, 5242890148]
ADMIN_PASSWORD = "aura_admin_pass"

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

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ckb" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>پانێڵی ئۆرا ئەنیمی</title>
    <style>
        body { font-family: sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; background: #1e293b; padding: 25px; border-radius: 12px; }
        h2, h3 { color: #38bdf8; text-align: center; }
        label { display: block; margin-top: 12px; font-weight: bold; }
        input { width: 100%; padding: 10px; margin-top: 5px; border-radius: 6px; border: 1px solid #334155; background: #0f172a; color: #fff; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: #0284c7; color: white; border: none; border-radius: 6px; font-size: 16px; margin-top: 18px; cursor: pointer; font-weight: bold; }
        button:hover { background: #0369a1; }
        table { width: 100%; border-collapse: collapse; margin-top: 25px; }
        th, td { border: 1px solid #334155; padding: 10px; text-align: center; }
        th { background-color: #0284c7; }
        .logout { background: #ef4444; padding: 8px 15px; float: left; text-decoration: none; color: white; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        {% if logged_in %}
            <a href="/logout" class="logout">دەرچوون 🚪</a>
            <h2>✨ پانێڵی بەڕێوەبردنی ئۆرا ئەنیمی</h2>
            
            <form action="/add" method="POST">
                <label>ناوی ئەنیمی (ئینگلیزی/کوردی):</label>
                <input type="text" name="anime_name" required>

                <label>ناوی ئەنیمی (ژاپۆنی):</label>
                <input type="text" name="japanese_name" required>

                <label>وەرز (Season):</label>
                <input type="text" name="season" placeholder="بۆ نموونە: 1" required>

                <label>ئەڵقەکان (Episodes):</label>
                <input type="text" name="episodes" placeholder="بۆ نموونە: 1-12" required>

                <label>لینکی پۆستی چەناڵ:</label>
                <input type="url" name="post_link" placeholder="https://t.me/..." required>

                <button type="submit">💾 پاشەکەوتکردن لە داتابەیس</button>
            </form>

            <h3>📁 ئەنیمییە پاشەکەوتکراوەکان</h3>
            <table>
                <tr>
                    <th>ناو</th>
                    <th>ژاپۆنی</th>
                    <th>وەرز</th>
                    <th>ئەڵقەکان</th>
                    <th>لینک</th>
                </tr>
                {% for anime in animes %}
                <tr>
                    <td>{{ anime[1] }}</td>
                    <td>{{ anime[2] }}</td>
                    <td>{{ anime[3] }}</td>
                    <td>{{ anime[4] }}</td>
                    <td><a href="{{ anime[5] }}" target="_blank" style="color: #38bdf8;">سەیرکردن</a></td>
                </tr>
                {% endfor %}
            </table>
        {% else %}
            <h2>🔒 چوونەژوورەوەی ئەدیمین</h2>
            <form action="/login" method="POST">
                <label>وشەی تێپەڕی ئەدیمین (Password):</label>
                <input type="password" name="password" required>
                <button type="submit">چوونەژوورەوە 🔑</button>
            </form>
        {% endif %}
    </div>
</body>
</html>
"""

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
    return render_template_string(HTML_TEMPLATE, logged_in=logged_in, animes=animes)

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
        f"✨ **ئەنیمیی نوێ لە ماڵپەڕەوە زیادکرا!**\n\n"
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
