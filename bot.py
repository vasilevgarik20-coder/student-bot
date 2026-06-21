import asyncio
import logging
import sqlite3
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
from db.database import get_connection

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()


# ================== УДАЛЕНИЕ СТАРЫХ СООБЩЕНИЙ ==================
last_msg = {}  # user_id -> message_id

async def delete_previous(user_id: int, chat_id: int):
    if user_id in last_msg:
        try:
            await bot.delete_message(chat_id, last_msg[user_id])
        except Exception:
            pass
        del last_msg[user_id]

async def send_with_delete(chat_id: int, user_id: int, *args, **kwargs):
    await delete_previous(user_id, chat_id)
    msg = await bot.send_message(chat_id, *args, **kwargs)
    last_msg[user_id] = msg.message_id
    return msg


# ---------------- FSM ----------------
class NewsState(StatesGroup):
    waiting_title = State()
    waiting_text = State()
    waiting_photo = State()
    waiting_admin_id = State()
    waiting_delete_admin_id = State()


# ---------------- KEYBOARDS ----------------
menu_button = InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_menu")

menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📚 FAQ"), KeyboardButton(text="📅 Расписание")],
        [KeyboardButton(text="📰 Новости"), KeyboardButton(text="ℹ️ Помощь")]
    ],
    resize_keyboard=True
)

# FAQ: только меню
faq_kb = InlineKeyboardMarkup(inline_keyboard=[[menu_button]])

# Новости: только меню
news_kb = InlineKeyboardMarkup(inline_keyboard=[[menu_button]])

# Помощь: только меню
help_kb = InlineKeyboardMarkup(inline_keyboard=[[menu_button]])

# Админ-панель (без меню)
admin_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="➕ Добавить новость", callback_data="add_news")],
    [InlineKeyboardButton(text="🗑 Удалить новость", callback_data="delete_news")],
    [InlineKeyboardButton(text="👤 Добавить админа", callback_data="add_admin")],
    [InlineKeyboardButton(text="👤 Удалить админа", callback_data="delete_admin")],
    [InlineKeyboardButton(text="🚪 Выйти из админ-панели", callback_data="exit_admin")]
])

# Клавиатура для удаления новостей (без меню, только "Назад")
delete_news_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔙 Назад", callback_data="exit_admin")]
])

# Клавиатура для удаления админов (без меню, только "Назад")
delete_admin_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔙 Назад", callback_data="exit_admin")]
])

groups_map = {
    "ИСиП": ["09C31", "09C32", "09C33", "09C34", "09C35", "09C41", "09C42"],
    "Электронные устройства": ["11C31", "11C41"],
    "Аддитивные технологии": ["15C41", "15C42"],
    "Технология машиностроения": ["27C31", "27C41"]
}
directions = list(groups_map.keys())


