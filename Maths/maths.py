from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from oauthlib.oauth2 import WebApplicationClient
import requests
import json
from functools import wraps
import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

import re
username_pattern = re.compile(r'^[a-z0-9_-]{3,16}$')
password_pattern = re.compile(r'^.{6,16}$')

app = Flask(__name__, template_folder='templates')
app.secret_key = 'your_secret_key'


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('You need to be logged in to access this page.', 'alert')
            return redirect(url_for('auth', action='login'))
        return f(*args, **kwargs)
    return decorated_function

def temp_session_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'temp_email' not in session or 'temp_given_name' not in session:
            flash('You need to complete the registration process.', 'alert')
            return redirect(url_for('login_google'))
        return f(*args, **kwargs)
    return decorated_function


# Google OAuth 2.0 setup
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

client = WebApplicationClient(GOOGLE_CLIENT_ID)

# Function to get a connection to the users.db database
def get_users_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

# Fuction to get a connection to the topics.db databse
def get_topics_db_connection():
    conn = sqlite3.connect('topics.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()


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

            # Validate username using regex
            if not username_pattern.match(username):
                flash('Username must be 3-16 characters long and can only contain lowercase letters, numbers, underscores, and hyphens.', 'alert')
                return redirect(url_for('auth', action='signup'))

            # Validate password using regex
            if not password_pattern.match(password):
                flash('Password must be 6-16 characters long.', 'alert')
                return redirect(url_for('auth', action='signup'))

            
            conn = get_users_db_connection()
            cursor = conn.cursor()
            
            # check if the email already exists
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            existing_user = cursor.fetchone()

            if existing_user:
                flash('Email already exists. Please log in.', 'alert')
                conn.close()
                return redirect(url_for('auth', action='login'))
            
            # check if the username already exists
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            existing_username = cursor.fetchone()
            
            if existing_username:
                flash('Username already exists. Please try another username', 'alert')
                conn.close()
                return redirect(url_for('auth', action='signup'))
            
            # Hash the password and insert the new user into the database
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            cursor.execute('INSERT INTO users (email, username, password) VALUES (?, ?, ?)',
                           (email, username, hashed_password))
            conn.commit()
            conn.close()
            flash('Signup successful! Please log in.', 'success')
            return redirect(url_for('auth', action='login'))

        else: # action == 'login'
            email = request.form.get('email')
            password = request.form.get('password')
            
            conn = get_users_db_connection()
            cursor = conn.cursor()
            
            # Check if the email exists
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()

            if not user:
                flash('Email not found. Please sign up.', 'alert')
                conn.close()
                return redirect(url_for('auth', action='signup'))
            
            # Verify the password
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
@login_required
def user_home():
    return render_template('user_home.html')


@app.route('/logout')
@login_required
def logout():
    if 'user' in session:
        session.pop('user', None)
        flash('You have been locked out!', 'info')
    return redirect(url_for('home'))
    

@app.route('/login/google')
def login_google():
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

@app.route('/login/google/callback')
def callback():
    code = request.args.get("code")
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    client.parse_request_body_response(json.dumps(token_response.json()))

    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    userinfo = userinfo_response.json()
    email = userinfo["email"]
    given_name = userinfo["given_name"]

    conn = get_users_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()

    if not user:
        session['temp_email'] = email
        session['temp_given_name'] = given_name
        conn.close()
        return redirect(url_for('create_username'))

    session['user'] = user['username']
    flash('Login successful!', 'success')
    conn.close()
    return redirect(url_for('user_home'))


@app.route('/create_username', methods=['GET', 'POST'])
@temp_session_required
def create_username():
    if request.method == 'POST':
        username = request.form.get('username')
        
        # Validate username using regex
        if not username_pattern.match(username):
            flash('Username must be 3-16 characters long and can only contain lowercase letters, numbers, underscores, and hyphens.', 'alert')
            return redirect(url_for('create_username'))

        conn = get_users_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        existing_username = cursor.fetchone()

        if existing_username:
            flash('Username already exists. Please try another username', 'alert')
            conn.close()
            return redirect(url_for('create_username'))

        email = session.get('temp_email')
        given_name = session.get('temp_given_name')
        hashed_password = generate_password_hash("defaultpassword", method='pbkdf2:sha256')
        cursor.execute('INSERT INTO users (email, username, password) VALUES (?, ?, ?)',
                       (email, username, hashed_password))
        conn.commit()
        conn.close()

        session.pop('temp_email', None)
        session.pop('temp_given_name', None)
        session['user'] = username
        flash('Signup successful!', 'success')
        return redirect(url_for('user_home'))

    return render_template('create_username.html')

@app.route('/topic/<string:level>/<string:topic_name>')
def topic_detail(level, topic_name):
    conn = get_topics_db_connection()
    cursor = conn.cursor()

    # Fetch the topic details
    cursor.execute('SELECT * FROM topics WHERE level = ? AND name = ?', (level, topic_name))
    topic = cursor.fetchone()

    if not topic:
        flash('Topic not found.', 'alert')
        conn.close()
        return redirect(url_for('home'))

    # Fetch the units associated with the topic
    cursor.execute('SELECT * FROM units WHERE topic_id = ?', (topic['id'],))
    units = cursor.fetchall()

    # Convert sqlite3.Row objects to dictionaries
    units = [dict(unit) for unit in units]

    # Calculate total points and total maximum points
    total_points = sum(unit['score'] for unit in units)
    total_maximum_points = sum(unit['maximum_score'] for unit in units)

    # Ensure progress is a number between 0 and 100
    for unit in units:
        unit['progress'] = (unit['score'] / unit['maximum_score']) * 100

    conn.close()
    return render_template('content_template.html', level=level, topic_name=topic_name, total_points=total_points, total_maximum_points=total_maximum_points, units=units, display_name=topic['display_name'], is_topic=True) #title=title

@app.route('/topic/<string:level>/<string:topic_name>/<string:unit_name>')
def unit_detail(level, topic_name, unit_name):
    conn = get_topics_db_connection()
    cursor = conn.cursor()

    # Fetch the topic details
    cursor.execute('SELECT * FROM topics WHERE level = ? AND name = ?', (level, topic_name))
    topic = cursor.fetchone()

    if not topic:
        flash('Topic not found.', 'alert')
        conn.close()
        return redirect(url_for('home'))

    # Fetch the units associated with the topic
    cursor.execute('SELECT * FROM units WHERE topic_id = ?', (topic['id'],))
    units = cursor.fetchall()

    #Fetch the specific unit details
    cursor.execute('SELECT * FROM units WHERE topic_id = ? AND name = ?', (topic['id'], unit_name))
    unit = cursor.fetchone()

    if not unit:
        flash('Unit not found.', 'alert')
        conn.close()
        return redirect(url_for('topic_detail', level=level, topic_name=topic_name))

    unit_content = f"This is the content for the {unit_name} unit in {level} {topic_name}."
    title = f"{topic['display_name']} - {unit['display_name']}"

    # Convert sqlite3.Row objects to dictionaries
    units = [dict(unit) for unit in units]

    # Ensure progress is a number between 0 and 100
    for unit in units:
        unit['progress'] = (unit['score'] / unit['maximum_score']) * 100

    conn.close()
    return render_template('content_template.html', level=level, topic_name=topic_name, unit_name=unit_name, unit_content=unit_content, units=units, display_name=topic['display_name'], title=title, is_topic=False)
    
if __name__ == '__main__':
    app.run(debug=True)