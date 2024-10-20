import sqlite3
import json

# Connect to the database (or create it if it doesn't exist)
conn_topics = sqlite3.connect('topics.db')

# Create a cursor object to execute SQL commands
cursor_topics = conn_topics.cursor()


# Create the topics table
cursor_topics.execute('''
CREATE TABLE IF NOT EXISTS topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT NOT NULL,
    name TEXT NOT NULL,
    display_name TEXT NOT NULL,
    content TEXT
)
''')

# Create the units table
cursor_topics.execute('''
CREATE TABLE IF NOT EXISTS units (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    display_name TEXT NOT NULL,
    content TEXT,
    FOREIGN KEY (topic_id) REFERENCES topics (id)
)
''')

# Create the sections table
cursor_topics.execute('''
CREATE TABLE IF NOT EXISTS sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    unit_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    display_name TEXT NOT NULL,
    content TEXT,
    FOREIGN KEY (unit_id) REFERENCES units (id)
)
''')

cursor_topics.execute('''
CREATE TABLE IF NOT EXISTS sub_sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    section_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    name TEXT NOT NULL,
    display_name TEXT NOT NULL,
    content TEXT,
    FOREIGN KEY (section_id) REFERENCES sections (id)
)
''')

# Remove the maximum_score and score columns from the units table




# Commit the changes and close the connection
conn_topics.commit()
conn_topics.close()

import sqlite3

def get_db_connection():
    conn_topics = sqlite3.connect('topics.db')
    conn_topics.row_factory = sqlite3.Row
    return conn_topics

def update_topic_content(topic_id, level=None, name=None, display_name=None, new_content=None):
    conn_topics = sqlite3.connect('topics.db')
    cursor_topics = conn_topics.cursor_topics()

    # Fetch the current values of the topic
    cursor_topics.execute('SELECT * FROM topics WHERE id = ?', (topic_id,))
    topic = cursor_topics.fetchone()

    if not topic:
        conn_topics.close()
        raise ValueError(f"Topic with id {topic_id} not found.")

    # Prepare the update statement with the current values if new values are empty
    updated_level = level if level else topic[1]  # topic[1] corresponds to 'level'
    updated_name = name if name else topic[2]  # topic[2] corresponds to 'name'
    updated_display_name = display_name if display_name else topic[3]  # topic[3] corresponds to 'display_name'
    updated_content = new_content if new_content else topic[4]  # topic[4] corresponds to 'content'

    cursor_topics.execute('''
        UPDATE topics
        SET level = ?, name = ?, display_name = ?, content = ?
        WHERE id = ?
    ''', (updated_level, updated_name, updated_display_name, updated_content, topic_id))

    conn_topics.commit()
    conn_topics.close()

def update_unit_content(unit_id, topic_id=None, name=None, display_name=None, score=None, maximum_score=None, new_content=None):
    conn_topics = sqlite3.connect('topics.db')
    cursor_topics = conn_topics.cursor_topics()

    # Fetch the current values of the unit
    cursor_topics.execute('SELECT * FROM units WHERE id = ?', (unit_id,))
    unit = cursor_topics.fetchone()

    if not unit:
        conn_topics.close()
        raise ValueError(f"Unit with id {unit_id} not found.")

    # Prepare the update statement with the current values if new values are empty
    updated_topic_id = topic_id if topic_id is not None else unit[1]  # unit[1] corresponds to 'topic_id'
    updated_name = name if name else unit[2]  # unit[2] corresponds to 'name'
    updated_display_name = display_name if display_name else unit[3]  # unit[3] corresponds to 'display_name'
    updated_score = score if score is not None else unit[4]  # unit[4] corresponds to 'score'
    updated_maximum_score = maximum_score if maximum_score is not None else unit[5]  # unit[5] corresponds to 'maximum_score'
    updated_content = new_content if new_content else unit[6]  # unit[6] corresponds to 'content'

    cursor_topics.execute('''
        UPDATE units
        SET topic_id = ?, name = ?, display_name = ?, score = ?, maximum_score = ?, content = ?
        WHERE id = ?
    ''', (updated_topic_id, updated_name, updated_display_name, updated_score, updated_maximum_score, updated_content, unit_id))

    conn_topics.commit()
    conn_topics.close()

def update_section(section_id, unit_id=None, name=None, display_name=None, content=None):
    conn_topics = sqlite3.connect('topics.db')
    cursor_topics = conn_topics.cursor()

    # Fetch the current values of the section
    cursor_topics.execute('SELECT * FROM sections WHERE id = ?', (section_id,))
    section = cursor_topics.fetchone()

    if not section:
        conn_topics.close()
        raise ValueError(f"Section with id {section_id} not found.")

    # Prepare the update statement with the current values if new values are empty
    updated_unit_id = unit_id if unit_id is not None else section[1]  # section[1] corresponds to 'unit_id'
    updated_name = name if name else section[2]  # section[2] corresponds to 'name'
    updated_display_name = display_name if display_name else section[3]  # section[3] corresponds to 'display_name'
    updated_content = content if content else section[4]  # section[4] corresponds to 'content'

    cursor_topics.execute('''
        UPDATE sections
        SET unit_id = ?, name = ?, display_name = ?, content = ?
        WHERE id = ?
    ''', (updated_unit_id, updated_name, updated_display_name, updated_content, section_id))

    conn_topics.commit()
    conn_topics.close()

def insert_section(unit_id, name, display_name, content=None):
    conn_topics = sqlite3.connect('topics.db')
    cursor_topics = conn_topics.cursor()
    cursor_topics.execute('INSERT INTO sections (unit_id, name, display_name, content) VALUES (?, ?, ?, ?)', 
                   (unit_id, name, display_name, content))
    conn_topics.commit()
    conn_topics.close()



