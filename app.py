import os
import json
import sys
import subprocess
import threading
import time
import tempfile
from flask import Flask, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from functools import wraps

app = Flask(__name__, static_folder='static', static_url_path='')
app.secret_key = 'antigravity-secret-key' # Replace with a real secret for production
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
# Use threading mode for maximum compatibility on Python 3.13 / Windows
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', logger=True, engineio_logger=True)

# Store active sessions
active_sessions = {}

# Language configurations for local execution
# Resolve real path for Python to avoid Windows App Execution Alias issues
REAL_PYTHON = os.path.realpath(sys.executable)

LANGUAGE_CONFIG = {
    "python": {
        "compile": None,
        "run": [REAL_PYTHON, "-u", "{file}"],
        "ext": ".py"
    },
    "c": {
        "compile": ["gcc", "-o", "{output}", "{file}"],
        "run": ["{output}"],
        "ext": ".c"
    },
    "cpp": {
        "compile": ["g++", "-o", "{output}", "{file}"],
        "run": ["{output}"],
        "ext": ".cpp"
    },
    "java": {
        "compile": ["javac", "{file}"],
        "run": ["java", "{classname}"],
        "ext": ".java",
        "main_file": "Main.java"
    },
    "csharp": {
        "compile": [r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe", "/out:{output}", "{file}"],
        "run": ["{output}"],
        "ext": ".cs"
    }
}

# Helper functions for data management
DATA_DIR = "data"

def get_data_path(filename):
    return os.path.join(DATA_DIR, filename)

def load_json(filename):
    path = get_data_path(filename)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(filename, data):
    path = get_data_path(filename)
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_permissions():
    """Load permissions configuration"""
    return load_json("permissions.json")

def has_permission(username, permission):
    """Check if user has specific permission"""
    users = load_json("users.json")
    user = next((u for u in users if u["username"] == username), None)
    if not user:
        return False
    
    # Get role permissions
    perms_config = load_permissions()
    role = user.get("role", "student")
    role_perms = perms_config.get("roles", {}).get(role, {}).get("permissions", [])
    
    # Super admin has all permissions
    if "*" in role_perms:
        return True
    
    # Check custom permissions
    custom_perms = user.get("custom_permissions", [])
    
    return permission in role_perms or permission in custom_perms

def get_user_permissions(username):
    """Get all permissions for a user"""
    users = load_json("users.json")
    user = next((u for u in users if u["username"] == username), None)
    if not user:
        return []
    
    perms_config = load_permissions()
    role = user.get("role", "student")
    role_perms = perms_config.get("roles", {}).get(role, {}).get("permissions", [])
    
    if "*" in role_perms:
        # Return all permissions
        return list(perms_config.get("permissions", {}).keys())
    
    custom_perms = user.get("custom_permissions", [])
    return list(set(role_perms + custom_perms))

# Auth Decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

def instructor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'instructor':
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated_function

def permission_required(permission):
    """Decorator to check if user has specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'username' not in session:
                return jsonify({"error": "Authentication required"}), 401
            
            if not has_permission(session['username'], permission):
                return jsonify({"error": "Permission denied"}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route("/")
@login_required
def index():
    # Redirect based on role - check if user has any admin permissions
    if 'username' in session:
        role = session.get('role', 'student')
        if role != 'student':
            return redirect(url_for('admin_page'))
    return redirect(url_for('student_dashboard_page'))

@app.route("/exercise")
@login_required
def exercise_page():
    response = app.send_static_file("sinhvien/exercise.html")
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

@app.route("/login")
def login_page():
    return app.send_static_file("login.html")

@app.route("/admin")
@app.route("/admin/dashboard")
@login_required
@instructor_required
def admin_page():
    return app.send_static_file("admin/dashboard.html")

@app.route("/admin/problems")
@login_required
@instructor_required
def admin_problems_page():
    return app.send_static_file("admin/problems.html")

@app.route("/admin/students")
@login_required
@instructor_required
def admin_students_page():
    return app.send_static_file("admin/students.html")

@app.route("/admin/reports")
@login_required
@instructor_required
def admin_reports_page():
    return app.send_static_file("admin/reports.html")

@app.route("/admin/exams")
@login_required
@instructor_required
def admin_exams_list_page():
    return app.send_static_file("admin/exams.html")

@app.route("/admin/submissions")
@login_required
@instructor_required
def admin_submissions_page():
    return app.send_static_file("admin/submissions.html")

@app.route("/admin/edit-problem")
@login_required
@permission_required("manage_problems")
def edit_problem_page():
    return app.send_static_file("admin/edit-problem.html")

@app.route("/admin/create-exam")
@login_required
@permission_required("manage_exams")
def create_exam_page():
    return app.send_static_file("admin/create-exam.html")

@app.route("/exam")
@login_required
def exam_page():
    # Frontend reads id from URL ?id=X
    return app.send_static_file("sinhvien/exam.html")

@app.route("/exams")
@login_required
def student_exams_list_page():
    return app.send_static_file("sinhvien/exams.html")

@app.route("/history")
@login_required
def student_history_page():
    return app.send_static_file("sinhvien/history.html")

@app.route("/dashboard")
@login_required
def student_dashboard_page():
    return app.send_static_file("sinhvien/dashboard.html")

@app.route("/profile")
@login_required
def student_profile_page():
    return app.send_static_file("sinhvien/profile.html")

@app.route("/admin/roles")
@login_required
@permission_required("manage_roles")
def admin_roles_page():
    return app.send_static_file("admin/roles.html")

@app.route("/admin/user-permissions")
@login_required
@permission_required("manage_roles")
def admin_user_permissions_page():
    return app.send_static_file("admin/user-permissions.html")


@app.route("/api/auth/login", methods=["POST"])
def api_login():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    
    users = load_json("users.json")
    user = next((u for u in users if u["username"] == username and u["password"] == password), None)
    
    if user:
        session['username'] = user['username']
        session['role'] = user['role']
        session['display_name'] = user.get('display_name', user['username'])
        
        # Track student logins specifically
        if user['role'] == 'student':
            try:
                hits = load_json("hits.json")
                hits["student_logins"] = hits.get("student_logins", 0) + 1
                
                today = time.strftime("%Y-%m-%d")
                daily_students = hits.get("daily_student_logins", {})
                daily_students[today] = daily_students.get(today, 0) + 1
                hits["daily_student_logins"] = daily_students
                
                save_json("hits.json", hits)
            except Exception as e:
                print(f"Error tracking student login: {e}")
                
        return jsonify({"status": "success", "role": user['role']})
    return jsonify({"status": "error", "message": "Sai tài khoản hoặc mật khẩu"}), 401

@app.route("/api/auth/logout")
def api_logout():
    session.clear()
    return redirect(url_for('login_page'))

@app.route("/api/auth/me")
def api_me():
    if 'username' in session:
        return jsonify({
            "username": session['username'],
            "role": session['role'],
            "display_name": session.get('display_name')
        })
    return jsonify({"error": "Not logged in"}), 401

@app.route("/api/auth/update-info", methods=["PUT"])
@login_required
def update_info():
    data = request.json
    username = session.get("username")
    display_name = data.get("display_name")
    class_name = data.get("class_name")
    
    users = load_json("users.json")
    found = False
    for user in users:
        if user["username"] == username:
            if display_name:
                user["display_name"] = display_name
                session['display_name'] = display_name
            if class_name:
                user["class_name"] = class_name
            found = True
            break
    
    if found:
        save_json("users.json", users)
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "User not found"}), 404

@app.route("/api/auth/change-password", methods=["PUT"])
@login_required
def change_password():
    data = request.json
    username = session.get("username")
    current_password = data.get("current_password")
    new_password = data.get("new_password")
    
    users = load_json("users.json")
    user_idx = next((i for i, u in enumerate(users) if u["username"] == username), -1)
    
    if user_idx == -1:
        return jsonify({"status": "error", "message": "User not found"}), 404
        
    if users[user_idx]["password"] != current_password:
        return jsonify({"status": "error", "message": "Mật khẩu hiện tại không đúng"}), 400
        
    users[user_idx]["password"] = new_password
    save_json("users.json", users)
    return jsonify({"status": "success"})

@app.route("/problems")
@login_required
def get_problems():
    try:
        data = load_json("problems.json")
        submissions = load_json("submissions.json")
        
        # Get solved problem IDs for current user
        user_solved_ids = set([
            s["problemId"] for s in submissions 
            if s["username"] == session.get("username")
        ])

        # Return info with solved status
        minimal_list = [
            {
                "id": p["id"], 
                "title": p["title"], 
                "difficulty": p["difficulty"], 
                "category": p.get("category", ""),
                "solved": p["id"] in user_solved_ids
            }
            for p in data
        ]
        return jsonify(minimal_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/problems/<int:pid>")
@login_required
def get_problem_detail(pid):
    problems = load_json("problems.json")
    problem = next((p for p in problems if p["id"] == pid), None)
    if not problem:
        return jsonify({"error": "Problem not found"}), 404
    return jsonify(problem)

# Administrative APIs - Statistics
@app.route("/api/admin/stats")
@login_required
@instructor_required
def get_stats():
    problems = load_json("problems.json")
    users = load_json("users.json")
    submissions = load_json("submissions.json")
    exams = load_json("tests.json")
    hits = load_json("hits.json")
    
    # Language distribution
    langs = {}
    for s in submissions:
        lang = s.get("language", "unknown")
        langs[lang] = langs.get(lang, 0) + 1
    
    # Exam stats
    active_exams = [e for e in exams if e.get("isActive", True)]
    exam_subs = [s for s in submissions if s.get("examId")]
    
    # Exam activity
    recent_exam_subs = []
    for s in exam_subs[-10:]:
        ex = next((e for e in exams if e["id"] == s.get("examId")), {"title": "Unknown"})
        recent_exam_subs.append({
            "username": s["username"],
            "examTitle": ex["title"],
            "problemTitle": s.get("problemTitle", f"ID: {s['problemId']}"),
            "timestamp": s["timestamp"]
        })
    
    return jsonify({
        "problem_count": len(problems),
        "student_count": len([u for u in users if u["role"] == "student"]),
        "submission_count": len(submissions),
        "total_hits": hits.get("total_hits", 0),
        "student_logins": hits.get("student_logins", 0),
        "languages": langs,
        "recent_activity": submissions[-10:] if submissions else [],
        "exam_count": len(exams),
        "active_exam_count": len(active_exams),
        "exam_submission_count": len(exam_subs),
        "recent_exam_activity": recent_exam_subs
    })

# Middleware-like function for traffic tracking
@app.before_request
def track_traffic():
    if request.path.startswith('/static') or request.path.startswith('/api/auth/me'):
        return
    
    try:
        hits = load_json("hits.json")
        hits["total_hits"] = hits.get("total_hits", 0) + 1
        
        today = time.strftime("%Y-%m-%d")
        daily = hits.get("daily_hits", {})
        daily[today] = daily.get(today, 0) + 1
        hits["daily_hits"] = daily
        
        save_json("hits.json", hits)
    except Exception as e:
        print(f"Error tracking traffic: {e}")

# Administrative APIs - Problems
@app.route("/api/admin/problems", methods=["POST"])
@login_required
@permission_required("manage_problems")
def add_problem():
    new_prob = request.json
    problems = load_json("problems.json")
    # Generate ID
    new_prob["id"] = max([p["id"] for p in problems], default=0) + 1
    problems.append(new_prob)
    save_json("problems.json", problems)
    return jsonify({"status": "success", "id": new_prob["id"]})

@app.route("/api/admin/students/list", methods=["GET"])
@login_required
@instructor_required
def get_all_students_for_selection():
    users = load_json("users.json")
    students = [{
        "username": u["username"],
        "display_name": u.get("display_name", u["username"]),
        "class_name": u.get("class_name", "--")
    } for u in users if u.get("role") == "student"]
    return jsonify(students)

@app.route("/api/admin/problems/<int:pid>", methods=["PUT", "DELETE"])
@login_required
@permission_required("manage_problems")
def manage_problem(pid):
    problems = load_json("problems.json")
    if request.method == "DELETE":
        problems = [p for p in problems if p["id"] != pid]
        save_json("problems.json", problems)
        return jsonify({"status": "success"})
    elif request.method == "PUT":
        data = request.json
        for p in problems:
            if p["id"] == pid:
                p.update(data)
                break
        save_json("problems.json", problems)
        return jsonify({"status": "success"})

# Administrative APIs - Exams
@app.route("/api/admin/exams", methods=["GET", "POST"])
@login_required
@permission_required("manage_exams")
def manage_exams():
    if request.method == "GET":
        return jsonify(load_json("tests.json"))
    
    new_exam = request.json
    exams = load_json("tests.json")
    
    # Generate ID and starting metadata
    new_exam["id"] = max([e["id"] for e in exams], default=0) + 1
    if "startTime" not in new_exam:
        new_exam["startTime"] = time.strftime("%Y-%m-%d %H:%M:%S")
    
    exams.append(new_exam)
    save_json("tests.json", exams)
    return jsonify({"status": "success", "id": new_exam["id"]})

@app.route("/api/admin/exams/<int:eid>", methods=["GET", "PUT", "DELETE"])
@login_required
@permission_required("manage_exams")
def manage_single_exam(eid):
    exams = load_json("tests.json")
    exam_idx = next((i for i, e in enumerate(exams) if e["id"] == eid), -1)
    
    if exam_idx == -1:
        return jsonify({"error": "Exam not found"}), 404
        
    if request.method == "GET":
        return jsonify(exams[exam_idx])
        
    if request.method == "PUT":
        updated_data = request.json
        # Maintain ID
        updated_data["id"] = eid
        exams[exam_idx] = updated_data
        save_json("tests.json", exams)
        return jsonify({"status": "success"})
        
    if request.method == "DELETE":
        exams.pop(exam_idx)
        save_json("tests.json", exams)
        return jsonify({"status": "success"})

@app.route("/api/exams/active")
@login_required
def get_active_exams():
    exams = load_json("tests.json")
    active_exams = [e for e in exams if e.get("isActive", True)]
    
    # Filter for students
    role = session.get("role")
    username = session.get("username")
    
    # DEBUG LOGGING (REMOVE LATER)
    with open("debug_log.txt", "a", encoding="utf-8") as f:
        f.write(f"\n--- API Call: /api/exams/active ---\nUser: {username}, Role: {role}\n")
    
    if role == "student":
        filtered_exams = []
        for exam in active_exams:
            allowed = exam.get("allowedStudents", [])
            
            # Check logic
            can_see = True
            if allowed and username not in allowed:
                can_see = False
            
            with open("debug_log.txt", "a", encoding="utf-8") as f:
                f.write(f"Exam {exam['id']} ({exam['title']}): Allowed={allowed}, UserIn={username in allowed}, Result={can_see}\n")
                
            if not can_see:
                continue
            filtered_exams.append(exam)
        return jsonify(filtered_exams)
        
    return jsonify(active_exams)

@app.route("/api/exams/<int:eid>")
@login_required
def get_exam_detail(eid):
    exams = load_json("tests.json")
    exam = next((e for e in exams if e["id"] == eid), None)
    if not exam:
        return jsonify({"error": "Exam not found"}), 404
        
    # Access control by allowedStudents for students
    if session.get("role") != "instructor":
        allowed_students = exam.get("allowedStudents", [])
        if allowed_students and session.get("username") not in allowed_students:
            return jsonify({"error": "Bạn không có quyền tham gia kỳ thi này."}), 403

        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%dT%H:%M") # Match input format
        open_time = exam.get("openTime")
        close_time = exam.get("closeTime")
        
        if open_time and now < open_time:
            return jsonify({"error": "Kỳ thi chưa đến thời gian thực hành. Mở lúc: " + open_time.replace("T", " ")}), 403
        if close_time and now > close_time:
            return jsonify({"error": "Kỳ thi đã kết thúc vào lúc: " + close_time.replace("T", " ")}), 403
        if not exam.get("isActive", True):
            return jsonify({"error": "Kỳ thi hiện đang đóng."}), 403
        
    all_problems = load_json("problems.json")
    exam_problems = [p for p in all_problems if p["id"] in exam["problemIds"]]
    
    # Attach points to each problem
    points_map = exam.get("problemPoints", {})
    for p in exam_problems:
        p["points"] = points_map.get(str(p["id"]), 0)
    
    # Fetch student's latest submissions for this exam if not instructor
    last_subs = {}
    if session.get("role") != "instructor":
        submissions = load_json("submissions.json")
        # Filter for this user and this exam
        user_exam_subs = [s for s in submissions if s["username"] == session["username"] and str(s.get("examId")) == str(eid)]
        # Get latest code for each problem
        for s in sorted(user_exam_subs, key=lambda x: x.get("timestamp", "")):
            last_subs[str(s["problemId"])] = {
                "code": s.get("code", ""),
                "allPassed": s.get("allPassed", False),
                "language": s.get("language", "python"),
                "timeRemaining": s.get("timeRemaining")
            }

    # Strip sensitive info and attach last submission for students
    if session.get("role") != "instructor":
        for p in exam_problems:
            p.pop("hint", None)
            p.pop("solution_code", None)
            p.pop("language_hints", None)
            p["last_submission"] = last_subs.get(str(p["id"]))
            
    return jsonify({
        "info": exam,
        "problems": exam_problems
    })

# Student Dashboard APIs
@app.route("/api/student/exams/summary")
@login_required
def get_student_exams_summary():
    username = session.get("username")
    exams = load_json("tests.json")
    submissions = load_json("submissions.json")
    
    summary = []
    user_subs = [s for s in submissions if s["username"] == username]
    
    for exam in exams:
        # Filtering by allowedStudents
        allowed_students = exam.get("allowedStudents", [])
        if allowed_students and username not in allowed_students:
            continue

        # Calculate total possible points
        points_map = exam.get("problemPoints", {})
        total_possible = sum(points_map.values())
        
        # Calculate achieved points
        achieved = 0
        solved_in_exam = []
        
        # We only count submissions made in "exam" mode for this specific exam
        # And only the latest/best one per problem? Actually any success counts.
        # Wait, submissions in the current system don't seem to have a "status" field in the JSON I saw. 
        # Ah, they are only saved if successful in the frontend's logic (usually).
        
        # We only count successful submissions made in "exam" mode for this specific exam
        exam_subs = [s for s in user_subs if str(s.get("examId")) == str(exam["id"]) and s.get("allPassed") is True]
        solved_ids = set([s["problemId"] for s in exam_subs])
        
        for pid in solved_ids:
            achieved += points_map.get(str(pid), 0)
            solved_in_exam.append(pid)
            
        summary.append({
            "id": exam["id"],
            "title": exam["title"],
            "isActive": exam.get("isActive", True),
            "totalPoints": total_possible,
            "achievedPoints": achieved,
            "problemCount": len(exam["problemIds"]),
            "solvedCount": len(solved_ids),
            "startTime": exam.get("startTime")
        })
        
    return jsonify(summary)

@app.route("/api/student/stats")
@login_required
def get_student_personal_stats():
    username = session.get("username")
    submissions = load_json("submissions.json")
    problems = load_json("problems.json")
    users = load_json("users.json")
    
    user_subs = [s for s in submissions if s["username"] == username]
    # Practice solved (not specifically exam mode)
    solved_ids = set([s["problemId"] for s in user_subs])
    
    # Calculate rank
    student_stats = []
    students = [u for u in users if u["role"] == "student"]
    for s in students:
        s_subs = [sub for sub in submissions if sub["username"] == s["username"]]
        s_solved = len(set([sub["problemId"] for sub in s_subs]))
        student_stats.append({"username": s["username"], "solved": s_solved})
    
    student_stats.sort(key=lambda x: x["solved"], reverse=True)
    rank = next((i + 1 for i, s in enumerate(student_stats) if s["username"] == username), "--")
    
    return jsonify({
        "solved_count": len(solved_ids),
        "total_problems": len(problems),
        "submission_count": len(user_subs),
        "success_rate": round(len(solved_ids) / len(user_subs) * 100, 1) if user_subs else 0,
        "rank": rank,
        "recent_activity": user_subs[-5:][::-1]
    })

def run_single_test(language, code, user_input):
    """Run a single test case for a given language and code."""
    config = LANGUAGE_CONFIG.get(language)
    if not config:
        return {"error": f"Unsupported language: {language}"}

    # Create temp directory
    base_temp = os.path.join(os.getcwd(), "temp_sessions")
    if not os.path.exists(base_temp):
        os.makedirs(base_temp)
    temp_dir = tempfile.mkdtemp(dir=base_temp)

    try:
        ext = config['ext']
        filename = config.get('main_file', f"code{ext}")
        code_file = os.path.join(temp_dir, filename)
        
        with open(code_file, 'w', encoding='utf-8') as f:
            f.write(code)
            
        exe_path = None
        run_cmd_template = config['run']
        
        # Compilation Step
        if config['compile']:
            output_file = os.path.join(temp_dir, "program.exe" if os.name == 'nt' else "program")
            compile_cmd_template = config['compile']
            compile_files = [code_file]
            
            if language == 'c':
                flush_file = os.path.join(temp_dir, "flush_init.c")
                with open(flush_file, 'w', encoding='utf-8') as f: f.write(FLUSH_INIT_C)
                compile_files.append(flush_file)
            elif language == 'cpp':
                flush_file = os.path.join(temp_dir, "flush_init.cpp")
                with open(flush_file, 'w', encoding='utf-8') as f: f.write(FLUSH_INIT_CPP)
                compile_files.append(flush_file)
            
            final_compile_cmd = []
            for arg in compile_cmd_template:
                if "{file}" in arg: final_compile_cmd.append(arg.format(file=code_file, output=output_file))
                elif "{output}" in arg: final_compile_cmd.append(arg.format(output=output_file))
                else: final_compile_cmd.append(arg)
            for extra_file in compile_files[1:]: final_compile_cmd.append(extra_file)

            compile_result = subprocess.run(final_compile_cmd, capture_output=True, text=True, encoding='utf-8', timeout=10)
            if compile_result.returncode != 0:
                return {"error": f"Compilation error:\n{compile_result.stderr}", "output": ""}
            exe_path = output_file
        
        # Run Step
        if exe_path:
            classname = "Main" if language == "java" else None
            run_cmd = [cmd.format(output=exe_path, classname=classname) for cmd in run_cmd_template]
        else:
            run_cmd = [cmd.format(file=code_file, project_dir=temp_dir) for cmd in run_cmd_template]

        process = subprocess.run(
            run_cmd,
            input=user_input,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=5,
            cwd=temp_dir
        )
        return {"output": process.stdout, "error": process.stderr if process.returncode != 0 else None}

    except subprocess.TimeoutExpired:
        return {"error": "Time Limit Exceeded (5s)", "output": ""}
    except Exception as e:
        return {"error": str(e), "output": ""}
    finally:
        import shutil
        try: shutil.rmtree(temp_dir)
        except: pass

@app.route("/api/admin/test-problem", methods=["POST"])
@login_required
@instructor_required
def test_new_problem():
    data = request.json
    language = data.get("language")
    code = data.get("code")
    test_cases = data.get("test_cases", [])
    
    results = []
    for tc in test_cases:
        res = run_single_test(language, code, tc.get("input", ""))
        actual = (res.get("output") or "").strip()
        expected = (tc.get("output") or "").strip()
        results.append({
            "input": tc.get("input"),
            "expected": expected,
            "actual": actual,
            "passed": actual == expected,
            "error": res.get("error")
        })
    
    return jsonify({"results": results})
@app.route("/api/admin/students", methods=["GET", "POST", "PUT"])
@login_required
@instructor_required
def manage_students():
    users = load_json("users.json")
    if request.method == "GET":
        submissions = load_json("submissions.json")
        students = [u for u in users if u["role"] == "student"]
        
        # Enrich students with stats
        for s in students:
            user_subs = [sub for sub in submissions if sub["username"] == s["username"]]
            s["solved_count"] = len(set([sub["problemId"] for sub in user_subs]))
            s["submission_count"] = len(user_subs)
            
            # Find main language
            if user_subs:
                langs = {}
                for sub in user_subs:
                    l = sub["language"]
                    langs[l] = langs.get(l, 0) + 1
                s["main_lang"] = max(langs, key=langs.get).upper()
            else:
                s["main_lang"] = "--"
            
            # Ensure class_name exists
            if "class_name" not in s:
                s["class_name"] = "--"
                
        return jsonify(students)
    elif request.method == "POST":
        new_student = request.json
        new_student["role"] = "student"
        if any(u["username"] == new_student["username"] for u in users):
            return jsonify({"status": "error", "message": "Tên đăng nhập đã tồn tại"}), 400
        users.append(new_student)
        save_json("users.json", users)
        return jsonify({"status": "success"})
    elif request.method == "PUT":
        data = request.json
        username = data.get("username")
        for u in users:
            if u["username"] == username:
                u.update(data)
                break
        save_json("users.json", users)
        return jsonify({"status": "success"})

@app.route("/api/admin/students/<username>/stats")
@login_required
@instructor_required
def get_student_stats(username):
    users = load_json("users.json")
    submissions = load_json("submissions.json")
    
    student = next((u for u in users if u["username"] == username), None)
    if not student:
        return jsonify({"status": "error", "message": "Sinh viên không tồn tại"}), 404
    
    user_subs = [s for s in submissions if s["username"] == username]
    
    # Aggregated stats
    solved_problems = list(set([s["problemId"] for s in user_subs]))
    langs = {}
    for s in user_subs:
        lang = s["language"]
        langs[lang] = langs.get(lang, 0) + 1
        
    return jsonify({
        "info": student,
        "solved_count": len(solved_problems),
        "total_submissions": len(user_subs),
        "languages": langs,
        "recent_activity": user_subs[-10:] if user_subs else []
    })

@app.route("/api/admin/reports")
@login_required
@instructor_required
def get_reports():
    users = load_json("users.json")
    problems = load_json("problems.json")
    submissions = load_json("submissions.json")
    
    # 1. Student Ranking
    students = [u for u in users if u["role"] == "student"]
    student_report = []
    for s in students:
        user_subs = [sub for sub in submissions if sub["username"] == s["username"]]
        solved = set([sub["problemId"] for sub in user_subs])
        student_report.append({
            "username": s["username"],
            "display_name": s["display_name"],
            "class_name": s.get("class_name", "--"),
            "solved_count": len(solved),
            "submission_count": len(user_subs),
            "success_rate": round(len(solved) / len(user_subs) * 100, 1) if user_subs else 0
        })
        
    # 2. Problem Statistics
    problem_report = []
    for p in problems:
        p_subs = [sub for sub in submissions if sub["problemId"] == p["id"]]
        p_passers = set([sub["username"] for sub in p_subs]) 
        
        # Map English difficulty to Vietnamese for consistent UI
        diff_map = {
            "Easy": "Dễ",
            "Medium": "Trung bình",
            "Hard": "Khó"
        }
        raw_diff = p.get("difficulty", "Dễ")
        
        problem_report.append({
            "id": p["id"],
            "title": p["title"],
            "difficulty": diff_map.get(raw_diff, raw_diff), # Use mapped value or fallback to original
            "category": p.get("category", "Chung"),
            "attempt_count": len(p_subs),
            "pass_count": len(p_passers)
        })

    # 3. Exam Reports
    exams = load_json("tests.json")
    exam_report = []
    
    for exam in exams:
        exam_id = exam["id"]
        points_map = exam.get("problemPoints", {})
        
        # All submissions for this exam (regardless of success, to count attendees)
        exam_all_subs = [s for s in submissions if str(s.get("examId")) == str(exam_id)]
        # Successful submissions for score calculation
        exam_pass_subs = [s for s in exam_all_subs if s.get("allPassed") is True]
        
        # Results per student in this exam
        student_results = []
        attendees = set([s["username"] for s in exam_all_subs])
        
        for username in attendees:
            user = next((u for u in students if u["username"] == username), None)
            if not user: continue
            
            user_exam_pass_subs = [s for s in exam_pass_subs if s["username"] == username]
            # Consider only distinct solved problems
            solved_ids = set([s["problemId"] for s in user_exam_pass_subs])
            
            score = 0
            for pid in solved_ids:
                score += points_map.get(str(pid), 0)
                
            student_results.append({
                "username": username,
                "display_name": user["display_name"],
                "class_name": user.get("class_name", "--"),
                "solved_count": len(solved_ids),
                "score": score
            })
        
        exam_report.append({
            "id": exam_id,
            "title": exam["title"],
            "total_points": sum(points_map.values()),
            "problem_count": len(exam["problemIds"]),
            "student_count": len(attendees),
            "results": student_results
        })
        
    return jsonify({
        "students": sorted(student_report, key=lambda x: x["solved_count"], reverse=True),
        "problems": sorted(problem_report, key=lambda x: x["attempt_count"], reverse=True),
        "exams": exam_report
    })

# Admin Pages Routing
@app.route("/admin/report-students")
@login_required
@instructor_required
def admin_report_students_page():
    return app.send_static_file("admin/report-students.html")

@app.route("/admin/report-problems")
@login_required
@instructor_required
def admin_report_problems_page():
    return app.send_static_file("admin/report-problems.html")

@app.route("/admin/report-exams")
@login_required
@instructor_required
def admin_report_exams_page():
    return app.send_static_file("admin/report-exams.html")

@app.route("/admin/report-exam-detail")
@login_required
@instructor_required
def admin_report_exam_detail_page():
    return app.send_static_file("admin/report-exam-detail.html")

@app.route("/admin/report-exam-submissions")
@login_required
@instructor_required
def admin_report_exam_submissions_page():
    return app.send_static_file("admin/report-exam-submissions.html")

# Permission Management APIs
@app.route("/api/admin/permissions/config", methods=["GET"])
@login_required
@permission_required("manage_roles")
def get_permissions_config():
    """Get all roles and permissions configuration"""
    return jsonify(load_permissions())

@app.route("/api/admin/roles", methods=["GET"])
@login_required
def get_roles():
    """Get all available roles"""
    perms = load_permissions()
    return jsonify(perms.get("roles", {}))

@app.route("/api/admin/permissions", methods=["GET"])
@login_required
def get_all_permissions():
    """Get all available permissions"""
    perms = load_permissions()
    return jsonify(perms.get("permissions", {}))

@app.route("/api/admin/users/<username>/permissions", methods=["GET", "PUT"])
@login_required
@permission_required("manage_roles")
def manage_user_permissions(username):
    """Get or update user permissions"""
    users = load_json("users.json")
    user = next((u for u in users if u["username"] == username), None)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    if request.method == "GET":
        return jsonify({
            "username": username,
            "role": user.get("role", "student"),
            "custom_permissions": user.get("custom_permissions", []),
            "all_permissions": get_user_permissions(username)
        })
    
    # PUT - Update permissions
    data = request.json
    new_role = data.get("role")
    custom_perms = data.get("custom_permissions", [])
    
    # Prevent changing super_admin role unless current user is super_admin
    current_user = next((u for u in users if u["username"] == session["username"]), None)
    if user.get("role") == "super_admin" and current_user.get("role") != "super_admin":
        return jsonify({"error": "Only super admin can modify super admin accounts"}), 403
    
    if new_role:
        user["role"] = new_role
    user["custom_permissions"] = custom_perms
    
    save_json("users.json", users)
    return jsonify({"status": "success"})

@app.route("/api/admin/users/non-students", methods=["GET"])
@login_required
@permission_required("manage_roles")
def get_non_student_users():
    """Get all non-student users for permission management"""
    users = load_json("users.json")
    non_students = [
        {
            "username": u["username"],
            "display_name": u.get("display_name", u["username"]),
            "role": u.get("role", "student"),
            "custom_permissions": u.get("custom_permissions", [])
        }
        for u in users if u.get("role") != "student"
    ]
    return jsonify(non_students)

@app.route("/api/admin/users/create", methods=["POST"])
@login_required
@permission_required("manage_roles")
def create_non_student_user():
    """Create a new non-student user"""
    data = request.json
    username = data.get("username", "").strip()
    display_name = data.get("display_name", "").strip()
    password = data.get("password", "")
    role = data.get("role", "instructor")
    custom_permissions = data.get("custom_permissions", [])
    
    # Validation
    if not username or not display_name or not password:
        return jsonify({"status": "error", "message": "Thiếu thông tin bắt buộc"}), 400
    
    if len(username) < 3:
        return jsonify({"status": "error", "message": "Tên đăng nhập phải có ít nhất 3 ký tự"}), 400
    
    if len(password) < 3:
        return jsonify({"status": "error", "message": "Mật khẩu phải có ít nhất 3 ký tự"}), 400
    
    # Check if role is valid and not student
    perms_config = load_permissions()
    if role not in perms_config.get("roles", {}) or role == "student":
        return jsonify({"status": "error", "message": "Vai trò không hợp lệ"}), 400
    
    users = load_json("users.json")
    
    # Check if username already exists
    if any(u["username"] == username for u in users):
        return jsonify({"status": "error", "message": "Tên đăng nhập đã tồn tại"}), 400
    
    # Create new user
    new_user = {
        "username": username,
        "password": password,
        "role": role,
        "display_name": display_name,
        "custom_permissions": custom_permissions
    }
    
    users.append(new_user)
    save_json("users.json", users)
    
    return jsonify({"status": "success", "message": "Tạo tài khoản thành công"})

# Permission CRUD APIs
@app.route("/api/admin/permissions", methods=["POST"])
@login_required
@permission_required("manage_roles")
def create_permission():
    """Create a new permission"""
    data = request.json
    perm_key = data.get("key", "").strip()
    perm_name = data.get("name", "").strip()
    perm_desc = data.get("description", "").strip()
    
    if not perm_key or not perm_name:
        return jsonify({"status": "error", "message": "Thiếu thông tin bắt buộc"}), 400
    
    # Validate key format (lowercase, numbers, underscores only)
    import re
    if not re.match(r'^[a-z0-9_]+$', perm_key):
        return jsonify({"status": "error", "message": "Permission key chỉ được chứa chữ thường, số và dấu gạch dưới"}), 400
    
    perms_config = load_permissions()
    
    if perm_key in perms_config.get("permissions", {}):
        return jsonify({"status": "error", "message": "Permission key đã tồn tại"}), 400
    
    perms_config.setdefault("permissions", {})[perm_key] = {
        "name": perm_name,
        "description": perm_desc
    }
    
    save_json("permissions.json", perms_config)
    return jsonify({"status": "success", "message": "Tạo permission thành công"})

@app.route("/api/admin/permissions/<perm_key>", methods=["PUT", "DELETE"])
@login_required
@permission_required("manage_roles")
def manage_permission(perm_key):
    """Update or delete a permission"""
    perms_config = load_permissions()
    
    if perm_key not in perms_config.get("permissions", {}):
        return jsonify({"status": "error", "message": "Permission không tồn tại"}), 404
    
    if request.method == "DELETE":
        # Check if permission is used in any role
        for role_key, role_data in perms_config.get("roles", {}).items():
            if perm_key in role_data.get("permissions", []):
                return jsonify({"status": "error", "message": f"Permission đang được sử dụng bởi role '{role_data.get('name', role_key)}'"}), 400
        
        del perms_config["permissions"][perm_key]
        save_json("permissions.json", perms_config)
        return jsonify({"status": "success", "message": "Xóa permission thành công"})
    
    # PUT - Update
    data = request.json
    perms_config["permissions"][perm_key] = {
        "name": data.get("name", ""),
        "description": data.get("description", "")
    }
    save_json("permissions.json", perms_config)
    return jsonify({"status": "success", "message": "Cập nhật permission thành công"})

@app.route("/api/admin/roles/<role_key>/permissions", methods=["PUT"])
@login_required
@permission_required("manage_roles")
def update_role_permissions(role_key):
    """Update permissions for a role"""
    perms_config = load_permissions()
    
    if role_key not in perms_config.get("roles", {}):
        return jsonify({"status": "error", "message": "Role không tồn tại"}), 404
    
    # Prevent modifying super_admin
    if role_key == "super_admin":
        return jsonify({"status": "error", "message": "Không thể sửa quyền của super_admin"}), 403
    
    data = request.json
    new_perms = data.get("permissions", [])
    
    # Validate all permissions exist
    all_perms = perms_config.get("permissions", {})
    for perm in new_perms:
        if perm not in all_perms:
            return jsonify({"status": "error", "message": f"Permission '{perm}' không tồn tại"}), 400
    
    perms_config["roles"][role_key]["permissions"] = new_perms
    save_json("permissions.json", perms_config)
    return jsonify({"status": "success", "message": "Cập nhật role thành công"})

# Tracking & Submissions
@app.route("/api/submissions", methods=["GET", "POST"])
@login_required
def handle_submissions():
    if request.method == "POST":
        data = request.json
        data["username"] = session["username"]
        data["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Consistent timeRemaining and code handling
        if "timeRemaining" not in data and "time_remaining" in data:
            data["timeRemaining"] = data.pop("time_remaining")
            
        submissions = load_json("submissions.json")
        submissions.append(data)
        save_json("submissions.json", submissions)
        return jsonify({"status": "success"})
    
    # GET: Fetch tracking info
    submissions = load_json("submissions.json")
    if session["role"] == "instructor":
        return jsonify(submissions)
    else:
        # Student only sees their own
        user_subs = [s for s in submissions if s["username"] == session["username"]]
        return jsonify(user_subs)

@app.route("/api/admin/exams/<int:eid>/submissions")
@login_required
@instructor_required
def get_exam_submissions(eid):
    submissions = load_json("submissions.json")
    exam_subs = [s for s in submissions if str(s.get("examId")) == str(eid)]
    return jsonify(exam_subs)

@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')
    emit('connected', {'status': 'ready'})

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected: {request.sid}')
    cleanup_session(request.sid)

# C code to disable buffering
FLUSH_INIT_C = r"""
#include <stdio.h>
#include <stdlib.h>

#ifdef _WIN32
#include <windows.h>
#endif

void __attribute__((constructor)) flush_init() {
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);
}
"""

# C++ code to disable buffering
FLUSH_INIT_CPP = r"""
#include <iostream>
#include <stdio.h>

