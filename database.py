from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

def init_db(app):
    # Configuration is now handled in app.py
    db.init_app(app)