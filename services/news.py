from db.database import get_connection

def get_news():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT text FROM news")
    data = cur.fetchall()

    conn.close()
    return data