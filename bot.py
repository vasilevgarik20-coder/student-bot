import asyncio
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from config import TOKEN, ADMIN_ID
from db.database import init_db, seed_data, get_connection
from services.faq import get_faq

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()


# ---------------- FSM ----------------
class NewsState(StatesGroup):
    waiting_text = State()


# ---------------- KEYBOARDS ----------------
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

# ГРУППЫ ДЛЯ КАЖДОГО НАПРАВЛЕНИЯ (ТОЧНО КАК В БД)
groups_map = {
    "ИСиП": ["09C31", "09C32", "09C33", "09C34", "09C35", "09C41", "09C42"],
    "Электронные устройства": ["11C31", "11C41"],
    "Аддитивные технологии": ["15C41", "15C42"],
    "Технология машиностроения": ["27C31", "27C41"]
}

directions = list(groups_map.keys())


# ---------------- ADMIN ----------------
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Нет доступа")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить новость", callback_data="add_news")]
    ])

    await message.answer("🛠 Админ-панель", reply_markup=kb)


@dp.callback_query(F.data == "add_news")
async def add_news(call: types.CallbackQuery, state: FSMContext):
    if call.from_user.id != ADMIN_ID:
        await call.answer("Нет доступа", show_alert=True)
        return

    await state.set_state(NewsState.waiting_text)
    await call.message.answer("📝 Введите текст новости:")
    await call.answer()


@dp.message(NewsState.waiting_text)
async def save_news(message: types.Message, state: FSMContext):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("INSERT INTO news (text) VALUES (?)", (message.text,))
    conn.commit()
    conn.close()

    await state.clear()
    await message.answer("✅ Новость добавлена!")


# ---------------- NEWS ----------------
@dp.message(F.text == "📰 Новости")
async def show_news(message: types.Message):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT text FROM news ORDER BY id DESC LIMIT 10")
    data = cur.fetchall()
    conn.close()

    if not data:
        await message.answer("Новостей пока нет")
        return

    text = "📰 Новости:\n\n" + "\n\n".join(f"• {n[0]}" for n in data)
    await message.answer(text)


# ---------------- START ----------------
@dp.message(Command("start"))
async def start(message: types.Message):
    now = datetime.now()
    week_number = now.isocalendar().week
    parity = "ЧЁТНАЯ" if week_number % 2 == 0 else "НЕЧЁТНАЯ"

    await message.answer(
        f"🤖 Студенческий бот\n"
        f"📖 Сейчас {parity.lower()} неделя\n\n"
        f"Выбери раздел:",
        reply_markup=menu
    )


# ---------------- FAQ ----------------
@dp.message(F.text == "📚 FAQ")
async def faq(message: types.Message):
    data = get_faq()

    if not data:
        await message.answer("FAQ пока пуст 😔")
        return

    text = "📚 FAQ:\n\n"
    text += "\n\n".join([f"❓ {q}\n➡️ {a}" for q, a in data])

    await message.answer(text, reply_markup=back_kb)


# ---------------- SCHEDULE ----------------
@dp.message(F.text == "📅 Расписание")
async def schedule_menu(message: types.Message):
    now = datetime.now()
    week_number = now.isocalendar().week
    parity = "ЧЁТНАЯ" if week_number % 2 == 0 else "НЕЧЁТНАЯ"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=d, callback_data=f"dir::{d}")]
        for d in directions
    ])

    await message.answer(
        f"📅 Расписание\n\n"
        f"📖 Текущая неделя: {parity}\n\n"
        f"Выберите направление:",
        reply_markup=kb
    )


@dp.callback_query(F.data.startswith("dir::"))
async def choose_direction(call: types.CallbackQuery):
    direction = call.data.split("::")[1]
    groups = groups_map.get(direction, [])

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=g, callback_data=f"group::{direction}::{g}")]
        for g in groups
    ])

    await call.message.answer("👥 Выберите группу:", reply_markup=kb)
    await call.answer()


