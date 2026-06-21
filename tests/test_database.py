import pytest
import sqlite3
from db.database import get_connection, DB_NAME

def test_get_connection():
    conn = get_connection()
    assert conn is not None
    assert isinstance(conn, sqlite3.Connection)
    conn.close()

def test_tables_exist():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cur.fetchall()]
    conn.close()
    expected = ['faq', 'schedule', 'news', 'admins', 'users']
    for table in expected:
        assert table in tables, f"Таблица {table} отсутствует"

def test_faq_not_empty():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM faq")
    count = cur.fetchone()[0]
    conn.close()
    assert count > 0, "FAQ пуст"

def test_schedule_not_empty():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM schedule")
    count = cur.fetchone()[0]
    conn.close()
    assert count > 0, "Расписание пусто"

def test_admins_contains_main_admin():
    from config import ADMIN_ID
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM admins WHERE user_id = ?", (ADMIN_ID,))
    admin = cur.fetchone()
    conn.close()
    assert admin is not None, f"Главный админ {ADMIN_ID} не найден в таблице admins"
