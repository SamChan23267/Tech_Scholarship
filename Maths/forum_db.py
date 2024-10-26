import sqlite3

def init_forum_db():
    conn = sqlite3.connect('forum.db')
    cursor = conn.cursor()

    # Create posts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            comments TEXT DEFAULT '{}'
        )
    ''')


    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_forum_db()