# ---------------- ОБРАБОТЧИК "ГЛАВНОЕ МЕНЮ" ----------------
@dp.callback_query(F.data == "to_menu")
async def to_menu(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await delete_previous(call.from_user.id, call.message.chat.id)
    now = datetime.now()
    parity = "ЧЁТНАЯ" if now.isocalendar().week % 2 == 0 else "НЕЧЁТНАЯ"
    msg = await call.message.answer(
        f"🤖 Студенческий бот\n"
        f"📖 Сейчас {parity.lower()} неделя\n\n"
        f"Выбери раздел:",
        reply_markup=menu
    )
    last_msg[call.from_user.id] = msg.message_id
    await call.answer()


# ============================== АДМИН-ПАНЕЛЬ ==============================
@dp.message(Command("aboba228"))
async def admin_panel(message: types.Message):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM admins WHERE user_id = ?", (message.from_user.id,))
    admin = cur.fetchone()
    conn.close()
    if not admin:
        await send_with_delete(message.chat.id, message.from_user.id, "⛔ Нет доступа")
        return
    await send_with_delete(message.chat.id, message.from_user.id, "🛠 Админ-панель", reply_markup=admin_kb)


# ============================== ДОБАВЛЕНИЕ НОВОСТИ ==============================
@dp.callback_query(F.data == "add_news")
async def add_news_start(call: types.CallbackQuery, state: FSMContext):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM admins WHERE user_id = ?", (call.from_user.id,))
    admin = cur.fetchone()
    conn.close()
    if not admin:
        await call.answer("Нет доступа", show_alert=True)
        return
    await state.set_state(NewsState.waiting_title)
    await call.message.answer("📝 Введите ЗАГОЛОВОК новости:")
    await call.answer()

@dp.message(NewsState.waiting_title)
async def get_news_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(NewsState.waiting_text)
    await message.answer("📝 Введите ТЕКСТ новости:")

@dp.message(NewsState.waiting_text)
async def get_news_text(message: types.Message, state: FSMContext):
    await state.update_data(text=message.text)
    await state.set_state(NewsState.waiting_photo)
    await message.answer("🖼 Отправьте ФОТО (или 'пропустить'):")

@dp.message(NewsState.waiting_photo)
async def save_news_with_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    title = data.get('title')
    text = data.get('text')
    photo_id = None
    if message.photo:
        photo_id = message.photo[-1].file_id
    elif message.text and message.text.lower() == 'пропустить':
        pass
    else:
        await message.answer("❌ Отправьте фото или 'пропустить'")
        return
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO news (title, text, photo_id) VALUES (?, ?, ?)", (title, text, photo_id))
    conn.commit()
    conn.close()
    await state.clear()
    await send_with_delete(message.chat.id, message.from_user.id, f"✅ Новость '{title}' добавлена!")
    await send_news_to_users(title, text, photo_id)

async def send_news_to_users(title, text, photo_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM admins")
    admins = [row[0] for row in cur.fetchall()]
    cur.execute("SELECT user_id FROM users")
    users = cur.fetchall()
    conn.close()
    sent = 0
    for user in users:
        if user[0] in admins:
            continue
        try:
            if photo_id:
                await bot.send_photo(user[0], photo_id, caption=f"📰 {title}\n\n{text}")
            else:
                await bot.send_message(user[0], f"📰 {title}\n\n{text}")
            sent += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            logging.error(f"Не удалось отправить пользователю {user[0]}: {e}")
    logging.info(f"✅ Новость отправлена {sent} пользователям")


# ============================== УДАЛЕНИЕ НОВОСТИ ==============================
@dp.callback_query(F.data == "delete_news")
async def delete_news_start(call: types.CallbackQuery):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM admins WHERE user_id = ?", (call.from_user.id,))
    admin = cur.fetchone()
    if not admin:
        await call.answer("Нет доступа", show_alert=True)
        return
    cur.execute("SELECT id, title FROM news ORDER BY id DESC LIMIT 20")
    news_list = cur.fetchall()
    conn.close()
    if not news_list:
        await send_with_delete(call.message.chat.id, call.from_user.id, "📭 Новостей нет")
        await call.answer()
        return
    # Формируем клавиатуру без меню, только кнопки новостей и "Назад"
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for news_id, title in news_list:
        kb.inline_keyboard.append([
            InlineKeyboardButton(text=f"🗑 {title[:30]}", callback_data=f"delete_news_{news_id}")
        ])
    kb.inline_keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="exit_admin")])
    await send_with_delete(call.message.chat.id, call.from_user.id, "🗑 Выберите новость для удаления:", reply_markup=kb)
    await call.answer()

@dp.callback_query(F.data.startswith("delete_news_"))
async def confirm_delete_news(call: types.CallbackQuery):
    news_id = int(call.data.split("_")[2])
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM admins WHERE user_id = ?", (call.from_user.id,))
    admin = cur.fetchone()
    if not admin:
        await call.answer("Нет доступа", show_alert=True)
        return
    cur.execute("SELECT title FROM news WHERE id = ?", (news_id,))
    news = cur.fetchone()
    if not news:
        await send_with_delete(call.message.chat.id, call.from_user.id, "❌ Новость не найдена")
        await call.answer()
        return
    title = news[0]
    cur.execute("DELETE FROM news WHERE id = ?", (news_id,))
    conn.commit()
    conn.close()
    await send_with_delete(call.message.chat.id, call.from_user.id, f"✅ Новость '{title}' удалена!")
    await call.answer()


# ============================== ДОБАВЛЕНИЕ АДМИНА ==============================
@dp.callback_query(F.data == "add_admin")
async def add_admin_start(call: types.CallbackQuery, state: FSMContext):
    if call.from_user.id != ADMIN_ID:
        await call.answer("❌ Только главный админ может добавлять админов", show_alert=True)
        return
    await state.set_state(NewsState.waiting_admin_id)
    await call.message.answer("👤 Введите ID пользователя, которого хотите сделать админом:")
    await call.answer()

