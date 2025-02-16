import os
from flask import Flask, render_template, redirect, url_for, flash
from flask_dance.contrib.github import make_github_blueprint, github
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# GitHub OAuth
github_bp = make_github_blueprint(client_id=os.getenv("GITHUB_CLIENT_ID"),
                                  client_secret=os.getenv("GITHUB_CLIENT_SECRET"))
app.register_blueprint(github_bp, url_prefix="/login")

# MongoDB Connection
client = MongoClient(os.getenv("MONGO_URI"))
db = client["notes_sharing"]
users_collection = db["users"]
notes_collection = db["notes"]

# Flask-Login setup
login_manager = LoginManager(app)
login_manager.login_view = "github.login"

# Admin User ID (Replace with your GitHub ID)
ADMIN_USER_ID = "samudhan2008"

class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data["_id"]
        self.username = user_data["username"]
        self.email = user_data.get("email", "")

@login_manager.user_loader
def load_user(user_id):
    user_data = users_collection.find_one({"_id": user_id})
    return User(user_data) if user_data else None

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/login/github")
def login():
    if not github.authorized:
        return redirect(url_for("github.login"))

    resp = github.get("/user")
    user_info = resp.json()

    user_data = {
        "_id": str(user_info["id"]),
        "username": user_info["login"],
        "email": user_info.get("email", ""),
    }

    users_collection.update_one({"_id": user_data["_id"]}, {"$set": user_data}, upsert=True)
    login_user(User(user_data))
    return redirect(url_for("home"))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

@app.route("/admin")
@login_required
def admin():
    if str(current_user.id) != ADMIN_USER_ID:
        flash("Access Denied: Admins Only!", "danger")
        return redirect(url_for("home"))

    users = list(users_collection.find({}))
    notes = list(notes_collection.find({}))
    return render_template("admin.html", users=users, notes=notes)

@app.route("/admin/delete_user/<user_id>")
@login_required
def delete_user(user_id):
    if str(current_user.id) != ADMIN_USER_ID:
        flash("Access Denied!", "danger")
        return redirect(url_for("admin"))

    users_collection.delete_one({"_id": user_id})
    flash("User deleted successfully!", "success")
    return redirect(url_for("admin"))

@app.route("/admin/delete_note/<note_id>")
@login_required
def delete_note(note_id):
    if str(current_user.id) != ADMIN_USER_ID:
        flash("Access Denied!", "danger")
        return redirect(url_for("admin"))

    notes_collection.delete_one({"_id": note_id})
    flash("Note deleted successfully!", "success")
    return redirect(url_for("admin"))

if __name__ == "__main__":
    app.run(debug=True)
