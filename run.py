from flask import Flask
from app.models import db
from app.routes import routes  # Isso registra as rotas no app
import app.config as config

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = config.DATABASE_URL
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config['DEBUG'] = config.DEBUG
    db.init_app(app)
    app.register_blueprint(routes)
    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)