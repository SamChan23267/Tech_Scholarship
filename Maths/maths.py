from flask import Flask, render_template, request

app = Flask(__name__, template_folder='templates')

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/auth.html')
def auth():
    action = request.args.get('action', 'login')  # Default action is 'login'
    if action == 'signup':
        # Render the signup page or section
        return render_template('auth.html', action='signup')
    else:
        # Render the login page or section
        return render_template('auth.html', action='login')


if __name__ == '__main__':
    app.run(debug=True)
