import os, dotenv, logging
from data import load_data
from datetime import datetime
from user_database import registered_users, user_data, collection, load_registered_users
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ConversationHandler,
    ContextTypes,
    CallbackContext,
)
import re

# Load environment variables
dotenv.load_dotenv()

BOT_USERNAME = os.getenv("BOT_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID"))

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
START, NAME, PHONE, ADMIN, NEW_REGISTRATION = range(5)


# Function to start the conversation
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_name = update.message.from_user.username
    if user_id in registered_users:
        await update.message.reply_text(
            "You are already registered! Which university do you want to look up?"
        )
        return ConversationHandler.END

    user_data[user_id] = {"username": user_name}
    await update.message.reply_text("Welcome! Please enter your name:")
    return NAME

# Function to handle name input
async def name(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_data[user_id]["name"] = update.message.text
    
    button = KeyboardButton("📞✅ Share Phone Number 📞✅", request_contact=True)
    reply_markup = ReplyKeyboardMarkup([[button]], one_time_keyboard=True, resize_keyboard=False)
    
    await update.message.reply_text("Please share your phone number!", reply_markup=reply_markup, parse_mode='HTML')
    return PHONE

# Function to handle phone number input
async def phone(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    
    if update.message.contact:
        phone_number = update.message.contact.phone_number
    else:
        phone_number = update.message.text
        
    signup_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    user_data[user_id].update({
        "phone_number": phone_number,
        "signup_datetime": signup_datetime,
        "search_count": 0,
        "roadmap_pressed": 0 
    })
    
    collection.update_one({"_id": user_id}, {"$set": user_data[user_id]}, upsert=True)
    registered_users.append(user_id)
    start_text = """
🎓 Thank you! Which university do you want to look up? 📚

When referencing universities, please adhere to the following guidelines:

Spell university names correctly, using their official titles. 🏛️

Example: Stanford University 🏫
Example: University of Cambridge 🏰
Example: Massachusetts Institute of Technology 💻
You may use either all capital letters or standard capitalization, but ensure the spelling is correct. 🔠

Example: HARVARD UNIVERSITY or Harvard University 🏛️
Example: UNIVERSITY OF OXFORD or University of Oxford 🎓
Do not include specific branch locations or campuses. 🏢

The rankings should be for the main university only.
If you're unsure about the correct spelling or official name of a university, double-check before submitting. ✔️

The system will not provide rankings based on specific locations or branches, so please only use the primary university name. 📊
    """
    await update.message.reply_text(start_text, reply_markup=ReplyKeyboardRemove())
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

Spell university names correctly, using their official titles. 🏛️

Example: Stanford University 🏫
Example: University of Cambridge 🏰
Example: Massachusetts Institute of Technology 💻
You may use either all capital letters or standard capitalization, but ensure the spelling is correct. 🔠

Example: HARVARD UNIVERSITY or Harvard University 🏛️
Example: UNIVERSITY OF OXFORD or University of Oxford 🎓
Do not include specific branch locations or campuses. 🏢

The rankings should be for the main university only.
If you're unsure about the correct spelling or official name of a university, double-check before submitting. ✔️

The system will not provide rankings based on specific locations or branches, so please only use the primary university name. 📊
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
    user_id = update.message.from_user.id
    text: str = update.message.text

    current_state = context.user_data.get("conversation_state")
    if current_state in [NAME, PHONE, ADMIN]:
        return

    print(f'User ({update.message.chat.id}) in {message_type}: "{text}"')
    
    if message_type in ["group", "supergroup", "channel"]:
        if BOT_USERNAME in text:
            new_text = re.sub(f'@{BOT_USERNAME}', '', text, flags=re.IGNORECASE).strip()
            response: str = handle_response(new_text, qs_data, times_data, us_news_data)
        else:
            return
    else:
        response: str = handle_response(text, qs_data, times_data, us_news_data)

    print("Bot:", response)
    
    # Creating an inline keyboard for Pollfish Survey
    keyboard = [[InlineKeyboardButton("💡✅ Take Survey 🚀🎯", url="https://wss.pollfish.com/link/3f802d5a-a567-42f8-9b53-c5f9826b74b6")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    roadmap_keyboard = [[InlineKeyboardButton("🛣🛫 EYUF Application roadmap ✨🗺", url="https://unicraft.uz/roadmaps/eyuf")]]
    roadmap_markup = InlineKeyboardMarkup(roadmap_keyboard)
    
    # Sending the response with the inline button 
    await update.message.reply_text(response, reply_markup=reply_markup, reply_markup=roadmap_markup)
    
    # Incrementing the user's number of presses on the Unicraft Roadmap Inline button
    if user_id in user_data:
        user_data[user_id]["roadmap_presses"] = user_data[user_id].get("roadmap_presses", 0) + 1
        collection.update_one({"_id": user_id}, {"$set": {"roadmap_presses": user_data[user_id]["roadmap_presses"]}})

    # Incrementing the user's search count for data analysis
    if user_id in user_data:
        user_data[user_id]["search_count"] = user_data[user_id].get("search_count", 0) + 1
        collection.update_one({"_id": user_id}, {"$set": {"search_count": user_data[user_id]["search_count"]}})

# Function to handle errors
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")
