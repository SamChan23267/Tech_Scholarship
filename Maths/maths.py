from flask import Flask, render_template, request, redirect, url_for, session, flash, g, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from oauthlib.oauth2 import WebApplicationClient
import requests
import json
import random
from functools import wraps
from datetime import datetime
import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

import re
username_pattern = re.compile(r'^[a-z0-9_-]{6,16}$')
password_pattern = re.compile(r'^.{6,16}$')

app = Flask(__name__, template_folder='templates')
app.secret_key = 'your_secret_key'


import pytz
auckland_tz = pytz.timezone('Pacific/Auckland')

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

@app.after_request
def add_header(response):
    response.cache_control.no_store = True
    return response


# Google OAuth 2.0 setup
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

client = WebApplicationClient(GOOGLE_CLIENT_ID)

# Function to get a connection to the users.db database
def get_users_db_connection():
    conn_users = getattr(g, 'conn_users', None)
    if conn_users is None:
        conn_users = g.conn_users = sqlite3.connect('users.db')
        conn_users.row_factory = sqlite3.Row
    return conn_users

# Fuction to get a connection to the topics.db databse
def get_topics_db_connection():
    conn_topics = getattr(g, 'conn_topics', None)
    if conn_topics is None:
        conn_topics = g.conn_topics = sqlite3.connect('topics.db')
        conn_topics.row_factory = sqlite3.Row
    return conn_topics

def get_forum_db_connection():
    conn_forum = getattr(g, 'conn_forum', None)
    if conn_forum is None:
        conn_forum = g.conn_forum = sqlite3.connect('forum.db')
        conn_forum.row_factory = sqlite3.Row
    return conn_forum

@app.teardown_appcontext
def close_conn(exception):
    if 'conn_users' in g:
        g.conn_users.close()
    if 'conn_topics' in g:
        g.conn_topics.close()
    if 'conn_forum' in g:
        g.conn_forum.close()    

def get_user_scores(user_id):
    conn_users = get_users_db_connection()
    cursor_users = conn_users.cursor()

    cursor_users.execute('SELECT score FROM users WHERE id = ?', (user_id,))
    user_scores = cursor_users.fetchone()
    user_scores = eval(user_scores['score']) if user_scores and user_scores['score'] else {}

    conn_users.close()
    return user_scores

def update_user_score(user_id, sub_section_id, score):
    conn_users = get_users_db_connection()
    cursor_users = conn_users.cursor()

    # Fetch existing scores
    cursor_users.execute('SELECT score FROM users WHERE id = ?', (user_id,))
    user_scores = cursor_users.fetchone()
    user_scores = eval(user_scores['score']) if user_scores and user_scores['score'] else {}

    # Update the score for the specific sub_section
    user_scores[str(sub_section_id)] = score

    # Store the updated scores back in the database
    cursor_users.execute('UPDATE users SET score = ? WHERE id = ?', (str(user_scores), user_id))
    conn_users.commit()
    conn_users.close()

def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()


