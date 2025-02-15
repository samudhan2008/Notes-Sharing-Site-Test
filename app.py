from flask import Flask, redirect, url_for, render_template, request, flash
from flask_mongoengine import MongoEngine
from flask_admin import Admin
from flask_admin.contrib.mongoengine import ModelView
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from flask_bcrypt import Bcrypt
import os

# Initialize Flask app
app = Flask(__name__)

# Load MongoDB connection from environment variable
app.config['MONGODB_SETTINGS'] = {'host': os.getenv('MONGO_URL', 'mongodb://localhost:27017/notes_db')}

# Initialize Extensions
db = MongoEngine(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# User Model
class User(db.Document, UserMixin):
    username = db.StringField(unique=True, required=True)
    password = db.StringField(required=True)
    is_admin = db.BooleanField(default=False)

    def get_id(self):
        return str(self.id)

# Notes Model
class Note(db.Document):
    title = db.StringField(required=True)
    filename = db.StringField(required=True)

# Flask-Admin Secure View
class AdminView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))

# Initialize Flask-Admin
admin = Admin(app, name='Admin Panel', template_mode='bootstrap4')
admin.add_view(AdminView(User))
admin.add_view(AdminView(Note))

@login_manager.user_loader
def load_user(user_id):
    return User.objects(id=user_id).first()

# Automatically create admin user if not exists
@app.before_first_request
def create_admin():
    if not User.objects(username="admin"):
        hashed_pw = bcrypt.generate_password_hash("adminpass").decode('utf-8')
        admin_user = User(username="admin", password=hashed_pw, is_admin=True)
        admin_user.save()
        print("Admin user created!")

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.objects(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('admin.index'))
        else:
            flash('Invalid credentials.', 'danger')

    return render_template('login.html')

# Logout Route
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

# Home Route
@app.route('/')
def home():
    return "Welcome to Notes Sharing Site!"

if __name__ == "__main__":
    app.run(debug=True)
