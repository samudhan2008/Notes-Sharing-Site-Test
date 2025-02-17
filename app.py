import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable is not set!")

client = MongoClient(MONGO_URI)
db = client["notes"]
users_collection = db["users"]
notes_collection = db["notes"]

# Flask-Login setup
login_manager = LoginManager(app)
login_manager.login_view = "login"

# Password hashing
bcrypt = Bcrypt(app)

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data["_id"])  # Ensure ID is stored as a string
        self.email = user_data["email"]

@login_manager.user_loader
def load_user(user_id):
    """Fetch user from MongoDB using ObjectId."""
    user_data = users_collection.find_one({"_id": ObjectId(user_id)})
    return User(user_data) if user_data else None

@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    if not os.path.exists("templates/dashboard.html"):
        return "dashboard.html is missing. Please add it to the templates folder.", 500
    return render_template("dashboard.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        if users_collection.find_one({"email": email}):
            flash("Email already registered. Please log in.", "warning")
            return redirect(url_for("login"))

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        users_collection.insert_one({"email": email, "password": hashed_password})

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user_data = users_collection.find_one({"email": email})

        if user_data and bcrypt.check_password_hash(user_data["password"], password):
            login_user(User(user_data))
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!", "info")
    return redirect(url_for("login"))

# File Upload Handling
UPLOAD_FOLDER = "uploaded_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/upload')
@login_required
def upload_page():
    return render_template('upload.html')

@app.route('/notes')
@login_required
def notes_page():
    notes = notes_collection.find({}, {"_id": 0, "filename": 1})
    return render_template('notes.html', notes=notes)

@app.route('/api/upload-file', methods=['POST'])
@login_required
def upload_file():
    try:
        if 'file' not in request.files:
            return render_template("upload_result.html", message="No file part", success=False)

        file = request.files['file']
        if file.filename == '':
            return render_template("upload_result.html", message="No selected file", success=False)

        filename = file.filename
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        file.save(file_path)

        notes_collection.insert_one({"filename": filename, "filepath": file_path})

        return render_template("upload_result.html", message="File uploaded successfully", success=True)

    except Exception as e:
        return render_template("upload_result.html", message=f"Error: {str(e)}", success=False)

@app.route('/api/download/<filename>', methods=['GET'])
@login_required
def download_file(filename):
    try:
        note = notes_collection.find_one({"filename": filename})
        if not note:
            return jsonify({"error": "File not found"}), 404

        file_path = note['filepath']
        if not os.path.exists(file_path):
            return jsonify({"error": "File does not exist on the server"}), 404

        return send_file(file_path, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
