import os

from flask import Flask, session, request, jsonify, render_template
from flask_session import Session
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import scoped_session, sessionmaker
from models import *

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/registration/")
def registration():
    return render_template("register.html")

@app.route("/registration/register/", methods=["POST"])
def register():
    username = request.form.get("username")

    try:
        db.query.filter_by(username=username).all()
    except AttributeError:
        #get data from form
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        password = request.form.get("password")

        user = User(first_name=first_name, last_name=last_name, username=username, password=password)
        db.add(user)
        db.commit()
        return render_template("books.html")

    #username already taken
    return render_template("index.html")

@app.route("/login/")
def log_in():
    return render_template("log_in.html", failed=False)

@app.route("/authenticate/")
def authenticate():
    username = request.form.get("username")
    password = request.form.get("password")

    try:
        db.query.filter(and_(username=username, password=password)).all()
    except: #authentication failed
        return render_template("log_in.html", failed=True) 
    
    #authentication succesfull
    return render_template("books.html")




@app.route("/books/<int:book_id>")
def get_book():

    return render_template("index.html")