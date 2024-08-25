import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import json

# Connect to the database (or create it if it doesn't exist)
conn_users = sqlite3.connect('users.db')

# Create a cursor object to execute SQL commands
cursor_users = conn_users.cursor()

# Create the users table
cursor_users.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
''')

# Add a user to the database
def add_user(email, username, password):
    cursor_users.execute('INSERT INTO users (email, username, password) VALUES (?, ?, ?)', (email, username,
        generate_password_hash(password)))
    conn_users.commit()

# Get a user from the database by email
def get_user(email):
    cursor_users.execute('SELECT * FROM users WHERE email = ?', (email,))
    return cursor_users.fetchone()

# Get a user from the database by username
def get_user_by_username(username):
    cursor_users.execute('SELECT * FROM users WHERE username = ?', (username,))
    return cursor_users.fetchone()

# Check if a user exists in the database by email
def check_user(email):
    cursor_users.execute('SELECT * FROM users WHERE email = ?', (email,))
    return cursor_users.fetchone() is not None

# Check if a user exists in the database by username
def check_user_by_username(username):
    cursor_users.execute('SELECT * FROM users WHERE username = ?', (username,))
    return cursor_users.fetchone() is not None

# Update a user's password in the database
def update_password(email, new_password):
    cursor_users.execute('UPDATE users SET password = ? WHERE email = ?', (generate_password_hash(new_password), email))
    conn_users.commit()

# Delete a user from the database
def delete_user(email):
    cursor_users.execute('DELETE FROM users WHERE email = ?', (email,))
    conn_users.commit()

sample_scores = {
        5: {  # user_id 1

        }
    }
for user_id, scores in sample_scores.items():
        cursor_users.execute('UPDATE users SET score = ? WHERE id = ?', (json.dumps(scores), user_id))


# Commit the changes and close the conn_usersection
conn_users.commit()
conn_users.close()