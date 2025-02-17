from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import flask_sqlalchemy
import flask_bcrypt 
# might want to use flash to give incorrect password messages 
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for sessions

DB_FILE = 'users.db'
CLARK_FILE = 'clark.db'
PROFILE_PIC_FOLDER = 'profile_pics'
os.makedirs(PROFILE_PIC_FOLDER, exist_ok=True)

# Initialize database
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                surname TEXT NOT NULL,
                forename TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                profile_pic TEXT
            )
        ''')
        conn.commit()

init_db()

@app.route('/')
def home():
    return render_template('login.html')

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        # queries the database for a user with the given username
        user = User.query.filter_by(username=username).first()
        # uses check_password from the bcrypt library to check if the password is correct compared to hashed version
        if user and user.check_password(password):
            session["user_id"] = user.id # used to monitor sessions activity
            return redirect(url_for("posts"))
        else:
            # shows an error if invalid login credentials
            flash("Invalid username or password. Please try again.")
    return render_template("login.html")

@app.route('/signup', methods=['GET', 'POST'])
def signup_form():
    if request.method == 'POST':
        # Handle profile picture upload
        profile_pic = request.files['propic']
        profile_pic_path = None
        if profile_pic:
            pic_filename = profile_pic.filename
            profile_pic_path = os.path.join(PROFILE_PIC_FOLDER, pic_filename)
            profile_pic.save(profile_pic_path)

        # Gather other form data
        username = request.form['uname']
        password = request.form['pass']
        surname = request.form['surname']
        forename = request.form['forename']
        email = request.form['email']

        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            # Check if username already exists
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                message = "Username already exists"
                return render_template('signup.html', message=message)

            # Insert new user
            cursor.execute('''
                INSERT INTO users (username, password, surname, forename, email, profile_pic)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (username, password, surname, forename, email, profile_pic_path))
            conn.commit()

        # Redirect to home page after signup
        return redirect(url_for('home'))

    return render_template('signup.html')

@app.route('/account/<username>')
def account(username):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

    if not user:
        return "User not found", 404

    user_info = {
        'id': user[0],
        'username': user[1],
        'password': user[2],
        'surname': user[3],
        'forename': user[4],
        'email': user[5],
        'profile_pic': user[6]
    }

    return render_template('account.html', user_info=user_info)

if __name__ == '__main__':
    app.run(debug=True)

    
    
    