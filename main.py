import os
import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# وەرگرتنی تۆکنی بۆت لە گۆڕاوەکانی ژینگە (Environment Variables)
BOT_TOKEN = os.environ.get("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # دروستکردنی دوگمەکان بۆ مۆنیۆی سەرەکی
    keyboard = [
        ["🎬 لیستی ئەنیمی", "🔍 گەڕانی ئەنیمی"],
        ["✨ دەربارەی ئۆرا ئەنیمی"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "بەخێر بێیت بۆ بۆتی ئۆرا ئەنیمی! فەرموو لە خوارەوە یەکێک لە بژاردەکان هەڵبژێرە:",
        reply_markup=reply_markup
    )

async def handle_slash_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    # ئەگەر لە هەر گروپێک یان چاتێکدا / نووسرا، مۆنیۆکە نیشان بدە
    if text and text.startswith("/"):
        keyboard = [
            ["🎬 لیستی ئەنیمی", "🔍 گەڕانی ئەنیمی"],
            ["✨ دەربارەی ئۆرا ئەنیمی"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "فەرموو، مۆنیۆی سەرەکی بۆت:",
            reply_markup=reply_markup
        )

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🎬 لیستی ئەنیمی":
        # لێرەدا دەتوانیت لیستی ئەنیمییەکان لە داتابەیسەوە بهێنیت
        await update.message.reply_text("📁 ئەمەش دوایین ئەنیمییە تۆمارکراوەکان لە چەناڵەکەتدا...")
    elif text == "🔍 گەڕانی ئەنیمی":
        await update.message.reply_text("🔍 ناو یان ژمارەی ئەنیمی بنووسە بۆ گەڕان:")
    elif text == "✨ دەربارەی ئۆرا ئەنیمی":
        await update.message.reply_text("✨ بۆتی فەرمی ئۆرا ئەنیمی بۆ بەڕێوەبردن و بڵاوکردنەوەی ئەنیمی.")

def main():
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN is missing!")
        return
        
    bot_app = Application.builder().token(BOT_TOKEN).build()
    
    # بەستنەوەی فەرمانەکان بە بۆتەکەوە
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^/"), handle_slash_commands))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))
    
    print("Bot is running...")
    bot_app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
