import os, requests

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

#developer key for API Goodreads
api_key = "T6EbvItXzLhlF1OCteZXkg"

@app.route("/")
def index():
    try:
        if session["user_id"] == None: #user is not logged in
            return render_template("index.html", logged_in=False)   
        else:
            user = db.execute("SELECT first_name FROM users WHERE username=:user_id",
                        {"user_id": session["user_id"]}).first()
            books = db.execute("SELECT * FROM books ORDER BY title").fetchall()
            return render_template("books.html", logged_in=True, books=books, user=user.first_name)
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
        db.execute("INSERT INTO users (first_name, last_name, username, password) VALUES (:first_name, :last_name, :username, :password)",
                  {"first_name": first_name, "last_name": last_name, "username": username, "password": password})
        db.commit()
        session["user_id"] = username
        books = db.execute("SELECT * FROM books ORDER BY title").fetchall()
        return render_template("books.html", logged_in=True, books=books, user=first_name) #return page with the books
    except: #username already taken
        return render_template("index.html")

@app.route("/login/")
def log_in():
    return render_template("log_in.html", failed=False, logged_in=False)

@app.route("/logout/")
def logout():
    session["user_id"] = None
    return render_template("index.html", logged_in=False)

@app.route("/authenticate/", methods=["POST"])
def authenticate():
    username = request.form.get("username")
    password = request.form.get("password")

    user = db.execute("SELECT username, password, first_name FROM users WHERE username=:user_id AND password=:password",
                        {"user_id": username, "password": password}).first()
    db.remove()
    if user == None: #authentication failed
        return render_template("log_in.html", failed=True, logged_in=False) 
    else: #authentication succesfull
        session["user_id"] = user.username
        books = db.execute("SELECT * FROM books ORDER BY title").fetchall()
        return render_template("books.html", logged_in=True, books=books, user=user.first_name)

@app.route("/books/")
def books():
    try:
        if session["user_id"] == None: #user is not logged in
            return render_template("index.html", logged_in=False)
        else:
            search_parameter = request.args.get("search_parameter")
            books = db.execute("SELECT isbn, title, author FROM books WHERE isbn LIKE :search_parameter " +
                                "OR author LIKE :search_parameter OR title LIKE :search_parameter ORDER BY title",
                                {"search_parameter": f"%{search_parameter}%"}).fetchall()
            user = db.execute("SELECT first_name FROM users WHERE username=:user_id",
                        {"user_id": session["user_id"]}).first()
            return render_template("books.html", logged_in=True, books=books, user=user.first_name)
    except KeyError: #special case for when there is no session["used_id"] yet
        return render_template("index.html", logged_in=False)


@app.route("/books/<string:book_isbn>/")
def get_book(book_isbn):
    try:
        if session["user_id"] == None: #user is not logged in
            return render_template("index.html", logged_in=False)
        else:
            book = db.execute("SELECT isbn, title, author, year, nr_reviews, average FROM books WHERE isbn=:isbn",
                                {"isbn": book_isbn}).first()
            reviews = db.execute("SELECT score, review, reviewer, book_id FROM reviews WHERE book_id=:isbn",
                                {"isbn": book_isbn}).fetchall()
            print(f"reviews: {reviews}")
            temp_data = get_goodreads_reviews(book_isbn)
            if temp_data != None:
                goodreads_data = None

                goodreads_data = {
                    "average_rating": temp_data['books'][0]['average_rating'],
                    "ratings_count": temp_data['books'][0]['ratings_count']
                }
            else:
                goodreads_data = None

            return render_template("book_details.html", logged_in=True, book=book, reviews=reviews, goodreads_data=goodreads_data)
    except KeyError: #special case for when there is no session["used_id"] yet
        return render_template("index.html", logged_in=False)

#function to make the request to goodreads API
def get_goodreads_reviews(book_isbn):
    try: 
        res = requests.get("https://www.goodreads.com/book/review_counts.json",
                        params={"key": api_key, "isbns": book_isbn})
        
        if res.status_code != 200:
            raise Exception("Error: API request unsuccessful")

        data = res.json()
    except Exception:
        return None

    return data
                        

@app.route("/books/add_review", methods=["POST"])
def add_review():
    try:
        if session["user_id"] == None: #user is not logged in
            return render_template("index.html", logged_in=False)
        else:
            book_isbn = request.form.get("book")
            book = db.execute("SELECT isbn, title, author, year, nr_reviews, average FROM books WHERE isbn=:isbn",
                                {"isbn": book_isbn}).first()
            check = db.execute("SELECT id FROM reviews WHERE book_id=:isbn AND reviewer=:user",
                                {"isbn": book_isbn, "user": session["user_id"]}).first()
            if check == None:
                score = int(request.form.get("score"))
                review = request.form.get("review_desc")

                #execute an update on number of reviews and average score of a book
                nr_reviews = book.nr_reviews + 1
                average = (book.average * (nr_reviews - 1) + score) / nr_reviews

                db.execute("UPDATE books SET nr_reviews=:nr_reviews, average=:average WHERE isbn=:isbn",
                            {"nr_reviews": nr_reviews, "average": average, "isbn": book_isbn})

                db.execute("INSERT INTO reviews (score, review, reviewer, book_id) VALUES (:score, :review, :reviewer, :book_id)",
                            {"score": score, "review": review, "reviewer": session['user_id'], "book_id": book_isbn})
                db.commit()
                books = db.execute("SELECT * FROM books ORDER BY title").fetchall()
                return render_template("books.html", logged_in=True, books=books, review_added=True)
            else:
                reviews = db.execute("SELECT score, review, reviewer, book_id FROM reviews WHERE book_id=:isbn",
                                {"isbn": book_isbn}).fetchall()
                temp_data = get_goodreads_reviews(book_isbn)
                if temp_data != None:
                    goodreads_data = None

                    goodreads_data = {
                        "average_rating": temp_data['books'][0]['average_rating'],
                        "ratings_count": temp_data['books'][0]['ratings_count']
                    }
                else:
                    goodreads_data = None

                return render_template("book_details.html", logged_in=True, book=book, invalid=True, reviews=reviews, goodreads_data=goodreads_data)
    except KeyError as err: #special case for when there is no session["used_id"] yet
        return render_template("index.html", logged_in=False)

@app.route("/api/<string:isbn>")
def api(isbn): 
    try:    
        book = db.execute("SELECT isbn, title, author, year, nr_reviews, average FROM books WHERE isbn=:isbn",
                            {"isbn": isbn}).first()
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
    except Exception as e:
        print(e)
        return jsonify({"error": "Failed request"}), 404

