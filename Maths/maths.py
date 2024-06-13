from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__, template_folder='templates')
app.secret_key = 'your_secret_key'  # Needed for session management

# Dummy user data for demonstration purposes
users = {
    'user@example.com': {
        'password': 'password123',
        'username': 'user'
    }
}

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
            if email in users:
                flash('Email already exists. Please log in.', 'alert')
                return redirect(url_for('auth', action='login'))
            if username in users:
                flash('Username already exist. Please try another username', 'alert')
            users[email] = {'password': password, 'username': username}
            flash('Signup successful! Please log in.', 'success')
            print(users)
            return redirect(url_for('auth', action='login'))
        else:
            email = request.form.get('email')
            password = request.form.get('password')
            if email not in users:
                flash('Email not found. Please sign up.', 'alert')
                return redirect(url_for('auth', action='signup'))
            print(f"Login form data: {email}, {password}")
            user = users.get(email)
            if user and user['password'] == password:
                session['user'] = email
                return redirect(url_for('user_home'))
            flash('Invalid credentials. Please try again.', 'alert')
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