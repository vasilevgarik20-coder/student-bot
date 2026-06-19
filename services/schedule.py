from db.database import get_connection

def get_schedule():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT day, lesson FROM schedule")
    data = cur.fetchall()

    conn.close()
    return data