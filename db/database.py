import sqlite3

DB_NAME = "bot.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # FAQ
    cur.execute("""
    CREATE TABLE IF NOT EXISTS faq (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        answer TEXT
    )
    """)

    # Schedule
    cur.execute("""
    CREATE TABLE IF NOT EXISTS schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        day TEXT,
        lesson TEXT
    )
    """)

    # News
    cur.execute("""
    CREATE TABLE IF NOT EXISTS news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT
    )
    """)

    conn.commit()
    conn.close()


def seed_data():
    conn = get_connection()
    cur = conn.cursor()

    # проверим чтобы не дублировать
    cur.execute("SELECT COUNT(*) FROM faq")
    if cur.fetchone()[0] == 0:

        cur.executemany(
            "INSERT INTO faq (question, answer) VALUES (?, ?)",
            [
                ("Как узнать расписание?", "Используй /schedule"),
                ("Где деканат?", "Главный корпус"),
            ]
        )

        cur.executemany(
            "INSERT INTO schedule (day, lesson) VALUES (?, ?)",
            [
                ("Понедельник", "Математика, Python"),
                ("Вторник", "Базы данных, Английский"),
            ]
        )

        cur.executemany(
            "INSERT INTO news (text) VALUES (?)",
            [
                ("Началась практика студентов",),
                ("Защита через неделю",),
            ]
        )

    conn.commit()
    conn.close()