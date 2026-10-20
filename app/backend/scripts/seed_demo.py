"""Load demo data through the CareerGPS API.

Creates a few demo students (emails @example.com) with education, skills,
experience, and projects, and turns on sharing so their projects appear in
GET /projects search results.

Usage (from app/backend):
    python scripts/seed_demo.py                                   # local API on :8000
    python scripts/seed_demo.py --api https://careergps-backend-n1uj.onrender.com

Safe to re-run: students that already exist are skipped. The demo accounts' password
is printed once at the end. To remove the demo data, delete the demo users in
Supabase (Table Editor > users); everything they own is deleted with them.
"""

import argparse
import secrets
import sys

import httpx

STUDENTS = [
    {
        "name": "Maya Chen",
        "email": "maya.chen.demo@example.com",
        "profile": {
            "headline": "Computer Engineering student building robots and embedded systems",
            "bio": "Junior at SFSU who likes making hardware and software talk to each other.",
            "location": "San Francisco, CA",
            "career_interests": ["Embedded Systems Engineer", "Robotics"],
        },
        "education": [{"school_name": "San Francisco State University", "degree": "B.S.", "major": "Computer Engineering",
                       "graduation_date": "2027-05-22", "coursework": ["CSC 615 Embedded Linux", "CSC 648 Software Engineering"]}],
        "skills": [("C", "technical"), ("Python", "technical"), ("Raspberry Pi", "technical"), ("Team leadership", "leadership")],
        "experience": [{"experience_type": "internship", "organization": "Bay Robotics Lab", "position": "Firmware Intern",
                        "start_date": "2026-06-01", "end_date": "2026-08-15",
                        "description": "Wrote motor-control firmware and sensor drivers for a warehouse robot prototype."}],
        "projects": [
            {"title": "Line Following Robot", "subject": "Embedded Systems", "project_date": "Spring 2026",
             "technologies": ["C", "Raspberry Pi", "I2C"],
             "description": "Autonomous car that follows a line, reacts to colored markers, and avoids obstacles using multithreaded sensor polling."},
            {"title": "Tapeless Ruler", "subject": "Embedded Systems", "project_date": "Spring 2026",
             "technologies": ["C", "HC-SR04", "Raspberry Pi"],
             "description": "Measures distance with an ultrasonic sonar sensor and shows readings on an LCD."},
            {"title": "Smart Plant Monitor", "subject": "Internet of Things", "project_date": "Fall 2025",
             "technologies": ["Python", "MQTT", "ESP32"],
             "description": "Soil-moisture sensors that publish readings to a dashboard and send watering alerts."},
        ],
    },
    {
        "name": "Jordan Rivera",
        "email": "jordan.rivera.demo@example.com",
        "profile": {
            "headline": "Full-stack developer focused on accessible web apps",
            "bio": "Senior CS student who enjoys building tools people use every day.",
            "location": "Oakland, CA",
            "career_interests": ["Frontend Developer", "Full-Stack Developer"],
        },
        "education": [{"school_name": "San Francisco State University", "degree": "B.S.", "major": "Computer Science",
                       "graduation_date": "2026-12-18", "coursework": ["CSC 648 Software Engineering", "CSC 675 Databases"]}],
        "skills": [("React", "technical"), ("JavaScript", "technical"), ("FastAPI", "technical"), ("Public speaking", "communication")],
        "experience": [{"experience_type": "work", "organization": "Campus IT Help Desk", "position": "Student Developer",
                        "start_date": "2025-01-15", "is_current": True,
                        "description": "Maintain the internal ticket dashboard and automate account provisioning scripts."}],
        "projects": [
            {"title": "Campus Budget Tracker", "subject": "Web Development", "project_date": "Fall 2025",
             "technologies": ["React", "Python", "PostgreSQL"],
             "description": "Web app for students to track spending, set savings goals, and see monthly charts."},
            {"title": "Accessible Course Planner", "subject": "Web Development", "project_date": "Spring 2026",
             "technologies": ["React", "TypeScript", "ARIA"],
             "description": "Drag-and-drop semester planner built to WCAG AA with full keyboard support."},
            {"title": "Study Group Finder", "subject": "Mobile Development", "project_date": "Fall 2026",
             "technologies": ["React Native", "Firebase"],
             "description": "Mobile app that matches students in the same course into study groups by availability."},
        ],
    },
    {
        "name": "Priya Nair",
        "email": "priya.nair.demo@example.com",
        "profile": {
            "headline": "Data science student interested in healthcare analytics",
            "bio": "I like turning messy data into decisions.",
            "location": "Daly City, CA",
            "career_interests": ["Data Scientist", "Machine Learning Engineer"],
        },
        "education": [{"school_name": "San Francisco State University", "degree": "B.S.", "major": "Data Science",
                       "graduation_date": "2027-05-22", "coursework": ["MATH 324 Probability", "CSC 671 Machine Learning"]}],
        "skills": [("Python", "technical"), ("pandas", "technical"), ("SQL", "technical"), ("Data storytelling", "communication")],
        "experience": [{"experience_type": "research", "organization": "SFSU Health Equity Lab", "position": "Undergraduate Researcher",
                        "start_date": "2025-09-01", "is_current": True,
                        "description": "Clean and analyze clinic visit data to study wait-time disparities."}],
        "projects": [
            {"title": "Clinic Wait-Time Predictor", "subject": "Machine Learning", "project_date": "Spring 2026",
             "technologies": ["Python", "scikit-learn", "pandas"],
             "description": "Regression model that predicts clinic wait times from appointment and staffing data."},
            {"title": "Bay Area Air Quality Dashboard", "subject": "Data Visualization", "project_date": "Fall 2025",
             "technologies": ["Python", "Plotly", "SQL"],
             "description": "Interactive dashboard of daily air-quality readings with wildfire-season comparisons."},
            {"title": "Course Review Sentiment Analysis", "subject": "Machine Learning", "project_date": "Fall 2026",
             "technologies": ["Python", "NLP", "Hugging Face"],
             "description": "Classifies course reviews as positive or negative and surfaces common complaints."},
        ],
    },
    {
        "name": "Diego Alvarez",
        "email": "diego.alvarez.demo@example.com",
        "profile": {
            "headline": "Architecture student combining design and 3D modeling",
            "bio": "I design spaces and show them off as interactive 3D models.",
            "location": "San Jose, CA",
            "career_interests": ["Architectural Designer", "3D Visualization Artist"],
        },
        "education": [{"school_name": "San Francisco State University", "degree": "B.A.", "major": "Interior Design",
                       "graduation_date": "2027-12-17", "coursework": ["DAI 330 Digital Modeling", "DAI 451 Studio"]}],
        "skills": [("Blender", "technical"), ("AutoCAD", "technical"), ("SketchUp", "technical"), ("Client presentations", "communication")],
        "experience": [{"experience_type": "volunteer", "organization": "Habitat for Humanity", "position": "Design Volunteer",
                        "start_date": "2025-03-01", "end_date": "2025-11-30",
                        "description": "Drafted floor plans for affordable housing renovations."}],
        "projects": [
            {"title": "Modular Tiny House", "subject": "Architecture", "project_date": "Spring 2026",
             "technologies": ["Blender", "SketchUp"],
             "description": "Tiny-house design with movable walls, presented as an interactive 3D walkthrough."},
            {"title": "Library Reading Room Redesign", "subject": "Interior Design", "project_date": "Fall 2025",
             "technologies": ["AutoCAD", "Blender"],
             "description": "Redesigned a campus reading room for natural light and flexible seating."},
            {"title": "Scanned Sculpture Gallery", "subject": "3D Modeling", "project_date": "Fall 2026",
             "technologies": ["Niantic Scaniverse", "Blender", "glTF"],
             "description": "Photogrammetry scans of campus sculptures cleaned up and exported as glTF models."},
        ],
    },
]


