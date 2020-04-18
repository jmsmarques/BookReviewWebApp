import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=False)
    username = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)

class Book(db.Model):
    __tablename__ = "books"
    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(13), nullable=False, unique=True)
    title = db.Column(db.String, nullable=False)
    author = db.Column(db.String, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    average = db.Column(db.Float, nullable=True)
    nr_reviews = db.Column(db.Integer, nullable=False)
    reviews = db.relationship('Review', backref='books', lazy=True)

    def add_review(self, score, review):
        r = Review(score=score, review=review, book_id=self.id)
        self.nr_reviews = self.nr_reviews + 1
        self.average = (self.average * (nr_reviews - 1) + score) / self.nr_reviews
        db.session.add(r)
        db.session.commit()

class Review(db.Model):
    __tablename__ = "reviews"
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Float, nullable=False)
    review = db.Column(db.Text, nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)

    