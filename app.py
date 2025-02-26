from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_cors import CORS
import os
import secrets
from pathlib import Path

app = Flask(__name__)
CORS(app)

# Configure MongoDB securely
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
if not app.config["MONGO_URI"]:
    raise ValueError("MONGO_URI environment variable not set")

mongo = PyMongo()
try:
    mongo.init_app(app)
    mongo.cx.server_info()
    print("MongoDB connected successfully!")
    # Access the database
    db = mongo.cx["Site"]
except Exception as e:
    print("MongoDB Connection Error:", e)
    mongo = None
    db = None

# Secure Secret Key
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", secrets.token_hex(16))

UPLOAD_FOLDER = "static/uploads"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {"pdf"}

def allowed_file(filename):
    return Path(filename).suffix[1:].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if db is not None and db.users.find_one({'email': email}):
            flash("Email already registered!", "danger")
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password)
        if db is not None:
            db.users.insert_one({'username': username, 'email': email, 'password': hashed_password})
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        print(f"DB is None: {db is None}")
        print(f"Email: {email}")

        if db is not None:
            user = db.users.find_one({'email': email})
            print(f"User Found: {user}")
        else:
            flash("Database connection error. Please try again later.", "danger")
            return redirect(url_for('login'))

        if user and 'password' in user:
            print(f"Checking Password for {user['email']}")
            if check_password_hash(user['password'], password):
                session['user_id'] = str(user['_id'])
                flash("Login successful!", "success")
                return redirect(url_for('dashboard'))
            else:
                print("Password mismatch!")
        else:
            print("User not found!")

        flash("Invalid email or password!", "danger")
        return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        if db is not None:
            notes = db.notes.find()
        else:
            notes = []
        return render_template('dashboard.html', notes=notes)
    
    flash("Please log in first!", "warning")
    return redirect(url_for('login'))

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash("No file part!", "danger")
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash("No selected file!", "warning")
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = Path(app.config['UPLOAD_FOLDER']) / filename
        file.save(filepath)
        
        if db is not None:
            db.notes.insert_one({'filename': filename, 'path': str(filepath)})
        flash("File uploaded successfully!", "success")
        return redirect(url_for('dashboard'))
    
    flash("Invalid file format. Only PDFs are allowed.", "danger")
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