@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/auth', methods=['GET', 'POST'])
def auth():
    action = request.args.get('action', 'login')  # Default action is 'login'

    # Check if the user is already logged in
    if 'user' in session and action == 'signup':
        return redirect(url_for('user_home'))
    
    if request.method == 'POST':
        conn_users = get_users_db_connection()
        cursor_users = conn_users.cursor()
        if action == 'signup':
            email = request.form.get('register email')
            password = request.form.get('create password')
            username = request.form.get('username')
            confirm_password = request.form.get('confirm password')

            # Validate username using regex
            if not username_pattern.match(username):
                flash('Username must be 6-16 characters long and can only contain lowercase letters, numbers, underscores, and hyphens.', 'alert')
                return redirect(url_for('auth', action='signup'))

            # Validate password using regex
            if not password_pattern.match(password):
                flash('Password must be 6-16 characters long.', 'alert')
                return redirect(url_for('auth', action='signup'))
            
            # Confirm password
            if password != confirm_password:
                flash('Passwords do not match!', 'danger')
                return redirect(url_for('auth', action='signup'))
            
            # check if the email already exists
            cursor_users.execute('SELECT * FROM users WHERE email = ?', (email,))
            existing_user = cursor_users.fetchone()

            if existing_user:
                flash('Email already exists. Please log in.', 'alert')
                conn_users.close()
                return redirect(url_for('auth', action='login'))
            
            # check if the username already exists
            cursor_users.execute('SELECT * FROM users WHERE username = ?', (username,))
            existing_username = cursor_users.fetchone()
            
            if existing_username:
                flash('Username already exists. Please try another username', 'alert')
                conn_users.close()
                return redirect(url_for('auth', action='signup'))
            
            # Hash the password and insert the new user into the database
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            cursor_users.execute('INSERT INTO users (email, username, password) VALUES (?, ?, ?)',
                           (email, username, hashed_password))
            conn_users.commit()
            conn_users.close()
            flash('Signup successful! Please log in.', 'success')
            return redirect(url_for('auth', action='login'))

        else: # action == 'login'
            email = request.form.get('email')
            password = request.form.get('password')
            
            cursor_users = conn_users.cursor()
            
            # Check if the email exists
            cursor_users.execute('SELECT * FROM users WHERE email = ?', (email,))
            user = cursor_users.fetchone()

            if not user:
                flash('Email not found. Please sign up.', 'alert')
                conn_users.close()
                return redirect(url_for('auth', action='signup'))
            
            # Verify the password
            if check_password_hash(user['password'], password):
                session['user'] = user['username']
                session['user_id'] = user['id']
                flash('Login successful!', 'success')
                conn_users.close()
                return redirect(url_for('user_home'))
            flash('Invalid credentials. Please try again.', 'alert')
            conn_users.close()
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
        flash('You have been logged out!', 'info')
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

    conn_users = get_users_db_connection()
    cursor_users = conn_users.cursor()

    cursor_users.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor_users.fetchone()

    if not user:
        session['temp_email'] = email
        session['temp_given_name'] = given_name
        conn_users.close()
        return redirect(url_for('create_username'))

    session['user'] = user['username']
    session['user_id'] = user['id']
    flash('Login successful!', 'success')
    conn_users.close()
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

        conn_users = get_users_db_connection()
        cursor_users = conn_users.cursor()

        cursor_users.execute('SELECT * FROM users WHERE username = ?', (username,))
        existing_username = cursor_users.fetchone()

        if existing_username:
            flash('Username already exists. Please try another username', 'alert')
            conn_users.close()
            return redirect(url_for('create_username'))

        email = session.get('temp_email')
        given_name = session.get('temp_given_name')
        hashed_password = generate_password_hash("defaultpassword", method='pbkdf2:sha256')
        cursor_users.execute('INSERT INTO users (email, username, password) VALUES (?, ?, ?)',
                       (email, username, hashed_password))
        conn_users.commit()
        conn_users.close()

        session.pop('temp_email', None)
        session.pop('temp_given_name', None)
        session['user'] = username
        flash('Signup successful!', 'success')
        return redirect(url_for('user_home'))

    return render_template('create_username.html')

@app.route('/topic/<string:level>/<string:topic_name>')
def topic_detail(level, topic_name):
    conn_topics = get_topics_db_connection()
    cursor_topics = conn_topics.cursor()

    conn_users = get_users_db_connection()
    cursor_users = conn_users.cursor()

    # Fetch the topic details
    cursor_topics.execute('SELECT * FROM topics WHERE level = ? AND name = ?', (level, topic_name))
    topic = cursor_topics.fetchone()

    if not topic:
        flash('Topic not found.', 'alert')
        conn_topics.close()
        conn_users.close()
        return redirect(url_for('home'))
    
    # Convert sqlite3.Row object to dictionary
    topic = dict(topic)

    # Fetch the units associated with the topic
    cursor_topics.execute('SELECT * FROM units WHERE topic_id = ?', (topic['id'],))
    units = cursor_topics.fetchall()

    # Convert sqlite3.Row objects to dictionaries
    units = [dict(unit) for unit in units]

    user_id = session['user_id']
    user_scores = get_user_scores(user_id)

    for unit in units:
        cursor_topics.execute('SELECT * FROM sections WHERE unit_id = ?', (unit['id'],))
        sections = cursor_topics.fetchall()
        unit['sections'] = [dict(section) for section in sections]

        for section in unit['sections']:
            cursor_topics.execute('SELECT * FROM sub_sections WHERE section_id = ?', (section['id'],))
            sub_sections = cursor_topics.fetchall()
            section['sub_sections'] = [dict(sub_section) for sub_section in sub_sections]

    # Calculate total points and total maximum points
    total_points = 0
    total_maximum_points = 0


    for unit in units:
        unit_points = 0
        unit_maximum_points = 0
        for section in unit['sections']:
            section_points = sum(user_scores.get(str(sub_section['id']), 0) for sub_section in section['sub_sections'])
            section_maximum_points = sum(json.loads(sub_section['content']).get('no. of questions', 0) if sub_section['type'] == 'practice' else 0 for sub_section in section['sub_sections'])
            section['score'] = section_points
            section['maximum_score'] = section_maximum_points
            unit_points += section_points
            unit_maximum_points += section_maximum_points
        unit['score'] = unit_points
        unit['maximum_score'] = unit_maximum_points
        total_points += unit_points
        total_maximum_points += unit_maximum_points

    # Ensure progress is a number between 0 and 100
    for unit in units:
        unit['progress'] = (unit['score'] / unit['maximum_score']) * 100 if unit['maximum_score'] > 0 else 0

    conn_topics.close()
    return render_template('content_template.html', level=level, topic_name=topic_name, total_points=total_points, total_maximum_points=total_maximum_points, units=units, display_name=topic.get('display_name', 'N/A'), content=topic.get('content', 'N/A'), is_topic=True) #title=title

