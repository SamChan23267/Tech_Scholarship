import gspread
from oauth2client.service_account import ServiceAccountCredentials
import sqlite3

# Set up Google Sheets API
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(r'C:\Users\chany\Downloads\shc-maths-academy-f1067487286a.json', scope)
client = gspread.authorize(creds)

# Open the Google Sheet
sheet_topics = client.open("SHC Maths Academy Topics").worksheet('topics_table')
sheet_units = client.open("SHC Maths Academy Topics").worksheet('units_table')
sheet_sections = client.open("SHC Maths Academy Topics").worksheet('sections_table')
sheet_sub_sections = client.open("SHC Maths Academy Topics").worksheet('sub_sections_table')


# Fetch all data from the sheet
data_topics = sheet_topics.get_all_records()
data_units = sheet_units.get_all_records()
data_sections = sheet_sections.get_all_records()
data_sub_sections = sheet_sub_sections.get_all_records()

# Print data to verify
conn_topics = sqlite3.connect('topics.db')
cursor_topics = conn_topics.cursor()

cursor_topics.execute('DROP TABLE topics')

cursor_topics.execute('''
CREATE TABLE IF NOT EXISTS topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT NOT NULL,
    name TEXT NOT NULL,
    display_name TEXT NOT NULL,
    content TEXT
)
''')

cursor_topics.execute('DROP TABLE units')

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

cursor_topics.execute('DROP TABLE sections')

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

cursor_topics.execute('DROP TABLE sub_sections')

# Create the sub_sections table
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
                      

for row in data_topics:
    cursor_topics.execute('''INSERT INTO topics (level, name, display_name, content) VALUES (?, ?, ?, ?)''', 
                   (row['level'], row['name'], row['display_name'], row['content']))
    
for row in data_units:
    cursor_topics.execute('''INSERT INTO units (topic_id, name, display_name, content) VALUES (?, ?, ?, ?)''', 
                   (row['topic_id'], row['name'], row['display_name'], row['content']))
    
for row in data_sections:
    cursor_topics.execute('''INSERT INTO sections (unit_id, name, display_name, content) VALUES (?, ?, ?, ?)''', 
                   (row['unit_id'], row['name'], row['display_name'], row['content']))
    
for row in data_sub_sections:
    cursor_topics.execute('''INSERT INTO sub_sections (section_id, type, name, display_name, content) VALUES (?, ?, ?, ?, ?)''', 
                   (row['section_id'], row['type'], row['name'], row['display_name'], row['content']))
    

conn_topics.commit()
conn_topics.close()