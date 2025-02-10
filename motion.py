#!/usr/bin/env python3
import fcntl
import os
import time
import logging
import glob  # For finding the latest photo
import requests

# --- START FCNTL TEST INSIDE MOTION.PY ---
log_file = "/tmp/motion_notification.log" # Ensure this matches your log file path
logging.basicConfig(level=logging.DEBUG, filename=log_file,
                    format='%(asctime)s - %(levelname)s - %(message)s')

logging.info("--- START FCNTL TEST INSIDE MOTION.PY ---") # Log start of test

if hasattr(fcntl, 'LOCK_EX'):
    logging.info("FCNTL TEST: fcntl.LOCK_EX is defined.")
else:
    logging.error("FCNTL TEST: fcntl.LOCK_EX is NOT defined.") # Log as ERROR if not defined

if os.name == 'posix':
    logging.info("FCNTL TEST: Operating system identified as POSIX-compliant (like Linux, macOS).")
else:
    logging.warning(f"FCNTL TEST: Operating system '{os.name}' is NOT POSIX-compliant (like Windows).")

logging.info("--- END FCNTL TEST INSIDE MOTION.PY ---") # Log end of test

print("Script started - VERY BASIC PRINT") # Keep your original print statement
# --- END FCNTL TEST INSIDE MOTION.PY ---

# --- Logging Setup ---
# Log file path is already defined and basicConfig is already called above in FCNTL test section
# log_file = "/tmp/motion_notification.log" # Redundant - defined above
# logging.basicConfig(...) # Redundant - already configured above

logging.info("Basic logging initialized (after fcntl test section)") # Log again after fcntl test section

# Telegram Bot and Chat ID from environment variables
bot_token = os.environ.get('BOT_TOKEN')
chat_id = os.environ.get('TELEGRAM_ID')

print(f"BOT_TOKEN from env: {bot_token}")
print(f"TELEGRAM_ID from env: {chat_id}")

logging.debug(f"BOT_TOKEN from env (log): {bot_token}")
logging.debug(f"TELEGRAM_ID from env (log): {chat_id}")

if not bot_token or not chat_id:
    error_message = "Environment variables BOT_TOKEN or TELEGRAM_ID are not set!"
    logging.error(error_message)
    print(error_message)
    exit(1)

telegram_url_message = f'https://api.telegram.org/bot{bot_token}/sendMessage' # URL for sending text messages
telegram_url_photo = f'https://api.telegram.org/bot{bot_token}/sendPhoto'    # URL for sending photos

last_notification_file = "/home/goku/Motion-detection/motion_last_notification.txt"
last_photo_sent_file = "/home/goku/Motion-detection/motion_last_photo_sent.txt" # File to store path of last sent photo
notification_cooldown = 10
pics_path = "/home/goku/Motion-detection/pics" # **IMPORTANT:** Adjust this to your actual photos path if different!

def send_motion_message_with_photo():
    message = "Motion detected! Last photo captured:"
    try:
        # --- Find Last Photo ---
        list_of_photos = glob.glob(os.path.join(pics_path, '*.jpg')) # Find all JPGs in pics_path
        if not list_of_photos:
            logging.warning("No photos found to send.")
            return  # Exit function if no photos

        latest_photo = max(list_of_photos, key=os.path.getctime) # Get newest photo
        logging.info(f"Latest photo found: {latest_photo}")

        last_photo_path_sent = None
        try:
            with open(last_photo_sent_file, "r") as f_last_photo:
                last_photo_path_sent = f_last_photo.read().strip() # Read last photo path
                logging.debug(f"Last photo path sent (read from file): {last_photo_path_sent}")
        except FileNotFoundError:
            logging.info("Last photo sent file not found. Sending notification anyway.")
            last_photo_path_sent = None # Treat as first run
        except Exception as e:
            logging.error(f"Error reading last photo sent file: {e}")
            last_photo_path_sent = None # Treat as error

        # --- Compare Last Photo with Newly Detected Photo ---
        if latest_photo == last_photo_path_sent:
            logging.info("Latest photo is the same as the last photo sent. Skipping notification.")
            print("Duplicate photo - Notification skipped (VERY BASIC PRINT)") # Basic print for quick check
            return # Exit function if photo is the same
        else:
            logging.info("Latest photo is different from last sent. Proceeding with notification.")


        # --- Send Text Message First ---
        message_params = {"chat_id": chat_id, "text": message}
        response_message = requests.post(telegram_url_message, data=message_params)
        response_message.raise_for_status() # Raise exception for bad status codes
        logging.info("Text message sent successfully to Telegram")

        # --- Send Last Photo ---
        with open(latest_photo, 'rb') as photo_file:
            photo_params = {"chat_id": chat_id}
            files = {'photo': photo_file} # 'photo' is the field name Telegram expects
            response_photo = requests.post(telegram_url_photo, params=photo_params, files=files)
            response_photo.raise_for_status()
            logging.info(f"Photo sent successfully: {latest_photo}")
            print(f"Telegram Photo API Response Content: {response_photo.text}") # Print photo response
            logging.debug(f"Telegram Photo API Response Content (log): {response_photo.text}") # Log photo response

        # --- Update Last Photo Sent File ---
        try:
            with open(last_photo_sent_file, "w") as f_last_photo:
                f_last_photo.write(latest_photo) # Save path of SENT photo
                logging.debug(f"Updated last photo sent file with: {latest_photo}")
        except Exception as e:
            logging.error(f"Error writing last photo sent file: {e}")


    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending Telegram message or photo: {e}")
        if hasattr(e.response, 'text'):
            logging.error(f"Full Telegram API error response: {e.response.text}")

def motion_event():
    logging.debug("motion_event() function called")

    current_time = time.time()
    last_notification_time = None
    lock_file_descriptor = None

    try:
        lock_file_descriptor = open(last_notification_file + ".lock", 'w')
        fcntl.lockf(lock_file_descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)

        # --- Critical Section ---
        logging.debug(f"Attempting to read last notification time from file: {last_notification_file}")
        try:
            with open(last_notification_file, "r") as f:
                last_notification_time = float(f.read())
            logging.debug(f"Successfully read last notification time: {last_notification_time}")
        except FileNotFoundError:
            last_notification_time = 0
            logging.debug("Last notification file NOT found, treating as first run.")
        except Exception as e:
            logging.error(f"Error reading last notification file: {e}")
            last_notification_time = 0

        time_since_last_notification = current_time - last_notification_time
        logging.debug(f"Time since last notification: {time_since_last_notification:.2f} seconds")

        if time_since_last_notification >= notification_cooldown:
            logging.info("Cooldown expired or first run. Sending Telegram notification with photo.")
            send_motion_message_with_photo() # Call the photo sending function

            try:
                logging.debug(f"Attempting to write last notification time to file: {last_notification_file}")
                with open(last_notification_file, "w") as f:
                    f.write(str(current_time))
                logging.debug(f"Successfully updated last notification time file: {current_time}")
            except Exception as e:
                logging.error(f"Error writing last notification time file: {e}")
        else:
            logging.info(f"Motion detected, cooldown active. Not sending new message.")
        # --- End Critical Section ---

    except BlockingIOError:
        logging.warning("Could not acquire lock, another process is likely handling notification. Skipping photo notification.")
    except Exception as e:
        logging.error(f"Error in motion_event: {e}")
    finally:
        if lock_file_descriptor:
            fcntl.lockf(lock_file_descriptor, fcntl.LOCK_UN)
            lock_file_descriptor.close()

if __name__ == "__main__":
    motion_event()