@dp.callback_query(F.data.startswith("group::"))
async def show_schedule(call: types.CallbackQuery):
    _, direction, group = call.data.split("::")

    # ---------- НОРМАЛИЗАЦИЯ ДНЕЙ ----------
    day_mapping = {
        "пн": "ПН", "понедельник": "ПН", "monday": "ПН",
        "вт": "ВТ", "вторник": "ВТ", "tuesday": "ВТ",
        "ср": "СР", "среда": "СР", "wednesday": "СР",
        "чт": "ЧТ", "четверг": "ЧТ", "thursday": "ЧТ",
        "пт": "ПТ", "пятница": "ПТ", "friday": "ПТ",
        "сб": "СБ", "суббота": "СБ", "saturday": "СБ",
        "вс": "ВС", "воскресенье": "ВС", "sunday": "ВС",
    }

    week_mapping = {
        "чётная": "ЧЁТНАЯ", "четная": "ЧЁТНАЯ",
        "чётная неделя": "ЧЁТНАЯ", "четная неделя": "ЧЁТНАЯ",
        "нечётная": "НЕЧЁТНАЯ", "нечетная": "НЕЧЁТНАЯ",
        "нечётная неделя": "НЕЧЁТНАЯ", "нечетная неделя": "НЕЧЁТНАЯ",
    }

    # ---------- ТЕКУЩАЯ ДАТА ----------
    now = datetime.now()
    week_number = now.isocalendar().week
    week_type = "ЧЁТНАЯ" if week_number % 2 == 0 else "НЕЧЁТНАЯ"
    
    days = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"]
    today = days[now.weekday()]

    # ---------- НОРМАЛИЗАЦИЯ ----------
    # Не трогаем direction и group - они уже правильные из callback_data
    today_norm = day_mapping.get(today.lower(), today)
    week_type_norm = week_mapping.get(week_type.lower(), week_type)

    # ---------- ДЕБАГ ----------
    print(f"DEBUG: direction='{direction}', group='{group}', day='{today_norm}', week='{week_type_norm}'")

    # ---------- ЗАПРОС К БД ----------
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT pair, time, lesson
        FROM schedule
        WHERE direction = ?
          AND group_name = ?
          AND day = ?
          AND week_type = ?
        ORDER BY pair
    """, (direction, group, today_norm, week_type_norm))

    data = cur.fetchall()
    conn.close()

    # ---------- ОТВЕТ ----------
    if not data:
        # Проверим, есть ли вообще расписание для этой группы
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM schedule WHERE group_name = ?", (group,))
        count = cur.fetchone()[0]
        conn.close()
        
        if count == 0:
            await call.message.answer(
                f"❌ Группа '{group}' не найдена в базе данных\n"
                f"Проверьте правильность названия группы"
            )
        else:
            await call.message.answer(
                f"📅 Группа: {group}\n"
                f"📖 Неделя: {week_type_norm}\n"
                f"🗓 День: {today_norm}\n\n"
                f"❌ Пар нет"
            )
        await call.answer()
        return

    text = (
        f"📅 Группа: {group}\n"
        f"📖 Неделя: {week_type_norm}\n"
        f"🗓 День: {today_norm}\n\n"
    )

    for pair, time, lesson in data:
        text += f"{pair} пара ({time}): {lesson}\n"

    await call.message.answer(text)
    await call.answer()


# ---------------- BACK ----------------
@dp.callback_query(F.data == "back")
async def back(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer("⬅️ Вы вернулись в меню", reply_markup=menu)
    await call.answer()

# ---------------- HELP ----------------
@dp.message(F.text == "ℹ️ Помощь")
async def help_command(message: types.Message):
    await message.answer(
        "🆘 Для управления ботом используй кнопки.\n"
        "🔄 Если бот не отвечает перезагрузи его /start.\n"
        "📱 Связь с разработчиком: @V_III_D"
    )

# ---------------- MAIN ----------------
async def main():
    init_db()
    seed_data()

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())