import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

from config import TOKEN
from db.database import init_db, seed_data
from services.faq import get_faq
from services.schedule import get_schedule
from services.news import get_news

bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Бот запущен 🤖\nИспользуй /faq /schedule /news")


@dp.message(Command("faq"))
async def faq(message: types.Message):
    data = get_faq()
    text = "❓ FAQ:\n\n"

    for q, a in data:
        text += f"{q}\n→ {a}\n\n"

    await message.answer(text)


@dp.message(Command("schedule"))
async def schedule(message: types.Message):
    data = get_schedule()
    text = "📅 Расписание:\n\n"

    for day, lesson in data:
        text += f"{day}: {lesson}\n"

    await message.answer(text)


@dp.message(Command("news"))
async def news(message: types.Message):
    data = get_news()
    text = "📰 Новости:\n\n"

    for (n,) in data:
        text += f"- {n}\n"

    await message.answer(text)


async def main():
    init_db()
    seed_data()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())