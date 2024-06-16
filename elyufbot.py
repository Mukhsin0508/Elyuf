import logging
import os
from data import load_data
from pymongo import MongoClient
import certifi
import pickle
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
    Application,
    CallbackContext,
)
from datetime import datetime # UPDATE_17
import dotenv

# Load environment variables
dotenv.load_dotenv()

# Telegram bot and MongoDB configuration
TOKEN = os.getenv("TOKEN")
BOT_USERNAME = os.getenv("BOT_USERNAME")
MONGODB_URI = os.getenv("MONGO_CLIENT")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")

# MongoDB connection
ca_cert_path = certifi.where()
client = MongoClient(MONGODB_URI, tlsCAFile=ca_cert_path)
db = client["elyufbot"]
collection = db["users"]
for db_name in client.list_database_names():
    print(db_name)
    

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
START, NAME, PHONE, ADMIN, NEW_REGISTRATION = range(5)

# Global variables to store user data
registered_users = []
user_data = {}

# Load registered users from MongoDB
def load_registered_users():
    global registered_users, user_data
    registered_users = [doc["_id"] for doc in collection.find()]
    user_data = {doc["_id"]: doc for doc in collection.find()}
    print("Registered Users successfully loaded!")

# Function to start the conversation
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_username = update.message.from_user.username
    if user_id in registered_users:
        await update.message.reply_text(
            "You are already registered! Which university do you want to look up?"
        )
        return ConversationHandler.END

    user_data[user_id] = {"username": user_username}
    await update.message.reply_text("Welcome! Please enter your name:")
    return NAME

# Function to handle name input
async def name(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_data[user_id]["name"] = update.message.text
    
    #UPDATE_17 Created a button to reequest phone number
    button = KeyboardButton("📞✅ Share Phone Number 📞✅", request_contact = True)
    reply_markup = ReplyKeyboardMarkup([[button]], one_time_keyboard=True, resize_keyboard=False)
    
    await update.message.reply_text("Please share your phone number!", reply_markup=reply_markup, parse_mode='HTML')
    return PHONE

# Function to handle phone number input
async def phone(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    
    #UPDATE_17 Check if the message contains a contact 
    if update.message.contact:
        phone_number = update.message.contact.phone_number
    else:
        phone_number = update.message.text
        
    # Added a signup datetime
    signup_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    user_data[user_id].update({
        "phone_number": phone_number,
        "signup_datetime": signup_datetime
    })
    
    collection.update_one({"_id": user_id}, {"$set": user_data[user_id]}, upsert=True)
    registered_users.append(user_id)
    
    await update.message.reply_text("Thank you! Which university do you want to look up?", reply_markup=ReplyKeyboardRemove()) #UPDATE_17 add a keyboardRemove to make the "Share Phone Number" disappear!
    return ConversationHandler.END

# Function to handle admin authentication
async def admin_id(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id == ADMIN_USER_ID:
        await update.message.reply_text("Please enter the admin password:")
        return ADMIN
    else:
        await update.message.reply_text("You are not authorized to perform this action.")
        return ConversationHandler.END
    
# Function to verify admin password
async def admin_password(update: Update, context: CallbackContext):
    password = update.message.text
    if password == ADMIN_PASSWORD:
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
    print("University Rankings data successfully loaded!")
except Exception as e:
    print(f"Error loading data: {e}")

# Command to provide help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
When referencing universities, please adhere to the following guidelines:

1. Spell university names correctly, using their official titles. For example:
   Stanford University
   University of Cambridge
   Massachusetts Institute of Technology

2. You may use either all capital letters or standard capitalization, but ensure the spelling is correct. For instance:
   HARVARD UNIVERSITY or Harvard University
   UNIVERSITY OF OXFORD or University of Oxford

3. Do not include specific branch locations or campuses. The rankings should be for the main university only.

4. If you're unsure about the correct spelling or official name of a university, double-check before submitting.

5. The system will not provide rankings based on specific locations or branches, so please only use the primary university name.
    """
    await update.message.reply_text(help_text)

# Command to restart the bot
async def restart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "I finished restarting myself! Is there any university you want to look up!?"
    )

# Function to handle message responses
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


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):       # Function to handle messages
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

# Function to handle errors
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")

# Main function to start the bot
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
            PHONE: [ MessageHandler(filters.CONTACT, phone) , # Added a messageHandler for contact
                        MessageHandler(filters.TEXT & ~filters.COMMAND, phone)],
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
    app.run_polling(poll_interval=1)
