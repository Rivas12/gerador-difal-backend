from flask import Flask

app = Flask(__name__)

from app.routes import routes  # Importing routes to register them with the app