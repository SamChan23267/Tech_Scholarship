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


            # Check if the username contains '@'
            if '@' in username:
                flash('Username should not contain @ symbol. Please choose another username.', 'alert')
                return redirect(url_for('auth', action='signup'))
            
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
                session['user'] = user['username']
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
    if 'user' in session:
        session.pop('user', None)
        flash('You have been locked out!', 'info')
    return redirect(url_for('home'))
    
@app.route('/topic/<string:topic_name>')
def topic_detail(topic_name):
    # Sample data
    points = 75
    maximum_points = 100
    units = [
        {'name': 'basics', 'display_name': 'Basics', 'progress': 80},
        {'name': 'intermediate', 'display_name': 'Intermediate', 'progress': 50},
        {'name': 'advanced', 'display_name': 'Advanced', 'progress': 30}
    ]

    # Ensure progress is a number between 0 and 100
    for unit in units:
        unit['progress'] = max(0, min(100, unit.get('progress', 0)))
    
    return render_template('content_template.html', topic_name=topic_name, points=points, maximum_points=maximum_points, units=units)

@app.route('/topic/<string:topic_name>/<string:unit_name>')
def unit_detail(topic_name, unit_name):
    # Sample data for unit detail
    unit_content = f"This is the content for the {unit_name} unit in {topic_name}."

    # Sample data for units (same as in topic_detail)
    units = [
        {'name': 'basics', 'display_name': 'Basics', 'progress': 80},
        {'name': 'intermediate', 'display_name': 'Intermediate', 'progress': 50},
        {'name': 'advanced', 'display_name': 'Advanced', 'progress': 30}
    ]
    
    return render_template('content_template.html', topic_name=topic_name, unit_name=unit_name, unit_content=unit_content, units=units)
if __name__ == '__main__':
    app.run(debug=True)