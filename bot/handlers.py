import json
import os
from aiogram import Router, types
from aiogram.filters import CommandStart
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async
from queue_site.models import TelegramLinkToken  # Импортируем модель
from django.utils import timezone
from datetime import timedelta

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

User = get_user_model()

@router.message(CommandStart(deep_link=True))
async def start_with_token(message: types.Message):
    chat_id = message.from_user.id
    telegram_username = message.from_user.username
    # Извлекаем токен из текста сообщения
    command_text = message.text  # Например, "/start xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    token = command_text.split(' ')[1] if len(command_text.split(' ')) > 1 else None

    print(f"Received /start with token: {token}, from user: {telegram_username}, chat_id: {chat_id}")

    if not telegram_username:
        print("User has no Telegram username")
        await message.reply("У вас нет Telegram username. Пожалуйста, установите его в настройках Telegram.")
        return

    # Сохраняем chat_id
    chat_ids[telegram_username] = chat_id
    save_chat_ids(chat_ids)
    print(f"Updated chat_ids: {chat_ids}")

    if not token:
        await message.reply(
            f"Привет, {telegram_username}!\n"
            f"Я бот для привязки Telegram к твоему аккаунту на сайте ПЛАКИ-ПЛАКИ.\n"
            f"Пожалуйста, используйте ссылку с сайта для привязки."
        )
        return

    # Проверяем токен в базе
    try:
        token_obj = await sync_to_async(TelegramLinkToken.objects.get)(token=token, is_used=False)
        # Проверяем время действия токена (10 минут)
        if token_obj.created_at < timezone.now() - timedelta(minutes=10):
            print(f"Token expired: {token}")
            await message.reply("Токен истёк. Пожалуйста, сгенерируйте новую ссылку на сайте.")
            return

        user = await sync_to_async(User.objects.get)(id=token_obj.user_id)
        user.telegram_id = str(chat_id)
        user.telegram_username = telegram_username
        await sync_to_async(user.save)()
        print(f"Linked Telegram for user {user.username}: chat_id={chat_id}, username={telegram_username}")

        # Помечаем токен как использованный
        token_obj.is_used = True
        await sync_to_async(token_obj.save)()
        print(f"Token {token} marked as used")

        await message.reply(
            f"Telegram успешно привязан к вашему аккаунту, {telegram_username}!\n"
            f"Вернитесь на сайт и обновите страницу, чтобы продолжить."
        )
    except TelegramLinkToken.DoesNotExist:
        print(f"Invalid or used token: {token}")
        await message.reply("Неверный или уже использованный токен. Пожалуйста, сгенерируйте новую ссылку на сайте.")
    except User.DoesNotExist:
        print(f"User with id {token_obj.user_id} not found")
        await message.reply("Пользователь не найден. Пожалуйста, попробуйте снова.")
    except Exception as e:
        print(f"Error linking Telegram: {str(e)}")
        await message.reply("Произошла ошибка при привязке. Пожалуйста, попробуйте снова.")

@router.message(CommandStart())
async def start_without_token(message: types.Message):
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