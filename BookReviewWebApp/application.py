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
    session.clear()
    try:
        if session["user_id"] == None: #user is not logged in
            return render_template("index.html", logged_in=False)
        else:
            return render_template("books.html")
    except KeyError: #special case for when there is no session["used_id"] yet
        return render_template("index.html", logged_in=False)

    


@app.route("/registration/")
def registration():
    return render_template("register.html", logged_in=False)

@app.route("/registration/register/", methods=["POST"])
def register():

    #get data from form
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    password = request.form.get("password")
    username = request.form.get("username")
        
    try:
        user = User(first_name=first_name, last_name=last_name, username=username, password=password)
        db.add(user)
        db.commit()
        session["user_id"] = user.id
        return render_template("books.html", logged_in=False)
    except: #username already taken
        return render_template("index.html")

@app.route("/login/")
def log_in():
    return render_template("log_in.html", failed=False, logged_in=False)

@app.route("/logout/")
def logout():
    session["user_id"] = None
    return render_template("index.html", logged_in=False)

@app.route("/authenticate/")
def authenticate():
    username = request.form.get("username")
    password = request.form.get("password")

    user = db.query(User).filter(and_(username=username, password=password)).all()
    print(user)
    if user != None: #authentication failed
        return render_template("log_in.html", failed=True, logged_in=False) 
    else: #authentication succesfull
        return render_template("books.html", logged_in=True)




@app.route("/books/<int:book_id>")
def get_book(book_id):
    return render_template("index.html")