@app.route('/topic/<string:level>/<string:topic_name>/<string:unit_name>')
def unit_detail(level, topic_name, unit_name):
    conn_topics = get_topics_db_connection()
    cursor_topics = conn_topics.cursor()

    conn_users = get_users_db_connection()
    cursor_users = conn_users.cursor()

    # Fetch the topic details
    cursor_topics.execute('SELECT * FROM topics WHERE level = ? AND name = ?', (level, topic_name))
    topic = cursor_topics.fetchone()

    if not topic:
        flash('Topic not found.', 'alert')
        conn_topics.close()
        conn_users.close()
        return redirect(url_for('home'))
    
    # Convert sqlite3.Row object to dictionary
    topic = dict(topic)

    # Fetch the units associated with the topic
    cursor_topics.execute('SELECT * FROM units WHERE topic_id = ?', (topic['id'],))
    unit_dict = cursor_topics.fetchall()

    # Convert sqlite3.Row objects to dictionaries
    unit_dict = [dict(unit) for unit in unit_dict]

    #Fetch the specific unit details
    cursor_topics.execute('SELECT * FROM units WHERE topic_id = ? AND name = ?', (topic['id'], unit_name))
    unit_current = cursor_topics.fetchone()

    if not unit_current:
        flash('Unit not found.', 'alert')
        conn_topics.close()
        conn_users.close()
        return redirect(url_for('topic_detail', level=level, topic_name=topic_name))

    # Convert sqlite3.Row object to dictionary
    unit_current = dict(unit_current)

    # unit_content = unit['content']
    title = f"{topic['display_name']} - {unit_current['display_name']}"

    user_id = session['user_id']
    user_scores = get_user_scores(user_id)

    # Fetch the sections associated with each unit
    for unit in unit_dict:
        cursor_topics.execute('SELECT * FROM sections WHERE unit_id = ?', (unit['id'],))
        sections = cursor_topics.fetchall()
        unit['sections'] = [dict(section) for section in sections]

        for section in unit['sections']:
            cursor_topics.execute('SELECT * FROM sub_sections WHERE section_id = ?', (section['id'],))
            sub_sections = cursor_topics.fetchall()
            section['sub_sections'] = [dict(sub_section) for sub_section in sub_sections]

    # Calculate unit score and maximum score
    for unit in unit_dict:
        unit_points = 0
        unit_maximum_points = 0
        for section in unit['sections']:
            section_points = sum(user_scores.get(str(sub_section['id']), 0) for sub_section in section['sub_sections'])
            section_maximum_points = sum(json.loads(sub_section['content']).get('no. of questions', 0) if sub_section['type'] == 'practice' else 0 for sub_section in section['sub_sections'])
            section['score'] = section_points
            section['maximum_score'] = section_maximum_points
            unit_points += section_points
            unit_maximum_points += section_maximum_points
        unit['score'] = unit_points
        unit['maximum_score'] = unit_maximum_points


    # Ensure progress is a number between 0 and 100
    for unit in unit_dict:
        unit['progress'] = (unit['score'] / unit['maximum_score']) * 100 if unit['maximum_score'] > 0 else 0


    cursor_topics.execute('SELECT * FROM sections WHERE unit_id = ?', (unit_current['id'],))
    sections_current = cursor_topics.fetchall()
    unit_current['sections'] = [dict(section) for section in sections_current]

    # Initialize section_current to an empty list
    section_current = []

    for section in unit_current['sections']:
        cursor_topics.execute('SELECT * FROM sub_sections WHERE section_id = ?', (section['id'],))
        sub_sections = cursor_topics.fetchall()
        section['sub_sections'] = [dict(sub_section) for sub_section in sub_sections]
        section_current.append(section)
    conn_topics.close()
    return render_template('content_template.html', level=level, topic_name=topic_name, unit_name=unit_name, unit_content=unit.get('content', 'N/A'), units=unit_dict, sections=sections, section_current=section_current, display_name=topic['display_name'], title=title, is_topic=False)
    

