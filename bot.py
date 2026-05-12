import os
from flask import Flask
from multiprocessing import Process
from pymongo import MongoClient

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# =========================
# VARIABLES
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
MONGO_URI = os.getenv("MONGO_URI")
PORT = int(os.getenv("PORT", 10000))

# =========================
# DATABASE
# =========================

client = MongoClient(MONGO_URI)

db = client["telegram_bot"]

users = db["users"]

# =========================
# WEB SERVER
# =========================

web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "Bot Running Successfully!"

def run_web():
    web_app.run(
        host="0.0.0.0",
        port=PORT
    )

# =========================
# START COMMAND
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = (
        "✅ Bot Active Hai\n\n"
        "Commands:\n"
        "/setname YOUR_NAME\n"
        "/mydata"
    )

    await update.message.reply_text(text)

# =========================
# SET NAME
# =========================

async def setname(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if not context.args:

        await update.message.reply_text(
            "Usage:\n/setname YourName"
        )

        return

    name = " ".join(context.args)

    users.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "name": name
            }
        },
        upsert=True
    )

    await update.message.reply_text(
        f"✅ Name Saved:\n{name}"
    )

# =========================
# SAVE THUMBNAIL
# =========================

async def save_thumbnail(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    photo = update.message.photo[-1]

    file_id = photo.file_id

    users.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "thumbnail": file_id
            }
        },
        upsert=True
    )

    await update.message.reply_text(
        "✅ Thumbnail Saved Successfully!"
    )

# =========================
# MY DATA
# =========================

async def mydata(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    data = users.find_one(
        {"user_id": user_id}
    )

    if not data:

        await update.message.reply_text(
            "❌ No Data Found"
        )

        return

    name = data.get(
        "name",
        "Not Set"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "❌ Close",
                callback_data="close"
            )
        ]
    ])

    text = f"📌 Saved Name:\n{name}"

    if data.get("thumbnail"):

        await update.message.reply_photo(
            photo=data["thumbnail"],
            caption=text,
            reply_markup=keyboard
        )

    else:

        await update.message.reply_text(
            text,
            reply_markup=keyboard
        )

# =========================
# CLOSE BUTTON
# =========================

async def close_button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    try:

        await query.message.delete()

    except:

        pass

# =========================
# OWNER PANEL
# =========================

async def owner(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != OWNER_ID:

        return

    total_users = users.count_documents({})

    text = (
        "👑 Owner Panel\n\n"
        f"👤 Total Users: {total_users}"
    )

    await update.message.reply_text(text)

# =========================
# MAIN
# =========================

def main():

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("setname", setname)
    )

    app.add_handler(
        CommandHandler("mydata", mydata)
    )

    app.add_handler(
        CommandHandler("owner", owner)
    )

    app.add_handler(
        CallbackQueryHandler(
            close_button,
            pattern="close"
        )
    )

    app.add_handler(
        MessageHandler(
            filters.PHOTO,
            save_thumbnail
        )
    )

    print("Bot Started Successfully!")

    app.run_polling()

# =========================
# RUN
# =========================

if __name__ == "__main__":

    web_process = Process(
        target=run_web
    )

    web_process.start()

    main()