def insert_sub_section(section_id, type, name, display_name, content=None):
    conn_topics = sqlite3.connect('topics.db')
    cursor_topics = conn_topics.cursor()
    cursor_topics.execute('INSERT INTO sub_sections (section_id, type, name, display_name, content) VALUES (?, ?, ?, ?, ?)', 
                   (section_id, type, name, display_name, content))
    conn_topics.commit()
    conn_topics.close()

def insert_sample_data():
    conn_topics = get_db_connection()
    cursor_topics = conn_topics.cursor()

    # Insert sample topics
    cursor_topics.execute('INSERT INTO topics (level, name, display_name) VALUES (?, ?, ?)', ('level1', 'number', 'Level 1 Number'))
    cursor_topics.execute('INSERT INTO topics (level, name, display_name) VALUES (?, ?, ?)', ('level1', 'algebra and graphs', 'Level 1 Algebra and Graphs'))
    cursor_topics.execute('INSERT INTO topics (level, name, display_name) VALUES (?, ?, ?)', ('level1', 'measurement', 'Level 1 Measurement'))
    cursor_topics.execute('INSERT INTO topics (level, name, display_name) VALUES (?, ?, ?)', ('level1', 'geometry and trignometry', 'Level 1 Geometry and Trigonometry'))
    cursor_topics.execute('INSERT INTO topics (level, name, display_name) VALUES (?, ?, ?)', ('level1', 'statistics and probability', 'Level 1 Statistics and Proabality'))

    # Insert sample units
    cursor_topics.execute('INSERT INTO units (topic_id, name, display_name) VALUES (?, ?, ?)', (1, 'addition', 'Addition'))
    cursor_topics.execute('INSERT INTO units (topic_id, name, display_name) VALUES (?, ?, ?)', (1, 'subtraction', 'Subtraction'))
    cursor_topics.execute('INSERT INTO units (topic_id, name, display_name) VALUES (?, ?, ?)', (1, 'multiplication', 'Multiplication'))
    cursor_topics.execute('INSERT INTO units (topic_id, name, display_name) VALUES (?, ?, ?)', (1, 'division', 'Division'))

    conn_topics.commit()
    conn_topics.close()


if __name__ == '__main__':

        # Connect to the topics.db database
    conn_topics = sqlite3.connect('topics.db')
    cursor_topics = conn_topics.cursor() 

    #insert_sub_section(1, 'practice', 'algebra basics practice 2', 'algebra basics practice', 20, 'This is an open ended question practice')

    sample_questions_mc = {
        "calculator": False,
        "no. of questions": 4,
        "questions": {
            1: {
                "type": "multiple_choice",
                "question": "2 + 2 = ?",
                "options": ["3", "4", "5", "6"],
                "answer": "4",
                "explanation": "2 + 2 equals 4."
            },
            2: {
                "type": "multiple_choice",
                "question": "2 + 3 = ?",
                "options": ["3", "4", "5", "6"],
                "answer": "5",
                "explanation": "2 + 3 equals 5."
            }, 
            3: {
                "type": "multiple_choice",
                "question": "2 + 4 = ?",
                "options": ["3", "4", "5", "6"],
                "answer": "6",
                "explanation": "2 + 4 equals 6."
            },
            4: {
                "type": "multiple_choice",
                "question": "3 + 5 = ?",
                "options": ["5", "6", "7", "8"],
                "answer": "8",
                "explanation": "2 + 5 equals 8."
            },
            5: {
                "type": "multiple_choice",
                "question": "3 + 6 = ?",
                "options": ["7", "8", "9", "10"],
                "answer": "9",
                "explanation": "3 + 6 equals 9."
            },
        }
    }

    sample_questions_oe = {
    "calculator": True,
    "no. of questions": 4,
    "questions": {
        1: {
            "type": "open_ended",
            "question": "2 + 2 = ?",
            "answer": ["4", "four"],
            "explanation": "2 + 2 equals 4."
        },
        2: {
            "type": "open_ended",
            "question": "2 + 3 = ?",
            "answer": ["5", "five"],
            "explanation": "2 + 3 equals 5."
        },
        3: {
            "type": "open_ended",
            "question": "2 + 4 = ?",
            "answer": ["6", "six"],
            "explanation": "2 + 4 equals 6."
        },
        4: {
            "type": "open_ended",
            "question": "3 + 5 = ?",
            "answer": ["8", "eight"],
            "explanation": "3 + 5 equals 8."
        },
        5: {
            "type": "open_ended",
            "question": "3 + 6 = ?",
            "answer": ["9", "nine"],
            "explanation": "3 + 6 equals 9."
        },
    }
}
    



    cursor_topics.execute('''
        UPDATE sub_sections
        SET content = ?
        WHERE id = 2
    ''', (json.dumps(sample_questions_mc),))
    
    cursor_topics.execute('''
        UPDATE sub_sections
        SET content = ?
        WHERE id = 3
    ''', (json.dumps(sample_questions_oe),))




    

    conn_topics.commit()
    conn_topics.close()
    
    '''insert_sample_data()
    insert_section(1, 'basic', 'addition basics', 'This section covers the basics of addition')
    insert_section(1, 'advanced', 'addition advanced', 'This section covers advanced addition')
    insert_sub_section(1, 'notes', 'addition theory 1', 'addition theory', 0, 0, 'This is a multiple choice question')
    insert_sub_section(1, 'practice', 'algebra basics practice 1', 'algebra basics practice', 10, 20, 'This is a multiple choice question')'''
