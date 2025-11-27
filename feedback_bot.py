import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command, CommandStart, CommandObject

# --- CONFIGURATION ---
API_TOKEN = ''
ADMIN_LIST = []  # Your ID

# --- SETUP ---
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)
active_sessions = {}

# --- KEYBOARD SETUP ---
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔗 Get My Link"), KeyboardButton(text="❓ Help")]
    ],
    resize_keyboard=True,
    input_field_placeholder="Choose an option..."
)

# --- DATABASE ---
def init_db():
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (
                     user_id
                     INTEGER
                     PRIMARY
                     KEY
                 )''')
    conn.commit()
    conn.close()

def add_user(user_id):
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('SELECT user_id FROM users')
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users
init_db()

# --- 1. START ---
@dp.message(CommandStart())
async def start_handler(message: Message, command: CommandObject):
    add_user(message.from_user.id)
    args = command.args

    if args and args.isdigit():
        target_admin_id = int(args)
        if target_admin_id == message.from_user.id:
            await message.answer("😅 You clicked your own link.", reply_markup=main_menu)
            return

        active_sessions[message.from_user.id] = target_admin_id
        await message.answer("✍️Connected!\n\nWrite your message now.", reply_markup=main_menu)
    else:
        await message.answer(
            "👋Welcome!\n\nClick 'Get My Link' to start receiving messages.",
            reply_markup=main_menu
        )

# --- 2. BUTTONS ---
@dp.message(F.text == "🔗 Get My Link")
async def button_get_link(message: Message):
    bot_username = (await bot.get_me()).username
    my_link = f"https://t.me/{bot_username}?start={message.from_user.id}"
    await message.answer(f"🔗 **Your Link:**\n`{my_link}`", parse_mode="Markdown")

@dp.message(F.text == "❓ Help")
async def button_help(message: Message):
    await message.answer("1. Share your link to get messages.\n2. Click a friend's link to send messages.")

# --- 3. BROADCAST ---
@dp.message(Command("broadcast"))
async def broadcast_handler(message: Message, command: CommandObject):
    if message.from_user.id not in ADMIN_LIST: return
    msg_text = command.args
    if not msg_text:
        await message.answer("❌ Usage: /broadcast [message]")
        return

    users = get_all_users()
    await message.answer(f"📢 Sending to {len(users)} users...")
    for user_id in users:
        try:
            await bot.send_message(user_id, msg_text)
            await asyncio.sleep(0.05)
        except:
            pass
    await message.answer("✅ Done.")

# --- 4. MESSAGES & REPLIES ---
@dp.message(F.text)
async def handle_text(message: Message):
    # Admin Reply Logic
    if message.reply_to_message and message.reply_to_message.from_user.id == bot.id:
        if "📩" in message.reply_to_message.text:
            try:
                lines = message.reply_to_message.text.splitlines()
                user_line = next((line for line in lines if line.startswith("#id")), None)
                if user_line:
                    uid = int(user_line.replace("#id", ""))
                    await bot.send_message(uid, f"🔔Reply: \n\n{message.text}")
                    await message.answer("✅ Sent!")
            except:
                pass
        return

    # User Anon Message Logic
    sender_id = message.from_user.id
    if sender_id in active_sessions:
        try:
            await bot.send_message(active_sessions[sender_id], f"📩New Message\n\n{message.text}")
            await message.answer("✅Sent!")
        except:
            await message.answer("❌User unavailable.")
    else:
        await message.answer("❓Click a link first.", reply_markup=main_menu)

async def main():
    print("Bot is running...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())