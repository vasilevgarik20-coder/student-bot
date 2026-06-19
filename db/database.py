import sqlite3

DB_NAME = "bot.db"


# ---------------- CONNECTION ----------------
def get_connection():
    return sqlite3.connect(DB_NAME)


# ---------------- INIT DB ----------------
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

    # SCHEDULE (ВАЖНО: структура под направление → группа → день → занятие)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        direction TEXT,
        group_name TEXT,
        day TEXT,
        lesson TEXT
    )
    """)

    # NEWS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT
    )
    """)

    conn.commit()
    conn.close()


# ---------------- SEED DATA ----------------
def seed_data():
    conn = get_connection()
    cur = conn.cursor()

    # ---------------- FAQ ----------------
    cur.execute("SELECT COUNT(*) FROM faq")
    if cur.fetchone()[0] == 0:

        cur.executemany(
            "INSERT INTO faq (question, answer) VALUES (?, ?)",
            [
                ("Где находится деканат?", "Следующая дверь после 459 аудитории"),
                ("Декан факультета", "Доктор экономических наук, профессор Шамина Любовь Константиновна"),
                ("Телефон деканата", "+7 (812) 490-05-40"),
                ("Телефон приемной комиссии", "+7 (812) 495-76-20"),
                ("Telegram канал факультета", "@BTSUVoenmeh"),
            ]
        )

    # ---------------- SCHEDULE ----------------
    cur.execute("SELECT COUNT(*) FROM schedule")
    if cur.fetchone()[0] == 0:

        cur.executemany(
            "INSERT INTO schedule (direction, group_name, day, lesson) VALUES (?, ?, ?, ?)",
            [
                # ---------------- ИСиП ----------------
                ("ИСиП", "09С31", "Понедельник", "Математика, Python"),
                ("ИСиП", "09С31", "Вторник", "Базы данных, Английский"),

                ("ИСиП", "09С32", "Понедельник", "Математика"),
                ("ИСиП", "09С32", "Вторник", "Python"),

                ("ИСиП", "09С33", "Понедельник", "Алгоритмы"),
                ("ИСиП", "09С34", "Понедельник", "ОС и сети"),

                # ---------------- Электронные устройства ----------------
                ("Электронные устройства", "11С31", "Понедельник", "Схемотехника"),
                ("Электронные устройства", "11С31", "Вторник", "Физика"),

                ("Электронные устройства", "11С41", "Понедельник", "Микропроцессоры"),

                # ---------------- Аддитивные технологии ----------------
                ("Аддитивные технологии", "15С41", "Понедельник", "3D моделирование"),
                ("Аддитивные технологии", "15С42", "Вторник", "CAD системы"),

                # ---------------- Машиностроение ----------------
                ("Технология машиностроения", "27С31", "Понедельник", "Детали машин"),
                ("Технология машиностроения", "27С41", "Вторник", "Технология обработки"),
            ]
        )

    conn.commit()
    conn.close()