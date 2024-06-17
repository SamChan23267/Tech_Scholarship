import sqlite3

# Connect to the database (or create it if it doesn't exist)
conn = sqlite3.connect('topics.db')

# Create a cursor object to execute SQL commands
cursor = conn.cursor()

# Create the topics table
cursor.execute('''
CREATE TABLE IF NOT EXISTS topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT NOT NULL,
    name TEXT NOT NULL,
    display_name TEXT NOT NULL
)
''')

# Create the units table
cursor.execute('''
CREATE TABLE IF NOT EXISTS units (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    display_name TEXT NOT NULL,
    progress INTEGER NOT NULL,
    FOREIGN KEY (topic_id) REFERENCES topics (id)
)
''')

# Commit the changes and close the connection
conn.commit()
conn.close()

import sqlite3

def get_db_connection():
    conn = sqlite3.connect('topics.db')
    conn.row_factory = sqlite3.Row
    return conn

def insert_sample_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert sample topics
    cursor.execute('INSERT INTO topics (level, name, display_name) VALUES (?, ?, ?)', ('level1', 'number', 'Level 1 Number'))
    cursor.execute('INSERT INTO topics (level, name, display_name) VALUES (?, ?, ?)', ('level1', 'algebra and graphs', 'Level 1 Algebra and Graphs'))
    cursor.execute('INSERT INTO topics (level, name, display_name) VALUES (?, ?, ?)', ('level1', 'measurement', 'Level 1 Measurement'))
    cursor.execute('INSERT INTO topics (level, name, display_name) VALUES (?, ?, ?)', ('level1', 'geometry and trignometry', 'Level 1 Geometry and Trigonometry'))
    cursor.execute('INSERT INTO topics (level, name, display_name) VALUES (?, ?, ?)', ('level1', 'statistics and probability', 'Level 1 Statistics and Proabality'))

    # Insert sample units
    cursor.execute('INSERT INTO units (topic_id, name, display_name, progress) VALUES (?, ?, ?, ?)', (1, 'addition', 'Addition', 80))
    cursor.execute('INSERT INTO units (topic_id, name, display_name, progress) VALUES (?, ?, ?, ?)', (1, 'subtraction', 'Subtraction', 60))
    cursor.execute('INSERT INTO units (topic_id, name, display_name, progress) VALUES (?, ?, ?, ?)', (1, 'multiplication', 'Multiplication', 50))
    cursor.execute('INSERT INTO units (topic_id, name, display_name, progress) VALUES (?, ?, ?, ?)', (1, 'division', 'Division', 30))

    conn.commit()
    conn.close()

if __name__ == '__main__':
    insert_sample_data()