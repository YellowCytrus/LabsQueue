import json
import os
from aiogram import Router, types
from aiogram.filters import Command

router = Router()

# Путь к файлу chat_ids.json
CHAT_IDS_FILE = '/home/cytr/PycharmProjects/ElectroQueryVEnv/lab_queue/chat_ids.json'

def load_chat_ids():
    if os.path.exists(CHAT_IDS_FILE):
        with open(CHAT_IDS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_chat_ids(chat_ids):
    try:
        with open(CHAT_IDS_FILE, 'w') as f:
            json.dump(chat_ids, f)
        print(f"Successfully saved chat_ids to {CHAT_IDS_FILE}")
    except Exception as e:
        print(f"Error saving chat_ids: {str(e)}")

chat_ids = load_chat_ids()

@router.message(Command("start"))
async def start_command(message: types.Message):
    chat_id = message.from_user.id
    telegram_username = message.from_user.username

    print(f"Received /start from user: {telegram_username}")

    if not telegram_username:
        print("User has no Telegram username")
        await message.reply("У вас нет Telegram username. Пожалуйста, установите его в настройках Telegram.")
        return

    chat_ids[telegram_username] = chat_id
    save_chat_ids(chat_ids)
    print(f"Updated chat_ids: {chat_ids}")

    await message.reply(
        f"Привет, {telegram_username}!\n"
        f"Я бот для привязки Telegram к твоему аккаунту на сайте ПЛАКИ-ПЛАКИ.\n"
        f"Пожалуйста, используйте ссылку с сайта для привязки."
    )