@dp.message(NewsState.waiting_admin_id)
async def add_admin_save(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)
    except ValueError:
        await send_with_delete(message.chat.id, message.from_user.id, "❌ Введите корректный ID (число)")
        return
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO admins (user_id) VALUES (?)", (user_id,))
        conn.commit()
        await send_with_delete(message.chat.id, message.from_user.id, f"✅ Пользователь {user_id} добавлен в админы!")
    except sqlite3.IntegrityError:
        await send_with_delete(message.chat.id, message.from_user.id, f"⚠️ Пользователь {user_id} уже является админом")
    finally:
        conn.close()
    await state.clear()


# ============================== УДАЛЕНИЕ АДМИНА ==============================
@dp.callback_query(F.data == "delete_admin")
async def delete_admin_start(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        await call.answer("❌ Только главный админ может удалять админов", show_alert=True)
        return
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM admins WHERE user_id != ?", (ADMIN_ID,))
    admins = cur.fetchall()
    conn.close()
    if not admins:
        await send_with_delete(call.message.chat.id, call.from_user.id, "📭 Нет других админов для удаления")
        await call.answer()
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for admin_id in admins:
        kb.inline_keyboard.append([
            InlineKeyboardButton(text=f"👤 {admin_id[0]}", callback_data=f"delete_admin_{admin_id[0]}")
        ])
    kb.inline_keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="exit_admin")])
    await send_with_delete(call.message.chat.id, call.from_user.id, "👤 Выберите админа для удаления:", reply_markup=kb)
    await call.answer()

@dp.callback_query(F.data.startswith("delete_admin_"))
async def confirm_delete_admin(call: types.CallbackQuery):
    user_id = int(call.data.split("_")[2])
    if call.from_user.id != ADMIN_ID:
        await call.answer("❌ Только главный админ может удалять админов", show_alert=True)
        return
    if user_id == ADMIN_ID:
        await send_with_delete(call.message.chat.id, call.from_user.id, "❌ Нельзя удалить главного админа!")
        await call.answer()
        return
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    await send_with_delete(call.message.chat.id, call.from_user.id, f"✅ Админ {user_id} удален!")
    await call.answer()


# ============================== ВЫХОД ИЗ АДМИНКИ ==============================
@dp.callback_query(F.data == "exit_admin")
async def exit_admin(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    # Удаляем последнее сообщение бота
    await delete_previous(call.from_user.id, call.message.chat.id)
    # Показываем главное меню
    now = datetime.now()
    parity = "ЧЁТНАЯ" if now.isocalendar().week % 2 == 0 else "НЕЧЁТНАЯ"
    msg = await call.message.answer(
        f"🤖 Студенческий бот\n"
        f"📖 Сейчас {parity.lower()} неделя\n\n"
        f"Выбери раздел:",
        reply_markup=menu
    )
    last_msg[call.from_user.id] = msg.message_id
    await call.answer()


# ============================== ПОКАЗ НОВОСТЕЙ ==============================
@dp.message(F.text == "📰 Новости")
async def show_news(message: types.Message):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, text, photo_id FROM news ORDER BY id DESC LIMIT 10")
    data = cur.fetchall()
    conn.close()
    if not data:
        await send_with_delete(message.chat.id, message.from_user.id, "📭 Новостей пока нет", reply_markup=news_kb)
        return

    await delete_previous(message.from_user.id, message.chat.id)
    for news_id, title, text, photo_id in data:
        try:
            if photo_id:
                msg = await bot.send_photo(
                    message.chat.id,
                    photo_id,
                    caption=f"📰 {title}\n\n{text}\n\n🆔 ID: {news_id}"
                )
            else:
                msg = await bot.send_message(
                    message.chat.id,
                    f"📰 {title}\n\n{text}\n\n🆔 ID: {news_id}"
                )
            last_msg[message.from_user.id] = msg.message_id
        except Exception as e:
            logging.error(f"Ошибка при показе новости: {e}")
    # Кнопка меню после списка
    await send_with_delete(message.chat.id, message.from_user.id, "⬅️ Вернуться в меню", reply_markup=news_kb)


# ============================== START ==============================
@dp.message(Command("start"))
async def start(message: types.Message):
    now = datetime.now()
    parity = "ЧЁТНАЯ" if now.isocalendar().week % 2 == 0 else "НЕЧЁТНАЯ"
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (message.from_user.id,))
    conn.commit()
    conn.close()
    await send_with_delete(
        message.chat.id,
        message.from_user.id,
        f"🤖 Студенческий бот\n📖 Сейчас {parity.lower()} неделя\n\nВыбери раздел:",
        reply_markup=menu
    )


