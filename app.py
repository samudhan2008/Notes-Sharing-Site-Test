from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from bson.objectid import ObjectId
import os
from werkzeug.utils import secure_filename
import config

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb+srv://scleechadp:scleechadp@site.1n1bj.mongodb.net/?retryWrites=true&w=majority&appName=Site"
app.config["UPLOAD_FOLDER"] = config.UPLOAD_FOLDER

mongo = PyMongo(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

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

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(url_for('dashboard'))
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(url_for('dashboard'))
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)

            mongo.db.notes.insert_one({"filename": filename, "user_id": current_user.id})
            flash('File uploaded successfully!', 'success')
        else:
            flash('Only PDF files are allowed!', 'danger')

    notes = mongo.db.notes.find({"user_id": current_user.id})
    return render_template('dashboard.html', username=current_user.username, notes=notes)

@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route('/delete_note/<note_id>')
@login_required
def delete_note(note_id):
    note = mongo.db.notes.find_one({"_id": ObjectId(note_id), "user_id": current_user.id})
    
    if note:
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], note["filename"])
        if os.path.exists(file_path):
            os.remove(file_path)
        
        mongo.db.notes.delete_one({"_id": ObjectId(note_id)})
        flash('Note deleted successfully!', 'success')
    
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
