import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"
    username = db.Column(db.String, primary_key=True)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    reviews = db.relationship('Review', backref='users', lazy=True)

class Book(db.Model):
    __tablename__ = "books"
    isbn = db.Column(db.String(13), primary_key=True)
    title = db.Column(db.String, nullable=False)
    author = db.Column(db.String, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    average = db.Column(db.Float, nullable=True)
    nr_reviews = db.Column(db.Integer, nullable=False)
    reviews = db.relationship('Review', backref='books', lazy=True)

    def add_review(self, score, review, reviewer):
        r = Review(score=score, review=review, reviewer=reviewer, book_id=self.isbn)
        self.nr_reviews = self.nr_reviews + 1
        self.average = (self.average * (self.nr_reviews - 1) + score) / self.nr_reviews
        return r

class Review(db.Model):
    __tablename__ = "reviews"
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Float, nullable=False)
    review = db.Column(db.Text, nullable=False)
    reviewer = db.Column(db.String, db.ForeignKey('users.username'), nullable=False)
    book_id = db.Column(db.String, db.ForeignKey('books.isbn'), nullable=False)

    