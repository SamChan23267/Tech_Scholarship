from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__, template_folder='templates')
app.secret_key = 'your_secret_key'  # Needed for session management

# Dummy user data for demonstration purposes
users = {
    'user@example.com': {
        'password': 'password123',
        'first_name': 'John',
        'last_name': 'Doe'
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
            password = request.form.get('password')
            first_name = request.form.get('first name')
            last_name = request.form.get('last name')
            print(f"Signup form data: {email}, {password}, {first_name}, {last_name}")
            if email in users:
                flash('Email already exists. Please log in.')
                return redirect(url_for('auth', action='login'))
            users[email] = {'password': password, 'first_name': first_name, 'last_name': last_name}
            flash('Signup successful! Please log in.')
            return redirect(url_for('auth', action='login'))
        else:
            email = request.form.get('email')
            password = request.form.get('password')
            print(f"Login form data: {email}, {password}")
            user = users.get(email)
            if user and user['password'] == password:
                session['user'] = email
                return redirect(url_for('user_home'))
            return redirect(url_for('auth', action='login'))
    return render_template('auth.html', action=action)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)