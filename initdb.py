import csv
import os
import sqlite3
from hashlib import pbkdf2_hmac
from secrets import token_hex


# map course code prefix to a department label
def departmentfromcode(coursecode):
    prefix = coursecode[:2]
    deptmap = {
        "AR": "Languages - Arabic",
        "AS": "Advanced Studies",
        "BI": "Science - Biology",
        "CH": "Science - Chemistry",
        "CN": "Languages - Chinese",
        "CS": "Computer Science",
        "DA": "Arts - Dance",
        "EC": "Economics",
        "EI": "Environmental Immersion",
        "EN": "English",
        "FR": "Languages - French",
        "HI": "History",
        "LA": "Languages - Latin",
        "MA": "Mathematics",
        "MD": "Multidisciplinary",
        "MU": "Arts - Music",
        "PH": "Science - Physics",
        "PL": "Philosophy",
        "RL": "Religion",
        "SC": "Science",
        "SP": "Languages - Spanish",
        "SS": "Social Sciences",
        "TA": "Arts - Theater",
        "VA": "Arts - Visual Arts",
    }
    return deptmap.get(prefix, "General")


# normalize csv keys so weird symbols do not break lookups
def cleankeys(item):
    clean = {}
    for key, value in item.items():
        newkey = key.replace(chr(95), "").replace("-", "")
        clean[newkey] = value
    return clean


# hash password in the same format used by app.py login checks
def hashpassword(password):
    salt = token_hex(16)
    iterations = 200000
    digest = pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations
    ).hex()
    return f"pbkdf2sha256${iterations}${salt}${digest}"


