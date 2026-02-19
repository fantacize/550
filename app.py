import hashlib
import os
import secrets
import sqlite3

from flask import Flask, flash, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")


# open sqlite database
def openconnection():
    con = sqlite3.connect("courses.db")
    con.row_factory = sqlite3.Row
    return con


def _verify_password(password, stored_hash):
    try:
        scheme, iterations, salt, expected = stored_hash.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations),
        ).hex()
        return secrets.compare_digest(digest, expected)
    except Exception:
        return False


def current_user():
    userid = session.get("userid")
    if not userid:
        return None
    con = openconnection()
    user = con.execute("SELECT id, username FROM users WHERE id = ?", (userid,)).fetchone()
    con.close()
    return user


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username and password are required.", "danger")
            return render_template("login.html"), 400

        con = openconnection()
        user = con.execute(
            "SELECT id, username, passwordhash FROM users WHERE username = ?", (username,)
        ).fetchone()
        con.close()

        if user and _verify_password(password, user["passwordhash"]):
            session["userid"] = user["id"]
            flash("Logged in successfully.", "success")
            return redirect(url_for("home"))

        flash("Invalid username or password.", "danger")
        return render_template("login.html"), 401

    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("login"))


# homepage: show all courses
@app.route("/")
def home():
    if not current_user():
        return redirect(url_for("login"))

    con = openconnection()
    # basic course list for home page
    courses = con.execute(
        """
        SELECT id, coursecode, coursename, department, professor, description
        FROM courses
        ORDER BY department, coursecode
        """
    ).fetchall()
    con.close()

    return render_template("home.html", courses=courses)


# course page: show one course and its reviews
@app.route("/course/<int:courseid>")
def coursedetail(courseid):
    if not current_user():
        return redirect(url_for("login"))

    con = openconnection()
    # get selected course
    course = con.execute(
        """
        SELECT id, coursecode, coursename, department, professor, description
        FROM courses
        WHERE id = ?
        """,
        (courseid,),
    ).fetchone()

    if course is None:
        con.close()
        return render_template("coursedetail.html", course=None, reviews=[]), 404

    # get existing reviews for this course
    reviews = con.execute(
        """
        SELECT id, courseid, overallrating, difficulty, workload, interest, reviewtext, semester, dateposted
        FROM reviews
        WHERE courseid = ?
        ORDER BY dateposted DESC
        """,
        (courseid,),
    ).fetchall()
    con.close()

    return render_template("coursedetail.html", course=course, reviews=reviews)


@app.context_processor
def inject_user():
    return {"currentuser": current_user()}


if __name__ == "__main__":
    app.run(debug=True)