@app.route('/topic/<string:level>/<string:topic_name>/<string:unit_name>/<string:section_name>')
def section_detail(level, topic_name, unit_name, section_name):
    conn_topics = get_topics_db_connection()
    cursor_topics = conn_topics.cursor()

    conn_users = get_users_db_connection()
    cursor_users = conn_users.cursor()

    # Fetch the topic details
    cursor_topics.execute('SELECT * FROM topics WHERE level = ? AND name = ?', (level, topic_name))
    topic = cursor_topics.fetchone()

    if not topic:
        flash('Topic not found.', 'alert')
        conn_topics.close()
        conn_users.close()
        return redirect(url_for('home'))

    # Fetch the unit details
    cursor_topics.execute('SELECT * FROM units WHERE topic_id = ? AND name = ?', (topic['id'], unit_name))
    unit = cursor_topics.fetchone()

    if not unit:
        flash('Unit not found.', 'alert')
        conn_topics.close()
        conn_users.close()
        return redirect(url_for('topic_detail', level=level, topic_name=topic_name))

    # Fetch the section details
    cursor_topics.execute('SELECT * FROM sections WHERE unit_id = ? AND name = ?', (unit['id'], section_name))
    section = cursor_topics.fetchone()

    if not section:
        flash('Section not found.', 'alert')
        conn_topics.close()
        conn_users.close()
        return redirect(url_for('unit_detail', level=level, topic_name=topic_name, unit_name=unit_name))

    # Covert sqlite3.Row object to dictionary
    section = dict(section)
    

    section_content = section['content']
    title = f"{topic['display_name']} - {unit['display_name']} - {section['display_name']}"

    # Fetch the sub-sections associated with the section
    cursor_topics.execute('SELECT * FROM sub_sections WHERE section_id = ?', (section['id'],))
    sub_sections = cursor_topics.fetchall()

    # Convert sqlite3.Row objects to dictionaries
    sub_sections = [dict(sub_section) for sub_section in sub_sections]

    # Fetch user scores
    user_id = session['user_id']
    user_scores = get_user_scores(user_id)

    # Calculate section score and maximum score
    section_points = sum(user_scores.get(str(sub_section['id']), 0) for sub_section in sub_sections)
    section_maximum_points = sum(json.loads(sub_section['content']).get('no. of questions', 0) if sub_section['type'] == 'practice' else 0 for sub_section in sub_sections)
    section['score'] = section_points
    section['maximum_score'] = section_maximum_points
    section_display_name=section['display_name']
    print(section['maximum_score'])

    # Ensure progress is a number between 0 and 100
    section['progress'] = (section['score'] / section['maximum_score']) * 100 if section['maximum_score'] > 0 else 0

    conn_topics.close()
    conn_users.close()
    return render_template('section_template.html', level=level, topic_name=topic_name, unit_name=unit_name, section_name=section_name, section_content=section_content, sub_sections=sub_sections, section_display_name=section_display_name, title=title, is_section=True, sub_section_content=NotImplemented)

