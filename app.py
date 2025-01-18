from flask import Flask, request, jsonify, render_template, send_file
from pymongo import MongoClient
import os
from requests import requests

app = Flask(__name__)

# Fetch MongoDB URI and API key from environment variables
MONGO_URI = os.getenv("MONGO_URI")
URL_SHORTENER_API_KEY = os.getenv("URL_SHORTENER_API_KEY")
URL_SHORTENER_BASE_URL = os.getenv("URL_SHORTENER_BASE_URL", "https://api.example.com/shorten")

if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable is not set!")
if not URL_SHORTENER_API_KEY:
    raise ValueError("URL_SHORTENER_API_KEY environment variable is not set!")

# Create the MongoDB client
client = MongoClient(MONGO_URI)

# Access the database
db = client.get_database('Site')

# Access the collection
notes_collection = db.get_collection('notes')

# Test the connection
try:
    print("Connected to MongoDB:", db.list_collection_names())
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    raise

# Folder to store uploaded files
UPLOAD_FOLDER = "uploaded_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def shorten_url(url):
    """Shorten a URL using a customizable URL shortener service"""
    headers = {
        "Authorization": f"Bearer {URL_SHORTENER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {"url": url}
    response = requests.post(URL_SHORTENER_BASE_URL, json=payload, headers=headers)
    if response.status_code == 201:
        return response.json().get("short_url", url)
    return url

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload')
def upload_page():
    return render_template('upload.html')

@app.route('/notes')
def notes_page():
    # Fetch all notes from the database
    notes = notes_collection.find({}, {"_id": 0, "filename": 1})
    return render_template('notes.html', notes=notes)

@app.route('/api/upload-file', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return render_template("upload_result.html", message="No file part", success=False)
        file = request.files['file']
        if file.filename == '':
            return render_template("upload_result.html", message="No selected file", success=False)

        filename = file.filename
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        # Save the file locally
        file.save(file_path)

        # Save metadata to MongoDB
        notes_collection.insert_one({"filename": filename, "filepath": file_path})

        return render_template("upload_result.html", message="File uploaded successfully", success=True)

    except Exception as e:
        return render_template("upload_result.html", message=f"Error: {str(e)}", success=False)

@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    try:
        # Find the file in the database
        note = notes_collection.find_one({"filename": filename})
        if not note:
            return jsonify({"error": "File not found"}), 404

        file_path = note['filepath']
        if not os.path.exists(file_path):
            return jsonify({"error": "File does not exist on the server"}), 404

        # Generate shortened URL for the download link
        download_url = request.url_root + f"api/download/{filename}"
        shortened_url = shorten_url(download_url)

        return jsonify({"shortened_url": shortened_url}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