def check(response: httpx.Response, what: str) -> dict:
    if response.is_error:
        sys.exit(f"Failed to {what}: {response.status_code} {response.text[:300]}")
    return response.json() if response.content else {}


def seed_student(client: httpx.Client, student: dict, password: str) -> bool:
    signup = client.post("/auth/signup", json={"name": student["name"], "email": student["email"], "password": password})
    if signup.status_code == 409:
        print(f"  skip  {student['name']} (already exists)")
        return False
    token = check(signup, f"sign up {student['email']}")["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    try:
        check(client.patch("/portfolio/me", json=student["profile"]), "update profile")
        for edu in student["education"]:
            check(client.post("/portfolio/me/education", json=edu), "add education")
        for name, category in student["skills"]:
            check(client.post("/portfolio/me/skills", json={"name": name, "category": category}), "add skill")
        for exp in student["experience"]:
            check(client.post("/portfolio/me/experience", json=exp), "add experience")
        for project in student["projects"]:
            check(client.post("/projects", json=project), f"add project {project['title']}")
        check(client.post("/portfolio/me/share"), "turn on sharing")
    finally:
        client.headers.pop("Authorization", None)
    print(f"  added {student['name']}: {len(student['projects'])} projects")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--api", default="http://localhost:8000", help="API base URL")
    args = parser.parse_args()

    password = f"Demo-{secrets.token_urlsafe(9)}1"
    # Render's free tier can take ~50s to wake up, hence the long timeout.
    with httpx.Client(base_url=args.api.rstrip("/"), timeout=90) as client:
        check(client.get("/health"), "reach the API")
        print(f"Seeding {args.api}")
        created = [s for s in STUDENTS if seed_student(client, s, password)]
        browse = client.get("/projects", params={"limit": 100})

    if browse.status_code == 200:
        print(f"\nDone. {len(browse.json())} projects are now searchable at {args.api.rstrip('/')}/projects")
    else:
        print(f"\nDone, but GET /projects returned {browse.status_code}: this API version has no public search yet.")
    if created:
        print(f"Demo login password for the new accounts: {password}")
        print("Demo emails: " + ", ".join(s["email"] for s in created))


if __name__ == "__main__":
    main()
