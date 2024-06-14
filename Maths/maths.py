from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, template_folder='templates')
app.secret_key = 'your_secret_key'

def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn






@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/auth', methods=['GET', 'POST'])
def auth():
    action = request.args.get('action', 'login')  # Default action is 'login'
    if request.method == 'POST':
        if action == 'signup':
            email = request.form.get('register email')
            password = request.form.get('create password')
            username = request.form.get('username')
            print(f"Signup form data: {email}, {password}, {username}")
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            existing_user = cursor.fetchone()

            if existing_user:
                flash('Email already exists. Please log in.', 'alert')
                conn.close()
                return redirect(url_for('auth', action='login'))
            
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            existing_username = cursor.fetchone()
            
            if existing_username:
                flash('Username already exists. Please try another username', 'alert')
                conn.close()
                return redirect(url_for('auth', action='signup'))
            
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            cursor.execute('INSERT INTO users (email, username, password) VALUES (?, ?, ?)',
                           (email, username, hashed_password))
            conn.commit()
            conn.close()
            flash('Signup successful! Please log in.', 'success')
            return redirect(url_for('auth', action='login'))

        else: #action == 'login
            email = request.form.get('email')
            password = request.form.get('password')
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()

            if not user:
                flash('Email not found. Please sign up.', 'alert')
                conn.close()
                return redirect(url_for('auth', action='signup'))
            
            if check_password_hash(user['password'], password):
                session['user'] = email
                flash('Login successful!', 'success')
                conn.close()
                return redirect(url_for('user_home'))
            flash('Invalid credentials. Please try again.', 'alert')
            conn.close()
            return redirect(url_for('auth', action='login'))
        
    return render_template('auth.html', action=action)


@app.route('/user_home')
def user_home():
    return render_template('user_home.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been locked out!', 'info')
    return redirect(url_for('home'))
    

if __name__ == '__main__':
    app.run(debug=True)