# ============================== FAQ ==============================
@dp.message(F.text == "📚 FAQ")
async def faq(message: types.Message):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT question, answer FROM faq")
    data = cur.fetchall()
    conn.close()
    if not data:
        await send_with_delete(message.chat.id, message.from_user.id, "FAQ пока пуст 😔", reply_markup=faq_kb)
        return
    text = "📚 FAQ:\n\n" + "\n\n".join([f"❓ {q}\n➡️ {a}" for q, a in data])
    await send_with_delete(message.chat.id, message.from_user.id, text, reply_markup=faq_kb)


# ============================== РАСПИСАНИЕ ==============================
@dp.message(F.text == "📅 Расписание")
async def schedule_menu(message: types.Message):
    now = datetime.now()
    parity = "ЧЁТНАЯ" if now.isocalendar().week % 2 == 0 else "НЕЧЁТНАЯ"
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=d, callback_data=f"dir::{d}")]
            for d in directions
        ] + [[menu_button]]
    )
    await send_with_delete(
        message.chat.id,
        message.from_user.id,
        f"📅 Расписание\n\n📖 Текущая неделя: {parity}\n\nВыберите направление:",
        reply_markup=kb
    )

@dp.callback_query(F.data.startswith("dir::"))
async def choose_direction(call: types.CallbackQuery):
    direction = call.data.split("::")[1]
    groups = groups_map.get(direction, [])
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=g, callback_data=f"group::{direction}::{g}")]
            for g in groups
        ] + [[menu_button]]
    )
    await send_with_delete(call.message.chat.id, call.from_user.id, "👥 Выберите группу:", reply_markup=kb)
    await call.answer()

@dp.callback_query(F.data.startswith("group::"))
async def show_schedule(call: types.CallbackQuery):
    _, direction, group = call.data.split("::")
    now = datetime.now()
    week_type = "ЧЁТНАЯ" if now.isocalendar().week % 2 == 0 else "НЕЧЁТНАЯ"
    days = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"]
    today = days[now.weekday()]
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT pair, time, lesson
        FROM schedule
        WHERE direction = ? AND group_name = ? AND day = ? AND week_type = ?
        ORDER BY pair
    """, (direction, group, today, week_type))
    data = cur.fetchall()
    conn.close()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад к группам", callback_data=f"back_to_groups::{direction}")],
        [menu_button]
    ])

    if not data:
        await send_with_delete(
            call.message.chat.id,
            call.from_user.id,
            f"📅 Группа: {group}\n📖 Неделя: {week_type}\n🗓 День: {today}\n\n❌ Пар нет",
            reply_markup=kb
        )
        await call.answer()
        return

    text = f"📅 Группа: {group}\n📖 Неделя: {week_type}\n🗓 День: {today}\n\n"
    for pair, time, lesson in data:
        text += f"{pair} пара ({time}): {lesson}\n"
    await send_with_delete(call.message.chat.id, call.from_user.id, text, reply_markup=kb)
    await call.answer()

@dp.callback_query(F.data.startswith("back_to_groups::"))
async def back_to_groups(call: types.CallbackQuery):
    direction = call.data.split("::")[1]
    groups = groups_map.get(direction, [])
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=g, callback_data=f"group::{direction}::{g}")]
            for g in groups
        ] + [[menu_button]]
    )
    await send_with_delete(call.message.chat.id, call.from_user.id, f"👥 Выберите группу для {direction}:", reply_markup=kb)
    await call.answer()


# ============================== ПОМОЩЬ ==============================
@dp.message(F.text == "ℹ️ Помощь")
async def help_command(message: types.Message):
    await send_with_delete(
        message.chat.id,
        message.from_user.id,
        "🆘 Для управления ботом используй кнопки.\n"
        "🔄 Если бот не отвечает перезагрузи его /start.\n"
        "📱 Связь с разработчиком: @V_III_D",
        reply_markup=help_kb
    )


# ============================== MAIN ==============================
async def main():
    from db.database import init_db, seed_data
    init_db()
    seed_data()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())