from django.core.management.base import BaseCommand
from bot.bot import bot, dp, on_startup, on_shutdown
import asyncio

class Command(BaseCommand):
    help = 'Запускает Telegram-бота'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Запускаем Telegram-бота...'))
        asyncio.run(self.run_bot())

    async def run_bot(self):
        await on_startup()
        await dp.start_polling(bot)
        await on_shutdown()