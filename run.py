from flask import Flask
from app.routes.gnre import gnre_bp

def create_app():
    app = Flask(__name__)
    
    # Register blueprints
    app.register_blueprint(gnre_bp, url_prefix='/gnre')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)