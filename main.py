
import os
import html
import logging
import sqlite3
from pathlib import Path
from urllib.parse import urlparse

from telegram import Update, ReplyKeyboardMarkup, BotCommand
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# =============== CONFIGURATION ===============

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()

ADMIN_IDS = {
    6450069400,
    5455374693,
    8535560894,
    1475355789,
    5242890148,
}

DB_PATH = Path(__file__).resolve().parent / "anime.db"

ANIME_NAME, JAPANESE_NAME, SEASON, EPISODES, POST_LINK = range(5)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("AuraAnime")

MENU = ReplyKeyboardMarkup(
    [
        ["🎬 لیستی ئەنیمی", "➕ زیادکردنی ئەنیمی"],
        ["🔍 گەڕانی ئەنیمی", "✨ دەربارەی ئێمە"],
    ],
    resize_keyboard=True,
    is_persistent=True,
)

CANCEL_MENU = ReplyKeyboardMarkup(
    [["❌ هەڵوەشاندنەوە"]],
    resize_keyboard=True,
)

PRIVATE = filters.ChatType.PRIVATE
GROUPS = filters.ChatType.GROUPS


# =============== DATABASE ===============

def db_connect():
    connection = sqlite3.connect(str(DB_PATH), timeout=15)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with db_connect() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS animes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                anime_name TEXT NOT NULL,
                japanese_name TEXT NOT NULL,
                season INTEGER NOT NULL CHECK (season > 0),
                episodes INTEGER NOT NULL CHECK (episodes > 0),
                post_link TEXT NOT NULL
            )
        """)
        db.commit()


def save_anime(data):
    with db_connect() as db:
        cursor = db.execute(
            """
            INSERT INTO animes
            (anime_name, japanese_name, season, episodes, post_link)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                data["anime_name"],
                data["japanese_name"],
                data["season"],
                data["episodes"],
                data["post_link"],
            ),
        )
        db.commit()
        return cursor.lastrowid