@app.route('/topic/<string:level>/<string:topic_name>/<string:unit_name>/<string:section_name>/<string:sub_section_name>')
def sub_section_detail(level, topic_name, unit_name, section_name, sub_section_name):
    conn_topics = get_topics_db_connection()
    cursor_topics = conn_topics.cursor()

    conn_users = get_users_db_connection()
    cursor_users = conn_users.cursor()

    # Fetch the topic details
    cursor_topics.execute('SELECT * FROM topics WHERE level = ? AND name = ?', (level, topic_name))
    topic = cursor_topics.fetchone()

    if not topic:
        flash('Topic not found.', 'alert')
        conn_topics.close()
        conn_users.close()
        return redirect(url_for('home'))

    # Fetch the unit details
    cursor_topics.execute('SELECT * FROM units WHERE topic_id = ? AND name = ?', (topic['id'], unit_name))
    unit = cursor_topics.fetchone()

    if not unit:
        flash('Unit not found.', 'alert')
        conn_topics.close()
        conn_users.close()
        return redirect(url_for('topic_detail', level=level, topic_name=topic_name))

    # Fetch the section details
    cursor_topics.execute('SELECT * FROM sections WHERE unit_id = ? AND name = ?', (unit['id'], section_name))
    section = cursor_topics.fetchone()

    if not section:
        flash('Section not found.', 'alert')
        conn_topics.close()
        conn_users.close()
        return redirect(url_for('unit_detail', level=level, topic_name=topic_name, unit_name=unit_name))

    
    # Fetch the sub-section details
    cursor_topics.execute('SELECT * FROM sub_sections WHERE section_id = ? AND name = ?', (section['id'], sub_section_name))
    sub_section = cursor_topics.fetchone()

    if not sub_section:
        flash('Sub-section not found.', 'alert')
        conn_topics.close()
        conn_users.close()
        return redirect(url_for('section_detail', level=level, topic_name=topic_name, unit_name=unit_name, section_name=section_name))

    cursor_topics.execute('SELECT * FROM sub_sections WHERE section_id = ?', (section['id'],))
    sub_sections = cursor_topics.fetchall()
    # Convert sqlite3.Row objects to dictionaries
    sub_section = dict(sub_section)
    sub_sections_list = [dict(sub_section) for sub_section in sub_sections]

    next_sub_section = None
    for i, sub_sec in enumerate(sub_sections_list):
        if sub_sec['name'] == sub_section_name and i + 1 < len(sub_sections_list):
            next_sub_section = sub_sections_list[i + 1]
            break

    sub_section_type = sub_section['type']
    sub_section_content = sub_section['content']
    if sub_section_type == 'practice':
        # Ensure sub_section_content is a dictionary
        if isinstance(sub_section_content, str):
            sub_section_content = json.loads(sub_section_content)


    section_display_name = section['display_name']
    sub_section_display_name = sub_section['display_name']
    title = f"{topic['display_name']} - {unit['display_name']} - {section['display_name']} - {sub_section['display_name']}"
    
    user_id = session['user_id']
    user_scores = get_user_scores(user_id)
    
    # Calculate sub-section score and maximum score
    sub_section_score = user_scores.get(str(sub_section['id']), 0)
    sub_section_maximum_score = sub_section_content.get('no. of questions', 0) if sub_section_type == 'practice' else 0

    sub_section_id = sub_section['id']


    if sub_section_type == 'practice':
        no_of_questions = sub_section_content.get('no. of questions', 0)
        questions = sub_section_content.get('questions', {})
        selected_questions = dict(random.sample(list(questions.items()), min(no_of_questions, len(questions))))
        sub_section_content['questions'] = selected_questions
        calculator = sub_section_content.get('calculator', False)
    else:
        calculator = False

    conn_topics.close()
    return render_template('section_template.html', level=level, topic_name=topic_name, unit_name=unit_name, section_name=section_name, sub_section_name=sub_section_name, sub_section_content=sub_section_content, sub_section_type=sub_section_type, section_display_name=section_display_name, sub_section_display_name=sub_section_display_name, title=title, sub_section_score=sub_section_score, sub_section_maximum_score=sub_section_maximum_score, sub_sections=sub_sections_list, sub_section_id=sub_section_id, calculator=calculator, is_section=False, next_sub_section=next_sub_section)


@app.route('/update_score', methods=['POST'])
def update_score():
    data = request.get_json()
    sub_section_id = data.get('sub_section_id')
    score = data.get('score')
    user_id = session['user_id']

    if sub_section_id is None or score is None:
        return jsonify({'success': False, 'message': 'Invalid data'}), 400

    update_user_score(user_id, sub_section_id, score)
    return jsonify({'success': True})

