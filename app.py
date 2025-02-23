from flask import Flask
from routes import app_routes
from database import mongo
import os

app = Flask(__name__)

# MongoDB Configuration
app.config["MONGO_URI"] = "mongodb+srv://scleechadp:scleechadp@site.1n1bj.mongodb.net/?retryWrites=true&w=majority&appName=Site"
mongo.init_app(app)

# Register routes
app.register_blueprint(app_routes)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
