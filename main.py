import os
import sqlite3
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_IDS = [6450069400, 5455374693, 8535560894, 1475355789, 5242890148]

# قۆناغەکانی زیادکردنی ئەنیمی
ANIME_NAME, JAPANESE_NAME, SEASON, EPISODES, POST_LINK = range(5)

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🎬 لیستی ئەنیمی", "➕ زیادکردنی ئەنیمی"],
        ["🔍 گەڕانی ئەنیمی", "✨ دەربارەی ئێمە"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "بەخێر بێیت بۆ بۆتی بەڕێوەبردنی ئۆرا ئەنیمی! فەرموو یەکێک لە بژاردەکان هەڵبژێرە:",
        reply_markup=reply_markup
    )

async def handle_slash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text and text.startswith("/"):
        keyboard = [
            ["🎬 لیستی ئەنیمی", "➕ زیادکردنی ئەنیمی"],
            ["🔍 گەڕانی ئەنیمی", "✨ دەربارەی ئێمە"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("فەرموو مۆنیۆی سەرەکی:", reply_markup=reply_markup)

# دەستپێکردنی پرۆسەی زیادکردنی ئەنیمی
async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("ببوورە، تەنها ئەدیمین دەتوانیت ئەنیمی زیاد بکات.")
        return ConversationHandler.END
        
    await update.message.reply_text(
        "📌 تکایە ناوی ئەنیمی (کوردی/ئینگلیزی) بنووسە:",
        reply_markup=ReplyKeyboardRemove()
    )
    return ANIME_NAME

async def receive_anime_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['anime_name'] = update.message.text
    await update.message.reply_text("🇯🇵 ئێستا ناوی ژاپۆنی ئەنیمییەکە بنووسە:")
    return JAPANESE_NAME

async def receive_japanese_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['japanese_name'] = update.message.text
    await update.message.reply_text("📂 وەرزەکەی بنووسە (بۆ نموونە: وەرزی 1):")
    return SEASON

async def receive_season(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['season'] = update.message.text
    await update.message.reply_text("🎬 ئەڵقەکان بنووسە (بۆ نموونە: 1-12):")
    return EPISODES

async def receive_episodes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['episodes'] = update.message.text
    await update.message.reply_text("🔗 لێنکی پۆستی چەناڵ (Telegram Link) بنووسە:")
    return POST_LINK

async def receive_post_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    post_link = update.message.text
    data = context.user_data
    
    # پاشەکەوتکردن لە داتابەیس
    conn = sqlite3.connect("anime.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO animes (anime_name, japanese_name, season, episodes, post_link)
        VALUES (?, ?, ?, ?, ?)
    ''', (data['anime_name'], data['japanese_name'], data['season'], data['episodes'], post_link))
    conn.commit()
    conn.close()

    keyboard = [
        ["🎬 لیستی ئەنیمی", "➕ زیادکردنی ئەنیمی"],
        ["🔍 گەڕانی ئەنیمی", "✨ دەربارەی ئێمە"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    success_text = (
        f"✨ **ئەنیمیی نوێ بە سەرکەوتوویی زیادکرا!**\n\n"
        f"📌 **ناو:** {data['anime_name']}\n"
        f"🇯🇵 **ژاپۆنی:** {data['japanese_name']}\n"
        f"📂 **وەرز:** {data['season']}\n"
        f"🎬 **ئەڵقەکان:** {data['episodes']}\n"
        f"🔗 **لینک:** {post_link}"
    )
    await update.message.reply_text(success_text, parse_mode="Markdown", reply_markup=reply_markup)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🎬 لیستی ئەنیمی", "➕ زیادکردنی ئەنیمی"],
        ["🔍 گەڕانی ئەنیمی", "✨ دەربارەی ئێمە"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("پرۆسەکە هەڵوەشایەوە.", reply_markup=reply_markup)
    return ConversationHandler.END

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🎬 لیستی ئەنیمی":
        conn = sqlite3.connect("anime.db")
        cursor = conn.cursor()
        cursor.execute("SELECT anime_name, season, episodes, post_link FROM animes ORDER BY id DESC LIMIT 5")
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            await update.message.reply_text("هیچ ئەنیمییەک تا ئێستا تۆمار نەکراوە.")
        else:
            msg = "📁 **دواین ئەنیمییە تۆمارکراوەکان:**\n\n"
            for r in rows:
                msg += f"📌 {r[0]} | {r[1]} | {r[2]}\n🔗 {r[3]}\n\n"
            await update.message.reply_text(msg, parse_mode="Markdown")
            
    elif text == "🔍 گەڕانی ئەنیمی":
        await update.message.reply_text("🔍 ناو یان ژمارەی ئەنیمی بنووسە:")
    elif text == "✨ دەربارەی ئێمە":
        await update.message.reply_text("✨ بۆتی فەرمی بەڕێوەبردنی ئۆرا ئەنیمی.")

def main():
    if not BOT_TOKEN:
        return
        
    bot_app = Application.builder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^➕ زیادکردنی ئەنیمی$"), add_start)],
        states={
            ANIME_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_anime_name)],
            JAPANESE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_japanese_name)],
            SEASON: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_season)],
            EPISODES: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_episodes)],
            POST_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_post_link)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(conv_handler)
    bot_app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^/"), handle_slash))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))
    
    bot_app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
