from flask import Flask, flash, redirect, render_template, request, session
from hashlib import pbkdf2_hmac
import os
import sqlite3

app = Flask(__name__)
app.secret_key = os.environ.get("APPSECRETKEY", "dev-secret-key-change-me")


# read db path from env so deploys can pick custom storage
def getdbpath():
    return os.environ.get("COURSEDBPATH", "courses.db")


# make sure parent folder exists before sqlite tries to open file
def ensuredbdir(dbpath):
    dbdir = os.path.dirname(dbpath)
    if dbdir:
        # create folder only when path includes a directory
        os.makedirs(dbdir, exist_ok=True)


# open sqlite database
def openconnection():
    dbpath = getdbpath()
    ensuredbdir(dbpath)
    con = sqlite3.connect(dbpath)
    con.row_factory = sqlite3.Row
    return con


# verify password hash using same algo format we store in init script
def verifypassword(storedhash, rawpassword):
    try:
        # expect format: algo$iterations$salt$digest
        algorithm, iterationstext, salt, digest = storedhash.split("$")
    except ValueError:
        # bad hash format should always fail auth
        return False

    if algorithm != "pbkdf2sha256":
        # reject unknown hash algorithm
        return False

    try:
        iterations = int(iterationstext)
    except ValueError:
        # reject malformed iteration count
        return False

    checkdigest = pbkdf2_hmac(
        "sha256", rawpassword.encode("utf-8"), salt.encode("utf-8"), iterations
    ).hex()
    return checkdigest == digest


# fetch logged-in user from session id, or return none if no login
def getcurrentuser():
    userid = session.get("userid")
    if not userid:
        # no active session means guest user
        return None

    con = openconnection()
    user = con.execute(
        "SELECT id, username FROM users WHERE id = ?",
        (userid,),
    ).fetchone()
    con.close()
    return user


@app.route("/health")
def health():
    # simple uptime check endpoint for hosting platforms
    return "ok", 200


@app.route("/login", methods=["GET", "POST"])
def login():
    # already logged in users just go home
    currentuser = getcurrentuser()
    if currentuser:
        return redirect("/")

    error = ""
    if request.method == "POST":
        # read login form values
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        con = openconnection()
        user = con.execute(
            "SELECT id, username, passwordhash FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        con.close()

        if user and verifypassword(user["passwordhash"], password):
            # store user id in session after successful login
            session["userid"] = user["id"]
            flash("Welcome back.", "success")
            return redirect("/")
        # keep user on login page with generic error text
        error = "Invalid username or password."

    # render login page for get requests or failed post attempts
    return render_template("login.html", error=error, currentuser=currentuser)


@app.route("/logout", methods=["POST"])
def logout():
    # clear session id and send user home
    session.pop("userid", None)
    flash("You have been logged out.", "info")
    return redirect("/")


# homepage: show all courses
@app.route("/")
def home():
    # collect optional filters from url query params
    currentuser = getcurrentuser()
    search = request.args.get("search", "").strip()
    department = request.args.get("department", "").strip()
    level = request.args.get("level", "").strip()
    if not (len(level) == 3 and level[0].isdigit() and level[1:] == "00"):
        # ignore invalid level filters like random strings
        level = ""
    minratingraw = request.args.get("minrating", "").strip()
    minrating = None
    homewarning = ""

    if minratingraw:
        # keep rating filter in valid range only
        try:
            minrating = float(minratingraw)
            if minrating < 1 or minrating > 5:
                # clear out-of-range values and show warning
                minrating = None
                minratingraw = ""
                homewarning = "Minimum rating must be between 1 and 5."
        except ValueError:
            # clear non-numeric values and show warning
            minrating = None
            minratingraw = ""
            homewarning = "Minimum rating must be between 1 and 5."

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

    # start with base query and append filters dynamically
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
        # search against name, code, and professor
        token = f"%{search}%"
        whereparts.append(
            "(c.coursename LIKE ? OR c.coursecode LIKE ? OR c.professor LIKE ?)"
        )
        params.extend([token, token, token])

    if department:
        # department filter path
        whereparts.append("c.department = ?")
        params.append(department)

    if level:
        # level filter path
        whereparts.append("CAST(SUBSTR(c.coursecode, 3, 1) AS INTEGER) * 100 = ?")
        params.append(int(level))

    if whereparts:
        # add where clause only when at least one filter exists
        query += " WHERE " + " AND ".join(whereparts)

    query += " GROUP BY c.id"

    if minrating is not None:
        # apply rating threshold after aggregation
        query += " HAVING AVG(r.overallrating) >= ?"
        params.append(minrating)

    query += " ORDER BY c.department, c.coursecode"

    courses = con.execute(query, params).fetchall()
    con.close()

    # render homepage with filters and query results
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
        currentuser=currentuser,
    )


