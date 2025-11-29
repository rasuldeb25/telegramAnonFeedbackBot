import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command, CommandStart, CommandObject

# --- CONFIGURATION ---
API_TOKEN = ''
ADMIN_LIST = []

# --- SETUP ---
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)
active_sessions = {}  # Only active chat sessions stay in RAM

# --- KEYBOARD SETUP ---
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔗Get My Link"), KeyboardButton(text="❓Help")]
    ],
    resize_keyboard=True,
    input_field_placeholder="Choose an option..."
)

# --- DATABASE (The Permanent Memory) ---
def init_db():
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    # Table 1: Users (For broadcast)
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (
                     user_id
                     INTEGER
                     PRIMARY
                     KEY
                 )''')
    # Table 2: Reply Mapping (For remembering who sent what)
    c.execute('''CREATE TABLE IF NOT EXISTS reply_map
                 (
                     admin_msg_id
                     INTEGER
                     PRIMARY
                     KEY,
                     original_sender_id
                     INTEGER
                 )''')
    conn.commit()
    conn.close()

def add_user(user_id):
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
    conn.commit()
    conn.close()

# --- MISSING FUNCTIONS RESTORED BELOW ---
def save_reply_link(admin_msg_id, sender_id):
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO reply_map (admin_msg_id, original_sender_id) VALUES (?, ?)',
              (admin_msg_id, sender_id))
    conn.commit()
    conn.close()

def get_sender_id(admin_msg_id):
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('SELECT original_sender_id FROM reply_map WHERE admin_msg_id = ?', (admin_msg_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None
# ----------------------------------------
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
            await message.answer("😅You clicked your own link.", reply_markup=main_menu)
            return

        active_sessions[message.from_user.id] = target_admin_id
        await message.answer("✍️Connected!\n\nWrite your message now.", reply_markup=main_menu,
                             parse_mode="Markdown")
    else:
        await message.answer(
            "👋Welcome!\n\nClick 'Get My Link' to start receiving messages.",
            reply_markup=main_menu, parse_mode="Markdown"
        )

# --- 2. BUTTONS ---
@dp.message(F.text == "🔗 Get My Link")
async def button_get_link(message: Message):
    bot_username = (await bot.get_me()).username
    my_link = f"https://t.me/{bot_username}?start={message.from_user.id}"
    await message.answer(f"🔗 **Your Link:**\n`{my_link}`", parse_mode="Markdown")

@dp.message(F.text == "❓Help")
async def button_help(message: Message):
    await message.answer("1. Share your link to get messages.\n2. Click a friend's link to send messages.")

# --- 3. BROADCAST ---
@dp.message(Command("broadcast"))
async def broadcast_handler(message: Message, command: CommandObject):
    if message.from_user.id not in ADMIN_LIST: return
    msg_text = command.args
    if not msg_text:
        await message.answer("❌Usage: /broadcast [message]")
        return

    users = get_all_users()
    await message.answer(f"📢Sending to {len(users)} users...")
    count = 0
    for user_id in users:
        try:
            await bot.send_message(user_id, msg_text)
            count += 1
            await asyncio.sleep(0.05)
        except:
            pass
    await message.answer(f"✅Sent to {count} users.")

# --- 4. MESSAGES & REPLIES (Final Logic) ---
@dp.message(F.text)
async def handle_text(message: Message):
    sender_id = message.from_user.id

    # --- A. USER LOGIC (Check this FIRST!) ---
    # If this person is connected to an Admin, SEND IT TO ADMIN.
    if sender_id in active_sessions:
        target_admin_id = active_sessions[sender_id]
        try:
            # 1. Send to Admin
            sent_message = await bot.send_message(
                target_admin_id,
                f"📩New Message\n\n{message.text}",
                parse_mode="Markdown"
            )
            # 2. SAVE TO DATABASE (So Admin can reply later)
            save_reply_link(sent_message.message_id, sender_id)

            await message.answer("✅Sent!")
        except Exception as e:
            await message.answer(f"❌User unavailable: {e}")
        return  # Stop here, don't check Admin logic

    # --- B. ADMIN REPLY LOGIC ---
    # Only run this if the sender is NOT a connected User
    if message.reply_to_message and message.reply_to_message.from_user.id == bot.id:

        replied_msg_id = message.reply_to_message.message_id

        # Ask Database: Who sent this originally?
        target_user_id = get_sender_id(replied_msg_id)

        if target_user_id:
            # Heal connection
            active_sessions[target_user_id] = message.from_user.id

            try:
                await bot.send_message(target_user_id, f"🔔Reply:\n\n{message.text}", parse_mode="Markdown")
                await message.answer("✅Reply sent!")
            except Exception as e:
                await message.answer(f"❌Failed: {e}")
        else:
            await message.answer("❌Error: Message too old (not in database).")
        return

    # --- C. LOST SOUL ---
    await message.answer("❓Click a link from an admin first.", reply_markup=main_menu)

async def main():
    print("Anon Bot is running...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())