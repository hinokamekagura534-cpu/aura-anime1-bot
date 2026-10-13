import os
from flask import Flask, render_template_string, request
import requests

app = Flask(__name__)

# وەرگرتنی تۆکن لە جێگیرەکانی ژینگە (Environment Variables)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_IDS = [6450069400, 5455374693, 8535560894, 1475355789, 5242890148]

# دیزاینی ماڵپەڕەکە بە کوردیی سۆرانی
HTML_FORM = """
<!DOCTYPE html>
<html lang="ckb" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>پانێڵی ئۆرا ئەنیمی - Aura Anime</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #0f172a;
            color: #f8fafc;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
        }
        .form-container {
            background: #1e293b;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            width: 100%;
            max-width: 420px;
            text-align: right;
        }
        h2 {
            text-align: center;
            color: #38bdf8;
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 6px;
            font-weight: bold;
            font-size: 14px;
        }
        input {
            width: 100%;
            padding: 10px;
            margin-bottom: 15px;
            border-radius: 6px;
            border: 1px solid #334155;
            background-color: #0f172a;
            color: #fff;
            box-sizing: border-box;
            font-size: 14px;
        }
        button {
            width: 100%;
            padding: 12px;
            background-color: #0284c7;
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: 0.3s;
        }
        button:hover {
            background-color: #0369a1;
        }
    </style>
</head>
<body>
    <div class="form-container">
        <h2>✨ زیادکردنی ئەنیمیی نوێ</h2>
        <form action="/add-anime" method="POST">
            <label>ناوی ئەنیمی (ئینگلیزی/کوردی):</label>
            <input type="text" name="anime_name" placeholder="بۆ نموونە: Solo Leveling" required>

            <label>ناوی ئەنیمی بە ژاپۆنی:</label>
            <input type="text" name="japanese_name" placeholder="بۆ نموونە: 俺だけレベルアップな件" required>

            <label>وەرز (Season):</label>
            <input type="text" name="season" placeholder="بۆ نموونە: 1 یان وەرزی 1" required>

            <label>ئەڵقەکان (Episode):</label>
            <input type="text" name="episodes" placeholder="بۆ نموونە: ئەڵقەی 1-12" required>

            <label>لینکی پۆستی چەناڵ (Telegram Link):</label>
            <input type="url" name="post_link" placeholder="https://t.me/..." required>

            <button type="submit">💾 پاشەکەوتکردن و ناردن بۆ بۆت</button>
        </form>
    </div>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_FORM)

@app.route("/add-anime", methods=["POST"])
def add_anime():
    anime_name = request.form.get("anime_name")
    japanese_name = request.form.get("japanese_name")
    season = request.form.get("season")
    episodes = request.form.get("episodes")
    post_link = request.form.get("post_link")

    # ئامادەکردنی دەقی نامەکە بۆ ئەدیمینەکان
    message = (
        f"✨ **ئەنیمیی نوێ لە ڕێگەی ماڵپەڕەوە زیادکرا!**\n\n"
        f"📌 **ناوی ئەنیمی:** {anime_name}\n"
        f"🇯🇵 **ناوی ژاپۆنی:** {japanese_name}\n"
        f"📂 **وەرز:** {season}\n"
        f"🎬 **ئەڵقەکان:** {episodes}\n"
        f"🔗 **لینک:** {post_link}"
    )

    # ناردنی ڕاگەیەندراو (Notification) بۆ هەموو ئەدیمینەکان لە تەلەگرام
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    if BOT_TOKEN:
        for admin_id in ADMIN_IDS:
            requests.post(url, json={"chat_id": admin_id, "text": message, "parse_mode": "Markdown"})

    return """
    <div style="text-align: center; font-family: sans-serif; padding: 50px; background-color: #0f172a; color: white; min-height: 100vh;">
        <h2 style="color: #4ade80;">✅ بە سەرکەوتوویی پاشەکەوت کرا و بۆ بۆتەکە نێردرا!</h2>
        <a href="/" style="color: #38bdf8; text-decoration: none; font-size: 18px;">🔙 گەڕانەوە بۆ لاپەڕەی سەرەکی</a>
    </div>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
