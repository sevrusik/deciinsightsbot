# handlers.py - Bot Command Handlers
"""
Обработчики команд для Dice of Isight Bot
"""

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging
import random

logger = logging.getLogger(__name__)

from config import ADMIN_IDS
from database import (
    get_or_create_user, update_last_interaction,
    save_throw, update_throw, get_user_throws, get_stats, get_detailed_analytics
)
from dice_meanings import (
    get_all_symbols, get_symbol_info, format_symbol_info,
    get_combined_interpretation, STORY_PATHS, get_path_info,
    DICE_POSITIONS, get_position_info
)
from ai_client import (
    generate_interpretation, generate_path_suggestions,
    generate_reflection_prompts
)

# Роутер
router = Router()

# FSM States
class ThrowState(StatesGroup):
    waiting_situation = State()
    showing_interpretation = State()
    choosing_path = State()


# ============================================
# BASIC COMMANDS
# ============================================

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Команда /start - приветствие"""
    await state.clear()

    user_id = str(message.from_user.id)
    username = message.from_user.username
    full_name = message.from_user.full_name

    # Создаем или получаем пользователя
    get_or_create_user(user_id, username, full_name)

    welcome_text = """🎲 **Добро пожаловать в Dice of Isight!**

Это пространство для метафорического исследования ваших жизненных ситуаций через символический язык кубиков.

**Как это работает:**

1️⃣ Опишите ситуацию, которая волнует вас
2️⃣ Бросьте виртуальные кубики с символами
3️⃣ Получите метафорическую интерпретацию от ИИ
4️⃣ Выберите свой путь действия
5️⃣ Получите вопросы для письменной рефлексии

**Команды:**
/throw - Бросить кубики
/history - История ваших бросков
/help - Подробная справка

_Готовы начать путешествие?_ 🌟"""

    await message.answer(welcome_text, parse_mode="Markdown")


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Команда /help - справка"""
    help_text = """📖 **Справка Dice of Isight**

**Философия бота:**
Кубики - это зеркало, в котором вы видите свою ситуацию по-новому. Символы не предсказывают будущее, они открывают новые перспективы.

**Основные команды:**
/start - Начать работу
/throw - Бросить кубики для новой ситуации
/history - Посмотреть историю бросков
/symbols - Посмотреть все символы и их значения

**Как использовать:**

🎯 **Шаг 1: Описание ситуации**
Опишите то, что вас волнует. Это может быть:
• Решение, которое нужно принять
• Ситуация, требующая понимания
• Вопрос о жизненном пути
• Эмоциональное состояние

🎲 **Шаг 2: Бросок кубиков**
Вы бросите 3 символических кубика. Каждый символ несет глубокое метафорическое значение.

🔮 **Шаг 3: Интерпретация**
ИИ создаст для вас уникальную историю-интерпретацию, сплетая символы и вашу ситуацию.

🛤️ **Шаг 4: Выбор пути**
Вы увидите 4 возможных пути:
• Путь Перемен 🔄
• Путь Стабильности 🛡️
• Путь Терпения 🌱
• Путь Исследования 🧭

📝 **Шаг 5: Рефлексия**
Получите вопросы для journaling - письменной рефлексии над выбранным путем.

**Важно помнить:**
Символы - это инструмент для размышления, а не абсолютная истина. Доверяйте своей интуиции."""

    await message.answer(help_text, parse_mode="Markdown")


@router.message(Command("symbols"))
async def cmd_symbols(message: Message):
    """Команда /symbols - показать все символы"""
    symbols = get_all_symbols()

    text = "🎲 **Символы Basic набора:**\n\n"
    text += "Каждый символ несет глубокое метафорическое значение.\n\n"

    for symbol in symbols:
        info = get_symbol_info(symbol)
        text += f"{symbol} **{info['name']}** - _{info['keyword']}_\n"

    text += "\n_Используйте /throw чтобы бросить кубики_"

    await message.answer(text, parse_mode="Markdown")


@router.message(Command("history"))
async def cmd_history(message: Message):
    """Команда /history - история бросков"""
    user_id = str(message.from_user.id)

    throws = get_user_throws(user_id, limit=5)

    if not throws:
        await message.answer(
            "📜 У вас пока нет истории бросков.\n\n"
            "Начните с команды /throw",
            parse_mode="Markdown"
        )
        return

    text = "📜 **Ваши последние 5 бросков:**\n\n"

    for i, throw in enumerate(throws, 1):
        timestamp = throw.timestamp.strftime("%d.%m.%Y %H:%M")
        text += f"**{i}. [{timestamp}]**\n"
        text += f"_{throw.situation[:60]}{'...' if len(throw.situation) > 60 else ''}_\n"
        text += f"🎲 {throw.symbol} {throw.archetype} {throw.emotion}\n"

        if throw.chosen_path:
            path_info = get_path_info(throw.chosen_path)
            text += f"→ {path_info['emoji']} {path_info['title']}\n"

        text += "\n"

    await message.answer(text, parse_mode="Markdown")


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Команда /stats - статистика бота (только для админа)"""
    user_id_str = str(message.from_user.id)
    logger.info(f"🔍 /stats вызван пользователем: {user_id_str}, ADMIN_IDS: {ADMIN_IDS}")
    if user_id_str not in ADMIN_IDS:
        await message.answer("⛔ Эта команда доступна только администратору")
        return

    stats = get_stats()

    text = f"""📊 **Статистика бота:**

