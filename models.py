from database import mongo

def save_user(username, email, password_hash):
    mongo.db.users.insert_one({"username": username, "email": email, "password": password_hash})

def get_user(email):
    return mongo.db.users.find_one({"email": email})

def save_note(user_id, filename):
    mongo.db.notes.insert_one({"user_id": user_id, "filename": filename})