@app.route("/stats")
def stats():
    # fetch summary numbers plus top 10 by volume and rating
    currentuser = getcurrentuser()
    con = openconnection()

    totals = con.execute(
        """
        SELECT
            (SELECT COUNT(*) FROM courses) totalcourses,
            (SELECT COUNT(*) FROM reviews) totalreviews,
            ROUND((SELECT AVG(overallrating) FROM reviews), 2) averageoverall
        """
    ).fetchone()

    # most reviewed list prioritizes review count first
    mostreviewed = con.execute(
        """
        SELECT
            c.id,
            c.coursecode,
            c.coursename,
            c.department,
            ROUND(AVG(r.overallrating), 2) avgrating,
            COUNT(r.id) reviewcount
        FROM courses c
        LEFT JOIN reviews r ON r.courseid = c.id
        GROUP BY c.id
        HAVING COUNT(r.id) > 0
        ORDER BY reviewcount DESC, avgrating DESC, c.coursecode
        LIMIT 10
        """
    ).fetchall()

    # highest rated list prioritizes avg score first
    highestrated = con.execute(
        """
        SELECT
            c.id,
            c.coursecode,
            c.coursename,
            c.department,
            ROUND(AVG(r.overallrating), 2) avgrating,
            COUNT(r.id) reviewcount
        FROM courses c
        LEFT JOIN reviews r ON r.courseid = c.id
        GROUP BY c.id
        HAVING COUNT(r.id) > 0
        ORDER BY avgrating DESC, reviewcount DESC, c.coursecode
        LIMIT 10
        """
    ).fetchall()
    con.close()

    # render stats page with both leaderboards
    return render_template(
        "stats.html",
        totals=totals,
        mostreviewed=mostreviewed,
        highestrated=highestrated,
        currentuser=currentuser,
    )


# course page: show one course and its reviews
@app.route("/course/<int:courseid>", methods=["GET", "POST"])
def coursedetail(courseid):
    # load course info first so we can 404 early
    currentuser = getcurrentuser()
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
        # invalid course id path returns 404 template
        con.close()
        return render_template(
            "coursedetail.html",
            course=None,
            reviews=[],
            saved=False,
            formerror="",
            formvalue={},
            currentuser=currentuser,
        ), 404

    saved = request.args.get("saved", "") == "1"
    savetype = request.args.get("savetype", "").strip()
    mode = request.args.get("mode", "review").strip()
    if mode not in {"review", "rating"}:
        # fallback to review mode on bad mode value
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
        # support two submit modes: full review or rating-only
        actiontype = request.form.get("actiontype", "review").strip()
        if actiontype not in {"review", "rating"}:
            # fallback to review mode on bad action value
            actiontype = "review"

        formvalue["overall"] = request.form.get("overall", "").strip()
        formvalue["difficulty"] = request.form.get("difficulty", "").strip()
        formvalue["workload"] = request.form.get("workload", "").strip()
        formvalue["interest"] = request.form.get("interest", "").strip()
        formvalue["reviewtext"] = request.form.get("reviewtext", "").strip()
        formvalue["semester"] = request.form.get("semester", "").strip()

        overall = None
        difficulty = None
        workload = None
        interest = None

        # parse all star fields as whole numbers
        try:
            overall = int(formvalue["overall"])
            difficulty = int(formvalue["difficulty"])
            workload = int(formvalue["workload"])
            interest = int(formvalue["interest"])
        except ValueError:
            # leave values as none so validation below fails cleanly
            pass

        if (
            overall is None
            or difficulty is None
            or workload is None
            or interest is None
            or overall < 1
            or overall > 5
            or difficulty < 1
            or difficulty > 5
            or workload < 1
            or workload > 5
            or interest < 1
            or interest > 5
        ):
            # invalid star values path
            formerror = "All rating fields must be whole numbers from 1 to 5."
        elif actiontype == "review" and len(formvalue["reviewtext"]) < 10:
            # review mode requires enough text content
            formerror = "Review text must be at least 10 characters."
        else:
            # rating-only posts can skip text and use fallback message
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
            # redirect after post to prevent duplicate resubmits
            return redirect(f"/course/{courseid}?saved=1&savetype={actiontype}")

    # show newest reviews first
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
        currentuser=currentuser,
    )


if __name__ == "__main__":
    # local dev entrypoint
    app.run(debug=True)
