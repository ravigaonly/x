import os
import subprocess
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Get the bot token from environment variable

def clear_download_directory(directory):
    if os.path.exists(directory):
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                os.rmdir(file_path)

async def download_media(tweet_url, chat_id, context):
    try:
        output_dir = f"downloads/{chat_id}/media"
        clear_download_directory(output_dir)
        os.makedirs(output_dir, exist_ok=True)
        
        # Get the cookies content from the environment variable and write it to a temporary file
        cookies_content = os.getenv("TWITTER_COOKIES")
        if cookies_content:
            cookies_path = "/tmp/cookies.txt"
            with open(cookies_path, "w") as f:
                f.write(cookies_content)
        else:
            raise Exception("Cookies not found in environment variable.")

        # Run gallery-dl command
        command = ["gallery-dl", "--cookies", cookies_path, "--directory", output_dir, tweet_url]
        subprocess.run(command, check=True)

        # Send downloaded media to Telegram chat
        for file in os.listdir(output_dir):
            file_path = os.path.join(output_dir, file)
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                await context.bot.send_photo(chat_id=chat_id, photo=open(file_path, "rb"))
            elif file.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
                await context.bot.send_video(chat_id=chat_id, video=open(file_path, "rb"))
            os.remove(file_path)  # Delete the file after sending
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"Error downloading media: {str(e)}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text

    if "twitter.com" in text or "x.com" in text:
        if "/status/" in text:
            await context.bot.send_message(chat_id=chat_id, text="Downloading media...")
            await download_media(text, chat_id, context)
        else:
            await context.bot.send_message(chat_id=chat_id, text="Please send a valid Twitter status link.")
    else:
        await context.bot.send_message(chat_id=chat_id, text="Send me a Twitter link with media.")

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == "__main__":
    main()
