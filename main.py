# main.py - Dice of Isight Bot
# AI Story Dice / Life Path App
"""
Бот для метафорического сторителлинга через виртуальные кубики.
Пользователь описывает ситуацию, кидает кубики, получает интерпретацию от ИИ.
"""

import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

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

    logger.info("✅ Бот готов к работе!")


async def on_shutdown():
    """Действия при остановке бота"""
    logger.info("🛑 Остановка бота...")
    await bot.session.close()
    logger.info("✅ Бот остановлен")


async def main():
    """Основная функция запуска бота"""
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    try:
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
