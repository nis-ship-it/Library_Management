from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Book, Member, Transaction
from datetime import datetime
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
    return render_template("index.html")


@app.route("/books")
def list_books():
    books = Book.query.all()
    return render_template("books.html", books=books)


@app.route("/delete_book/<int:id>", methods=["POST"])
def delete_book(id):
    book = db.session.get(Book, id)
    if book:
        db.session.delete(book)
        db.session.commit()
        flash("Book deleted successfully!")
    else:
        flash("Book not found.")
    return redirect(url_for("list_books"))


@app.route("/edit_book/<int:id>", methods=["GET", "POST"])
def edit_book(id):
    book = Book.query.get_or_404(id)

    if request.method == "POST":
        # Update book details with the form data
        book.title = request.form["title"]
        book.authors = request.form["authors"]
        book.isbn = request.form["isbn"]
        book.publisher = request.form["publisher"]
        book.stock = request.form["stock"]

        db.session.commit()  # Save changes to the database
        flash("Book updated successfully!")
        return redirect(url_for("list_books"))

    return render_template("edit_book.html", book=book)


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


@app.route("/issue_book", methods=["GET", "POST"])
def issue_book():
    if request.method == "POST":
        book_id = request.form["book_id"]
        member_id = request.form["member_id"]
        book = db.session.get(Book, book_id)
        member = db.session.get(Member, member_id)

        if book and book.stock > 0:
            book.stock -= 1
            new_transaction = Transaction(
                book_id=book.id,
                member_id=member.id,
                issue_date=datetime.now(),
            )
            db.session.add(new_transaction)
            member.outstanding_debt += 10  # Charge ₹10 on issue
            db.session.commit()
            flash(
                "Book issued successfully! A fee of ₹10 has been added to your outstanding debt."
            )
        else:
            flash("Book not available!")
        return redirect(url_for("index"))

    books = Book.query.all()
    members = Member.query.all()
    return render_template("issue_book.html", books=books, members=members)


# Search for Books
@app.route("/search_books", methods=["GET"])
def search_books():
    query = request.args.get("query")
    books = Book.query.filter(
        (Book.title.ilike(f"%{query}%")) | (Book.authors.ilike(f"%{query}%"))
    ).all()
    return render_template("books.html", books=books)


@app.route("/import_books", methods=["GET", "POST"])
def import_books():
    if request.method == "POST":
        title = request.form.get("title", "")
        total_count = int(request.form.get("count", 1))

        books_imported = 0
        page = 1

        while books_imported < total_count:
            response = requests.get(
                f"https://frappe.io/api/method/frappe-library?page={
                    page}&title={title}"
            )

            if response.status_code != 200:
                flash("Failed to fetch data from the API.")
                return redirect(url_for("index"))

            books = response.json().get("message", [])

            if not books:
                flash("No more books found.")
                break

            for book in books:
                if books_imported >= total_count:
                    break  # Stop if we've reached the desired count

                existing_book = (
                    db.session.query(Book).filter_by(isbn=book["isbn"]).first()
                )

                if existing_book is None:
                    new_book = Book(
                        title=book["title"],
                        authors=book["authors"],
                        isbn=book["isbn"],
                        publisher=book["publisher"],
                        stock=1,  # Default stock when importing
                    )
                    db.session.add(new_book)
                    books_imported += 1
                else:
                    flash(f"Book '{book['title']
                                   }' already exists in the database.")

            db.session.commit()
            page += 1  # Move to the next page

        flash(f"{books_imported} books imported successfully!")
        return redirect(url_for("index"))

    return render_template("import_books.html")


@app.route("/members")
def list_members():
    members = Member.query.all()
    return render_template("members.html", members=members)


@app.route("/add_member", methods=["GET", "POST"])
def add_member():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        new_member = Member(name=name, email=email)
        db.session.add(new_member)
        db.session.commit()
        flash("Member added successfully!")
        return redirect(url_for("index"))
    return render_template("add_member.html")


@app.route("/delete_member/<int:id>", methods=["POST"])
def delete_member(id):
    member = db.session.get(Member, id)
    if member:
        db.session.delete(member)
        db.session.commit()
        flash("Member deleted successfully!")
    else:
        flash("Member not found.")
    return redirect(url_for("list_members"))


@app.route("/edit_member/<int:id>", methods=["GET", "POST"])
def edit_member(id):
    member = db.session.get(Member, id)
    if member is None:
        flash("Member not found.")
        return redirect(url_for("list_members"))

    if request.method == "POST":
        member.name = request.form["name"]
        member.email = request.form["email"]
        member.outstanding_debt = request.form.get(
            "outstanding_debt", 0, type=float)

        db.session.commit()  # Save changes to database
        flash("Member updated successfully!")
        return redirect(url_for("list_members"))

    return render_template("edit_member.html", member=member)


@app.route("/transactions", methods=["GET"])
def transactions():
    transactions = Transaction.query.all()
    return render_template("transactions.html", transactions=transactions)


@app.route("/return_book/<int:transaction_id>", methods=["GET", "POST"])
def return_book(transaction_id):
    transaction = db.session.get(Transaction, transaction_id)
    if request.method == "POST":
        member_id = request.form["member_id"]
        member = db.session.get(Member, member_id)

        if transaction:
            book = db.session.get(Book, transaction.book_id)
            if book:
                book.stock += 1  # Increment stock
                days_issued = (datetime.now() - transaction.issue_date).days
                total_fee = days_issued * 10
                member.outstanding_debt += total_fee  # Charge based on days issued
                db.session.delete(transaction)
                db.session.commit()
                flash(f"Book returned successfully! Total fee charged: ₹{
                      total_fee}.")
            else:
                flash("Book not found.")
        else:
            flash("Transaction not found.")
        return redirect(url_for("index"))

    members = Member.query.all()
    return render_template("return_book.html", members=members, transaction=transaction)


@app.route("/book/<int:book_id>")
def book_detail(book_id):
    book = db.session.get(Book, book_id)
    if book is None:
        flash("Book not found.")
        return redirect(url_for("list_books"))
    return render_template("book_detail.html", book=book)


@app.route("/member/<int:member_id>")
def member_detail(member_id):
    member = db.session.get(Member, member_id)
    if member is None:
        flash("Member not found.")
        return redirect(url_for("list_members"))
    return render_template("member_detail.html", member=member)


if __name__ == "__main__":
    app.run(debug=True)
