# Telegram Feedback Bot

A Python-based Telegram bot built with the aiogram framework that allows users to receive anonymous feedback and messages via a unique referral link.

## Overview

This application facilitates anonymous communication between users. Each user can generate a unique link. When another user clicks this link, they can send anonymous messages to the link owner. The recipient can reply to these messages directly through the bot without knowing the sender's identity.

## Features

- **Anonymous Messaging:** Users can send messages anonymously to others via a shared link.
- **Unique Referral Links:** Each user can generate a unique link to share with others.
- **Reply System:** Recipients can reply to anonymous messages directly. The reply is forwarded to the original sender.
- **Broadcast System:** Administrators can send broadcast messages to all registered users.
- **User Database:** Uses SQLite to store registered user IDs.
- **Interactive Keyboard:** Simple interface with buttons to generate links and view help instructions.

## Prerequisites

- Python 3.7+
- A Telegram Bot Token (obtained from BotFather)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Install the required dependencies:
   ```bash
   pip install aiogram
   ```

## Configuration

Before running the bot, you must configure the `feedback_bot.py` file:

1. Open `feedback_bot.py` in a text editor.
2. Locate the configuration section at the top of the file.
3. Replace the `API_TOKEN` placeholder with your actual Telegram Bot API token.
4. Add your Telegram User ID to the `ADMIN_LIST` to enable broadcast capabilities.

```python
# --- CONFIGURATION ---
API_TOKEN = 'YOUR_API_TOKEN_HERE'
ADMIN_LIST = [123456789]  # Replace with your numeric User ID
```

## Usage

1. Run the bot script:
   ```bash
   python feedback_bot.py
   ```

2. Open Telegram and search for your bot.
3. Click "Start" or type `/start`.
4. Use the **Get My Link** button to generate your unique link.
5. Share the link with others. When they click it, they can send you anonymous messages.
6. To reply to a message, simply reply to the message received from the bot.

## Project Structure

- `feedback_bot.py`: The main entry point and logic for the bot.
- `bot_database.db`: SQLite database file (created automatically upon first run) which stores user IDs.

## Disclaimer

This bot is intended for educational and personal use. Ensure you comply with Telegram's Terms of Service when using this bot.