class FlushInit {
public:
    FlushInit() {
        std::setvbuf(stdout, NULL, _IONBF, 0);
        std::setvbuf(stderr, NULL, _IONBF, 0);
        std::cout.setf(std::ios::unitbuf);
        std::cerr.setf(std::ios::unitbuf);
    }
};

static FlushInit flush_init_obj;
"""

@socketio.on('start_session')
def handle_start_session(data):
    session_id = request.sid
    language = data.get('language')
    code = data.get('code')
    
    print(f'Starting session {session_id} for language {language}')
    
    # Cleanup any existing session
    cleanup_session(session_id)
    
    try:
        # Create temp directory for this session
        config = LANGUAGE_CONFIG.get(language)
        if not config:
            emit('error', {'message': f'Unsupported language: {language}'})
            return
        
         # Use a local temp directory to avoid path/permission issues on Windows
        base_temp = os.path.join(os.getcwd(), "temp_sessions")
        if not os.path.exists(base_temp):
            os.makedirs(base_temp)
            
        temp_dir = tempfile.mkdtemp(dir=base_temp)
        ext = config['ext']
        
        # Java needs specific filename
        filename = config.get('main_file', f"code{ext}")
        code_file = os.path.join(temp_dir, filename)
        
        with open(code_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        # Compile if needed
        if config['compile']:
            output_file = os.path.join(temp_dir, "program.exe" if os.name == 'nt' else "program")
            
            # Prepare compilation command
            compile_cmd_template = config['compile']
            compile_files = [code_file]
            
            # Inject flushing code for C/C++
            if language == 'c':
                flush_file = os.path.join(temp_dir, "flush_init.c")
                with open(flush_file, 'w', encoding='utf-8') as f:
                    f.write(FLUSH_INIT_C)
                compile_files.append(flush_file)
            elif language == 'cpp':
                flush_file = os.path.join(temp_dir, "flush_init.cpp")
                with open(flush_file, 'w', encoding='utf-8') as f:
                    f.write(FLUSH_INIT_CPP)
                compile_files.append(flush_file)
            
            # Construct the compile command
            # The template usually looks like ["gcc", "-o", "{output}", "{file}"]
            # We need to replace "{file}" with all source files
            
            # Simplistic approach: replace "{file}" in the template with the primary file,
            # and append the extra files to the end of the command (before -o if possible, or just append)
            # GCC/G++ allows input files anywhere.
            
            final_compile_cmd = []
            for arg in compile_cmd_template:
                if "{file}" in arg:
                    # Replace {file} with the main code file
                    final_compile_cmd.append(arg.format(file=code_file, output=output_file))
                elif "{output}" in arg:
                    final_compile_cmd.append(arg.format(output=output_file))
                else:
                    final_compile_cmd.append(arg)
            
            # Append extra source files (flushing logic)
            # We skip the first file in compile_files because it was likely handled by {file} replacement
            # actually we should be careful. let's just append the extra files to the command list.
            for extra_file in compile_files[1:]:
                final_compile_cmd.append(extra_file)

            try:
                compile_result = subprocess.run(
                    final_compile_cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    timeout=10
                )
                
                if compile_result.returncode != 0:
                    emit('error', {'message': f'Compilation error:\n{compile_result.stderr}'})
                    cleanup_session(session_id)
                    return
                
                # For compiled languages, classname/classname might still be needed (e.g. Java)
                classname = "Main" if language == "java" else None
                run_cmd = [cmd.format(output=output_file, classname=classname) for cmd in config['run']]
            except FileNotFoundError:
                emit('error', {'message': f'System error: Compiler not found for {language}. Please install it to run code locally.'})
                cleanup_session(session_id)
                return
        else:
            # For interpreted languages
            run_cmd = [cmd.format(file=code_file, project_dir=temp_dir) for cmd in config['run']]
            
        print(f"Executing: {' '.join(run_cmd)}")
        # Send the command to the terminal so user knows what's happening
        emit('output', {'data': f"\r\n[Lệnh chạy]: {' '.join(run_cmd)}\r\n\r\n", 'session_id': session_id})
        
        # Start the process - Redirect stderr to stdout to see all errors
        process = subprocess.Popen(
            run_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=False, # Use binary mode for unbuffered I/O
            bufsize=0,  # Unbuffered
            cwd=temp_dir
        )
        
        # Store session info
        active_sessions[session_id] = {
            'process': process,
            'temp_dir': temp_dir,
            'language': language
        }
        
        # Start threads to read output
        stdout_thread = threading.Thread(target=read_output, args=(session_id, process.stdout, 'stdout'), daemon=True)
        stdout_thread.start()
        
        # Store thread in session so we can join it later
        active_sessions[session_id]['stdout_thread'] = stdout_thread
        
        # threading.Thread(target=read_output, args=(session_id, process.stderr, 'stderr'), daemon=True).start() # Stderr is redirected to stdout
        threading.Thread(target=monitor_process, args=(session_id,), daemon=True).start()
        
        emit('session_started', {'status': 'running'})
        
    except Exception as e:
        print(f'Error starting session: {e}')
        emit('error', {'message': f'Error: {str(e)}'})
        cleanup_session(session_id)

@socketio.on('send_input')
def handle_input(data):
    session_id = request.sid
    user_input = data.get('input', '')
    
    session = active_sessions.get(session_id)
    if not session:
        emit('error', {'message': 'No active session'})
        return
    
    process = session['process']
    
    try:
        if process.poll() is None:  # Process still running
            # Encode input for binary mode
            process.stdin.write((user_input + '\n').encode('utf-8'))
            process.stdin.flush()
    except Exception as e:
        print(f'Error sending input: {e}')
        emit('error', {'message': f'Error sending input: {str(e)}'})

@socketio.on('run_test_cases')
def handle_run_test_cases(data):
    session_id = request.sid
    language = data.get('language')
    code = data.get('code')
    test_cases = data.get('test_cases', [])
    
    print(f'Running test cases for session {session_id}, language {language}')
    
    # Create temp directory
    # Use a local temp directory to avoid path/permission issues on Windows
    # We use a new temp dir per test run to keep things clean
    base_temp = os.path.join(os.getcwd(), "temp_sessions")
    if not os.path.exists(base_temp):
        os.makedirs(base_temp)
    temp_dir = tempfile.mkdtemp(dir=base_temp)
    
    try:
        config = LANGUAGE_CONFIG.get(language)
        if not config:
            emit('error', {'message': f'Unsupported language: {language}'})
            return

        ext = config['ext']
        filename = config.get('main_file', f"code{ext}")
        code_file = os.path.join(temp_dir, filename)
        
        with open(code_file, 'w', encoding='utf-8') as f:
            f.write(code)
            
        # Compile ONCE
        exe_path = None
        run_cmd_template = config['run']
        
        if config['compile']:
            output_file = os.path.join(temp_dir, "program.exe" if os.name == 'nt' else "program")
            
            # Re-use the compilation logic from start_session (checking for injection)
            compile_cmd_template = config['compile']
            compile_files = [code_file]
            
            if language == 'c':
                flush_file = os.path.join(temp_dir, "flush_init.c")
                with open(flush_file, 'w', encoding='utf-8') as f:
                    f.write(FLUSH_INIT_C)
                compile_files.append(flush_file)
            elif language == 'cpp':
                flush_file = os.path.join(temp_dir, "flush_init.cpp")
                with open(flush_file, 'w', encoding='utf-8') as f:
                    f.write(FLUSH_INIT_CPP)
                compile_files.append(flush_file)
            
            final_compile_cmd = []
            for arg in compile_cmd_template:
                if "{file}" in arg:
                    final_compile_cmd.append(arg.format(file=code_file, output=output_file))
                elif "{output}" in arg:
                    final_compile_cmd.append(arg.format(output=output_file))
                else:
                    final_compile_cmd.append(arg)
            for extra_file in compile_files[1:]:
                final_compile_cmd.append(extra_file)

            try:
                compile_result = subprocess.run(
                    final_compile_cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    timeout=10
                )
                if compile_result.returncode != 0:
                    emit('test_results', {'error': f'Compilation error:\n{compile_result.stderr}'})
                    return
                exe_path = output_file
            except Exception as e:
                emit('test_results', {'error': f'Compilation failed: {str(e)}'})
                return
        
        # Prepare run command
        if exe_path:
             # For compiled
            classname = "Main" if language == "java" else None
            run_cmd = [cmd.format(output=exe_path, classname=classname) for cmd in run_cmd_template]
        else:
             # For interpreted
            run_cmd = [cmd.format(file=code_file, project_dir=temp_dir) for cmd in run_cmd_template]

        results = []
        
        for i, case in enumerate(test_cases):
            case_input = case.get('input', '')
            case_expected = case.get('output', '')
            
            try:
                # Use binary mode (text=False) for consistent behavior with our fix
                process = subprocess.Popen(
                    run_cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=False,
                    bufsize=0,
                    cwd=temp_dir
                )
                
                try:
                    stdout_data, _ = process.communicate(input=(case_input + '\n').encode('utf-8'), timeout=5)
                    actual_output = stdout_data.decode('utf-8', errors='replace')
                except subprocess.TimeoutExpired:
                    process.kill()
                    actual_output = "Error: Timeout (5s)"
                
                # Normalize text for comparison (ignore trailing whitespace/newlines differences)
                passed = normalize_text(actual_output) == normalize_text(case_expected)
                
                # Check if actual output merely CONTAINS the expected output (sometimes prompts are included)
                # But for competitive programming style, typically we want clean output.
                # However, since we forced prompts to appear immediateley, they are part of stdout.
                # If the problem asks for "Sum: 8", but user prints "Input a: Input b: Sum: 8", we might need smarter matching.
                # For now, let's try strict normalization, but maybe strip prompts if we could identify them?
                # Actually, standard CP problems usually don't print prompts like "Input a:". 
                # But this is a learning app. Users write prompts.
                # Let's trust the logic: existing test cases in problems.json for "A+B" only show numbers.
                # If the user code prints prompts, it will fail current test cases. 
                # We should probably modify the usage instructions or the test cases to include prompts?
                # Or invalid solution?
                # Let's stick to standard strict comparison for now.
                
                results.append({
                    'input': case_input,
                    'expected': case_expected,
                    'actual': actual_output,
                    'passed': passed
                })
                
            except Exception as e:
                 results.append({
                    'input': case_input,
                    'expected': case_expected,
                    'actual': f"Error: {str(e)}",
                    'passed': False
                })

        emit('test_results', {'results': results})

    except Exception as e:
        print(f"Error in run_test_cases: {e}")
        emit('test_results', {'error': str(e)})
        
    finally:
        # Cleanup
        try:
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except:
            pass

def normalize_text(text):
    """Normalize text for comparison: strip whitespace, unify newlines"""
    if not text: return ""
    return "\n".join([line.rstrip() for line in text.strip().splitlines() if line.strip()])


@socketio.on('stop_session')
def handle_stop_session():
    session_id = request.sid
    cleanup_session(session_id)
    emit('session_ended', {'reason': 'stopped by user'})

def read_output(session_id, stream, stream_type):
    """Read output from process and emit to client"""
    try:
        # Read character by character for a more interactive feel
        while True:
            # Read bytes in binary mode
            byte = stream.read(1)
            if not byte:
                break
            
            # Note: We removed the check 'if session_id not in active_sessions'
            # to ensure we finish reading the stream even if cleanup has started,
            # provided the stream is still open and yielding data.
            
            # Decode byte to string
            try:
                char = byte.decode('utf-8', errors='replace')
            except:
                char = '?'
                
            socketio.emit('output', {
                'data': char,
                'type': stream_type
            }, room=session_id)
    except Exception as e:
        print(f'Error reading {stream_type}: {e}')
    finally:
        stream.close()

def monitor_process(session_id):
    """Monitor process and cleanup when it exits"""
    session = active_sessions.get(session_id)
    if not session:
        return
    
    process = session['process']
    stdout_thread = session.get('stdout_thread')
    
    try:
        # Wait for process to complete (with timeout)
        process.wait(timeout=60)
        
        # After process finishes, wait for the output reader to finish flushing
        if stdout_thread and stdout_thread.is_alive():
            stdout_thread.join(timeout=2)
            
    except subprocess.TimeoutExpired:
        print(f'Process timeout for session {session_id}')
        process.kill()
        socketio.emit('error', {
            'message': 'Process timeout (60s limit)'
        }, room=session_id)
    
    # Emit session ended
    socketio.emit('session_ended', {
        'reason': 'process completed',
        'exit_code': process.returncode
    }, room=session_id)
    
    # Cleanup
    cleanup_session(session_id)

def cleanup_session(session_id):
    """Clean up session resources"""
    session = active_sessions.pop(session_id, None)
    if not session:
        return
    
    process = session['process']
    temp_dir = session['temp_dir']
    
    # Kill process if still running
    if process.poll() is None:
        try:
            process.kill()
            process.wait(timeout=5)
        except:
            pass
    
    # Clean up temp directory
    try:
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    except Exception as e:
        print(f'Error cleaning up temp dir: {e}')


def cleanup_dangling_temps():
    """Clean up any dangling temporary directories from previous runs"""
    try:
        current_dir = os.getcwd()
        # Clean up temp_sessions directory content but keep the directory
        temp_sessions = os.path.join(current_dir, "temp_sessions")
        if os.path.exists(temp_sessions):
            try:
                import shutil
                shutil.rmtree(temp_sessions)
                os.makedirs(temp_sessions)
                print("Cleaned up temp_sessions directory")
            except Exception as e:
                print(f"Warning: Could not clean temp_sessions: {e}")

        # Clean up legacy temp_* directories in root
        for name in os.listdir(current_dir):
            if name.startswith("temp_") and os.path.isdir(os.path.join(current_dir, name)):
                if name == "temp_sessions": continue
                try:
                    import shutil
                    shutil.rmtree(os.path.join(current_dir, name))
                    print(f"Removed dangling temp dir: {name}")
                except Exception as e:
                    print(f"Warning: Could not remove {name}: {e}")
    except Exception as e:
        print(f"Error during cleanup: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("Server starting on http://localhost:5001")
    print("Python version:", os.sys.version)
    print("Async mode: threading")
    
    # Clean up temp files on startup
    cleanup_dangling_temps()
    
    print("=" * 50)
    
    socketio.run(app, host='0.0.0.0', port=5001, debug=True, use_reloader=False)