👥 Всего пользователей: {stats['users']}
🔥 Активных за неделю: {stats['active_users_7d']}
🎲 Всего бросков: {stats['throws']}
✅ Завершённых: {stats['completed_throws']}

📈 Метрики:
• Среднее бросков/пользователь: {stats['avg_throws_per_user']}
• Процент завершения: {stats['completion_rate']}%

_Dice of Isight помогает людям видеть по-новому_ ✨"""

    await message.answer(text, parse_mode="Markdown")


@router.message(Command("analytics"))
async def cmd_analytics(message: Message):
    """Команда /analytics - детальная аналитика (только для админа)"""
    if str(message.from_user.id) not in ADMIN_IDS:
        await message.answer("⛔ Эта команда доступна только администратору")
        return

    stats = get_stats()
    analytics = get_detailed_analytics()

    # Форматируем пути
    path_text = ""
    path_names = {
        "change": "🔄 Перемен",
        "stay": "🛡️ Стабильности",
        "patience": "🌱 Терпения",
        "explore": "🧭 Исследования"
    }

    for path_key, count in stats['path_distribution'].items():
        path_name = path_names.get(path_key, path_key)
        percentage = (count / stats['completed_throws'] * 100) if stats['completed_throws'] > 0 else 0
        path_text += f"  {path_name}: {count} ({percentage:.1f}%)\n"

    text = f"""📊 **Детальная аналитика**

**Общие показатели:**
👥 Всего пользователей: {stats['users']}
🔥 Активных (7 дней): {stats['active_users_7d']}
🔁 Вернувшихся: {analytics['returning_users']}
💚 Retention rate: {analytics['retention_rate']}%

**Броски:**
🎲 Всего: {stats['throws']}
✅ Завершено: {stats['completed_throws']}
📈 Конверсия: {stats['completion_rate']}%
📊 Среднее/юзер: {stats['avg_throws_per_user']}

**Популярные пути:**
{path_text if path_text else "  Нет данных"}

**Рост за 30 дней:**
• Новых юзеров: {sum(item['count'] for item in analytics['users_by_day'])}
• Бросков: {sum(item['count'] for item in analytics['throws_by_day'])}

_Используйте эти данные для улучшения продукта_ 💡"""

    await message.answer(text, parse_mode="Markdown")


# ============================================
# DICE THROW FLOW
# ============================================

@router.message(Command("throw"))
async def cmd_throw(message: Message, state: FSMContext):
    """Команда /throw - начать процесс броска"""
    await state.clear()
    await state.set_state(ThrowState.waiting_situation)

    text = """🎲 **Начинаем новый бросок**

Опишите ситуацию, которая вас волнует. Это может быть:
• Решение, которое нужно принять
• Вопрос о жизненном пути
• Ситуация, требующая понимания
• Эмоциональное состояние

**Напишите свободно, от души.** Чем честнее вы с собой, тем глубже будет интерпретация.

_Или используйте /cancel чтобы отменить_"""

    await message.answer(text, parse_mode="Markdown")


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Команда /cancel - отмена"""
    current_state = await state.get_state()

    if current_state is None:
        await message.answer("Нечего отменять. Используйте /throw чтобы начать")
        return

    await state.clear()
    await message.answer("✅ Действие отменено. Используйте /throw чтобы начать заново")


