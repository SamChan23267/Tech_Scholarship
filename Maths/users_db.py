import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

# Connect to the database (or create it if it doesn't exist)
conn = sqlite3.connect('users.db')

# Create a cursor object to execute SQL commands
cursor = conn.cursor()

# Create the users table
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
''')

# Add a user to the database
def add_user(email, username, password):
    cursor.execute('INSERT INTO users (email, username, password) VALUES (?, ?, ?)', (email, username,
        generate_password_hash(password)))
    conn.commit()

# Get a user from the database by email
def get_user(email):
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    return cursor.fetchone()

# Get a user from the database by username
def get_user_by_username(username):
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    return cursor.fetchone()

# Check if a user exists in the database by email
def check_user(email):
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    return cursor.fetchone() is not None

# Check if a user exists in the database by username
def check_user_by_username(username):
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    return cursor.fetchone() is not None

# Update a user's password in the database
def update_password(email, new_password):
    cursor.execute('UPDATE users SET password = ? WHERE email = ?', (generate_password_hash(new_password), email))
    conn.commit()

# Delete a user from the database
def delete_user(email):
    cursor.execute('DELETE FROM users WHERE email = ?', (email,))
    conn.commit()


# Commit the changes and close the connection
conn.commit()
conn.close()