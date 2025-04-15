from aiogram import Bot, Dispatcher
from django.conf import settings
from .handlers import router

print("Импортируем Bot и Dispatcher из aiogram")

# Инициализация бота
print(f"Инициализируем Bot с токеном: {settings.TELEGRAM_BOT_TOKEN[:10]}...")
bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
print("Bot успешно инициализирован")

# Инициализация Dispatcher
print("Инициализируем Dispatcher...")
try:
    dp = Dispatcher()  # В версии 3.x Dispatcher не принимает bot
    print("Dispatcher успешно инициализирован")
except Exception as e:
    print(f"Ошибка при инициализации Dispatcher: {str(e)}")
    raise

# Регистрируем обработчики
print("Регистрируем router...")
dp.include_router(router)
print("Router успешно зарегистрирован")

async def on_startup():
    print("Telegram-бот запущен!")

async def on_shutdown():
    print("Telegram-бот остановлен!")