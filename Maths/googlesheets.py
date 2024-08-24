import gspread
from oauth2client.service_account import ServiceAccountCredentials
import sqlite3

# Set up Google Sheets API
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(r'C:\Users\chany\Downloads\shc-maths-academy-f1067487286a.json', scope)
client = gspread.authorize(creds)

# Open the Google Sheet
sheet = client.open("SHC Maths Academy Topics").sheet1

# Fetch all data from the sheet
data = sheet.get_all_records()

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

for row in data:
    cursor_topics.execute('''INSERT INTO topics (level, name, display_name, content) VALUES (?, ?, ?, ?)''', 
                   (row['level'], row['name'], row['display_name'], row['content']))

conn_topics.commit()
conn_topics.close()