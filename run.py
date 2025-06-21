from flask import Flask
from app.routes.routes import app

def create_app():
    application = Flask(__name__)

    return application

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)