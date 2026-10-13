```python
import os
import html
import csv
import io
import zipfile
import logging
import sqlite3

from pathlib import Path
from urllib.parse import urlparse

from telegram import ReplyKeyboardMarkup, BotCommand
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)

# =============== CONFIGURATION ===============

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()

ADMIN_IDS = {
    6450069400,  # Sung Jin
    7741069173,  # Tessia
    5455374693,  # Kaell
    8535560894,  # Peshin
}

DB_PATH = Path(__file__).resolve().parent / "anime.db"

MAX_ZIP_SIZE = 20 * 1024 * 1024
MAX_CSV_SIZE = 5 * 1024 * 1024

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
    except (ValueError, AttributeError):
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


# =============== ZIP / CSV IMPORT ===============

async def receive_zip(update, context):
    message = update.effective_message
    user = update.effective_user
    document = message.document

    # Only the listed admins can import anime.
    if not user or user.id not in ADMIN_IDS:
        await message.reply_text(
            "⛔ تەنها ئەدمینە ڕێگەپێدراوەکان دەتوانن ZIP زیاد بکەن."
        )
        return

    if not document or not document.file_name:
        await message.reply_text(
            "⚠️ تکایە فایلێکی ZIP بنێرە."
        )
        return

    if not document.file_name.lower().endswith(".zip"):
        await message.reply_text(
            "⚠️ فایلەکە ZIP نییە.\n"
            "فایلەکەت بە شێوەی .zip بنێرە."
        )
        return

    if document.file_size and document.file_size > MAX_ZIP_SIZE:
        await message.reply_text(
            "⚠️ قەبارەی ZIP زۆرە. سنوورەکە ٢٠ مێگابایتە."
        )
        return

    await message.reply_text(
        "⏳ فایلەکە وەردەگرم و زانیارییەکان دەخوێنمەوە..."
    )

    try:
        telegram_file = await document.get_file()
        buffer = io.BytesIO()
        await telegram_file.download_to_memory(out=buffer)
        buffer.seek(0)

        added = 0
        updated = 0
        skipped = 0

        with zipfile.ZipFile(buffer, "r") as archive:
            csv_names = [
                name for name in archive.namelist()
                if Path(name).name.lower() == "animes.csv"
                and not name.endswith("/")
            ]

            if not csv_names:
                await message.reply_text(
                    "❌ فایلەکە دروست نییە.\n"
                    "تکایە animes.csv لە ناو ZIP ـەکە دابنێ."
                )
                return

            csv_info = archive.getinfo(csv_names[0])

            if csv_info.file_size > MAX_CSV_SIZE:
                await message.reply_text(
                    "⚠️ قەبارەی animes.csv زۆرە."
                )
                return

            raw_csv = archive.read(csv_names[0])
            csv_text = raw_csv.decode("utf-8-sig")
            reader = csv.DictReader(io.StringIO(csv_text))

            required_columns = {
                "name_kurdish",
                "name_japanese",
                "telegram_post_link",
            }

            actual_columns = set(reader.fieldnames or [])
            missing = required_columns - actual_columns

            if missing:
                await message.reply_text(
                    "❌ ستوونە پێویستەکان لە CSV نییە:\n"
                    + ", ".join(sorted(missing))
                )
                return

            with db_connect() as db:
                for row in reader:
                    kurdish_name = (
                        row.get("name_kurdish") or ""
                    ).strip()
                    japanese_name = (
                        row.get("name_japanese") or ""
                    ).strip()
                    post_link = (
                        row.get("telegram_post_link") or ""
                    ).strip()

                    season_text = (
                        row.get("season") or "1"
                    ).strip()
                    episodes_text = (
                        row.get("episodes") or "1"
                    ).strip()

                    if (
                        not kurdish_name
                        or not japanese_name
                        or not safe_url(post_link)
                    ):
                        skipped += 1
                        continue

                    try:
                        season = int(season_text)
                        episodes = int(episodes_text)
                    except (ValueError, TypeError):
                        skipped += 1
                        continue

                    if (
                        not 1 <= season <= 100
                        or not 1 <= episodes <= 10000
                    ):
                        skipped += 1
                        continue

                    existing = db.execute(
                        """
                        SELECT id FROM animes
                        WHERE anime_name = ? COLLATE NOCASE
                           OR japanese_name = ? COLLATE NOCASE
                        LIMIT 1
                        """,
                        (kurdish_name, japanese_name),
                    ).fetchone()

                    if existing:
                        db.execute(
                            """
                            UPDATE animes
                            SET anime_name = ?,
                                japanese_name = ?,
                                season = ?,
                                episodes = ?,
                                post_link = ?
                            WHERE id = ?
                            """,
                            (
                                kurdish_name,
                                japanese_name,
                                season,
                                episodes,
                                post_link,
                                existing["id"],
                            ),
                        )
                        updated += 1
                    else:
                        db.execute(
                            """
                            INSERT INTO animes
                            (anime_name, japanese_name, season,
                             episodes, post_link)
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (
                                kurdish_name,
                                japanese_name,
                                season,
                                episodes,
                                post_link,
                            ),
                        )
                        added += 1

                db.commit()

        await message.reply_text(
            "✅ <b>هاوردنی ئەنیمی تەواو بوو!</b>\n\n"
            f"🆕 زیادکرا: {added}\n"
            f"🔄 نوێکرایەوە: {updated}\n"
            f"⚠️ پشتگوێ خرا: {skipped}\n"
            f"📚 کۆی ئەنیمی لە داتابەیس: {anime_count()}",
            parse_mode=ParseMode.HTML,
            reply_markup=MENU,
        )

    except zipfile.BadZipFile:
        await message.reply_text(
            "❌ فایلەکە ZIP ـێکی دروست نییە."
        )
    except UnicodeDecodeError:
        await message.reply_text(
            "❌ CSV ناتوانرێت بخوێندرێتەوە. "
            "تکایە بە UTF-8 پاشەکەوتی بکە."
        )
    except (sqlite3.Error, OSError, ValueError) as error:
        logger.exception("ZIP import failed")
        await message.reply_text(
            "❌ هەڵەیەک لە هاوردنی فایل ڕوویدا.\n"
            f"جۆری هەڵە: {html.escape(str(error)[:250])}",
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        logger.exception("Unexpected ZIP import error")
        await message.reply_text(
            "❌ هەڵەیەکی نەناسراو ڕوویدا. "
            "لۆگی بۆتەکە بپشکنە."
        )


# =============== SHOW MENU ===============

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
    if update.effective_chat and update.effective_chat.type == "private":
        context.user_data.pop("anime_data", None)
        context.user_data.pop("search_mode", None)

    await show_menu(update, context)


async def other_command(update, context):
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
                PRIVATE & filters.Regex(r"^➕ زیادکردنی ئەنیمی$"),
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

    # Add the single-anime conversation first.
    app.add_handler(add_conversation)

    # ZIP uploads: admin-only check is inside receive_zip().
    app.add_handler(
        MessageHandler(
            PRIVATE & filters.Document.ALL,
            receive_zip,
        )
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(MessageHandler(filters.COMMAND, other_command))

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
```