# create tables and seed starter data if db is empty
def builddatabase():
    dbpath = os.environ.get("COURSEDBPATH", "courses.db")
    dbdir = os.path.dirname(dbpath)
    if dbdir:
        # create folder only when db path includes directories
        os.makedirs(dbdir, exist_ok=True)

    con = sqlite3.connect(dbpath)
    cur = con.cursor()

    # users table stores login credentials
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            passwordhash TEXT NOT NULL
        )
        """
    )

    # courses table stores class metadata
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            coursecode TEXT NOT NULL,
            coursename TEXT NOT NULL,
            department TEXT NOT NULL,
            professor TEXT,
            description TEXT
        )
        """
    )

    # reviews table stores user ratings and comments
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            courseid INTEGER NOT NULL,
            overallrating INTEGER NOT NULL,
            difficulty INTEGER NOT NULL,
            workload INTEGER NOT NULL,
            interest INTEGER NOT NULL,
            reviewtext TEXT NOT NULL,
            semester TEXT,
            dateposted TIMESTAMP DEFAULT (datetime('now')),
            FOREIGN KEY (courseid) REFERENCES courses (id)
        )
        """
    )

    professorpool = [
        "Dr. Thompson",
        "Ms. Rodriguez",
        "Mr. Chen",
        "Dr. Martinez",
        "Prof. Blake",
        "Dr. Harrison",
        "Ms. Williams",
        "Mr. Johnson",
        "Dr. Anderson",
        "Ms. Lee",
        "Prof. Kumar",
        "Dr. Zhang",
        "Mr. Brown",
        "Dr. Green",
        "Ms. Clark",
        "Prof. Walker",
        "Dr. Adams",
        "Ms. Rivera",
        "Mr. Collins",
        "Dr. Foster",
        "Prof. Bennett",
        "Dr. Patel",
        "Ms. Singh",
        "Mr. Davis",
        "Dr. Wilson",
        "Ms. Morgan",
        "Prof. Taylor",
        "Dr. Romano",
        "Ms. Wang",
        "Mr. Garcia",
        "Dr. Nakamura",
        "Prof. Hernandez",
        "Dr. Dubois",
        "Ms. Kim",
        "Mr. Miller",
        "Prof. Jones",
    ]

    # only load the large csv once on a fresh db
    addedcourses = 0
    existingcourses = cur.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
    if existingcourses == 0:
        # fresh db path: build insert batch from csv
        coursebatch = []
        with open("choatecoursesp2284cleaned.csv", "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for index, raw in enumerate(reader):
                row = cleankeys(raw)
                coursecode = row.get("coursecode", "").strip()
                coursename = row.get("title", "").strip()
                description = (
                    row.get("fulldescription")
                    or row.get("sectionblurb")
                    or "A Choate Rosemary Hall course."
                ).strip()
                if len(description) > 500:
                    # cap long descriptions so rows stay manageable
                    description = description[:497] + "..."
                department = departmentfromcode(coursecode)
                professor = professorpool[index % len(professorpool)]
                coursebatch.append(
                    (coursecode, coursename, department, professor, description)
                )

        cur.executemany(
            """
            INSERT INTO courses (coursecode, coursename, department, professor, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            coursebatch,
        )
        addedcourses = len(coursebatch)
    else:
        # existing db path: skip reseeding courses
        coursebatch = []

    # create a default login user if it does not exist yet
    adminusername = os.environ.get("APPADMINUSERNAME", "admin")
    adminpassword = os.environ.get("APPADMINPASSWORD", "admin123")
    cur.execute(
        "INSERT OR IGNORE INTO users (username, passwordhash) VALUES (?, ?)",
        (adminusername, hashpassword(adminpassword)),
    )
    # rowcount is 1 when user was inserted, 0 when already present
    admincreated = cur.rowcount == 1

    # starter reviews make the app look populated from day one
    samplereviews = [
        (
            1,
            5,
            1,
            2,
            5,
            "This class was a great reset in my schedule because the atmosphere was supportive and low pressure. We still worked hard on technique each week, but the teacher gave clear demos and specific feedback that made progress feel realistic even for beginners.",
            "Fall 2025",
        ),
        (
            15,
            4,
            2,
            3,
            4,
            "A strong introduction to music theory that balanced concepts with actual playing time. The ukulele practice helped me hear chord progressions in context, and short quizzes kept me accountable without feeling overwhelming.",
            "Fall 2025",
        ),
        (
            18,
            5,
            2,
            3,
            5,
            "The course connected historical events, cultural context, and musical innovation in a way that finally made jazz chronology stick for me. Listening journals took time, but class discussion made every unit feel alive and relevant.",
            "Spring 2025",
        ),
        (
            25,
            5,
            2,
            2,
            5,
            "This class pushed me out of my comfort zone in a good way through scene work, voice drills, and frequent reflection. Feedback from both peers and the teacher was direct but respectful, so confidence grew week by week.",
            "Winter 2025",
        ),
        (
            30,
            4,
            2,
            3,
            4,
            "I improved most in proportion and shading because assignments were sequenced from fundamentals to more complex compositions. Critique days were detailed and practical, and I could see clear growth when comparing early and late sketches.",
            "Spring 2025",
        ),
        (
            100,
            5,
            3,
            4,
            5,
            "Discussion quality was high because everyone came prepared and the instructor asked sharp follow up questions. Writing expectations were rigorous, but the draft feedback was concrete, which helped me make meaningful revisions instead of surface edits.",
            "Fall 2025",
        ),
        (
            150,
            4,
            4,
            5,
            3,
            "Calculus moved quickly and problem sets were long, but instruction was organized and examples in class matched assessment style. Office hours were essential for me, and once I started using them consistently my quiz scores improved.",
            "Fall 2025",
        ),
        (
            120,
            5,
            2,
            3,
            5,
            "The readings were challenging but chosen well, and seminar discussions consistently linked historical themes to current issues without feeling forced. Major papers required real argument development, so I left the term writing with much more precision.",
            "Spring 2025",
        ),
        (
            50,
            5,
            2,
            3,
            5,
            "Lab days were the highlight because we did real data collection and had to explain method choices, not just follow steps. The workload was steady across the term, but the structure made it manageable if you planned ahead.",
            "Winter 2025",
        ),
        (
            40,
            5,
            3,
            4,
            5,
            "A very solid foundation in programming fundamentals with a good mix of guided exercises and open ended projects. Debugging was emphasized early, and that focus helped me become much more independent by the final assignment.",
            "Fall 2025",
        ),
        (
            62,
            4,
            3,
            3,
            4,
            "Conversation drills felt repetitive at first, but they clearly improved fluency and confidence in spontaneous speaking. The instructor corrected mistakes in the moment and gave targeted phrases to practice before the next class.",
            "Winter 2025",
        ),
        (
            74,
            5,
            2,
            2,
            5,
            "The demonstrations made abstract chemistry concepts easier to visualize, especially before lab write ups and tests. Assessments were fair and closely aligned with class practice, so preparation felt efficient rather than guesswork.",
            "Spring 2025",
        ),
        (
            132,
            4,
            4,
            4,
            4,
            "The reading load was heavy and sometimes technical, but lectures and discussion sections translated models into concrete examples. Group activities were useful for testing assumptions, and exam prompts rewarded clear reasoning over memorization.",
            "Fall 2025",
        ),
        (
            205,
            5,
            3,
            3,
            5,
            "Seminar debate was thoughtful and respectful, and we were expected to support claims with close reading rather than vague opinions. Written feedback was specific about logic and structure, which noticeably improved my argument essays.",
            "Winter 2025",
        ),
        (
            260,
            4,
            3,
            4,
            4,
            "Problem sets were demanding and required multi step reasoning, but they reflected what we practiced in class and review sessions. Lab reports took effort, yet they helped connect theory to measurement in a way that improved test performance.",
            "Spring 2025",
        ),
        (
            9,
            4,
            2,
            3,
            4,
            "The class had clear expectations and each assignment built naturally on the previous one. I liked that feedback came quickly, so I could fix mistakes before the next deadline.",
            "Fall 2025",
        ),
        (
            27,
            5,
            3,
            4,
            5,
            "This was one of my favorite classes because discussions were active and connected ideas across units really well. The projects took effort, but I felt like every assignment had a clear purpose.",
            "Winter 2025",
        ),
        (
            43,
            4,
            3,
            3,
            4,
            "Course pacing was steady and manageable if you kept up with weekly tasks. The instructor explained difficult topics using examples that were easy to remember later on quizzes.",
            "Spring 2025",
        ),
        (
            58,
            5,
            2,
            2,
            5,
            "I enjoyed the class structure because we mixed short lectures with hands-on work almost every day. It made the content more interesting and helped concepts stick long term.",
            "Fall 2025",
        ),
        (
            76,
            4,
            3,
            4,
            4,
            "The assignments were challenging but fair, and rubric expectations were very clear. Review sessions before major assessments were useful and reduced a lot of stress.",
            "Spring 2025",
        ),
        (
            88,
            5,
            2,
            3,
            5,
            "Group work was actually productive in this class because roles were defined and checkpoints were built in. I learned a lot from hearing other approaches during peer feedback.",
            "Winter 2025",
        ),
        (
            111,
            4,
            4,
            4,
            4,
            "There was a lot of reading, but class notes and review guides made preparation realistic. The teacher was approachable and gave practical suggestions for improving essays.",
            "Fall 2025",
        ),
        (
            173,
            5,
            3,
            3,
            5,
            "The final project tied together everything from earlier units and felt rewarding to complete. I appreciated that grading focused on both understanding and effort instead of perfection.",
            "Spring 2025",
        ),
    ]

    # seed sample reviews only for a fresh db
    addedreviews = 0
    existingreviews = cur.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
    if existingreviews == 0:
        # fresh reviews path: insert starter review rows
        cur.executemany(
            """
            INSERT INTO reviews (courseid, overallrating, difficulty, workload, interest, reviewtext, semester)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            samplereviews,
        )
        addedreviews = len(samplereviews)

    con.commit()
    cur.execute(
        """
        SELECT department, COUNT(*) countvalue
        FROM courses
        GROUP BY department
        ORDER BY countvalue DESC
        """
    )
    summary = cur.fetchall()
    con.close()

    # print a quick setup summary for local dev
    print("=" * 62)
    print("DATABASE READY")
    print("=" * 62)
    print(f"Database path: {dbpath}")
    print(f"Added {addedcourses} courses")
    print(f"Added {addedreviews} sample reviews")
    if admincreated:
        # brand new admin user was created this run
        print(f"Created login user: {adminusername}")
    else:
        # admin already existed before this run
        print(f"Login user already exists: {adminusername}")
    print("Top departments:")
    for dept, countvalue in summary[:15]:
        print(f" - {dept}: {countvalue}")
    print("=" * 62)
    print("Run: python app.py")


if __name__ == "__main__":
    # run db init when this file is executed directly
    builddatabase()
