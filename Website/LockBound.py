from flask import Flask, request, redirect, url_for, flash, session, render_template, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
import os
import csv
import sys

app = Flask(__name__)
app.secret_key = 'your_secret_key'

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
    password = db.Column(db.String(255), nullable=False)
    profile_pic = db.Column(db.String(255), nullable=True)

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')
        
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

# Define UserInventory model for unlock states
class UserInventory(db.Model):
    __tablename__ = 'UserInventory'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    # One boolean column per inventory item
    a_record_of_the_black_prince = db.Column(db.Boolean, default=False)
    oxford_lectern_bible = db.Column(db.Boolean, default=False)
    bassandyne_bible = db.Column(db.Boolean, default=False)
    plantin_bible = db.Column(db.Boolean, default=False)
    doves_bible = db.Column(db.Boolean, default=False)
    baskerville_bible = db.Column(db.Boolean, default=False)
    gutenberg_bible_leaf = db.Column(db.Boolean, default=False)
    uncle_tom_s_cabin = db.Column(db.Boolean, default=False)
    autotypography = db.Column(db.Boolean, default=False)
    kelmscott_chaucer = db.Column(db.Boolean, default=False)
    nuremberg_chronicle = db.Column(db.Boolean, default=False)
    lizars_atlas = db.Column(db.Boolean, default=False)
    book_of_hours_dutch_manuscript = db.Column(db.Boolean, default=False)

@app.route('/profile_pics/<filename>')
def profile_pics(filename):
    return send_from_directory(os.path.join(app.root_path, 'profile_pics'), filename)

# Load items from CSV and generate keys
def load_items_from_csv():
    csv_path = os.path.join(os.path.dirname(__file__), "instance", "edClarkCsv.csv")
    print(f"Loading CSV from: {csv_path}", file=sys.stderr)
    items = []

    if not os.path.exists(csv_path):
        print(f"Error: CSV file does not exist at {csv_path}", file=sys.stderr)
        return items

    try:
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip the header row
            for row in reader:
                if len(row) < 5:
                    print(f"Skipping row due to insufficient columns: {row}", file=sys.stderr)
                    continue
                
                item = {
                    'id': row[0].strip(),
                    'title': row[4].strip() if len(row) > 4 else "Unnamed",
                    'image': row[1].strip() if len(row) > 1 else "",
                    'key': row[4].strip().lower().replace(' ', '_').replace('-', '_') if len(row) > 4 else "unnamed"
                }
                
                if not item['image']:
                    print(f"Warning: No image for item {item['title']} (ID: {item['id']})", file=sys.stderr)
                else:
                    item['image'] = f"ecPhotos/{item['image']}"
                    full_path = os.path.join(app.static_folder, item['image'])
                    if not os.path.exists(full_path):
                        print(f"Image file not found: {full_path}", file=sys.stderr)
                    else:
                        print(f"Image file exists: {full_path}", file=sys.stderr)
                
                items.append(item)
                print(f"Loaded item: {item}", file=sys.stderr)
    
    except Exception as e:
        print(f"Error reading CSV: {e}", file=sys.stderr)
    
    return items

@app.route("/inventory", methods=["GET"])
def inventory():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    # Load all items from CSV
    all_items = load_items_from_csv()
    if not all_items:
        flash("No items found in the inventory CSV.")
        return render_template('inv.html', items=[])
    
    # Get the current user
    user = User.query.filter_by(username=session.get('username')).first()
    if not user:
        flash("User not found. Please log in again.")
        return redirect(url_for('login'))
    
    # Get or create the user's inventory record
    user_inventory = UserInventory.query.filter_by(user_id=user.id).first()
    if not user_inventory:
        user_inventory = UserInventory(user_id=user.id)
        db.session.add(user_inventory)
        db.session.commit()
    
    # Add unlock status to each item
    for item in all_items:
        item_key = item['key']
        item['unlocked'] = getattr(user_inventory, item_key, False)
    
    return render_template('inv.html', items=all_items)
    
@app.route('/add_item/<title>')
def add_item(title):
    books = read_csv()
    print("Requested title:", title)
    print("Available titles:", [book['title'] for book in books])
    book_info = next((book for book in books if book['title'].strip().lower() == title.strip().lower()), None)
    if not book_info:
        print(f"No book found for title: {title}")
        return "Page not found", 404
    print("Book found:", book_info)
    return render_template('add2inv.html', book_info=book_info)
        
