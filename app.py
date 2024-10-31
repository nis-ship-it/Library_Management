from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Book, Member, Transaction
import requests

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///library.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "super_secret_key"
db.init_app(app)

with app.app_context():
    db.create_all()


@app.route("/")
def index():
    books = Book.query.all()
    members = Member.query.all()
    return render_template("index.html", books=books, members=members)


@app.route("/add_book", methods=["GET", "POST"])
def add_book():
    if request.method == "POST":
        title = request.form["title"]
        authors = request.form["authors"]
        isbn = request.form["isbn"]
        publisher = request.form["publisher"]
        stock = request.form["stock"]
        new_book = Book(
            title=title, authors=authors, isbn=isbn, publisher=publisher, stock=stock
        )
        db.session.add(new_book)
        db.session.commit()
        flash("Book added successfully!")
        return redirect(url_for("index"))
    return render_template("add_book.html")


@app.route("/add_member", methods=["GET", "POST"])
def add_member():
    if request.method == "POST":
        name = request.form["name"]
        new_member = Member(name=name)
        db.session.add(new_member)
        db.session.commit()
        flash("Member added successfully!")
        return redirect(url_for("index"))
    return render_template("add_member.html")


@app.route("/issue_book", methods=["GET", "POST"])
def issue_book():
    if request.method == "POST":
        book_id = request.form["book_id"]
        member_id = request.form["member_id"]
        book = Book.query.get(book_id)
        if book and book.stock > 0:
            book.stock -= 1
            new_transaction = Transaction(
                book_id=book.id,
                member_id=member_id,
                issue_date=db.func.current_timestamp(),
            )
            db.session.add(new_transaction)
            db.session.commit()
            flash("Book issued successfully!")
        else:
            flash("Book not available!")
        return redirect(url_for("index"))
    books = Book.query.all()
    members = Member.query.all()
    return render_template("issue_book.html", books=books, members=members)


@app.route("/return_book", methods=["GET", "POST"])
def return_book():
    if request.method == "POST":
        transaction_id = request.form["transaction_id"]
        transaction = Transaction.query.get(transaction_id)
        if transaction:
            book = Book.query.get(transaction.book_id)
            book.stock += 1
            fee = 10  # Example fee
            member = Member.query.get(transaction.member_id)
            member.outstanding_debt += fee
            db.session.commit()
            flash("Book returned successfully!")
        return redirect(url_for("index"))
    transactions = Transaction.query.all()
    return render_template("return_book.html", transactions=transactions)


@app.route("/import_books", methods=["GET", "POST"])
def import_books():
    if request.method == "POST":
        title = request.form.get("title", "")
        count = int(request.form.get("count", 1))
        for page in range(1, count + 1):
            response = requests.get(
                f"https://frappe.io/api/method/frappe-library?page={
                    page}&title={title}"
            )
            books = response.json().get("message", [])
            for book in books:
                new_book = Book(
                    title=book["title"],
                    authors=book["authors"],
                    isbn=book["isbn"],
                    publisher=book["publisher"],
                    stock=1,  # Default stock when importing
                )
                db.session.add(new_book)
            db.session.commit()
        flash("Books imported successfully!")
        return redirect(url_for("index"))
    return render_template("import_books.html")


if __name__ == "__main__":
    app.run(debug=True)
