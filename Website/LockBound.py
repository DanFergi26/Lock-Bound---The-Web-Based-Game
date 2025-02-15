#imports
from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for sessions

@app.route('/')
def home():

@app.route('/account/<username>')
def account(username):
    # Ensure user database exists
    if not os.path.exists(USER_FILE):
        return "User database not found", 404

    # Load user data from file
    df = pd.read_excel(USER_FILE)
    user = df[df['username'] == username]

    if user.empty:
        return "User not found", 404
        
    # Get user data as a dictionary
    user_info = user.iloc[0].to_dict()  
                    
                    
    user_id = get_user_id(username)
    if user_id is None:
        return "User not found", 404

    # Load user details
    df = pd.read_excel(USER_FILE)
    user = df[df['username'] == username]
    user_info = user.iloc[0].to_dict() 

    return render_template('account.html', user_info=user_info)