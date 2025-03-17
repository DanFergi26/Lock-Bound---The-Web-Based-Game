from flask import Flask, request, redirect, url_for, flash, session, render_template, send_from_directory
from flask_sqlalchemy import SQLAlchemy  # Ensure Flask-SQLAlchemy is installed
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
import os
import csv


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for sessions

# Ensure instance directory exists
INSTANCE_DIR = os.path.join(os.path.dirname(__file__), "instance")
PROPIC_DIR = os.path.join(os.path.dirname(__file__), "profile_pics")
os.makedirs(INSTANCE_DIR, exist_ok=True)
os.makedirs(PROPIC_DIR, exist_ok=True)
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
    surname = db.Column(db.String(50), nullable=False)
    forename = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # Store full hash
    profile_pic = db.Column(db.String(255), nullable=True)

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')
        
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)


@app.route('/profile_pics/<filename>')
def profile_pics(filename):
    return send_from_directory(os.path.join(app.root_path, 'profile_pics'), filename)
    
    
@app.route("/inventory", methods=["GET", "POST"])
def inventory():
    return render_template('inv.html')
    
@app.route("/minigames", methods=["GET", "POST"])
def minigames():    
    return render_template('minigames.html')
    
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    message = None

    # Gather login data
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']  # Fixed typo in password field

        # Query the database for the user
        user = User.query.filter_by(username=username).first()

        if not user:
            message = "Account doesn't exist"
        elif not user.check_password(password):  # Ensure password is checked correctly with bcrypt
            message = "The password is incorrect"
        else:
            # Set session login status and store user info in session
            session['logged_in'] = True
            session['username'] = username
            session['profile_pic'] = user.profile_pic if user.profile_pic else "profile_pics/default_pfp.png"

            # Redirect to the home page after login
            return redirect(url_for('home'))

    return render_template("home.html", message=message)
    
    
@app.route('/logout')
def logout():
    # Remove the user from the session
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('profile_pic', None)
    
    # Redirect to the home page after logging out
    return redirect(url_for('home'))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    with app.app_context():
        db.create_all()

    if request.method == "POST":
        # Handle profile picture upload
        profile_pic = request.files.get("propic")
        pic_filename = None
        
        if profile_pic and profile_pic.filename:
            # Secure the filename to prevent directory traversal
            pic_filename = secure_filename(profile_pic.filename)
            
            # Define the directory where the profile pictures will be stored
            profile_pics_folder = os.path.join(app.root_path, 'profile_pics')
            
            # Ensure the folder exists
            if not os.path.exists(profile_pics_folder):
                os.makedirs(profile_pics_folder)
            
            # Save the profile picture with just the filename
            profile_pic.save(os.path.join(profile_pics_folder, pic_filename))
        
        # Get other form data
        username = request.form["username"]
        surname = request.form["surname"]
        forename = request.form["forename"]
        email = request.form["email"]
        password = request.form["password"]
        repassword = request.form["repassword"]

        # Check if user or email already exists
        existing_user = User.query.filter_by(username=username).first()
        existing_email = User.query.filter_by(email=email).first()

        # Flash messages for validation errors
        if existing_user:
            flash("Username already exists. Please choose a different username.")
        elif existing_email:
            flash("Email already exists. Please use a different email.")
        elif len(password) < 8:
            flash("Password must be at least 8 characters long.")
        elif password != repassword:
            flash("Passwords must be the same!")
        else:
            # Create a new user and store the filename (not the full path)
            user = User(username=username, surname=surname, forename=forename, email=email, profile_pic=pic_filename)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            return redirect(url_for("login"))
    
    return render_template("signup.html")

@app.route('/posts')
def posts():
    # Code to handle the 'posts' endpoint
    return 'This is the posts page'
    


def read_csv():
    csv_path = os.path.join(os.path.dirname(__file__), "instance", "edClarkCsv.csv")


    books = []
    try:
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            headers = next(reader)  # Read the first row as headers


            for row in reader:
                if len(row) < 7:
                    continue
                
                title = row[4].strip()
                image = row[1].strip()
                image2 = row[2].strip() 
                image3 = row[3].strip()
                info = row[5].strip()
                info2 = row[6].strip()

                if title:
                    book = {
                        'title': title,
                        'image': image,
                        'image2': image2,
                        'image3': image3,
                        'info': info,
                        'info2': info2,
                    }
                    books.append(book)


    except FileNotFoundError:
        print("CSV file not found.")
    except Exception as e:
        print(f"Error reading CSV: {e}")

    return books


@app.route("/")
def home():
    return render_template(
        "home.html",
        logged_in=session.get("logged_in", False),
        username=session.get("username"),
        profile_pic=session.get("profile_pic"),
    )
    
@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("q", "").lower().strip()
    all_books = read_csv()
    filtered_books = [
        book for book in all_books
        if query in book.get('title', '').lower() or query in book.get('description', '').lower()
    ]
    return render_template("search.html", books=filtered_books, search_query=query)

@app.route('/wiki/<title>')
def wiki(title):
    books = read_csv()  # Load books from CSV

    # Debugging: Print all book titles to verify they match correctly
    print("Requested title:", title)
    print("Available titles:", [book['title'] for book in books])

    # Find the book by title (case-insensitive, trimmed)
    book_info = next((book for book in books if book['title'].strip().lower() == title.strip().lower()), None)

    if not book_info:
        print(f"No book found for title: {title}")  # Debugging
        return "Page not found", 404

    print("Book found:", book_info)  # Debugging

    return render_template('wiki.html', book_info=book_info)
    
    
# Run the app
if __name__ == '__main__':
    app.run(debug=True)
