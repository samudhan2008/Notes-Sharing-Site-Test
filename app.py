from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, jsonify, abort
import os
import uuid
from werkzeug.utils import secure_filename
from pymongo import MongoClient, ASCENDING
from datetime import datetime
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secure random secret key
csrf = CSRFProtect(app)  # Enable CSRF protection

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# MongoDB Connection
client = MongoClient("mongodb+srv://scleechadp:scleechadp@site.1n1bj.mongodb.net/?retryWrites=true&w=majority&appName=Site", serverSelectionTimeoutMS=5000)  # Change URI as needed
db = client['notes_db']
collection = db['notes']
collection.create_index([("upload_date", ASCENDING), ("filename", ASCENDING)])  # Optimized index

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def format_file_data(file):
    return {
        "filename": file["filename"],
        "original_name": file["original_name"],
        "upload_date": file["upload_date"].strftime("%Y-%m-%d %H:%M:%S"),
        "size_kb": round(file["size"] / 1024, 2)  # Convert bytes to KB
    }

@app.route('/')
def index():
    page = max(int(request.args.get('page', 1)), 1)  # Ensure page is at least 1
    per_page = 10
    files = list(collection.find({}, {"_id": 0, "filename": 1, "original_name": 1, "upload_date": 1, "size": 1})
                   .sort("upload_date", -1)
                   .skip((page - 1) * per_page)
                   .limit(per_page))
    formatted_files = [format_file_data(file) for file in files]
    return render_template('index.html', files=formatted_files, page=page)

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        if file and allowed_file(file.filename):
            original_filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{original_filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            file_size = os.path.getsize(file_path)
            collection.insert_one({"filename": unique_filename, "original_name": original_filename, "upload_date": datetime.utcnow(), "size": file_size})
            return jsonify({"message": "File successfully uploaded", "filename": unique_filename}), 200
    return render_template('upload.html')

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    safe_filename = secure_filename(filename)
    file_entry = collection.find_one({"filename": safe_filename})
    if not file_entry:
        return jsonify({"error": "File not found"}), 404
    return send_from_directory(app.config['UPLOAD_FOLDER'], safe_filename, as_attachment=True)

@app.route('/delete/<path:filename>', methods=['DELETE'])
def delete_file(filename):
    safe_filename = secure_filename(filename)
    file_entry = collection.find_one({"filename": safe_filename})
    if not file_entry:
        return jsonify({"error": "File not found"}), 404
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
    try:
        os.remove(file_path)
        collection.delete_one({"filename": safe_filename})
        return jsonify({"message": "File successfully deleted"}), 200
    except Exception as e:
        return jsonify({"error": f"Error deleting file: {str(e)}"}), 500

@app.route('/api/files', methods=['GET'])
def api_files():
    page = max(int(request.args.get('page', 1)), 1)
    per_page = 10
    files = list(collection.find({}, {"_id": 0, "filename": 1, "original_name": 1, "upload_date": 1, "size": 1})
                   .sort("upload_date", -1)
                   .skip((page - 1) * per_page)
                   .limit(per_page))
    formatted_files = [format_file_data(file) for file in files]
    return jsonify(formatted_files)

if __name__ == '__main__':
    try:
        client.server_info()  # Check MongoDB connection
        app.run(debug=True)
    except Exception as e:
        print("Error connecting to MongoDB:", e)
