import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from config import TOKEN

bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Привет! Я студенческий бот 🤖\n\n"
        "Команды:\n"
        "/faq - частые вопросы\n"
        "/schedule - расписание\n"
        "/news - новости\n"
        "/help - помощь"
    )


@dp.message(Command("faq"))
async def faq(message: types.Message):
    await message.answer(
        "❓ FAQ:\n"
        "1. Как узнать расписание?\n"
        "→ /schedule\n\n"
        "2. Где деканат?\n"
        "→ Главный корпус"
    )


@dp.message(Command("schedule"))
async def schedule(message: types.Message):
    await message.answer(
        "📅 Расписание:\n"
        "Понедельник: Математика, Python\n"
        "Вторник: БД, Английский"
    )


@dp.message(Command("news"))
async def news(message: types.Message):
    await message.answer(
        "📰 Новости:\n"
        "- Началась практика\n"
        "- Защита через 3 дня"
    )


@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    await message.answer(
        "/start\n"
        "/faq\n"
        "/schedule\n"
        "/news"
    )


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())