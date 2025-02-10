import glob
import os
import subprocess
import logging
import datetime
from telegram import Bot, BotCommand, Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
import psutil
import time
import asyncio
from telegram.error import RetryAfter, NetworkError

# Configuration for Telegram Bot
chat_id = os.environ['TELEGRAM_ID']
bot_token = os.environ['BOT_TOKEN']
application = Application.builder().token(bot_token).build()

# Set up the pics directory for storing images and videos
pics_path = '/home/goku/Motion-detection/pics'

# Initialize logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)

# Function to send messages safely with rate limiting
async def safe_send_message(bot, chat_id, text):
    try:
        logging.info(f"Sending message: {text}")
        await bot.send_message(chat_id, text=text)
    except RetryAfter as e:
        logging.error(f"Rate limited. Retrying in {e.retry_after} seconds...")
        await asyncio.sleep(e.retry_after)
        await bot.send_message(chat_id, text=text)
    except NetworkError as e:
        logging.error(f"Network error while sending message: {e}")
        await asyncio.sleep(5)  # Wait for a bit before retrying
        await bot.send_message(chat_id, text=text)

# Function to take a snapshot using fswebcam (for laptops)
async def take_snap(update, context):
    bot = context.bot
    filename = '01-' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.jpg'
    snapshot_path = os.path.join(pics_path, filename)

    logging.info(f"Request received to take a snapshot. Saving to {snapshot_path}...")
    
    try:
        # Use fswebcam to capture snapshot for laptops
        res = subprocess.Popen(["fswebcam", "-r", "640x480", snapshot_path], shell=False, stdout=subprocess.PIPE)
        res.wait()
        
        # Check if the file is created
        if os.path.exists(snapshot_path):
            logging.info(f"Snapshot saved successfully: {snapshot_path}")
            await safe_send_message(bot, chat_id, text="Snapshot taken successfully!")
            await bot.send_photo(chat_id, photo=open(snapshot_path, "rb"))
        else:
            logging.error(f"Snapshot file not found after capture: {snapshot_path}")
            await safe_send_message(bot, chat_id, text="Error: Snapshot capture failed.")
    
    except Exception as e:
        logging.error(f"Error during snapshot capture: {e}")
        await safe_send_message(bot, chat_id, text="Error: Could not capture snapshot.")

# Start Motion Detection
async def start_motion(update, context):
    logging.info("Starting motion detection...")

    # Check if motion is already running
    for proc in psutil.process_iter(attrs=['pid', 'name']):
        if 'motion' in proc.info['name']:
            await update.message.reply_text("Motion is already running.")
            logging.info("Motion is already running.")
            return

    try:
        # Start motion in the background
        process = subprocess.Popen(
            ["motion", "-c", "/home/goku/Motion-detection/motion.conf"],
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        stdout, stderr = process.communicate()

        # Log output and errors from motion process
        if stdout:
            logging.info(f"Motion output: {stdout.decode()}")
        if stderr:
            logging.error(f"Motion error: {stderr.decode()}")

        if process.returncode == 0:
            await update.message.reply_text("Motion detection started successfully.")
            logging.info("Motion started successfully.")
        else:
            await update.message.reply_text("Failed to start motion detection.")
            logging.error(f"Motion failed to start with return code: {process.returncode}")
        
    except Exception as e:
        logging.error(f"Failed to start motion: {e}")
        await update.message.reply_text("Error: Failed to start motion detection.")

# Stop Motion Detection
async def stop_motion(update, context):
    logging.info("Stopping motion detection...")
    for proc in psutil.process_iter():
        if proc.name() == "motion":
            proc.kill()
            logging.info(f"Stopped motion process with PID: {proc.pid}")
    await update.message.reply_text("Motion detection stopped.")

# Check if motion is running (Improved version)
async def check_motion(update, context):
    logging.info("Checking if motion is running...")
    try:
        # Use 'pgrep' to check if a process named 'motion' is running.
        # pgrep returns exit code 0 if motion is running, 1 if not.
        subprocess.run(["pgrep", "motion"], check=True, capture_output=True)
        motion_running = True
    except subprocess.CalledProcessError:
        motion_running = False

    if motion_running:
        await update.message.reply_text("Motion is running.")
        logging.info("Motion is running.")
    else:
        await update.message.reply_text("Motion is not running.")
        logging.warning("Motion is not running.")
# Send the latest video
async def send_last_video(update, context):
    logging.info("Request received to send the last video...")
    
    list_of_videos = glob.glob(os.path.join(pics_path, '*.mkv'))
    if not list_of_videos:
        logging.warning("No videos found.")
        await update.message.reply_text("No videos captured.")
        return
    
    latest_video = max(list_of_videos, key=os.path.getctime)
    logging.info(f"Sending last video: {latest_video}")
    
    try:
        await update.message.reply_video(video=open(latest_video, 'rb'))
        logging.info(f"Video sent successfully: {latest_video}")
    except Exception as e:
        logging.error(f"Error while sending video: {e}")
        await update.message.reply_text("Error: Could not send video.")

# Send the latest photo
async def send_last_photo(update, context):
    logging.info("Request received to send the last photo...")
    
    list_of_photos = glob.glob(os.path.join(pics_path, '*.jpg'))
    if not list_of_photos:
        logging.warning("No photos found.")
        await update.message.reply_text("No photos captured.")
        return
    
    latest_photo = max(list_of_photos, key=os.path.getctime)
    logging.info(f"Sending last photo: {latest_photo}")
    
    try:
        await update.message.reply_photo(photo=open(latest_photo, 'rb'))
        logging.info(f"Photo sent successfully: {latest_photo}")
    except Exception as e:
        logging.error(f"Error while sending photo: {e}")
        await update.message.reply_text("Error: Could not send photo.")

# Define /help command handler
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        "Here are the available commands:\n"
        "/start - Start the bot and motion detection\n"
        "/stop - Stop motion detection\n"
        "/check - Check if motion is running\n"
        "/lastphoto - Send the last photo taken\n"
        "/lastvideo - Send the last video taken"
    )
    await update.message.reply_text(help_text)

# Register commands
start_handler = CommandHandler('start', start_motion)
application.add_handler(start_handler)

stop_handler = CommandHandler('stop', stop_motion)
application.add_handler(stop_handler)

check_motion_handler = CommandHandler('check', check_motion)
application.add_handler(check_motion_handler)

last_photo_handler = CommandHandler('lastphoto', send_last_photo)
application.add_handler(last_photo_handler)

last_video_handler = CommandHandler('lastvideo', send_last_video)
application.add_handler(last_video_handler)
help_handler = CommandHandler('help', help_command)
application.add_handler(help_handler)

# Set the available commands
async def set_commands():
    bot = Bot(token=bot_token)
    commands = [
        ('start', 'Start the bot and motion detection'),
        ('stop', 'Stop motion detection'),
        ('check', 'Check if motion is running'),
        ('lastphoto', 'Send the last photo taken'),
        ('lastvideo', 'Send the last video taken'),
        ('help', 'Show this help message'),
    ]
    await bot.set_my_commands(commands)

if __name__ == '__main__':
    set_commands()
    application.run_polling()

