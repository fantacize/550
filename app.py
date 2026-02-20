from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)


# open sqlite database
def openconnection():
    con = sqlite3.connect("courses.db")
    con.row_factory = sqlite3.Row
    return con


def parselevel(rawvalue):
    if (
        len(rawvalue) == 3
        and rawvalue.endswith("00")
        and rawvalue[0].isdigit()
    ):
        return rawvalue
    return ""


def parserating(rawvalue):
    try:
        rating = float(rawvalue)
    except ValueError:
        return None

    if rating < 1 or rating > 5:
        return None
    return rating


def parsescore(rawvalue):
    try:
        score = int(rawvalue)
    except ValueError:
        return None

    if score < 1 or score > 5:
        return None
    return score


# homepage: show all courses
@app.route("/")
def home():
    search = request.args.get("search", "").strip()
    department = request.args.get("department", "").strip()
    level = parselevel(request.args.get("level", "").strip())
    minratingraw = request.args.get("minrating", "").strip()
    minrating = parserating(minratingraw) if minratingraw else None
    homewarning = ""

    if minratingraw and minrating is None:
        homewarning = "Minimum rating must be between 1 and 5."
        minratingraw = ""

    con = openconnection()
    departments = con.execute(
        """
        SELECT DISTINCT department
        FROM courses
        ORDER BY department
        """
    ).fetchall()
    levels = con.execute(
        """
        SELECT DISTINCT CAST(SUBSTR(coursecode, 3, 1) AS INTEGER) * 100 level
        FROM courses
        WHERE SUBSTR(coursecode, 3, 1) GLOB '[0-9]'
        ORDER BY level
        """
    ).fetchall()

    query = """
        SELECT
            c.id,
            c.coursecode,
            c.coursename,
            c.department,
            c.professor,
            c.description,
            CASE
                WHEN SUBSTR(c.coursecode, 3, 1) GLOB '[0-9]'
                THEN CAST(SUBSTR(c.coursecode, 3, 1) AS INTEGER) * 100
                ELSE NULL
            END level,
            ROUND(AVG(r.overallrating), 2) avgrating,
            COUNT(r.id) reviewcount
        FROM courses c
        LEFT JOIN reviews r ON r.courseid = c.id
    """

    whereparts = []
    params = []

    if search:
        token = f"%{search}%"
        whereparts.append(
            "(c.coursename LIKE ? OR c.coursecode LIKE ? OR c.professor LIKE ?)"
        )
        params.extend([token, token, token])

    if department:
        whereparts.append("c.department = ?")
        params.append(department)

    if level:
        whereparts.append("CAST(SUBSTR(c.coursecode, 3, 1) AS INTEGER) * 100 = ?")
        params.append(int(level))

    if whereparts:
        query += " WHERE " + " AND ".join(whereparts)

    query += " GROUP BY c.id"

    if minrating is not None:
        query += " HAVING AVG(r.overallrating) >= ?"
        params.append(minrating)

    query += " ORDER BY c.department, c.coursecode"

    courses = con.execute(query, params).fetchall()
    con.close()

    return render_template(
        "home.html",
        courses=courses,
        departments=departments,
        levels=levels,
        search=search,
        department=department,
        level=level,
        minrating=minratingraw,
        homewarning=homewarning,
    )


# course page: show one course and its reviews
@app.route("/course/<int:courseid>", methods=["GET", "POST"])
def coursedetail(courseid):
    con = openconnection()
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
        return render_template(
            "coursedetail.html",
            course=None,
            reviews=[],
            saved=False,
            formerror="",
            formvalue={},
        ), 404

    saved = request.args.get("saved", "") == "1"
    savetype = request.args.get("savetype", "").strip()
    mode = request.args.get("mode", "review").strip()
    if mode not in {"review", "rating"}:
        mode = "review"
    formerror = ""
    formvalue = {
        "overall": "",
        "difficulty": "",
        "workload": "",
        "interest": "",
        "reviewtext": "",
        "semester": "",
    }

    if request.method == "POST":
        actiontype = request.form.get("actiontype", "review").strip()
        if actiontype not in {"review", "rating"}:
            actiontype = "review"

        formvalue["overall"] = request.form.get("overall", "").strip()
        formvalue["difficulty"] = request.form.get("difficulty", "").strip()
        formvalue["workload"] = request.form.get("workload", "").strip()
        formvalue["interest"] = request.form.get("interest", "").strip()
        formvalue["reviewtext"] = request.form.get("reviewtext", "").strip()
        formvalue["semester"] = request.form.get("semester", "").strip()

        overall = parsescore(formvalue["overall"])
        difficulty = parsescore(formvalue["difficulty"])
        workload = parsescore(formvalue["workload"])
        interest = parsescore(formvalue["interest"])

        if (
            overall is None
            or difficulty is None
            or workload is None
            or interest is None
        ):
            formerror = "All rating fields must be whole numbers from 1 to 5."
        elif actiontype == "review" and len(formvalue["reviewtext"]) < 10:
            formerror = "Review text must be at least 10 characters."
        else:
            commenttext = formvalue["reviewtext"]
            if actiontype == "rating" and not commenttext:
                commenttext = "Rating only submission."

            con.execute(
                """
                INSERT INTO reviews (
                    courseid,
                    overallrating,
                    difficulty,
                    workload,
                    interest,
                    reviewtext,
                    semester
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    courseid,
                    overall,
                    difficulty,
                    workload,
                    interest,
                    commenttext,
                    formvalue["semester"],
                ),
            )
            con.commit()
            con.close()
            return redirect(f"/course/{courseid}?saved=1&savetype={actiontype}")

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

    return render_template(
        "coursedetail.html",
        course=course,
        reviews=reviews,
        saved=saved,
        savetype=savetype,
        mode=mode,
        formerror=formerror,
        formvalue=formvalue,
    )


app.run(debug=True)
