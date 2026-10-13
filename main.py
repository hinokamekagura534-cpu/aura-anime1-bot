import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ڕێکخستنی Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_IDS = [6450069400, 5455374693, 8535560894, 1475355789, 5242890148]

# لینکی ماڵپەڕەکەت لە Railway (ئەگەر ناونیشانی دومەینەکەت جیاوازە، دەتوانیت لێرەدا بیگۆڕیت)
WEBSITE_URL = os.environ.get("RAILWAY_STATIC_URL", "https://aura-anime1-bot.up.railway.app")

ANIMES_DATABASE = {}


def get_main_menu():
    keyboard = [
        ["🎬 لیستی ئەنیمی", "🔍 گەڕانی خێرا"],
        ["🛠 پانێڵی ستاف (ئەدیمین)"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "✨ بەخێر بێیت بۆ بۆتی فەرمیی Aura Anime! 🎬\n\n"
        "👨‍💻 Developer: @safenyorochi\n\n"
        "👇 بۆ دەستپێکردن، یەکێک لە دوگمەکانی خوارەوە هەڵبژێرە:"
    )
    await update.message.reply_text(welcome_text, reply_markup=get_main_menu())


async def anime_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ANIMES_DATABASE:
        await update.message.reply_text(
            "⚠️ ئێستا هیچ ئەنیمییەک لە لیستەکەدا بەردەست نییە.",
            reply_markup=get_main_menu()
        )
        return

    keyboard = []
    for anime_name in ANIMES_DATABASE.keys():
        keyboard.append([InlineKeyboardButton(anime_name, callback_data=f"anime_{anime_name}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("✨ **لیستی ئەنیمییەکان:**", reply_markup=reply_markup, parse_mode="Markdown")


async def search_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 تکایە ناوی ئەو ئەنیمییە بنووسە کە دەتەوێت بۆی بگەڕێیت:")
    context.user_data["searching"] = True


async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "🎬 لیستی ئەنیمی":
        await anime_list(update, context)
        return
    elif text == "🔍 گەڕانی خێرا":
        await search_item(update, context)
        return
    elif text == "🛠 پانێڵی ستاف (ئەدیمین)":
        await staff_panel(update, context)
        return

    if context.user_data.get("searching"):
        query = text.lower()
        context.user_data["searching"] = False

        results = [name for name in ANIMES_DATABASE.keys() if query in name.lower()]

        if not results:
            await update.message.reply_text("❌ هیچ ئەنیمییەک بەم ناوەوە نەدۆزرایەوە.", reply_markup=get_main_menu())
            return

        keyboard = [[InlineKeyboardButton(f"🎬 {name}", callback_data=f"anime_{name}")] for name in results]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("🔍 **ئەنجامی گەڕان:**", reply_markup=reply_markup, parse_mode="Markdown")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith("anime_"):
        anime_name = data.replace("anime_", "")
        seasons = ANIMES_DATABASE.get(anime_name, {}).get("Seasons", {})

        keyboard = []
        for season_name in seasons.keys():
            keyboard.append([InlineKeyboardButton(season_name, callback_data=f"season_{anime_name}_{season_name}")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(f"📂 **{anime_name}** - وەرزی داواکراو هەڵبژێرە:", reply_markup=reply_markup, parse_mode="Markdown")

    elif data.startswith("season_"):
        _, anime_name, season_name = data.split("_", 2)
        episodes = ANIMES_DATABASE.get(anime_name, {}).get("Seasons", {}).get(season_name, {})

        keyboard = []
        for ep_name, link in episodes.items():
            keyboard.append([InlineKeyboardButton(f"▶️ {ep_name}", url=link)])

        keyboard.append([InlineKeyboardButton("🔙 گەڕانەوە", callback_data=f"anime_{anime_name}")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(f"🎬 **{anime_name}** - **{season_name}**:", reply_markup=reply_markup, parse_mode="Markdown")


# پانێڵی ئەدیمین بە بەستەرەوە بۆ ماڵپەڕ
async def staff_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        await update.message.reply_text("⛔️ ببوورە، تەنها ئەدیمین دەتوانێت ئەم پانێڵە بەکاربهێنێت!", reply_markup=get_main_menu())
        return

    # دروستکردنی دوگمەی شێوە ماڵپەڕ (Web App / Inline URL Button)
    keyboard = [
        [InlineKeyboardButton("🌐 کردنەوەی ماڵپەڕی بەڕێوەبردن (Admin Website)", url=f"https://{WEBSITE_URL}" if not WEBSITE_URL.startswith("http") else WEBSITE_URL)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    admin_message = (
        "🛠 **بەخێر بێیت بۆ پانێڵی کۆنتڕۆڵی ستاف**\n\n"
        "لێرەوە دەتوانیت بچیتە سەر ماڵپەڕی تایبەت بە ئەنیمییەکان بۆ زیادکردن، دەستکاریکردن و پاشەکەوتکردنی هەموو داتاکان بە ئاسانی:\n\n"
        "🔑 **Password بۆ چوونەژوورەوە:** `aura_admin_pass`"
    )

    await update.message.reply_text(admin_message, reply_markup=reply_markup, parse_mode="Markdown")


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))

    print("بۆتەکە چالاککرا و کار دەکات...")
    app.run_polling()


if __name__ == "__main__":
    main()
