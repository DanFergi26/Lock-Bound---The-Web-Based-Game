from flask import Flask, request, redirect, url_for, flash, session, render_template
from flask_sqlalchemy import SQLAlchemy  # Ensure Flask-SQLAlchemy is installed
from flask_bcrypt import Bcrypt
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for sessions

# Ensure instance directory exists
INSTANCE_DIR = os.path.join(os.path.dirname(__file__), "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)
DB_FILE = os.path.join(INSTANCE_DIR, "users.db")

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_FILE}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database and bcrypt
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Define User model
class User(db.Model):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # Store full hash

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')
        
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

# Routes
@app.route('/')
def home():
    return render_template('login.html')

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            return redirect(url_for("posts"))  # Ensure 'posts' route exists
        else:
            flash("Invalid username or password. Please try again.")
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    with app.app_context():
        db.create_all()
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists. Please choose a different username.")
        elif len(password) < 8:
            flash("Password must be at least 8 characters long.")
        else:
            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            return redirect(url_for("login"))
    return render_template("signup.html")

@app.route('/posts')
def posts():
    # Code to handle the 'posts' endpoint
    return 'This is the posts page'

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
