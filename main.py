# main.py - Dice of Isight Bot
# AI Story Dice / Life Path App
"""
Бот для метафорического сторителлинга через виртуальные кубики.
Пользователь описывает ситуацию, кидает кубики, получает интерпретацию от ИИ.
"""

import asyncio
import logging
import sys
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from config import BOT_TOKEN

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('dice_bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Webhook настройки для Render
WEBHOOK_HOST = os.getenv('RENDER_EXTERNAL_URL', '')
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = int(os.getenv('PORT', 10000))

# Инициализация бота
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


async def on_startup():
    """Действия при запуске бота"""
    logger.info("🎲 Dice of Isight Bot запускается...")

    # Регистрация обработчиков
    try:
        from handlers import register_handlers
        register_handlers(dp, bot)
        logger.info("✅ Обработчики зарегистрированы")
    except Exception as e:
        logger.error(f"❌ Ошибка регистрации обработчиков: {e}")
        raise

    # Установка webhook
    if WEBHOOK_HOST:
        await bot.set_webhook(
            url=WEBHOOK_URL,
            drop_pending_updates=True
        )
        logger.info(f"✅ Webhook установлен: {WEBHOOK_URL}")
    else:
        logger.warning("⚠️ RENDER_EXTERNAL_URL не установлен, используем polling")

    logger.info("✅ Бот готов к работе!")


async def on_shutdown():
    """Действия при остановке бота"""
    logger.info("🛑 Остановка бота...")
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.session.close()
    logger.info("✅ Бот остановлен")


async def main():
    """Основная функция запуска бота"""
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    try:
        if WEBHOOK_HOST:
            # Webhook режим для Render
            logger.info(f"📡 Запуск webhook сервера на {WEBAPP_HOST}:{WEBAPP_PORT}")

            app = web.Application()
            webhook_requests_handler = SimpleRequestHandler(
                dispatcher=dp,
                bot=bot,
            )
            webhook_requests_handler.register(app, path=WEBHOOK_PATH)
            setup_application(app, dp, bot=bot)

            # Запуск веб-сервера
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, WEBAPP_HOST, WEBAPP_PORT)
            await site.start()

            logger.info(f"✅ Webhook сервер запущен на порту {WEBAPP_PORT}")

            # Держим сервер запущенным
            await asyncio.Event().wait()
        else:
            # Polling режим для локальной разработки
            logger.info("📡 Начинаем polling...")
            await dp.start_polling(
                bot,
                allowed_updates=dp.resolve_used_update_types()
            )
    except Exception as e:
        logger.exception(f"❌ Критическая ошибка: {e}")
        raise
    finally:
        await on_shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⚠️ Бот остановлен пользователем (Ctrl+C)")
    except Exception as e:
        logger.exception(f"❌ Необработанная ошибка: {e}")
        sys.exit(1)
