import csv
import sqlite3


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


def cleankeys(item):
    clean = {}
    for key, value in item.items():
        newkey = key.replace(chr(95), "").replace("-", "")
        clean[newkey] = value
    return clean


def builddatabase():
    con = sqlite3.connect("courses.db")
    cur = con.cursor()

    cur.execute("DROP TABLE IF EXISTS reviews")
    cur.execute("DROP TABLE IF EXISTS courses")

    cur.execute(
        """
        CREATE TABLE courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            coursecode TEXT NOT NULL,
            coursename TEXT NOT NULL,
            department TEXT NOT NULL,
            professor TEXT,
            description TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE reviews (
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

    samplereviews = [
        (
            1,
            5,
            1,
            2,
            5,
            "Such a fun class! No dance experience needed. Really supportive environment.",
            "Fall 2025",
        ),
        (
            15,
            4,
            2,
            3,
            4,
            "Great intro to music theory with ukulele practice.",
            "Fall 2025",
        ),
        (
            18,
            5,
            2,
            3,
            5,
            "Jazz history was fascinating and very well taught.",
            "Spring 2025",
        ),
        (
            25,
            5,
            2,
            2,
            5,
            "Acting class was supportive and confidence building.",
            "Winter 2025",
        ),
        (
            30,
            4,
            2,
            3,
            4,
            "Drawing class improved my technical skills a lot.",
            "Spring 2025",
        ),
        (
            100,
            5,
            3,
            4,
            5,
            "Great discussion and strong writing growth.",
            "Fall 2025",
        ),
        (
            150,
            4,
            4,
            5,
            3,
            "Calculus was hard but clearly taught.",
            "Fall 2025",
        ),
        (
            120,
            5,
            2,
            3,
            5,
            "History discussion connected past and present well.",
            "Spring 2025",
        ),
        (
            50,
            5,
            2,
            3,
            5,
            "Biology labs were practical and engaging.",
            "Winter 2025",
        ),
        (
            40,
            5,
            3,
            4,
            5,
            "Excellent introduction to programming fundamentals.",
            "Fall 2025",
        ),
    ]

    cur.executemany(
        """
        INSERT INTO reviews (courseid, overallrating, difficulty, workload, interest, reviewtext, semester)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        samplereviews,
    )

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

    print("=" * 62)
    print("DATABASE READY")
    print("=" * 62)
    print(f"Added {len(coursebatch)} courses")
    print(f"Added {len(samplereviews)} sample reviews")
    print("Top departments:")
    for dept, countvalue in summary[:15]:
        print(f" - {dept}: {countvalue}")
    print("=" * 62)
    print("Run: python app.py")


builddatabase()