@app.route('/unlock/<item_key>', methods=['POST'])
def unlock_item(item_key):
    if not session.get('logged_in'):
        return redirect(url_for('signup'))
    
    # Get the current user
    user = User.query.filter_by(username=session.get('username')).first()
    if not user:
        flash("User not found. Please log in again.")
        return redirect(url_for('login'))
    
    # Get the user's inventory record
    user_inventory = UserInventory.query.filter_by(user_id=user.id).first()
    if not user_inventory:
        user_inventory = UserInventory(user_id=user.id)
        db.session.add(user_inventory)
    
    # Validate item_key
    valid_keys = [
        'a_record_of_the_black_prince', 'oxford_lectern_bible', 'bassandyne_bible',
        'plantin_bible', 'doves_bible', 'baskerville_bible', 'gutenberg_bible_leaf',
        'uncle_tom_s_cabin', 'autotypography', 'kelmscott_chaucer', 'nuremberg_chronicle',
        'lizars_atlas', 'book_of_hours_dutch_manuscript'
    ]
    if item_key not in valid_keys:
        flash("Invalid item key.")
        return redirect(url_for('inventory'))
    
    if hasattr(user_inventory, item_key):
        setattr(user_inventory, item_key, True)
        db.session.commit()
        flash(f"Item {item_key.replace('_', ' ').title()} has been unlocked!")
    else:
        flash("Invalid item key.")
    
    return redirect(url_for('inventory'))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    with app.app_context():
        db.create_all()  # Create tables if they don't exist

    if request.method == "POST":
        profile_pic = request.files.get("propic")
        pic_filename = None
        
        if profile_pic and profile_pic.filename:
            pic_filename = secure_filename(profile_pic.filename)
            profile_pics_folder = os.path.join(app.root_path, 'profile_pics')
            if not os.path.exists(profile_pics_folder):
                os.makedirs(profile_pics_folder)
            profile_pic.save(os.path.join(profile_pics_folder, pic_filename))
        
        username = request.form["username"]
        surname = request.form["surname"]
        forename = request.form["forename"]
        email = request.form["email"]
        password = request.form["password"]
        repassword = request.form["repassword"]

        existing_user = User.query.filter_by(username=username).first()
        existing_email = User.query.filter_by(email=email).first()

        if existing_user:
            flash("Username already exists. Please choose a different username.")
        elif existing_email:
            flash("Email already exists. Please use a different email.")
        elif len(password) < 8:
            flash("Password must be at least 8 characters long.")
        elif password != repassword:
            flash("Passwords must be the same!")
        else:
            user = User(username=username, surname=surname, forename=forename, email=email, profile_pic=pic_filename)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            # Create a UserInventory record for the new user
            user_inventory = UserInventory(user_id=user.id)
            db.session.add(user_inventory)
            db.session.commit()

            return redirect(url_for("login"))
    
    return render_template("signup.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    message = None

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if not user:
            message = "Account doesn't exist"
        elif not user.check_password(password):
            message = "The password is incorrect"
        else:
            session['logged_in'] = True
            session['username'] = username
            session['profile_pic'] = user.profile_pic if user.profile_pic else "profile_pics/default_pfp.png"
            return redirect(url_for('home'))

    return render_template("home.html", message=message)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('profile_pic', None)
    return redirect(url_for('home'))

@app.route('/account')
def account():
    return render_template("account.html")

@app.route('/posts')
def posts():
    return 'This is the posts page'

@app.route('/aboutus')
def aboutus():
    return render_template('aboutus.html')

@app.route("/minigames", methods=["GET", "POST"])
def minigames():    
    return render_template('minigames.html')

@app.route("/minigames/wordle", methods=["GET", "POST"])
def wordle():    
    return render_template('wordle.html')

@app.route("/minigames/connections", methods=["GET", "POST"])
def connections():    
    return render_template('connections.html')

def read_csv():
    csv_path = os.path.join(os.path.dirname(__file__), "instance", "edClarkCsv.csv")
    books = []
    try:
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            headers = next(reader)
            for row in reader:
                if len(row) < 8:
                    continue
                title = row[4].strip()
                image = row[1].strip()
                image2 = row[2].strip() 
                image3 = row[3].strip()
                info = row[5].strip()
                info2 = row[6].strip()
                riddle = row[7].strip()
                if title:
                    book = {
                        'title': title,
                        'image': image,
                        'image2': image2,
                        'image3': image3,
                        'info': info,
                        'info2': info2,
                        'riddle': riddle
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

    # Riddle answers and their corresponding book titles
    riddle_redirects = {
        "the bible": "A RECORD OF THE BLACK PRINCE",
        "a book": "OXFORD LECTERN BIBLE",
        "typeface": "BASSANDYNE BIBLE",
        "johannes gutenberg": "PLANTIN BIBLE",
        "typography": "DOVES BIBLE",
        "edward clark collection": "BASKERVILLE BIBLE",
        "bookbinding": "GUTENBERG BIBLE LEAF",
        "a written word": "UNCLE TOM'S CABIN",
        "novel": "AUTOTYPOGRAPHY",
        "scripture": "KELMSCOTT CHAUCER"
    }

    # Check if query matches any riddle key
    if query in riddle_redirects:
        return redirect(url_for("add_item", title=riddle_redirects[query]))

    # Default behavior: filter books from CSV
    all_books = read_csv()
    filtered_books = [
        book for book in all_books
        if query in book.get('title', '').lower() or query in book.get('description', '').lower()
    ]
    return render_template("search.html", books=filtered_books, search_query=query)




@app.route('/wiki/<title>')
def wiki(title):
    books = read_csv()
    print("Requested title:", title)
    print("Available titles:", [book['title'] for book in books])
    book_info = next((book for book in books if book['title'].strip().lower() == title.strip().lower()), None)
    if not book_info:
        print(f"No book found for title: {title}")
        return "Page not found", 404
    print("Book found:", book_info)
    return render_template('wiki.html', book_info=book_info)

@app.route('/wiki')
def wikipage():
    books = read_csv()
    if not books:
        return "No books found", 404
    return render_template('wikipage.html', books=books)
    



# Run the app
if __name__ == '__main__':
    app.run(debug=True)