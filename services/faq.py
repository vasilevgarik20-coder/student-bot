from db.database import get_connection

def get_faq():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT question, answer FROM faq")
    data = cur.fetchall()

    conn.close()
    return data