@app.route('/forum')
def forum():
    conn_forum = get_forum_db_connection()
    cursor_forum = conn_forum.cursor()
    
    conn_users = get_users_db_connection()
    cursor_users = conn_users.cursor()
    
    cursor_forum.execute('SELECT * FROM posts')
    posts = cursor_forum.fetchall()
    
    # Retrieve usernames for each post
    posts_with_usernames = []
    for post in posts:
        cursor_users.execute('SELECT username FROM users WHERE id = ?', (post['user_id'],))
        user = cursor_users.fetchone()
        post_with_username = dict(post)
        post_with_username['username'] = user['username'] if user else 'Unknown'
        post_with_username['created_at'] = datetime.fromisoformat(post['created_at']).astimezone(auckland_tz).strftime("%Y-%m-%dT%H:%M:%S")
        posts_with_usernames.append(post_with_username)
    
    conn_forum.close()
    conn_users.close()
    
    return render_template('forum.html', posts=posts_with_usernames)

@app.route('/forum/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        user_id = session['user_id']
        title = request.form['title']
        content = request.form['content']
        
        conn_forum = get_forum_db_connection()
        cursor_forum = conn_forum.cursor()
        cursor_forum.execute('''
            INSERT INTO posts (user_id, title, content)
            VALUES (?, ?, ?)
        ''', (user_id, title, content))
        conn_forum.commit()
        conn_forum.close()
        
        flash('Post created successfully!', 'success')
        return redirect(url_for('forum'))
    
    return render_template('create_post.html')

@app.route('/forum/post/<int:post_id>')
def view_post(post_id):
    conn_forum = get_forum_db_connection()
    cursor_forum = conn_forum.cursor()
    
    conn_users = get_users_db_connection()
    cursor_users = conn_users.cursor()
    
    cursor_forum.execute('SELECT * FROM posts WHERE id = ?', (post_id,))
    post = cursor_forum.fetchone()
    

    
    # Retrieve username for the post
    cursor_users.execute('SELECT username FROM users WHERE id = ?', (post['user_id'],))
    user = cursor_users.fetchone()

    post = dict(post) if user else 'Unknown'
    post['username'] = user['username']
    post['created_at'] = datetime.fromisoformat(post['created_at']).astimezone(auckland_tz).strftime("%Y-%m-%dT%H:%M:%S")

    # Parse comments from JSON string
    comments = json.loads(post['comments']) if post['comments'] else []
    for comment in comments:
        cursor_users.execute('SELECT username FROM users WHERE id = ?', (comment['user_id'],))
        user = cursor_users.fetchone()
        comment['username'] = user['username'] if user else 'Unknown'
        comment['created_at'] = datetime.fromisoformat(comment['created_at']).astimezone(auckland_tz).strftime("%Y-%m-%dT%H:%M:%S")
    
    conn_forum.close()
    conn_users.close()

    return render_template('view_post.html', post=post, comments=comments)


@app.route('/forum/post/<int:post_id>/add_comment', methods=['POST'])
@login_required
def add_comment(post_id):
    user_id = session['user_id']
    title = request.form['title']
    content = request.form['content']

    conn_forum = get_forum_db_connection()
    cursor_forum = conn_forum.cursor()
    cursor_forum.execute('SELECT comments FROM posts WHERE id = ?', (post_id,))
    post = cursor_forum.fetchone()

    # Ensure comments is a list
    try:
        comments = json.loads(post['comments']) if post['comments'] else []
        if not isinstance(comments, list):
            comments = []
    except json.JSONDecodeError:
        comments = []

    new_comment = {
        'id': len(comments) + 1,
        'user_id': user_id,
        'title': title,
        'content': content,
        'created_at': datetime.now().isoformat()
    }
    comments.append(new_comment)

    # Update the comments column with the new JSON string
    cursor_forum.execute('''
        UPDATE posts
        SET comments = ?
        WHERE id = ?
    ''', (json.dumps(comments), post_id))
    conn_forum.commit()
    conn_forum.close()

    flash('Comment added successfully!', 'success')
    return redirect(url_for('view_post', post_id=post_id))



if __name__ == '__main__':
    app.run(debug=True)