@router.message(ThrowState.waiting_situation)
async def process_situation(message: Message, state: FSMContext):
    """Обработка описания ситуации"""
    situation = message.text
    user_id = str(message.from_user.id)

    # Сохраняем ситуацию
    await state.update_data(situation=situation)

    # Показываем индикатор
    await message.bot.send_chat_action(message.chat.id, "typing")

    # Бросаем кубики (6 символов)
    symbols = random.sample(get_all_symbols(), 6)

    # Названия позиций для отображения
    position_keys = ["root", "outer", "inner", "shadow", "gift", "step"]

    # Сохраняем бросок в базу с 6 символами
    symbols_data = {pos: sym for pos, sym in zip(position_keys, symbols)}
    throw = save_throw(
        telegram_id=user_id,
        situation=situation,
        symbol=symbols[0],  # root
        archetype=symbols[1],  # outer
        emotion=symbols[2],  # inner
        shadow_symbol=symbols[3],  # тень
        gift_symbol=symbols[4],  # дар
        step_symbol=symbols[5]  # шаг
    )

    # Сохраняем ID броска и все символы
    await state.update_data(
        throw_id=throw.id,
        symbols=symbols,
        symbols_data=symbols_data
    )

    # Показываем результат броска с позициями
    text = "🎲 **Кубики брошены!**\n\n"

    for position_key, symbol in zip(position_keys, symbols):
        pos_info = get_position_info(position_key)
        symbol_info = get_symbol_info(symbol)
        text += f"**{pos_info['title']}:** {symbol} {symbol_info['name']} - _{symbol_info['keyword']}_\n"

    text += "\n_Генерирую интерпретацию..._"

    await message.answer(text, parse_mode="Markdown")

    # Генерируем интерпретацию через ИИ
    await message.bot.send_chat_action(message.chat.id, "typing")

    try:
        interpretation = generate_interpretation(situation, symbols)

        # Сохраняем интерпретацию
        update_throw(throw.id, interpretation=interpretation)

        # Отправляем интерпретацию
        await message.answer(f"🔮 **Интерпретация:**\n\n{interpretation}", parse_mode="Markdown")

        # Генерируем варианты путей
        await message.bot.send_chat_action(message.chat.id, "typing")
        path_suggestions = generate_path_suggestions(situation, symbols, interpretation)

        # Сохраняем предложения путей
        await state.update_data(path_suggestions=path_suggestions)

        # Создаем клавиатуру с путями
        keyboard = create_path_keyboard()

        path_text = "🛤️ **Выберите свой путь:**\n\n"
        for path_key, path_data in STORY_PATHS.items():
            suggestion = path_suggestions.get(path_key, path_data['description'])
            path_text += f"{path_data['emoji']} **{path_data['title']}**\n_{suggestion}_\n\n"

        await message.answer(path_text, reply_markup=keyboard, parse_mode="Markdown")

        await state.set_state(ThrowState.choosing_path)

    except Exception as e:
        logging.error(f"Error in interpretation: {e}")
        await message.answer(
            "😔 Произошла ошибка при генерации интерпретации.\n"
            "Попробуйте позже или используйте /throw снова"
        )
        await state.clear()


def create_path_keyboard() -> InlineKeyboardMarkup:
    """Создать клавиатуру с выбором пути"""
    buttons = []

    for path_key, path_data in STORY_PATHS.items():
        buttons.append([
            InlineKeyboardButton(
                text=f"{path_data['emoji']} {path_data['title']}",
                callback_data=f"path_{path_key}"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data.startswith("path_"))
async def process_path_choice(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора пути"""
    path_key = callback.data.split("_")[1]
    data = await state.get_data()

    throw_id = data.get("throw_id")
    situation = data.get("situation")
    symbols = data.get("symbols")

    if not throw_id:
        await callback.answer("Ошибка: бросок не найден")
        return

    # Сохраняем выбранный путь
    update_throw(throw_id, chosen_path=path_key)

    path_info = get_path_info(path_key)

    await callback.message.edit_text(
        f"✨ Вы выбрали: **{path_info['emoji']} {path_info['title']}**\n\n"
        f"_{path_info['description']}_",
        parse_mode="Markdown"
    )

    # Генерируем вопросы для рефлексии
    await callback.message.answer("_Генерирую вопросы для рефлексии..._", parse_mode="Markdown")

    try:
        reflection_prompts = generate_reflection_prompts(situation, path_key, symbols)

        # Сохраняем вопросы
        update_throw(throw_id, reflection_prompts=reflection_prompts)

        # Отправляем вопросы
        prompts_text = f"📝 **Вопросы для письменной рефлексии:**\n\n"
        prompts_text += f"_{path_info['reflection']}_\n\n"

        for i, prompt in enumerate(reflection_prompts, 1):
            prompts_text += f"{i}. {prompt}\n\n"

        prompts_text += "_Выделите время для письменных ответов. "
        prompts_text += "Это поможет углубить понимание и найти свой путь._"

        await callback.message.answer(prompts_text, parse_mode="Markdown")

        # Завершаем
        finish_text = "✅ **Бросок завершен!**\n\n"
        finish_text += "Вы можете:\n"
        finish_text += "• /throw - Сделать новый бросок\n"
        finish_text += "• /history - Посмотреть историю\n"
        finish_text += "• /help - Узнать больше о боте"

        await callback.message.answer(finish_text, parse_mode="Markdown")

    except Exception as e:
        logging.error(f"Error generating prompts: {e}")
        await callback.message.answer(
            "😔 Ошибка при генерации вопросов. Но ваш выбор сохранен!"
        )

    await state.clear()
    await callback.answer()




# ============================================
# REGISTRATION
# ============================================

def register_handlers(dp: Dispatcher, bot: Bot):
    """Регистрация всех обработчиков"""
    dp.include_router(router)
    logging.info("✅ Обработчики зарегистрированы")
