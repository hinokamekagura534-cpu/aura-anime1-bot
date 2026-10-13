import os
import sqlite3
from flask import Flask, render_template_string, request, redirect, url_for, session
import requests

app = Flask(__name__)
app.secret_key = "aura_anime_secret_admin_key"

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_IDS = [6450069400, 5455374693, 8535560894, 1475355789, 5242890148]
ADMIN_PASSWORD = "aura_admin_pass"

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

# دیزاینی Index (لاپەڕەی سەرەکی بە شێوازی مۆدێرن و کوردی)
INDEX_TEMPLATE = """
<!DOCTYPE html>
<html lang="ckb" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>پانێڵی بەڕێوەبردنی ئۆرا ئەنیمی</title>
    <style>
        :root {
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --text-color: #f8fafc;
            --accent-color: #38bdf8;
            --button-bg: #0284c7;
            --button-hover: #0369a1;
            --border-color: #334155;
        }
        body {
            font-family: 'Segoe UI', Tahoma, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 850px;
            margin: 30px auto;
            background: var(--card-bg);
            padding: 30px;
            border-radius: 16px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }
        h2, h3 { color: var(--accent-color); text-align: center; margin-bottom: 20px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; font-size: 14px; }
        input {
            width: 100%;
            padding: 12px;
            border-radius: 8px;
            border: 1px solid var(--border-color);
            background: var(--bg-color);
            color: #fff;
            box-sizing: border-box;
            font-size: 14px;
        }
        input:focus {
            border-color: var(--accent-color);
            outline: none;
        }
        button {
            width: 100%;
            padding: 14px;
            background-color: var(--button-bg);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: 0.3s;
            margin-top: 10px;
        }
        button:hover { background-color: var(--button-hover); }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 30px;
        }
        th, td { border: 1px solid var(--border-color); padding: 12px; text-align: center; font-size: 14px; }
        th { background-color: var(--button-bg); color: white; }
        tr:nth-child(even) { background-color: rgba(255,255,255,0.02); }
        .logout {
            background: #ef4444;
            padding: 8px 16px;
            text-decoration: none;
            color: white;
            border-radius: 6px;
            font-size: 13px;
            font-weight: bold;
            float: left;
        }
        .logout:hover { background: #dc2626; }
        .login-box { max-width: 400px; margin: 50px auto; }
    </style>
</head>
<body>
    <div class="container">
        {% if logged_in %}
            <a href="/logout" class="logout">دەرچوون 🚪</a>
            <h2>✨ پانێڵی بەڕێوەبردنی ئۆرا ئەنیمی (Index)</h2>
            
            <form action="/add" method="POST">
                <div class="form-group">
                    <label>ناوی ئەنیمی (ئینگلیزی/کوردی):</label>
                    <input type="text" name="anime_name" placeholder="بۆ نموونە: Solo Leveling" required>
                </div>

                <div class="form-group">
                    <label>ناوی ئەنیمی (ژاپۆنی):</label>
                    <input type="text" name="japanese_name" placeholder="بۆ نموونە: 俺だけレベルアップな件" required>
                </div>

                <div class="form-group">
                    <label>وەرز (Season):</label>
                    <input type="text" name="season" placeholder="بۆ نموونە: وەرزی 1" required>
                </div>

                <div class="form-group">
                    <label>ئەڵقەکان (Episodes):</label>
                    <input type="text" name="episodes" placeholder="بۆ نموونە: ئەڵقەی 1-12" required>
                </div>

                <div class="form-group">
                    <label>لینکی پۆستی چەناڵ (Telegram Link):</label>
                    <input type="url" name="post_link" placeholder="https://t.me/..." required>
                </div>

                <button type="submit">💾 پاشەکەوتکردن لە داتابەیس و ناردن بۆ بۆت</button>
            </form>

            <h3>📁 لیستی ئەنیمییە تۆمارکراوەکان</h3>
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
                    <td><a href="{{ anime[5] }}" target="_blank" style="color: var(--accent-color); text-decoration: none;">سەیرکردن 🔗</a></td>
                </tr>
                {% endfor %}
            </table>
        {% else %}
            <div class="login-box">
                <h2>🔒 چوونەژوورەوەی ئەدیمین</h2>
                <form action="/login" method="POST">
                    <div class="form-group">
                        <label>وشەی تێپەڕ (Password):</label>
                        <input type="password" name="password" placeholder="پاسوۆرد بنووسە..." required>
                    </div>
                    <button type="submit">چوونەژوورەوە 🔑</button>
                </form>
            </div>
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
    return render_template_string(INDEX_TEMPLATE, logged_in=logged_in, animes=animes)

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
