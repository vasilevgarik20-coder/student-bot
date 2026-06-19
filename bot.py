import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from config import TOKEN

bot = Bot(token=TOKEN)
dp = Dispatcher()

# 📌 КНОПКИ МЕНЮ
menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📚 FAQ"), KeyboardButton(text="📅 Расписание")],
        [KeyboardButton(text="📰 Новости"), KeyboardButton(text="ℹ️ Помощь")]
    ],
    resize_keyboard=True
)


@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Привет! Я студенческий бот 🤖\nВыбери действие:",
        reply_markup=menu
    )


@dp.message()
async def handle_buttons(message: types.Message):
    text = message.text

    if text == "📚 FAQ":
        await message.answer(
            "❓ FAQ:\n"
            "Как узнать расписание? → кнопка 📅\n"
            "Где деканат? → главный корпус"
        )

    elif text == "📅 Расписание":
        await message.answer(
            "📅 Расписание:\n"
            "Пн: Математика, Python\n"
            "Вт: БД, Английский"
        )

    elif text == "📰 Новости":
        await message.answer(
            "📰 Новости:\n"
            "- Началась практика\n"
            "- Защита скоро"
        )

    elif text == "ℹ️ Помощь":
        await message.answer("Используй кнопки меню 👇")


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())