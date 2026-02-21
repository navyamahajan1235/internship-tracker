from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secretkey"


def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        db = get_db()

        user = db.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()

        if user:
            session["user_id"] = user["id"]
            return redirect("/dashboard")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        db = get_db()

        db.execute(
            "INSERT INTO users (username, password) VALUES (?,?)",
            (username, password)
        )

        db.commit()

        return redirect("/")

    return render_template("register.html")


@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/")

    db = get_db()

    apps = db.execute(
        "SELECT * FROM applications WHERE user_id=?",
        (session["user_id"],)
    ).fetchall()

    stats = db.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN status='applied' THEN 1 ELSE 0 END) as applied,
            SUM(CASE WHEN status='interview' THEN 1 ELSE 0 END) as interview,
            SUM(CASE WHEN status='offer' THEN 1 ELSE 0 END) as offer,
            SUM(CASE WHEN status='rejected' THEN 1 ELSE 0 END) as rejected
        FROM applications
        WHERE user_id=?
    """, (session["user_id"],)).fetchone()

    return render_template("dashboard.html", apps=apps, stats=stats)


@app.route("/add", methods=["GET", "POST"])
def add_application():

    if "user_id" not in session:
        return redirect("/")

    if request.method == "POST":

        company = request.form["company"]
        role = request.form["role"]
        status = request.form["status"].lower()
        deadline = request.form["deadline"]

        db = get_db()

        db.execute(
            """INSERT INTO applications
               (user_id, company, role, status, deadline)
               VALUES (?,?,?,?,?)""",
            (session["user_id"], company, role, status, deadline)
        )

        db.commit()

        return redirect("/dashboard")

    return render_template("add_application.html")


@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_application(id):

    if "user_id" not in session:
        return redirect("/")

    db = get_db()

    if request.method == "POST":

        company = request.form["company"]
        role = request.form["role"]
        status = request.form["status"].lower()
        deadline = request.form["deadline"]

        db.execute("""
            UPDATE applications
            SET company=?, role=?, status=?, deadline=?
            WHERE id=? AND user_id=?
        """, (company, role, status, deadline, id, session["user_id"]))

        db.commit()

        return redirect("/dashboard")

    app_data = db.execute(
        "SELECT * FROM applications WHERE id=? AND user_id=?",
        (id, session["user_id"])
    ).fetchone()

    return render_template("edit_application.html", app=app_data)


@app.route("/delete/<int:id>")
def delete_application(id):

    if "user_id" not in session:
        return redirect("/")

    db = get_db()

    db.execute(
        "DELETE FROM applications WHERE id=? AND user_id=?",
        (id, session["user_id"])
    )

    db.commit()

    return redirect("/dashboard")


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)