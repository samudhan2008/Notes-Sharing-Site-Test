from flask import Flask, render_template, redirect, url_for, request, flash
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from bson.objectid import ObjectId
import os

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb+srv://scleechadp:scleechadp@site.1n1bj.mongodb.net/?retryWrites=true&w=majority&appName=Site"  # Change to your MongoDB URI

mongo = PyMongo(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Use a temporary secret key for session management (reset on server restart)
app.config['SECRET_KEY'] = os.urandom(24)

@login_manager.user_loader
def load_user(user_id):
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    return User(user) if user else None

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']
        self.email = user_data['email']
        self.password = user_data['password']

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')

        user = mongo.db.users.find_one({"email": email})
        if user:
            flash("Email already registered!", "danger")
            return redirect(url_for('register'))

        mongo.db.users.insert_one({"username": username, "email": email, "password": password})
        flash("Account created successfully!", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = mongo.db.users.find_one({"email": request.form['email']})
        if user and bcrypt.check_password_hash(user['password'], request.form['password']):
            user_obj = User(user)
            login_user(user_obj)
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password.", "danger")

    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        note_content = request.form['content']
        mongo.db.notes.insert_one({"content": note_content, "user_id": current_user.id})

    notes = mongo.db.notes.find({"user_id": current_user.id})
    return render_template('dashboard.html', username=current_user.username, notes=notes)

@app.route('/delete_note/<note_id>')
@login_required
def delete_note(note_id):
    mongo.db.notes.delete_one({"_id": ObjectId(note_id), "user_id": current_user.id})
    return redirect(url_for('dashboard'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        new_username = request.form['username']
        new_email = request.form['email']
        new_password = request.form['password']

        update_data = {"username": new_username, "email": new_email}
        if new_password:
            update_data["password"] = bcrypt.generate_password_hash(new_password).decode('utf-8')

        mongo.db.users.update_one({"_id": ObjectId(current_user.id)}, {"$set": update_data})
        flash("Profile updated successfully!", "success")
        return redirect(url_for('dashboard'))

    return render_template('profile.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
