import os

from flask import Flask, session, request, jsonify, render_template
from flask_session import Session
from sqlalchemy import create_engine, and_, or_
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
    try:
        req = db()
        if session["user_id"] == None: #user is not logged in
            return render_template("index.html", logged_in=False)   
        else:
            user = req.query(User).get(session["user_id"])
            books = req.query(Book).order_by(Book.title).all()
            return render_template("books.html", logged_in=True, books=books, user=user.first_name)
    except KeyError: #special case for when there is no session["used_id"] yet
        return render_template("index.html", logged_in=False)
    finally:
        db.remove()

@app.route("/registration/")
def registration():
    return render_template("register.html", logged_in=False)

@app.route("/registration/register/", methods=["POST"])
def register():
    req = db()

    #get data from form
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    password = request.form.get("password")
    username = request.form.get("username")
        
    try:
        user = User(first_name=first_name, last_name=last_name, username=username, password=password)
        req.add(user)
        req.commit()
        session["user_id"] = user.username
        books = req.query(Book).order_by(Book.title).all()
        return render_template("books.html", logged_in=True, books=books, user=first_name) #return page with the books
    except: #username already taken
        return render_template("index.html")
    finally:
        db.remove()

@app.route("/login/")
def log_in():
    return render_template("log_in.html", failed=False, logged_in=False)

@app.route("/logout/")
def logout():
    session["user_id"] = None
    return render_template("index.html", logged_in=False)

@app.route("/authenticate/", methods=["POST"])
def authenticate():
    req = db()

    username = request.form.get("username")
    password = request.form.get("password")

    user = req.query(User).filter(and_(User.username==username, User.password==password)).first()
    db.remove()
    if user == None: #authentication failed
        return render_template("log_in.html", failed=True, logged_in=False) 
    else: #authentication succesfull
        session["user_id"] = user.username
        books = req.query(Book).order_by(Book.title).all()
        return render_template("books.html", logged_in=True, books=books, user=user.first_name)

@app.route("/books/")
def books():
    try:
        req = db()
        if session["user_id"] == None: #user is not logged in
            return render_template("index.html", logged_in=False)
        else:
            search_parameter = request.args.get("search_parameter")
            books = req.query(Book).filter(or_(Book.isbn.like(f"%{search_parameter}%"), Book.title.like(f"%{search_parameter}%"), Book.author.like(f"%{search_parameter}%"))).order_by(Book.title)
            user = req.query(User).get(session["user_id"])
            return render_template("books.html", logged_in=True, books=books, user=user.first_name)
    except KeyError: #special case for when there is no session["used_id"] yet
        return render_template("index.html", logged_in=False)
    finally:
        db.remove()

@app.route("/books/<string:book_isbn>/")
def get_book(book_isbn):
    try:
        req = db()
        if session["user_id"] == None: #user is not logged in
            return render_template("index.html", logged_in=False)
        else:
            book = req.query(Book).get(book_isbn)
            users = req.query(User).all()
            return render_template("book_details.html", logged_in=True, book=book, users=users)
    except KeyError: #special case for when there is no session["used_id"] yet
        return render_template("index.html", logged_in=False)
    finally:
        db.remove()

@app.route("/books/add_review", methods=["POST"])
def add_review():
    try:
        req = db()
        if session["user_id"] == None: #user is not logged in
            return render_template("index.html", logged_in=False)
        else:
            book_isbn = request.form.get("book")
            print(f"ISBN: {book_isbn}")
            book = req.query(Book).get(book_isbn)
            score = int(request.form.get("score"))
            review = request.form.get("review_desc")
            new_review = book.add_review(score, review, session['user_id'])
            req.add(new_review)
            req.commit()
            books = req.query(Book).order_by(Book.title).all()
            return render_template("books.html", logged_in=True, books=books, review_added=True)
    except KeyError as err: #special case for when there is no session["used_id"] yet
        return render_template("index.html", logged_in=False)
    finally:
        db.remove()

@app.route("/api/<string:isbn>")
def api(isbn): 
    try:    
        req = db()    
        book = req.query(Book).get(isbn)
        
        if book is None:
            return jsonify({"error": "Invalid isbn"}), 404
        
        return jsonify({
            "title": book.title,
            "author": book.author,
            "year": book.year,
            "isbn": book.isbn,
            "review_count": book.nr_reviews,
            "average_score": book.average
        })
    except:
        return jsonify({"error": "Failed request"}), 404
    finally:
        db.remove()
