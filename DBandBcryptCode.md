# you will need to create a virtual enviroment first for the web app and then use an import flask statement as shown in last years adv web dev course practical book


# these statements need to be done within the folder of the venve or .py file on your command line! 
(
# bash code to download sql
pip install flask-sqlalchemy
# bash code to download bcrypt (for password encryption)
pip install flask-bcrypt
)


### THESE GO IN .PY FILE ###

# flask import statement
from flask import Flask
# sql import statement for app.py 
from flask_sqlalchemy import SQLAlchemy
# encryption import statement for app.py
from flask_bcrypt import Bcrypt 

# code for database creation 
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(os.path.dirname(__file__), "instance", "users.db")

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# initialises database 
db = SQLAlchemy(app)

# initialises bcrypt to app 
bcrypt = Bcrypt(app)

# sample code used to create a simple class holding a users information
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(8), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

# another example of sqlalchemy class creation:
class Post(db.Model):
    postID = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='posts', lazy=True)

# bcrypt statements for hashing passwords: 
def set_password(self, password):
# generates a hashed version of the password using bcrypt, 
# then stores it in the password attribute of user table within the database 
    self.password = bcrypt.generate_password_hash(password).decode('utf-8')
        
def check_password(self, password):
# checks if the password matches the hashed password stored in the database
# returns true or false
    return bcrypt.check_password_hash(self.password, password)


# statement used to create the database and all the aforementioned classes (please note that all classes should be defined before this statement, any after will not work)
with app.app_context():
    db.create_all()