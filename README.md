# Project Title: Motion Detection Telegram Bot

## Description

This project is a motion detection system that uses a Raspberry Pi (or similar Linux system) with a camera to monitor for motion. When motion is detected, it captures a photo and sends a notification with the photo to a Telegram chat.  It also provides Telegram bot commands to control motion detection, take snapshots, and retrieve the latest media.

## Features

*   **Motion Detection:** Uses the `motion` daemon for efficient motion detection.
*   **Telegram Notifications:** Sends instant notifications to your Telegram chat when motion is detected, including a photo of the event.
*   **Continuous Recording:**  `motion` daemon can be configured to continuously record videos.
*   **Telegram Bot Commands:**
    *   `/start`: Starts motion detection and the Telegram bot.
    *   `/stop`: Stops motion detection.
    *   `/check`: Checks if motion detection is currently running.
    *   `/lastphoto`: Sends the latest captured photo.
    *   `/lastvideo`: Sends the latest captured video.
    *   `/help`: Displays a list of available commands.

*   **Rate Limiting and Error Handling:** Implements safe message sending with retry mechanisms to handle Telegram API rate limits and network errors.
*   **Configuration:** Easily configurable via `motion.conf` file and environment variables.
*   **Logging:** Comprehensive logging for debugging and monitoring.

## Prerequisites

*   **Hardware:**
    *   A Linux-based system (e.g., Raspberry Pi, Laptop running Linux).
    *   A camera connected to the system (e.g., USB webcam, Raspberry Pi camera module).
*   **Software:**
    *   Python 3.x
    *   `motion` daemon (installation instructions below)
    *   `fswebcam` (if using laptop webcam for snapshots, install if needed: `sudo apt-get install fswebcam`)
    *   Python libraries (install using pip):
        ```bash
        pip install python-telegram-bot python-telegram-bot[ext] requests psutil
        ```
*   **Telegram Bot:**
    *   Create a Telegram bot using BotFather and obtain a `BOT_TOKEN`.
    *   Get your Telegram chat ID (`TELEGRAM_ID`). You can use a bot like `@userinfobot` to find your chat ID.
*   **Environment Variables:**
    *   Set the following environment variables in your system:
        *   `BOT_TOKEN`: Your Telegram bot token.
        *   `TELEGRAM_ID`: Your Telegram chat ID.

## Installation and Setup

1.  **Install `motion` daemon:**

    ```bash
    sudo apt-get update
    sudo apt-get install motion
    ```

2.  **Clone the repository:**

    ```bash
    git clone [https://github.com/GokulrajKS/Motion-detection.git](https://github.com/GokulrajKS/Motion-detection.git)
    cd motion # Or the project directory name if different
    ```


3.  **Configure `motion` daemon:**

    *   Copy the provided `motion.conf` to the desired configuration directory.  A common location is within your project directory or `/etc/motion/motion.conf`.
    *   **Important:** Edit `motion.conf`:
        *   Adjust `videodevice` to your camera device (e.g., `/dev/video0`, `/dev/video1`).
        *   Modify `width`, `height`, `framerate` as needed.
        *   Verify `target_dir` is set to the path where you want to store pictures and videos. This should align with the `pics_path` variable in `engine.py` and `motion.py`.
        *   Tune motion detection parameters (`threshold`, `minimum_motion_frames`, etc.) as needed.

4.  **Set Environment Variables:**

    *   You need to set `BOT_TOKEN` and `TELEGRAM_ID` environment variables.
    *   You can set them in your `.bashrc`, `.zshrc`, or directly before running the scripts:

        **Example (in terminal before running):**
        ```bash
        export BOT_TOKEN="YOUR_BOT_TOKEN"
        export TELEGRAM_ID="YOUR_TELEGRAM_ID"
        python engine.py
        ```
        **For persistent environment variables (add to `.bashrc` or `.zshrc` and source the file):**
        ```bash
        echo 'export BOT_TOKEN="YOUR_BOT_TOKEN"' >> ~/.bashrc
        echo 'export TELEGRAM_ID="YOUR_TELEGRAM_ID"' >> ~/.bashrc
        source ~/.bashrc
        ```

5.  **Run the Telegram Bot Engine:**

    ```bash
    python engine.py
    ```

    The bot should start polling for commands. Use `/start` command in Telegram to start motion detection.

## Configuration Files and Scripts

*   **`engine.py`**:  The main Python script that runs the Telegram bot. It handles bot commands, interacts with the `motion` daemon, and sends Telegram messages.
*   **`motion.conf`**: Configuration file for the `motion` daemon. Defines camera settings, recording options, motion detection parameters, and specifies `motion.py` to be executed on motion detection. **Important:** Ensure the paths within this file, especially `target_dir`, `log_file`, `process_id_file`, and `on_motion_detected` script path, are correctly configured for your system.
*   **`motion.py`**: Python script executed by `motion` when motion is detected. It sends Telegram notifications with photos. **Important**: Verify the paths for `pics_path`, `last_notification_file`, and `last_photo_sent_file` within this script match your intended file locations.
*   **`pics/`**: Directory where captured photos and videos are stored. This path is defined in both `engine.py` and `motion.conf` and should be consistent.
*   **`motion_last_notification.txt`**: File used for cooldown mechanism to prevent excessive notifications. Ensure the path in `motion.py` is correct.
*   **`motion_last_photo_sent.txt`**: File to track the last photo sent to avoid duplicate notifications. Ensure the path in `motion.py` is correct.
*   `/tmp/motion/motion.pid`: Process ID file for the `motion` daemon. This is a common temporary file path on Linux systems.
*   `[project_directory]/motion.log`: Log file for the `motion` daemon. This path is configured in `motion.conf` and is relative to your project directory in the provided example, but can be configured to another location.
*   `/tmp/motion_notification.log`: Log file for the `motion.py` script. This is a common temporary file path on Linux systems, configured within `motion.py`.

## Usage

After starting `engine.py` and setting up the environment variables, you can use the following commands in your Telegram chat with the bot:

*   `/start` - Starts motion detection and the bot.
*   `/stop` - Stops motion detection.
*   `/check` - Checks if motion detection is running.
*   `/lastphoto` - Requests and sends the latest captured photo.
*   `/lastvideo` - Requests and sends the latest captured video.
*   `/help` - Displays this help message with available commands.

## Troubleshooting

*   **Check Logs:** Examine the log files. The `motion` daemon log is typically found at the path configured in `motion.conf` (e.g., `[project_directory]/motion.log`), and the `motion.py` script log is at `/tmp/motion_notification.log`. Check these files for errors.
*   **Permissions:** Ensure the scripts have execute permissions (`chmod +x motion.py` and `chmod +x engine.py` if needed). Check directory permissions for the `pics` folder and other directories where the scripts need to write files.
*   **Environment Variables:** Verify that `BOT_TOKEN` and `TELEGRAM_ID` are correctly set in your environment.
*   **Camera Device:** Double-check the `videodevice` path in `motion.conf` and ensure it corresponds to your camera device.
*   **Dependencies:** Ensure all Python libraries (listed in Prerequisites) and the `motion` daemon are installed.
*   **Telegram Bot:** Verify the bot token is correct and the bot is not blocked. Test sending a message to your bot directly through the Telegram Bot API if needed.
*   **Network:** Check internet connectivity for sending Telegram messages.
