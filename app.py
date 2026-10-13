import os
import sqlite3
import threading
from flask import Flask, render_template, request, redirect, url_for, session
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

app = Flask(__name__)
app.secret_key = "aura_anime_secret_admin_key"

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_IDS = [6450069400, 5455374693, 8535560894, 1475355789, 5242890148]
ADMIN_PASSWORD = "aura_admin_pass"

def init_db():
    conn = sqlite3.connect("anime.db", check_same_thread=False)
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
            try:
                requests.post(url, json={"chat_id": admin_id, "text": message, "parse_mode": "Markdown"})
            except:
                pass

    return redirect(url_for("home"))

# بەشی بۆتی تەلەگرام بە شێوازێکی یەکخراو
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["🎬 لیستی ئەنیمی", "🔍 گەڕان"]]
    await update.message.reply_text("بەخێر بێیت بۆ بۆتی ئۆرا ئەنیمی!", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

def run_bot():
    if BOT_TOKEN:
        try:
            bot_app = Application.builder().token(BOT_TOKEN).build()
            bot_app.add_handler(CommandHandler("start", start_command))
            bot_app.run_polling(drop_pending_updates=True)
        except Exception as e:
            print(f"Bot error: {e}")

if __name__ == "__main__":
    # کارپێکردنی بۆتەکە لە پشتەوە بە بێ کێشەی کانفڵیکت
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
