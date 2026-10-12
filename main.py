import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler,
)

# ڕێکخستنی Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# ---------------------------------------------------------
# ١. بەشی ڕێکخستنە سەرەتاییەکان (Configuration)
# ---------------------------------------------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# لیستی ئەدیمینەکان (ئۆوێنەر Sung Jin Woo لەسەرەتاوەیە)
ADMIN_IDS = [6450069400, 5455374693, 8535560894, 1475355789, 5242890148]

# داتابەیسی ئەنیمی
ANIMES_DATABASE = {}

# حاڵەتەکانی Conversation Handler بۆ بەشی ستاف
ADD_NAME, ADD_SEASON, ADD_EPISODE, ADD_LINK = range(4)


# ---------------------------------------------------------
# ٢. دروستکردنی دوگمەکانی خوارەوەی چات (Menu Keyboard)
# ---------------------------------------------------------
def get_main_menu():
    keyboard = [
        ["🎬 لیستی ئەنیمی", "🔍 گەڕانی خێرا"],
        ["🛠 پانێڵی ستاف (ئەدیمین)"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


# ---------------------------------------------------------
# ٣. فەرمانە سەرەکییەکان (User Commands & Text Handlers)
# ---------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "✨ بەخێر بێیت بۆ بۆتی فەرمیی Aura Anime! 🎬\n\n"
        "لێرە بە ئاسانی دەستت بە سەرجەم ئەنیمییە وەرگێڕدراوەکان دەگات بە بەرزترین کوالێتی.\n\n"
        "🔹 تایبەتمەندییەکان:\n"
        "▫️ 🎬 لیستی گشتی ئەنیمییەکان\n"
        "▫️ 🔍 گەڕانی خێرا و ئاسان\n"
        "▫️ 🎞 بەستەری ڕاستەوخۆی ئەڵقەکان\n\n"
        "👨‍💻 Developer: @safenyorochi\n\n"
        "👇 بۆ دەستپێکردن، یەکێک هەڵبژێرە لە دوگمەکانی خوارەوە:"
    )
    await update.message.reply_text(welcome_text, reply_markup=get_main_menu())


# پیشاندانی لیستی ئەنیمی
async def anime_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ANIMES_DATABASE:
        await update.message.reply_text(
            "⚠️ ئێستا هیچ ئەنیمییەک لە لیستەکەدا بەردەست نییە.\n(ئەدیمین دەتوانێت لە ڕێگەی پانێڵی ستافەوە زیادی بکات)",
            reply_markup=get_main_menu()
        )
        return

    keyboard = []
    for anime_name in ANIMES_DATABASE.keys():
        keyboard.append([InlineKeyboardButton(anime_name, callback_data=f"anime_{anime_name}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("✨ **لیستی ئەنیمییەکانی Aura:**\nتکایە ئەنیمییەک هەڵبژێرە:", reply_markup=reply_markup, parse_mode="Markdown")


# گەڕان
async def search_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 تکایە ناوی ئەو ئەنیمییە بنووسە کە دەتەوێت بۆی بگەڕێیت:")
    context.user_data["searching"] = True


# پشکنینی نامەکان بۆ دوگمەکانی چات
async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "🎬 لیستی ئەنیمی":
        await anime_list(update, context)
        return
    elif text == "🔍 گەڕانی خێرا":
        await search_item(update, context)
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


# ---------------------------------------------------------
# ٤. سیستەمی هەڵبژاردنی وەرز و ئەڵقە (Callback Queries)
# ---------------------------------------------------------
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
        await query.edit_message_text(f"📂 پێڕستی وەررزەکان بۆ: **{anime_name}**\nتکایە وەرزێک هەڵبژێرە:", reply_markup=reply_markup, parse_mode="Markdown")

    elif data.startswith("season_"):
        _, anime_name, season_name = data.split("_", 2)
        episodes = ANIMES_DATABASE.get(anime_name, {}).get("Seasons", {}).get(season_name, {})

        keyboard = []
        for ep_name, link in episodes.items():
            keyboard.append([InlineKeyboardButton(f"▶️ {ep_name}", url=link)])

        keyboard.append([InlineKeyboardButton("🔙 گەڕانەوە", callback_data=f"anime_{anime_name}")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(f"🎬 ئەڵقەکانی **{anime_name}** - **{season_name}**:", reply_markup=reply_markup, parse_mode="Markdown")


# ---------------------------------------------------------
# ٥. پانێڵی ستاف (Staff Panel & Admin Check)
# ---------------------------------------------------------
async def staff_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        await update.message.reply_text("⛔️ ببوورە، تەنها ئەدیمین دەسەڵاتی بەکارهێنانی پانێڵی ستافی هەیە!", reply_markup=get_main_menu())
        return ConversationHandler.END

    await update.message.reply_text(
        "🛠 **بەخێر بێیت بۆ پانێڵی ستاف**\n"
        "📌 تکایە ناوی ئەو ئەنیمییە نووسە کە دەتەوێت زیادی بکەیت:\n"
        "(بۆ هەڵوەشاندنەوە فەرمانی /cancel بنووسە)",
        reply_markup=ReplyKeyboardRemove()
    )
    return ADD_NAME


async def get_anime_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_anime_name"] = update.message.text
    await update.message.reply_text("📂 ئێستا ناوی وەرزەکە بنووسە (بۆ نموونە: Season 1):")
    return ADD_SEASON


async def get_season_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_season_name"] = update.message.text
    await update.message.reply_text("🎬 ئێستا ناوی ئەڵقەکە بنووسە (بۆ نموونە: Episode 1):")
    return ADD_EPISODE


async def get_episode_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_episode_name"] = update.message.text
    await update.message.reply_text("🔗 ئێستا لینکی ئەڵقەکە لە چەناڵ بنووسە (https://t.me/...):")
    return ADD_LINK


async def save_anime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link = update.message.text
    anime_name = context.user_data["new_anime_name"]
    season_name = context.user_data["new_season_name"]
    episode_name = context.user_data["new_episode_name"]

    if anime_name not in ANIMES_DATABASE:
        ANIMES_DATABASE[anime_name] = {"Seasons": {}}

    if season_name not in ANIMES_DATABASE[anime_name]["Seasons"]:
        ANIMES_DATABASE[anime_name]["Seasons"][season_name] = {}

    ANIMES_DATABASE[anime_name]["Seasons"][season_name][episode_name] = link

    await update.message.reply_text(
        f"✅ بە سەرکەوتوویی زیادکرا!\n\n"
        f"📌 ئەنیمی: {anime_name}\n"
        f"📂 وەرز: {season_name}\n"
        f"🎬 ئەڵقە: {episode_name}\n"
        f"🔗 لینک: {link}",
        reply_markup=get_main_menu()
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ کردارەکە هەڵوەشێنرایەوە.", reply_markup=get_main_menu())
    return ConversationHandler.END


# ---------------------------------------------------------
# ٦. بەشی سەرەکی کارپێکردنی بۆت
# ---------------------------------------------------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    staff_handler = ConversationHandler(
        entry_points=[
            CommandHandler("staff", staff_panel),
            MessageHandler(filters.Regex("^🛠 پانێڵی ستاف \(ئەدیمین\)$"), staff_panel)
        ],
        states={
            ADD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_anime_name)],
            ADD_SEASON: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_season_name)],
            ADD_EPISODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_episode_name)],
            ADD_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_anime)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(staff_handler)
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))

    print("بۆتەکە چالاککرا و کار دەکات...")
    app.run_polling()


if __name__ == "__main__":
    main()
