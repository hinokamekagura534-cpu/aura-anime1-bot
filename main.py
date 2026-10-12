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

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_IDS = [6450069400, 5455374693, 8535560894, 1475355789, 5242890148]

ANIMES_DATABASE = {}

# حاڵەتەکانی Conversation Handler
ADD_NAME, ADD_SEASON, ADD_EPISODE, ADD_LINK = range(4)


def get_main_menu():
    keyboard = [
        ["🎬 لیستی ئەنیمی", "🔍 گەڕانی خێرا"],
        ["🛠 پانێڵی ستاف (ئەدیمین)"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_admin_menu():
    keyboard = [
        ["➕ زیادکردنی ئەنیمی", "✏️ دەستکاریکردنی ئەنیمی"],
        ["🗑 سڕینەوەی ئەنیمی", "🔙 گەڕانەوە بۆ منیووی سەرەکی"]
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
    elif text == "🔙 گەڕانەوە بۆ منیووی سەرەکی":
        await update.message.reply_text("🔙 گەڕانەوە بۆ منیووی سەرەکی.", reply_markup=get_main_menu())
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

    elif data.startswith("del_"):
        anime_name = data.replace("del_", "")
        if anime_name in ANIMES_DATABASE:
            del ANIMES_DATABASE[anime_name]
            await query.edit_message_text(f"✅ ئەنیمی **{anime_name}** بەسەرکەوتوویی سڕایەوە!", parse_mode="Markdown")
        else:
            await query.edit_message_text("❌ ئەم ئەنیمییە پێشتر سڕاوەتەوە یان بوونی نییە.")


# پانێڵی ئەدیمین
async def staff_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        await update.message.reply_text("⛔️ ببوورە، تەنها ئەدیمین دەتوانێت ئەم پانێڵە بەکاربهێنێت!", reply_markup=get_main_menu())
        return

    await update.message.reply_text(
        "🛠 **بەخێر بێیت بۆ پانێڵی ستاف**\nتکایە بژاردەیەک هەڵبژێرە:",
        reply_markup=get_admin_menu()
    )


async def start_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return ConversationHandler.END

    await update.message.reply_text("📌 ناوی ئەو ئەنیمییە بنووسە کە دەتەوێت زیادی بکەیت یان دەستکاری بکەیت:\n(/cancel بۆ هەڵوەشاندنەوە)", reply_markup=ReplyKeyboardRemove())
    return ADD_NAME


async def get_anime_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_anime_name"] = update.message.text
    await update.message.reply_text("📂 ناوی وەرزەکە بنووسە (بۆ نموونە: وەرزی 1):")
    return ADD_SEASON


async def get_season_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_season_name"] = update.message.text
    await update.message.reply_text("🎬 ناوی ئەڵقەکە یان ڕێژەی ئەڵقەکان بنووسە (بۆ نموونە: ئەڵقەی 1-12 یان ئەڵقەی 1):")
    return ADD_EPISODE


async def get_episode_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_episode_name"] = update.message.text
    await update.message.reply_text("🔗 لینکی ئەڵقەکە یان لینکی پۆستی چەناڵەکە بنووسە:")
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
        f"✅ بە سەرکەوتوویی پاشەکەوت کرا!\n\n📌 ئەنیمی: {anime_name}\n📂 وەرز: {season_name}\n🎬 ئەڵقە: {episode_name}",
        reply_markup=get_admin_menu()
    )
    return ConversationHandler.END


async def start_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return

    if not ANIMES_DATABASE:
        await update.message.reply_text("⚠️ هیچ ئەنیمییەک لە لیستەکەدا نییە بۆ سڕینەوە.", reply_markup=get_admin_menu())
        return

    keyboard = []
    for name in ANIMES_DATABASE.keys():
        keyboard.append([InlineKeyboardButton(f"🗑 {name}", callback_data=f"del_{name}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🗑 **ئەو ئەنیمییە هەڵبژێرە کە دەتەوێت بسڕێتەوە:**", reply_markup=reply_markup, parse_mode="Markdown")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ کردارەکە هەڵوەشێنرایەوە.", reply_markup=get_admin_menu())
    return ConversationHandler.END


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    add_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^➕ زیادکردنی ئەنیمی$"), start_add),
            MessageHandler(filters.Regex("^✏️ دەستکاریکردنی ئەنیمی$"), start_add)
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
    app.add_handler(add_handler)
    app.add_handler(MessageHandler(filters.Regex("^🗑 سڕینەوەی ئەنیمی$"), start_delete))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))

    print("بۆتەکە چالاککرا و کار دەکات...")
    app.run_polling()


if __name__ == "__main__":
    main()
