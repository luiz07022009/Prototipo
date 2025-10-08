# /mnt/data/__init__.py  (ou app/__init__.py conforme seu projeto)
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv
import os

db = SQLAlchemy()

def create_app():
    load_dotenv()
    app = Flask(__name__, template_folder="templates")
    CORS(app)

    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        # fallback para sqlite local (não precisa psql)
        database_url = 'sqlite:///valida.db'
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    from app import routes
    routes.init_routes(app)

    with app.app_context():
        # cria tabelas automaticamente (SQLite local se não tiver DATABASE_URL)
        db.create_all()

    return app
