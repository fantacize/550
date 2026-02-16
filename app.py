from flask import Flask, render_template
import sqlite3

app = Flask(__name__)


# open sqlite database
def openconnection():
    con = sqlite3.connect("courses.db")
    con.row_factory = sqlite3.Row
    return con


# homepage: show all courses
@app.route("/")
def home():
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


app.run(debug=True)
