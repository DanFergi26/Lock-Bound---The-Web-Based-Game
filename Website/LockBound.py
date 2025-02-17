from flask import Flask, request, redirect, url_for, flash, session, render_template
import sqlite3
from flask_sqlalchemy import SQLAlchemy # remember to download flask-sqlalchemy on server of deployment
from flask_bcrypt import Bcrypt
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for sessions

db = 'users.db'
#os.makedirs(PROFILE_PIC_FOLDER, exist_ok=True)

# secret key used for session management
app.config["SECRET_KEY"] = "gb2576eetc445"

# database code for the create account and login page
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(os.path.dirname(__file__), "instance", "users.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

#initialiseas database
db = SQLAlchemy(app) 

# create the database file if it doesn't exist
with app.app_context():
    if not os.path.exists(os.path.join(os.path.dirname(__file__), "instance", "users.db")):
        db.create_all()

# decleration used for database table security/encryption
bcrypt = Bcrypt(app)

# creates a class within databse called User which contains the user id, username, password,
# and a timestamp (created_at) attribute
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(8), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # uses the bcrypt library   
    def set_password(self, password):
        # generates a hashed version of the password using bcrypt, 
        # then stores it in the password attribute of user table within the database 
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')
        
    def check_password(self, password):
        # checks if the password matches the hashed password stored in the database
        # returns true or false
        return bcrypt.check_password_hash(self.password, password)
    





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
        birth = request.form['birth']

        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            # Check if username already exists
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                message = "Username already exists"
                return render_template('signup.html', message=message)

            # Insert new user
            cursor.execute('''
                INSERT INTO users (username, password, surname, forename, email, birth, profile_pic)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (username, password, surname, forename, email, birth, profile_pic_path))
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
        'birth': user[6],
        'profile_pic': user[7]
    }

    return render_template('account.html', user_info=user_info)

# used for removing the database file and dropping all the tables 
#if not os.path.exists(os.path.join(os.path.dirname(__file__), "instance", "users.db")):
#        db.drop_all()

if __name__ == '__main__':
    app.run(debug=True)

    
    
    