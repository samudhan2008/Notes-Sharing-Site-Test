from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from database import mongo
import os

app_routes = Blueprint("app_routes", __name__)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app_routes.route("/")
def home():
    return render_template("index.html")

@app_routes.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        if mongo.db.users.find_one({"email": email}):
            flash("Email already exists!", "danger")
            return redirect(url_for("app_routes.register"))

        mongo.db.users.insert_one({"username": username, "email": email, "password": password})
        flash("Registration successful!", "success")
        return redirect(url_for("app_routes.login"))

    return render_template("register.html")

@app_routes.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = mongo.db.users.find_one({"email": email})

        if user and user["password"] == password:
            flash("Login successful!", "success")
            return redirect(url_for("app_routes.home"))

        flash("Invalid credentials!", "danger")

    return render_template("login.html")

@app_routes.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part!", "danger")
            return redirect(request.url)

        file = request.files["file"]

        if file.filename == "":
            flash("No selected file!", "danger")
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            mongo.db.notes.insert_one({"filename": filename})
            flash("File uploaded successfully!", "success")
            return redirect(url_for("app_routes.home"))

        flash("Only PDF files are allowed!", "danger")

    return render_template("upload.html")
