import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from config import TOKEN
from db.database import init_db, seed_data, get_connection
from services.faq import get_faq

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()


# ---------------- MAIN MENU ----------------
menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📚 FAQ"), KeyboardButton(text="📅 Расписание")],
        [KeyboardButton(text="📰 Новости"), KeyboardButton(text="ℹ️ Помощь")]
    ],
    resize_keyboard=True
)

back_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back")]
    ]
)


# ---------------- НАПРАВЛЕНИЯ ----------------
directions = [
    "ИСиП",
    "Электронные устройства",
    "Аддитивные технологии",
    "Технология машиностроения"
]


# ---------------- START ----------------
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "🤖 БОТ ОБНОВЛЕН ✅ cтуденческий бот запущен\nВыбери раздел:",
        reply_markup=menu
    )


# ---------------- FAQ ----------------
@dp.message(lambda m: m.text == "📚 FAQ")
async def faq(message: types.Message):
    data = get_faq()

    if not data:
        await message.answer("FAQ пока пуст 😔")
        return

    text = "📚 FAQ:\n\n"
    for q, a in data:
        text += f"❓ {q}\n➡️ {a}\n\n"

    await message.answer(text, reply_markup=back_kb)


# ---------------- SCHEDULE STEP 1 ----------------
@dp.message(lambda m: m.text == "📅 Расписание")
async def schedule_menu(message: types.Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=d, callback_data=f"dir::{d}")]
            for d in directions
        ]
    )

    await message.answer("📅 Выберите направление:", reply_markup=kb)


# ---------------- SCHEDULE STEP 2 ----------------
@dp.callback_query(lambda c: c.data.startswith("dir::"))
async def choose_direction(call: types.CallbackQuery):
    direction = call.data.split("::")[1]

    groups_map = {
        "ИСиП": ["09С31", "09С32", "09С33", "09С34", "09С35", "09С41", "09С42"],
        "Электронные устройства": ["11С31", "11С41"],
        "Аддитивные технологии": ["15С41", "15С42"],
        "Технология машиностроения": ["27С31", "27С41"]
    }

    groups = groups_map.get(direction, [])

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=g, callback_data=f"group::{direction}::{g}")]
            for g in groups
        ]
    )

    await call.message.answer("👥 Выберите группу:", reply_markup=kb)
    await call.answer()


# ---------------- SCHEDULE STEP 3 ----------------
@dp.callback_query(lambda c: c.data.startswith("group::"))
async def show_schedule(call: types.CallbackQuery):
    _, direction, group = call.data.split("::")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT day, lesson
        FROM schedule
        WHERE direction=? AND group_name=?
    """, (direction, group))

    data = cur.fetchall()
    conn.close()

    if not data:
        await call.message.answer("❌ Нет данных по расписанию")
        await call.answer()
        return

    text = f"📅 Расписание {group}:\n\n"

    for day, lesson in data:
        text += f"{day}: {lesson}\n"

    await call.message.answer(text)
    await call.answer()


# ---------------- BACK ----------------
@dp.callback_query(lambda c: c.data == "back")
async def back(call: types.CallbackQuery):
    await call.message.answer("⬅️ Вы вернулись в меню", reply_markup=menu)
    await call.answer()


# ---------------- FALLBACK ----------------
@dp.message()
async def fallback(message: types.Message):
    if not message.text:
        return

    await message.answer("Используй кнопки 👇", reply_markup=menu)


# ---------------- MAIN ----------------
async def main():
    init_db()
    seed_data()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())