import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from config import TOKEN
from db.database import init_db, seed_data
from services.faq import get_faq
from services.schedule import get_schedule
from services.news import get_news


# ----------------------------
# ЛОГИРОВАНИЕ (для отчёта)
# ----------------------------
logging.basicConfig(level=logging.INFO)


# ----------------------------
# BOT INIT
# ----------------------------
bot = Bot(token=TOKEN)
dp = Dispatcher()


# ----------------------------
# UI (КНОПКИ)
# ----------------------------
menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📚 FAQ"),
            KeyboardButton(text="📅 Расписание")
        ],
        [
            KeyboardButton(text="📰 Новости"),
            KeyboardButton(text="ℹ️ Помощь")
        ]
    ],
    resize_keyboard=True
)


# ----------------------------
# START COMMAND
# ----------------------------
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "🤖 Привет! Я студенческий бот.\n"
        "Выбери действие ниже:",
        reply_markup=menu
    )


# ----------------------------
# MAIN HANDLER (КНОПКИ)
# ----------------------------
@dp.message()
async def handle_messages(message: types.Message):
    try:
        text = message.text

        # FAQ
        if text == "📚 FAQ":
            data = get_faq()
            if not data:
                await message.answer("FAQ пока пуст 😔")
                return

            response = "📚 FAQ:\n\n"
            for q, a in data:
                response += f"❓ {q}\n➡️ {a}\n\n"

            await message.answer(response)

        # SCHEDULE
        elif text == "📅 Расписание":
            data = get_schedule()
            if not data:
                await message.answer("Расписание пусто 😔")
                return

            response = "📅 Расписание:\n\n"
            for day, lesson in data:
                response += f"📌 {day}: {lesson}\n"

            await message.answer(response)

        # NEWS
        elif text == "📰 Новости":
            data = get_news()
            if not data:
                await message.answer("Новостей пока нет 😔")
                return

            response = "📰 Новости:\n\n"
            for (n,) in data:
                response += f"• {n}\n"

            await message.answer(response)

        # HELP
        elif text == "ℹ️ Помощь":
            await message.answer(
                "ℹ️ Помощь:\n"
                "- Используй кнопки меню\n"
                "- /start для перезапуска"
            )

        # UNKNOWN INPUT
        else:
            await message.answer(
                "Я не понимаю это сообщение 🤖\n"
                "Используй кнопки ниже 👇",
                reply_markup=menu
            )

    except Exception as e:
        logging.error(f"Error: {e}")
        await message.answer("⚠️ Произошла ошибка. Попробуй позже.")


# ----------------------------
# MAIN FUNCTION
# ----------------------------
async def main():
    # Инициализация БД
    init_db()
    seed_data()

    # Запуск polling
    await dp.start_polling(bot)


# ----------------------------
# ENTRY POINT
# ----------------------------
if __name__ == "__main__":
    asyncio.run(main())