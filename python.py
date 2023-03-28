from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
db = SQLAlchemy(app)
app.app_context().push()

class Item():
    __tablename__ = 'items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, index=True, unique=True)
    description = db.Column(db.String)
    price = db.Column(db.Float)
    environmental_impact = db.Column(db.Integer)
