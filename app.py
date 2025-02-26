from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_cors import CORS
import os
from pathlib import Path

app = Flask(__name__)
CORS(app)

# Configure MongoDB securely
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
if not app.config["MONGO_URI"]:
    raise ValueError("MONGO_URI environment variable not set")

mongo = PyMongo(app)

# Secure Secret Key
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
if not app.config['SECRET_KEY']:
    raise ValueError("SECRET_KEY environment variable not set")

UPLOAD_FOLDER = "static/uploads"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)

# Test MongoDB connection
try:
    mongo.cx.server_info()
    print("MongoDB connected successfully!")
except Exception as e:
    print("MongoDB Connection Error:", e)
    exit(1)

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

        if mongo.db.users.find_one({'email': email}):
            flash("Email already registered!", "danger")
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password)
        mongo.db.users.insert_one({'username': username, 'email': email, 'password': hashed_password})
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = mongo.db.users.find_one({'email': email})

        if user and check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password!", "danger")
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        notes = mongo.db.notes.find()
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
        
        mongo.db.notes.insert_one({'filename': filename, 'path': str(filepath)})
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
