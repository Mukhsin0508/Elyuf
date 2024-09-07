import os
import dotenv 
from telegram.ext import CommandHandler, ConversationHandler, MessageHandler, filters, Application
from telegram_src.handlers import start_command, name, phone, admin_password, help_command, restart_command, handle_message, \
    error, NAME, PHONE, ADMIN


dotenv.load_dotenv()
TOKEN = os.getenv("TOKEN")


# Main function to start the bot and add handlers, conversation handlers, and error handlers, and run the bot.
# The bot will start polling for new messages.
# The bot will respond to commands and messages from users.
# This file is just like run.py in PastAPI
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
