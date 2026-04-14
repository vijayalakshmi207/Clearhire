import os
import hashlib
import secrets
from datetime import datetime

import pandas as pd
from flask import Flask, render_template_string, request, redirect, url_for, session, send_file
from flask_session import Session
import PyPDF2

# ============================================
# FLASK APP SETUP
# ============================================

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# ============================================
# FILE SETUP
# ============================================

DATA_DIR = "data"
UPLOAD_DIR = "uploads"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

ADMIN_FILE = f"{DATA_DIR}/admins.csv"
STUDENT_FILE = f"{DATA_DIR}/students.csv"
QUESTION_FILE = f"{DATA_DIR}/questions.csv"
RESULT_FILE = f"{DATA_DIR}/results.csv"
SETTINGS_FILE = f"{DATA_DIR}/settings.csv"


# ============================================
# INIT FILES
# ============================================

def init_files():
    if not os.path.exists(ADMIN_FILE):
        df = pd.DataFrame([{
            "admin_id": "ADM001",
            "username": "admin",
            "password": hashlib.md5("admin123".encode()).hexdigest(),
            "email": "admin@system.com",
            "created_date": datetime.now()
        }])
        df.to_csv(ADMIN_FILE, index=False)

    if not os.path.exists(STUDENT_FILE):
        pd.DataFrame(columns=[
            "student_id","name","reg_no","email","phone","cgpa","department",
            "skills","projects","certifications","hackathons","password"
        ]).to_csv(STUDENT_FILE, index=False)

    if not os.path.exists(QUESTION_FILE):
        pd.DataFrame(columns=[
            "question_id","question","option_a","option_b",
            "option_c","option_d","answer","category"
        ]).to_csv(QUESTION_FILE, index=False)

    if not os.path.exists(RESULT_FILE):
        pd.DataFrame(columns=[
            "student_id","exam_score","final_score","status"
        ]).to_csv(RESULT_FILE, index=False)

    if not os.path.exists(SETTINGS_FILE):
        pd.DataFrame([{"passing_score": 80}]).to_csv(SETTINGS_FILE, index=False)


init_files()


# ============================================
# HOME
# ============================================

@app.route("/")
def home():
    session.clear()
    return "<h2>Placement System Running 🚀</h2><p>Go to /admin/login or /student/login</p>"


# ============================================
# ADMIN LOGIN
# ============================================

@app.route("/admin/login", methods=["GET","POST"])
def admin_login():
    if request.method == "POST":
        u = request.form["username"]
        p = hashlib.md5(request.form["password"].encode()).hexdigest()

        df = pd.read_csv(ADMIN_FILE)
        user = df[(df["username"] == u) & (df["password"] == p)]

        if len(user) > 0:
            session["admin"] = True
            return redirect("/admin/dashboard")

        return "Invalid login"

    return '''
    <form method="post">
        <input name="username" placeholder="admin"><br>
        <input name="password" type="password"><br>
        <button>Login</button>
    </form>
    '''


# ============================================
# ADMIN DASHBOARD
# ============================================

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin"):
        return redirect("/admin/login")

    students = pd.read_csv(STUDENT_FILE)
    questions = pd.read_csv(QUESTION_FILE)

    return f"""
    <h2>Admin Dashboard</h2>
    <p>Students: {len(students)}</p>
    <p>Questions: {len(questions)}</p>
    <a href='/logout'>Logout</a>
    """


# ============================================
# STUDENT REGISTER
# ============================================

@app.route("/student/register", methods=["GET","POST"])
def student_register():
    if request.method == "POST":
        df = pd.read_csv(STUDENT_FILE)

        sid = f"STU{len(df)+1:03d}"

        new = {
            "student_id": sid,
            "name": request.form["name"],
            "reg_no": request.form["reg_no"],
            "email": request.form["email"],
            "phone": request.form["phone"],
            "cgpa": request.form["cgpa"],
            "department": request.form["department"],
            "skills": request.form["skills"],
            "projects": "",
            "certifications": "",
            "hackathons": 0,
            "password": hashlib.md5(request.form["password"].encode()).hexdigest()
        }

        df = pd.concat([df, pd.DataFrame([new])])
        df.to_csv(STUDENT_FILE, index=False)

        return f"Registered! Your ID: {sid}"

    return '''
    <form method="post">
        <input name="name" placeholder="name"><br>
        <input name="reg_no"><br>
        <input name="email"><br>
        <input name="phone"><br>
        <input name="cgpa"><br>
        <input name="department"><br>
        <input name="skills"><br>
        <input name="password" type="password"><br>
        <button>Register</button>
    </form>
    '''


# ============================================
# STUDENT LOGIN
# ============================================

@app.route("/student/login", methods=["GET","POST"])
def student_login():
    if request.method == "POST":
        u = request.form["username"]
        p = hashlib.md5(request.form["password"].encode()).hexdigest()

        df = pd.read_csv(STUDENT_FILE)
        user = df[(df["student_id"] == u) | (df["email"] == u)]
        user = user[user["password"] == p]

        if len(user) > 0:
            session["student_id"] = user.iloc[0]["student_id"]
            return redirect("/student/dashboard")

        return "Invalid login"

    return '''
    <form method="post">
        <input name="username"><br>
        <input name="password" type="password"><br>
        <button>Login</button>
    </form>
    '''


# ============================================
# STUDENT DASHBOARD
# ============================================

@app.route("/student/dashboard")
def student_dashboard():
    if not session.get("student_id"):
        return redirect("/student/login")

    df = pd.read_csv(STUDENT_FILE)
    st = df[df["student_id"] == session["student_id"]].iloc[0]

    return f"""
    <h2>Welcome {st['name']}</h2>
    <p>Reg No: {st['reg_no']}</p>
    <p>CGPA: {st['cgpa']}</p>
    <a href='/logout'>Logout</a>
    """


# ============================================
# LOGOUT
# ============================================

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ============================================
# RUN (RENDER SAFE)
# ============================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
