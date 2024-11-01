from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    authors = db.Column(db.String(200), nullable=False)
    isbn = db.Column(db.String(100), unique=True, nullable=False)
    publisher = db.Column(db.String(100))
    stock = db.Column(db.Integer, default=0)
    rented_count = db.Column(db.Integer, default=0)


class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    outstanding_debt = db.Column(db.Float, default=0)


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey("book.id"), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey(
        "member.id"), nullable=False)
    issue_date = db.Column(db.DateTime)
    return_date = db.Column(db.DateTime)
    per_day_fee = db.Column(db.Float, default=0)
    amount_paid = db.Column(db.Float, default=0)