def list_animes(limit=10):
    with db_connect() as db:
        return db.execute(
            "SELECT * FROM animes ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()


def search_animes(query, limit=10):
    with db_connect() as db:
        pattern = f"%{query}%"
        return db.execute(
            """
            SELECT * FROM animes
            WHERE anime_name LIKE ? COLLATE NOCASE
               OR japanese_name LIKE ? COLLATE NOCASE
            ORDER BY id DESC LIMIT ?
            """,
            (pattern, pattern, limit),
        ).fetchall()


def anime_count():
    with db_connect() as db:
        return db.execute(
            "SELECT COUNT(*) FROM animes"
        ).fetchone()[0]


# =============== HELPERS ===============

def is_admin(update):
    user = update.effective_user
    return bool(user and user.id in ADMIN_IDS)


def safe_url(value):
    try:
        parsed = urlparse(value.strip())
        return (
            parsed.scheme in ("https", "http")
            and bool(parsed.netloc)
            and "." in parsed.netloc
        )
    except ValueError:
        return False


def anime_card(anime):
    return (
        f"🎬 <b>{html.escape(anime['anime_name'])}</b>\n"
        f"🇯🇵 ناوی ژاپۆنی: "
        f"{html.escape(anime['japanese_name'])}\n"
        f"📀 وەرز: {anime['season']}\n"
        f"🎞 ئەڵقەکان: {anime['episodes']}\n"
        f'🔗 <a href="{html.escape(anime["post_link"], quote=True)}">'
        f"بینینی پۆست</a>\n"
        f"🆔 {anime['id']}"
    )


async def show_menu(update, context):
    message = update.effective_message
    if message:
        await message.reply_text(
            "🌟 <b>بەخێربێیت بۆ Aura Anime!</b>\n\n"
            "تکایە فەرمانێک یان دوگمەیەک هەڵبژێرە.",
            parse_mode=ParseMode.HTML,
            reply_markup=MENU,
        )


# =============== COMMANDS ===============

async def start(update, context):
    # Clear unfinished private workflows when restarting.
    if update.effective_chat.type == "private":
        context.user_data.pop("anime_data", None)
        context.user_data.pop("search_mode", None)

    await show_menu(update, context)


async def other_command(update, context):
    # Slash commands work, but ordinary group conversation is ignored.
    await show_menu(update, context)


async def cancel(update, context):
    context.user_data.pop("anime_data", None)
    context.user_data.pop("search_mode", None)

    await update.effective_message.reply_text(
        "❌ کردارەکە هەڵوەشێنرایەوە.",
        reply_markup=MENU,
    )
    return ConversationHandler.END


# =============== ADD ANIME ===============

async def add_start(update, context):
    if not is_admin(update):
        await update.effective_message.reply_text(
            "⛔ تەنها ئەدمین دەتوانێت ئەنیمی زیاد بکات.",
            reply_markup=MENU,
        )
        return ConversationHandler.END

    context.user_data["anime_data"] = {}

    await update.effective_message.reply_text(
        "➕ <b>زیادکردنی ئەنیمی</b>\n\n"
        "١. ناوی ئەنیمی بنووسە:",
        parse_mode=ParseMode.HTML,
        reply_markup=CANCEL_MENU,
    )
    return ANIME_NAME


async def get_name(update, context):
    value = update.effective_message.text.strip()
    if not value or len(value) > 200:
        await update.effective_message.reply_text(
            "⚠️ ناوێکی دروست بنووسە."
        )
        return ANIME_NAME

    context.user_data["anime_data"]["anime_name"] = value
    await update.effective_message.reply_text(
        "٢. ناوی ژاپۆنی ئەنیمی بنووسە:"
    )
    return JAPANESE_NAME


async def get_japanese_name(update, context):
    value = update.effective_message.text.strip()
    if not value or len(value) > 200:
        await update.effective_message.reply_text(
            "⚠️ ناوێکی دروست بنووسە."
        )
        return JAPANESE_NAME

    context.user_data["anime_data"]["japanese_name"] = value
    await update.effective_message.reply_text(
        "٣. ژمارەی وەرز بنووسە:"
    )
    return SEASON


async def get_season(update, context):
    value = update.effective_message.text.strip()
    if not value.isdigit() or not 1 <= int(value) <= 100:
        await update.effective_message.reply_text(
            "⚠️ ژمارەی وەرز دەبێت لە ١ تا ١٠٠ بێت."
        )
        return SEASON

    context.user_data["anime_data"]["season"] = int(value)
    await update.effective_message.reply_text(
        "٤. ژمارەی ئەڵقەکان بنووسە:"
    )
    return EPISODES


async def get_episodes(update, context):
    value = update.effective_message.text.strip()
    if not value.isdigit() or not 1 <= int(value) <= 10000:
        await update.effective_message.reply_text(
            "⚠️ ژمارەیەکی دروست لە ١ تا ١٠٠٠٠ بنووسە."
        )
        return EPISODES

    context.user_data["anime_data"]["episodes"] = int(value)
    await update.effective_message.reply_text(
        "٥. لینکی پۆستی تێلەگرام بنێرە:"
    )
    return POST_LINK


async def get_post_link(update, context):
    link = update.effective_message.text.strip()

    if not safe_url(link):
        await update.effective_message.reply_text(
            "⚠️ لینکەکە دروست نییە. لینکی http یان https بنێرە."
        )
        return POST_LINK

    data = context.user_data.get("anime_data")
    if not data:
        await update.effective_message.reply_text(
            "❌ زانیارییەکان نەدۆزرایەوە.",
            reply_markup=MENU,
        )
        return ConversationHandler.END

    data["post_link"] = link

    try:
        anime_id = save_anime(data)
    except sqlite3.Error:
        logger.exception("Database save failed")
        context.user_data.pop("anime_data", None)
        await update.effective_message.reply_text(
            "❌ هەڵەیەک لە پاشەکەوتکردندا ڕوویدا.",
            reply_markup=MENU,
        )
        return ConversationHandler.END

    confirmation = (
        "✅ <b>ئەنیمی بە سەرکەوتوویی زیادکرا!</b>\n\n"
        f"🎬 ناو: {html.escape(data['anime_name'])}\n"
        f"🇯🇵 ناوی ژاپۆنی: "
        f"{html.escape(data['japanese_name'])}\n"
        f"📀 وەرز: {data['season']}\n"
        f"🎞 ئەڵقەکان: {data['episodes']}\n"
        f'🔗 <a href="{html.escape(link, quote=True)}">پۆست</a>\n'
        f"🆔 {anime_id}"
    )

    context.user_data.pop("anime_data", None)

    await update.effective_message.reply_text(
        confirmation,
        parse_mode=ParseMode.HTML,
        reply_markup=MENU,
        disable_web_page_preview=True,
    )
    return ConversationHandler.END


# =============== LIST ===============

async def show_animes(update, context):
    try:
        items = list_animes()
        count = anime_count()
    except sqlite3.Error:
        logger.exception("Database read failed")
        await update.effective_message.reply_text(
            "❌ نەتوانرا داتاکان بخوێندرێنەوە.",
            reply_markup=MENU,
        )
        return

    if not items:
        await update.effective_message.reply_text(
            "📭 هێشتا هیچ ئەنیمییەک زیاد نەکراوە.",
            reply_markup=MENU,
        )
        return

    await update.effective_message.reply_text(
        f"🎬 <b>لیستی ئەنیمی</b>\n📚 کۆی گشتی: {count}",
        parse_mode=ParseMode.HTML,
        reply_markup=MENU,
    )

    await send_cards(update, items)


async def send_cards(update, items):
    message = ""

    for anime in items:
        card = anime_card(anime)
        if message and len(message) + len(card) + 2 > 3800:
            await update.effective_message.reply_text(
                message,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
            message = card
        else:
            message = f"{message}\n\n{card}" if message else card

    if message:
        await update.effective_message.reply_text(
            message,
            parse_mode=ParseMode.HTML,
            reply_markup=MENU,
            disable_web_page_preview=True,
        )


# =============== SEARCH ===============

async def search_start(update, context):
    context.user_data["search_mode"] = True
    await update.effective_message.reply_text(
        "🔍 ناوی ئەنیمی یان ناوی ژاپۆنی بنووسە:",
        reply_markup=CANCEL_MENU,
    )


async def search_text(update, context):
    query = update.effective_message.text.strip()
    context.user_data.pop("search_mode", None)

    if not query or len(query) > 200:
        await update.effective_message.reply_text(
            "⚠️ ناوێکی دروست بنووسە.",
            reply_markup=MENU,
        )
        return

    try:
        results = search_animes(query)
    except sqlite3.Error:
        logger.exception("Anime search failed")
        await update.effective_message.reply_text(
            "❌ هەڵەیەک لە گەڕاندا ڕوویدا.",
            reply_markup=MENU,
        )
        return

    if not results:
        await update.effective_message.reply_text(
            f"🔎 هیچ ئەنجامێک بۆ «{html.escape(query)}» نەدۆزرایەوە.",
            parse_mode=ParseMode.HTML,
            reply_markup=MENU,
        )
        return

    await send_cards(update, results)


# =============== ABOUT ===============

async def about(update, context):
    await update.effective_message.reply_text(
        "✨ <b>دەربارەی Aura Anime</b>\n\n"
        "🎬 شوێنێک بۆ لیستکردن و گەڕان بەدوای ئەنیمی.\n"
        "🇯🇵 ناوی ژاپۆنی و زانیارییەکانی ئەنیمی.\n\n"
        "💜 سوپاس بۆ بەکارهێنانی Aura Anime!",
        parse_mode=ParseMode.HTML,
        reply_markup=MENU,
    )


# =============== PRIVATE TEXT ROUTER ===============

async def private_text_router(update, context):
    text = update.effective_message.text.strip()

    # Handle search text only after the search button was clicked.
    if context.user_data.get("search_mode"):
        await search_text(update, context)
        return

    if text == "🎬 لیستی ئەنیمی":
        await show_animes(update, context)
    elif text == "➕ زیادکردنی ئەنیمی":
        await add_start(update, context)
    elif text == "🔍 گەڕانی ئەنیمی":
        await search_start(update, context)
    elif text == "✨ دەربارەی ئێمە":
        await about(update, context)
    else:
        await update.effective_message.reply_text(
            "تکایە یەکێک لە دوگمەکانی مینیو هەڵبژێرە.",
            reply_markup=MENU,
        )


# =============== TELEGRAM COMMAND MENU ===============

async def setup_commands(app):
    await app.bot.set_my_commands([
        BotCommand("start", "کردنەوەی مینیو"),
        BotCommand("cancel", "هەڵوەشاندنەوە"),
    ])


# =============== ERROR HANDLER ===============

async def error_handler(update, context):
    logger.error(
        "Unhandled error: %s",
        context.error,
        exc_info=(
            type(context.error),
            context.error,
            context.error.__traceback__,
        ) if context.error else None,
    )


# =============== MAIN ===============

def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN environment variable is missing."
        )

    init_db()

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(setup_commands)
        .build()
    )

    add_conversation = ConversationHandler(
        entry_points=[
            MessageHandler(
                PRIVATE
                & filters.Regex(r"^➕ زیادکردنی ئەنیمی$"),
                add_start,
            )
        ],
        states={
            ANIME_NAME: [
                MessageHandler(
                    PRIVATE & filters.TEXT & ~filters.COMMAND,
                    get_name,
                )
            ],
            JAPANESE_NAME: [
                MessageHandler(
                    PRIVATE & filters.TEXT & ~filters.COMMAND,
                    get_japanese_name,
                )
            ],
            SEASON: [
                MessageHandler(
                    PRIVATE & filters.TEXT & ~filters.COMMAND,
                    get_season,
                )
            ],
            EPISODES: [
                MessageHandler(
                    PRIVATE & filters.TEXT & ~filters.COMMAND,
                    get_episodes,
                )
            ],
            POST_LINK: [
                MessageHandler(
                    PRIVATE & filters.TEXT & ~filters.COMMAND,
                    get_post_link,
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(
                PRIVATE & filters.Regex(r"^❌ هەڵوەشاندنەوە$"),
                cancel,
            ),
        ],
        allow_reentry=True,
    )

    # Add conversation first, and only in private chat.
    app.add_handler(add_conversation)

    # Commands remain available in groups and private chats.
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(MessageHandler(filters.COMMAND, other_command))

    # All normal text handlers are private-chat only.
    # The bot will not answer ordinary group conversation.
    app.add_handler(
        MessageHandler(
            PRIVATE & filters.TEXT & ~filters.COMMAND,
            private_text_router,
        )
    )

    app.add_error_handler(error_handler)

    logger.info("Aura Anime is starting...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
