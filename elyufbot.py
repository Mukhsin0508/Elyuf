import logging
import os
from data import load_data
import pickle
from telegram import Update
from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
    Application,
    CallbackContext,
)
import dotenv

dotenv.load_dotenv()

TOKEN: str = os.getenv("TOKEN")
BOT_USERNAME: str = os.getenv("BOT_USERNAME")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

START, NAME, PHONE, ADMIN, NEW_REGISTRATION = range(5)

user_data = {}
registered_users = []
admin_password ="ADMIN_PASSWORD"
admin_user_id = "ADMIN_USER_ID"

# File to save registered users data
DATA_FILE = "registered_users.pkl"


def save_registered_users():
    with open(DATA_FILE, "wb") as f:
        pickle.dump((registered_users, user_data), f)


def load_registered_users():
    global registered_users, user_data
    if os.path.exists(DATA_FILE) and os.path.getsize(DATA_FILE) > 0:
        with open(DATA_FILE, "rb") as f:
            registered_users, user_data = pickle.load(f)
    else:
        registered_users = []
        user_data = {}


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in registered_users:
        await update.message.reply_text(
            "You are already registered! Which university you want to look up?"
        )
        return ConversationHandler.END

    user_data[user_id] = {}
    await update.message.reply_text("Welcome! Please enter your name:")
    return NAME


async def name(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_data[user_id]["name"] = update.message.text
    await update.message.reply_text("Please enter your phone number:")
    return PHONE


async def phone(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_data[user_id]["phone"] = update.message.text
    await update.message.reply_text("Thank you, Which university you want to look up?")
    registered_users.append(user_id)
    save_registered_users()  # Save data after registration
    return ConversationHandler.END


async def admin_id(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id == admin_user_id:
        await update.message.reply_text("Please enter the admin password:")
        return ADMIN
    else:
        return ConversationHandler.END


async def admin_password(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    password = update.message.text
    if password == admin_password:
        await update.message.reply_text("Welcome, admin!")
        return NEW_REGISTRATION
    else:
        await update.message.reply_text("Incorrect password.")
        return ConversationHandler.END


# Load registered users data
load_registered_users()

# Load university rankings data
try:
    qs_data, times_data, us_news_data = load_data()
    print("Loaded data successfully!")
except Exception as e:
    print(f"Error loading data: {e}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("I am Elyuf Ranker! How can I help?")


async def restart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "I finished restarting myself! Is there any university you want to look up!?"
    )


def handle_response(text: str, qs_data, times_data, us_news_data) -> str:
    university = text.strip().lower()
    response = []

    print(f"Looking up rankings for university: {university}")

    qs_rank = "Not found, The university name is either misspelled or not in the top 300 rankings of QS World University Rankings!"
    times_rank = "Not found, The university name is either misspelled or not in the top 300 rankings of Times Higher Education World University Rankings!"
    us_news_rank = "Not found, The university name is either misspelled or not in the top 300 rankings of US News & World Report Best Global Universities!"

    for item in qs_data:
        if item["university"].lower() == university:
            qs_rank = item["rank"]
            break

    for item in times_data:
        if item["university"].lower() == university:
            times_rank = item["rank"]
            break

    for item in us_news_data:
        if item["university"].lower() == university:
            us_news_rank = item["rank"]
            break

    response.append(f"QS World University Rank: {qs_rank}\n")
    response.append(f"Times Higher Education Rank: {times_rank}\n")
    response.append(f"US News & World Report Rank: {us_news_rank}\n")

    return "\n".join(response)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text

    # Check if the conversation handler is active
    current_state = context.user_data.get("conversation_state")
    if current_state in [NAME, PHONE, ADMIN]:
        return

    print(f'User ({update.message.chat.id}) in {message_type}: "{text}"')

    if message_type == "group":
        if BOT_USERNAME in text:
            new_text: str = text.replace(BOT_USERNAME, "").strip()
            response: str = handle_response(new_text, qs_data, times_data, us_news_data)
        else:
            return
    else:
        response: str = handle_response(text, qs_data, times_data, us_news_data)

    print("Bot:", response)
    await update.message.reply_text(response)


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Update {update} caused error {context.error}")


if __name__ == "__main__":
    print("Starting bot...")
    app = Application.builder().token(TOKEN).build()

    # Command Handlers
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("restart", restart_command))

    # Conversation Handler for registration
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone)],
            ADMIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_password)],
        },
        fallbacks=[CommandHandler("start", start_command)],
    )
    app.add_handler(conv_handler)

    # Message Handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Error Handler
    app.add_error_handler(error)

    # Polling
    print("Polling...")
    app.run_polling(poll_interval=3)
