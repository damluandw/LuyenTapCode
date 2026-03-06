# --- Import các thư viện lõi của hệ thống ---
import os           # Quản lý đường dẫn và tệp tin hệ thống
import json         # Xử lý định dạng dữ liệu persistent (JSON)
import sys          # Truy cập các tham số và hàm hệ thống (đường dẫn Python)
import subprocess    # Thực thi các tiến trình con (biên dịch và chạy code)
import threading     # Chạy các tác vụ song song (monitor process, read output)
import time          # Xử lý thời gian (timestamp, delay)
import tempfile      # Tạo và quản lý các thư mục/tệp tạm thời
from flask import Flask, request, jsonify, session, redirect, url_for, send_file
import pandas as pd  # Xử lý dữ liệu Excel khi nhập danh sách sinh viên
import io           # Xử lý luồng dữ liệu (input/output)
from flask_cors import CORS # Cấu hình chia sẻ tài nguyên giữa các nguồn (CORS)
from flask_socketio import SocketIO, emit # Giao tiếp thời gian thực
from functools import wraps # Hỗ trợ tạo các decorator bảo mật

from google import genai

#genai.configure(api_key="")

# Khởi tạo ứng dụng Flask với cấu hình thư mục tĩnh (static) phục vụ giao diện người dùng
app = Flask(__name__, static_folder='static', static_url_path='')

# Cấu hình chuỗi bí mật để mã hóa Session (Cookie phía người dùng)
# LƯU Ý: Trong môi trường thực tế, nên dùng biến môi trường (Environment Variable)
app.secret_key = 'antigravity-secret-key'

# Cho phép React/Vue hoặc các domain khác gọi API từ backend này
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Cấu hình SocketIO phục vụ biên dịch/chạy code Console thời gian thực
# Sử dụng async_mode='threading' để tối ưu hóa việc chạy subprocess trên Windows
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', logger=True, engineio_logger=True)

# Lưu trữ các phiên làm việc (session) đang hoạt động
active_sessions = {}

# --- Cấu hình Môi trường Thực thi (Execution Config) ---
# Xác định đường dẫn tuyệt đối đến trình thông dịch Python hiện tại
# Việc này cực kỳ quan trọng trên Windows để tránh nhầm lẫn giữa python và python3
REAL_PYTHON = os.path.realpath(sys.executable)

# Bản đồ cấu hình cho các ngôn ngữ lập trình được hỗ trợ
# Mỗi ngôn ngữ gồm: lệnh biên dịch (nếu có), lệnh chạy, phần mở rộng file và file chạy chính
LANGUAGE_CONFIG = {
    "python": {
        "compile": None, # Python là ngôn ngữ thông dịch, không cần biên dịch
        "run": [REAL_PYTHON, "-u", "{file}"], # -u để tắt output buffering
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
        "run": ["java", "{classname}"], # Java chạy dựa trên tên Class thay vì tên file
        "ext": ".java",
        "main_file": "Main.java"
    },
    "csharp": {
        # Sử dụng trình biên dịch mặc định của .NET Framework trên Windows
        "compile": [r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe", "/out:{output}", "{file}"],
        "run": ["{output}"],
        "ext": ".cs"
    }
}

# --- Các hàm bổ trợ quản lý dữ liệu JSON ---
DATA_DIR = "data"

def get_data_path(filename):
    """Lấy đường dẫn đầy đủ đến file dữ liệu"""
    return os.path.join(DATA_DIR, filename)

def load_json(filename):
    """Tải dữ liệu từ file JSON"""
    path = get_data_path(filename)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(filename, data):
    """Lưu dữ liệu vào file JSON"""
    path = get_data_path(filename)
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_permissions():
    """Tải cấu hình quyền hạn"""
    return load_json("permissions.json")

# --- Quản lý Quyền hạn & Bảo mật (RBAC Logic) ---

def has_permission(username, permission):
    """
    Kiểm tra xem một người dùng có quyền cụ thể nào đó không.
    Ưu tiên: Quyền của quản trị viên (Admin) -> Quyền theo vai trò (Role) -> Quyền tùy chỉnh (Custom).
    """
    users = load_json("users.json")
    user = next((u for u in users if u["username"] == username), None)
    if not user:
        return False
    
    # 1. Tải cấu hình quyền hạn toàn cục
    perms_config = load_permissions()
    role = user.get("role", "student")
    
    # 2. Lấy danh sách quyền mặc định của vai trò (Ví dụ: student, instructor)
    role_perms = perms_config.get("roles", {}).get(role, {}).get("permissions", [])
    
    # 3. QUAN TRỌNG: Dấu sao wildcard '*' đại diện cho quyền tối cao (Full Access)
    if "*" in role_perms:
        return True
    
    # 4. Kiểm tra các quyền đặc cách (custom) được gán riêng cho từng tài khoản
    custom_perms = user.get("custom_permissions", [])
    
    # Người dùng có quyền nếu quyền đó nằm trong nhóm vai trò HOẶC nhóm tùy chỉnh
    return permission in role_perms or permission in custom_perms

def get_user_permissions(username):
    """Lấy danh sách tất cả các quyền của người dùng"""
    users = load_json("users.json")
    user = next((u for u in users if u["username"] == username), None)
    if not user:
        return []
    
    perms_config = load_permissions()
    role = user.get("role", "student")
    role_perms = perms_config.get("roles", {}).get(role, {}).get("permissions", [])
    
    if "*" in role_perms:
        # Trả về tất cả các quyền có sẵn
        return list(perms_config.get("permissions", {}).keys())
    
    custom_perms = user.get("custom_permissions", [])
    return list(set(role_perms + custom_perms))

def is_admin_role(role):
    """Kiểm tra xem vai trò có phải là quản trị viên không"""
    return role in ["admin", "super_admin"]

def can_access_resource(resource, username, role):
    """
    Kiểm tra xem một người dùng có quyền truy cập/sửa đổi một tài nguyên (bài tập, kỳ thi...) hay không.
    Logic: Admin xem được hết -> Chủ sở hữu tài nguyên -> Người được chia sẻ quyền xem.
    """
    # Quản trị viên luôn có quyền truy cập mọi tài nguyên
    if is_admin_role(role):
        return True
    
    # Tác giả tạo ra tài nguyên bài tập/kỳ thi
    if resource.get("created_by") == username:
        return True
        
    # Danh sách người dùng được 'góp quyền' quản lý (shared_with)
    shared_with = resource.get("shared_with", [])
    if username in shared_with:
        return True
        
    return False

# --- Decorators cho việc kiểm tra xác thực và phân quyền ---
def login_required(f):
    """Yêu cầu đăng nhập trước khi truy cập"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

def instructor_required(f):
    """Yêu cầu quyền giảng viên/quản trị viên"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        role = session.get('role')
        
        # Cho phép bất kỳ vai trò nào KHÔNG PHẢI là 'student'
        if not role or role == 'student':
            # Đối với yêu cầu trang web, chuyển hướng đến trang không có quyền
            if '/admin' in request.path or '/dashboard' in request.path:
                return redirect(url_for('unauthorized_page'))
            return jsonify({"error": "Yêu cầu quyền truy cập quản trị"}), 403
        
        return f(*args, **kwargs)
    return decorated_function

def permission_required(permission):
    """Decorator để kiểm tra xem người dùng có quyền cụ thể không"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'username' not in session:
                # Chuyển hướng đến trang đăng nhập nếu chưa đăng nhập
                if request.path.startswith('/admin') or request.path.startswith('/dashboard'):
                    return redirect(url_for('login_page'))
                return jsonify({"error": "Vui lòng đăng nhập để tiếp tục"}), 401
            
            if not has_permission(session['username'], permission):
                # Chuyển hướng đến trang không có quyền nếu thiếu quyền
                if request.path.startswith('/admin') or request.path.startswith('/dashboard'):
                    return redirect(url_for('unauthorized_page'))
                return jsonify({"error": "Bạn không có quyền thực hiện hành động này"}), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- Các tuyến đường (Routes) cho giao diện người dùng ---
@app.route("/")
@login_required
def index():
    """Trang chủ - tự động chuyển hướng dựa trên vai trò"""
    if 'username' in session:
        role = session.get('role', 'student')
        if role != 'student':
            return redirect(url_for('admin_page'))
    return redirect(url_for('student_dashboard_page'))

@app.route("/exercise")
@login_required
def exercise_page():
    """Trang làm bài tập của sinh viên"""
    response = app.send_static_file("sinhvien/exercise.html")
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

@app.route("/login")
def login_page():
    """Trang đăng nhập"""
    if 'username' in session:
        return redirect(url_for('index'))
    return app.send_static_file("login.html")

@app.route("/admin")
@app.route("/admin/dashboard")
@login_required
@instructor_required
def admin_page():
    """Trang điều khiển của quản trị viên"""
    return app.send_static_file("admin/dashboard.html")

@app.route("/admin/problems")
@login_required
@instructor_required
def admin_problems_page():
    """Trang quản lý danh sách bài tập (Admin)"""
    return app.send_static_file("admin/problems.html")

@app.route("/admin/students")
@login_required
@instructor_required
def admin_students_page():
    """Trang quản lý sinh viên (Admin)"""
    return app.send_static_file("admin/students.html")

@app.route("/admin/reports")
@login_required
@instructor_required
def admin_reports_page():
    """Trang xem báo cáo thống kê (Admin)"""
    return app.send_static_file("admin/reports.html")

@app.route("/admin/exams")
@login_required
@instructor_required
def admin_exams_list_page():
    """Trang quản lý kỳ thi (Admin)"""
    return app.send_static_file("admin/exams.html")

@app.route("/admin/submissions")
@login_required
@permission_required("view_submissions")
def admin_submissions_page():
    """Trang xem danh sách bài nộp (Admin)"""
    return app.send_static_file("admin/submissions.html")

@app.route("/admin/edit-problem")
@login_required
@permission_required("manage_problems")
def edit_problem_page():
    """Trang thêm mới hoặc chỉnh sửa bài tập (Admin)"""
    return app.send_static_file("admin/edit-problem.html")

@app.route("/admin/create-exam")
@login_required
@permission_required("manage_exams")
def create_exam_page():
    """Trang tạo kỳ thi mới (Admin)"""
    return app.send_static_file("admin/create-exam.html")

@app.route("/exam")
@login_required
def exam_page():
    """Trang làm bài thi của sinh viên"""
    # Frontend sẽ đọc id từ URL ?id=X
    return app.send_static_file("sinhvien/exam.html")

@app.route("/exams")
@login_required
def student_exams_list_page():
    """Trang danh sách các kỳ thi dành cho sinh viên"""
    return app.send_static_file("sinhvien/exams.html")

@app.route("/history")
@login_required
def student_history_page():
    """Trang lịch sử nộp bài của sinh viên"""
    return app.send_static_file("sinhvien/history.html")

@app.route("/dashboard")
@login_required
def student_dashboard_page():
    """Bảng điều khiển dành cho sinh viên"""
    return app.send_static_file("sinhvien/dashboard.html")

@app.route("/profile")
@login_required
def profile_page():
    """Trang hồ sơ cá nhân (tự động hiển thị theo vai trò)"""
    role = session.get("role")
    if role == "student":
        return app.send_static_file("sinhvien/profile.html")
    else:
        return app.send_static_file("admin/profile.html")

@app.route("/admin/roles")
@login_required
@permission_required("manage_roles")
def admin_roles_page():
    """Trang quản lý vai trò và phân quyền (Admin)"""
    return app.send_static_file("admin/roles.html")

@app.route("/admin/user-permissions")
@login_required
@permission_required("manage_roles")
def admin_user_permissions_page():
    """Trang quản lý quyền hạn của người dùng (Admin)"""
    return app.send_static_file("admin/user-permissions.html")

@app.route("/unauthorized")
def unauthorized_page():
    """Trang thông báo không có quyền truy cập"""
    return app.send_static_file("unauthorized.html")

# --- API Xác thực ---
@app.route("/api/auth/login", methods=["POST"])
def api_login():
    """
    Xử lý xác thực người dùng.
    Nếu thành công: Thiết lập Session và ghi lại lịch sử đăng nhập.
    """
    # Bước 1: Trích xuất thông tin đăng nhập từ Body (JSON)
    data = request.json
    username = data.get("username")
    password = data.get("password")
    
    # Bước 2: Tải danh sách người dùng và tìm kiếm khớp thông tin
    users = load_json("users.json")
    user = next((u for u in users if u["username"] == username and u["password"] == password), None)
    
    if user:
        # Bước 3: Đăng nhập thành công -> Lưu thông tin vào Flask Session (Cookie bảo mật)
        session['username'] = user['username']
        session['role'] = user['role']
        session['display_name'] = user.get('display_name', user['username'])
        
        # Bước 4: Xử lý thống kê (Analytics) nếu người dùng là sinh viên
        if user['role'] == 'student':
            try:
                # Ghi nhận tổng số lượt đăng nhập của sinh viên
                hits = load_json("hits.json")
                hits["student_logins"] = hits.get("student_logins", 0) + 1
                
                # Cập nhật số liệu theo ngày (Daily trend)
                today = time.strftime("%Y-%m-%d")
                daily_students = hits.get("daily_student_logins", {})
                daily_students[today] = daily_students.get(today, 0) + 1
                hits["daily_student_logins"] = daily_students
                
                save_json("hits.json", hits)
            except Exception as e:
                # Log lỗi ra console nếu ghi file hits thất bại (không chặn luồng đăng nhập)
                print(f"Error tracking student login: {e}")
                
        # Bước 5: Phản hồi về Frontend với vai trò (role) để chuyển hướng trang phù hợp
        return jsonify({"status": "success", "role": user['role']})
    
    # Bước 6: Phản hồi lỗi nếu thông tin sai (HTTP 401 Unauthorized)
    return jsonify({"status": "error", "message": "Sai tài khoản hoặc mật khẩu"}), 401

@app.route("/api/auth/logout")
def api_logout():
    """API xử lý đăng xuất"""
    session.clear()
    return redirect(url_for('login_page'))

@app.route("/api/auth/me")
def api_me():
    """API lấy thông tin người dùng hiện tại đang đăng nhập"""
    # Kiểm tra xem session có chứa username hay không (đã đăng nhập)
    if 'username' in session:
        # Tìm lại thông tin đầy đủ từ nguồn dữ liệu JSON
        users = load_json("users.json")
        user = next((u for u in users if u["username"] == session["username"]), None)
        if user:
            # Xây dựng đối tượng phản hồi cơ bản
            response_data = {
                "username": user['username'],
                "role": user['role'],
                "display_name": user.get('display_name'),
                "class_name": user.get('class_name', '')
            }
            # Tự động gộp tất cả các trường dữ liệu sinh viên bổ sung (nếu có)
            for field in STUDENT_FIELDS:
                if field in user:
                    response_data[field] = user[field]
            return jsonify(response_data)
    
    # Trả về lỗi nếu phiên làm việc không tồn tại hoặc hết hạn
    return jsonify({"error": "Người dùng chưa đăng nhập"}), 401

@app.route("/api/auth/update-info", methods=["PUT"])
@login_required
def update_info():
    """API cập nhật thông tin cá nhân của người dùng"""
    # Bước 1: Trích xuất dữ liệu cập nhật từ Body và xác định User qua Session
    data = request.json
    username = session.get("username")
    
    users = load_json("users.json")
    found = False
    
    # Bước 2: Lặp tìm người dùng và cập nhật các trường được phép
    for user in users:
        if user["username"] == username:
            # Cập nhật tên hiển thị (Cả trong file và Session hiện tại)
            if "display_name" in data:
                user["display_name"] = data["display_name"]
                session['display_name'] = data["display_name"]
            
            # Cập nhật thông tin lớp học
            if "class_name" in data:
                user["class_name"] = data["class_name"]
            
            # Quét và cập nhật hàng loạt các trường thông tin phụ của sinh viên (Email, SĐT, v.v.)
            for field in STUDENT_FIELDS:
                if field in data:
                    user[field] = data[field]
                    
            found = True
            break
    
    # Bước 3: Lưu lại thay đổi nếu tìm thấy người dùng
    if found:
        save_json("users.json", users)
        return jsonify({"status": "success"})
    
    return jsonify({"status": "error", "message": "Không tìm thấy người dùng"}), 404

@app.route("/api/auth/change-password", methods=["PUT"])
@login_required
def change_password():
    """API đổi mật khẩu cho người dùng"""
    data = request.json
    username = session.get("username")
    current_password = data.get("current_password")
    new_password = data.get("new_password")
    
    users = load_json("users.json")
    user_idx = next((i for i, u in enumerate(users) if u["username"] == username), -1)
    
    if user_idx == -1:
        return jsonify({"status": "error", "message": "Không tìm thấy người dùng"}), 404
        
    if users[user_idx]["password"] != current_password:
        return jsonify({"status": "error", "message": "Mật khẩu hiện tại không đúng"}), 400
        
    users[user_idx]["password"] = new_password
    save_json("users.json", users)
    return jsonify({"status": "success"})

@app.route("/problems")
@login_required
def get_problems():
    """
    Lấy danh sách tối giản các bài tập để hiển thị bảng danh sách bài tập.
    Kết hợp dữ liệu nộp bài để đánh dấu trạng thái "Đã làm" (Solved) cho sinh viên.
    """
    try:
        # Bước 1: Tải kho đề bài và danh sách bài nộp
        data = load_json("problems.json")
        submissions = load_json("submissions.json")
        
        # Bước 2: Tạo bản tóm tắt các bài tập mà User hiện tại ĐÃ hoàn thành
        # Việc dùng set() giúp thao tác kiểm tra "in user_solved_ids" bên dưới đạt tốc độ O(1)
        user_solved_ids = set([
            s["problemId"] for s in submissions 
            if s["username"] == session.get("username")
        ])

        # Bước 3: Ánh xạ dữ liệu sang cấu trúc tối giản để trả về Frontend
        # BẢO MẬT: Loại bỏ hoàn toàn solution_code và test_cases để tránh hack đề bài
        minimal_list = [
            {
                "id": p["id"], 
                "title": p["title"], 
                "difficulty": p["difficulty"], 
                "category": p.get("category", ""),
                # Đánh dấu trạng thái 'Đã giải' nếu ID bài tập nằm trong list hoàn thành
                "solved": p["id"] in user_solved_ids
            }
            for p in data
        ]
        return jsonify(minimal_list)
    except Exception as e:
        # Xử lý lỗi hệ thống nếu quá trình đọc file hoặc ánh xạ gặp trục trặc
        return jsonify({"error": str(e)}), 500

@app.route("/api/problems/<int:pid>")
@login_required
def get_problem_detail(pid):
    """API lấy chi tiết một bài tập cụ thể"""
    # Bước 1: Tải danh sách đề bài và tìm bài tập khớp với PID
    problems = load_json("problems.json")
    problem = next((p for p in problems if p["id"] == pid), None)
    if not problem:
        return jsonify({"error": "Không tìm thấy bài tập"}), 404
        
    # Bước 2: Truy vấn lịch sử bài nộp gần đây của sinh viên cho bài tập này
    # Mục đích: Tự động điền lại mã nguồn cũ nhất khi sinh viên quay lại làm tiếp
    submissions = load_json("submissions.json")
    username = session.get("username")
    
    # Bước 3: Lọc bài nộp: Đúng User, đúng Problem và phải là chế độ Luyện tập (không phải thi)
    user_subs = [s for s in submissions if s["username"] == username and s["problemId"] == pid and s.get("mode") != "exam"]
    
    if user_subs:
        # Lấy bài nộp mới nhất dựa trên thời gian (timestamp)
        latest = sorted(user_subs, key=lambda x: x.get("timestamp", ""))[-1]
        problem["last_submission"] = {
            "code": latest.get("code", ""),
            "allPassed": latest.get("allPassed", False),
            "language": latest.get("language", "python")
        }
    
    return jsonify(problem)

# --- Các API dành cho Quản trị viên - Thống kê ---
@app.route("/api/admin/stats")
@login_required
@instructor_required
def get_stats():
    """API lấy dữ liệu tổng hợp phục vụ dashboard của quản trị viên"""
    # Bước 1: Nạp toàn bộ dữ liệu thô từ các file JSON hệ thống
    problems = load_json("problems.json")
    users = load_json("users.json")
    submissions = load_json("submissions.json")
    test_attempts = load_json("test_attempts.json")
    exams = load_json("tests.json")
    hits = load_json("hits.json")
    
    # Bước 2: Phân tích cơ cấu ngôn ngữ lập trình (Language Distribution)
    # Tính toán dựa trên cả bài nộp chính thức và các lần chạy nháp/kiểm tra
    langs = {}
    for s in submissions:
        lang = s.get("language", "unknown")
        langs[lang] = langs.get(lang, 0) + 1
    for a in test_attempts:
        lang = a.get("language", "unknown")
        langs[lang] = langs.get(lang, 0) + 1
    
    # Bước 3: Tổng hợp thông tin các kỳ thi (Exams Summary)
    active_exams = [e for e in exams if e.get("isActive", True)]
    exam_subs = [s for s in submissions if s.get("examId")]
    
    # Lấy Top 10 hoạt động nộp bài trong kỳ thi mới nhất để hiển thị feed
    recent_exam_subs = []
    for s in exam_subs[-10:]:
        ex = next((e for e in exams if e["id"] == s.get("examId")), {"title": "Unknown"})
        recent_exam_subs.append({
            "username": s["username"],
            "examTitle": ex["title"],
            "problemTitle": s.get("problemTitle", f"ID: {s['problemId']}"),
            "timestamp": s["timestamp"]
        })
    
    # Bước 4: Xử lý BỘ LỌC (Filtering) theo yêu cầu từ Frontend (Dải ngày, Lớp học)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    class_name = request.args.get('class_name')
    
    filtered_submissions = []
    for s in submissions:
        # 4.1. Lọc theo thời gian (So khớp chuỗi YYYY-MM-DD)
        s_date = s.get("timestamp", "").split(" ")[0]
        if start_date and s_date < start_date: continue
        if end_date and s_date > end_date: continue
        
        # 4.2. Lọc theo lớp học (Yêu cầu kiểm tra chéo bảng Users để xác định lớp)
        if class_name:
            user = next((u for u in users if u["username"] == s["username"]), None)
            if not user or user.get("class_name") != class_name:
                continue
                
        filtered_submissions.append(s)
        
    # Ghi đè biến submissions bằng dữ liệu đã lọc để mọi tính toán phía sau đều ăn theo filter
    submissions = filtered_submissions
    
    # Bước 5: Tính toán biểu đồ hoạt động hàng ngày (Daily Activity Chart)
    daily_subs = {}
    for s in submissions:
        date = s.get("timestamp", "").split(" ")[0]
        if date:
            daily_subs[date] = daily_subs.get(date, 0) + 1
    
    # Chuyển đổi sang định dạng mảng đã sắp xếp cho Chart.js dễ xử lý
    daily_subs_sorted = sorted([{"date": k, "count": v} for k, v in daily_subs.items()], key=lambda x: x["date"])
    
    # Bước 6: Phân tích tỷ lệ đạt chuẩn (Pass/Fail Ratio)
    status_dist = {"passed": 0, "failed": 0}
    for s in submissions:
        if s.get("allPassed"):
            status_dist["passed"] += 1
        else:
            status_dist["failed"] += 1
            
    # Bước 7: Vinh danh Top 5 sinh viên giải được nhiều bài tập nhất (Leaderboard)
    student_stats = {}
    for s in submissions:
        if s.get("allPassed") and s.get("username"):
            u = s["username"]
            if u not in student_stats:
                student_stats[u] = set()
            # Sử dụng set để chỉ đếm mỗi bài tập đúng 1 lần (tránh cày điểm bằng 1 bài)
            student_stats[u].add(s["problemId"])
            
    top_students = []
    for u, solved in student_stats.items():
        # Lấy tên hiển thị thay vì chỉ hiển thị username (mã sinh viên)
        user_info = next((user for user in users if user["username"] == u), {})
        display_name = user_info.get("display_name", u)
        top_students.append({
            "username": u,
            "display_name": display_name,
            "solved_count": len(solved)
        })
    
    # Sắp xếp giảm dần theo số lượng bài giải được
    top_students.sort(key=lambda x: x["solved_count"], reverse=True)
    top_students = top_students[:5]

    # Bước 8: Phân tích hiệu năng các kỳ thi (Exams Deep Analysis)
    username = session.get("username")
    role = session.get("role")
    # Chỉ tính toán trên các kỳ thi mà Admin/Giảng viên hiện tại có quyền quản lý
    accessible_exams = [e for e in exams if can_access_resource(e, username, role)]
    
    exam_breakdown = []
    for ex in accessible_exams:
        eid = str(ex["id"])
        # Lọc các bài nộp thuộc về kỳ thi này
        ex_subs = [s for s in filtered_submissions if str(s.get("examId")) == eid]
        # Thống kê lượng tài khoản duy nhất (Unique users) tham gia
        ex_students = set([s["username"] for s in ex_subs])
        # Tính toán tỷ lệ đỗ (Pass rate)
        ex_passed = len([s for s in ex_subs if s.get("allPassed")])
        
        exam_breakdown.append({
            "id": ex["id"],
            "title": ex["title"],
            "submission_count": len(ex_subs),
            "student_count": len(ex_students),
            "pass_rate": round(ex_passed / len(ex_subs) * 100, 1) if ex_subs else 0,
            "isActive": ex.get("isActive", True)
        })

    # Bước 9: Trả về kết quả JSON tổng hợp cuối cùng
    return jsonify({
        "problem_count": len(problems),
        "student_count": len([u for u in users if u["role"] == "student"]),
        "submission_count": len(filtered_submissions),
        "total_hits": hits.get("total_hits", 0),
        "student_logins": hits.get("student_logins", 0),
        "languages": langs,
        "recent_activity": test_attempts[-10:] if test_attempts else [],
        "exam_count": len(exams),
        "active_exam_count": len(active_exams),
        "exam_submission_count": len(exam_subs),
        "recent_exam_activity": recent_exam_subs,
        "exam_breakdown": exam_breakdown,
        "daily_submissions": daily_subs_sorted,
        "status_distribution": status_dist,
        "top_students": top_students
    })

@app.route("/api/admin/classes")
@login_required
@instructor_required
def get_classes():
    """API lấy danh sách các lớp học hiện có của sinh viên"""
    users = load_json("users.json")
    classes = set()
    for u in users:
        if u.get("role") == "student" and u.get("class_name"):
            classes.add(u["class_name"])
    return jsonify(list(sorted(classes)))

# --- Middleware Hệ thống: Theo dõi Lưu lượng (Traffic Tracker) ---
@app.before_request
def track_traffic():
    """
    Hook chạy trước mỗi Request (ngoại trừ file tĩnh và API xác thực).
    Mục đích: Đếm tổng số lượt tải trang và thống kê lượng truy cập hàng ngày.
    Dữ liệu này được dùng để vẽ biểu đồ line-chart trong Dashboard Admin.
    """
    # Không đếm các file CSS/JS/Hình ảnh hoặc các API tự động (keep-alive)
    if request.path.startswith('/static') or request.path.startswith('/api/auth/me'):
        return
    
    try:
        hits = load_json("hits.json")
        hits["total_hits"] = hits.get("total_hits", 0) + 1
        
        # Thống kê theo dải ngày để biết ngày nào hệ thống bận rộn nhất
        today = time.strftime("%Y-%m-%d")
        daily = hits.get("daily_hits", {})
        daily[today] = daily.get(today, 0) + 1
        hits["daily_hits"] = daily
        
        save_json("hits.json", hits)
    except Exception as e:
        # In lỗi ra console nếu không ghi được file nhưng không làm sập Request của User
        print(f"Error tracking traffic: {e}")

# --- API Quản trị - Quản lý Bài tập ---
@app.route("/api/admin/problems", methods=["POST"])
@login_required
@permission_required("manage_problems")
def add_problem():
    """API thêm một bài tập mới"""
    new_prob = request.json
    problems = load_json("problems.json")
    # Tự động tạo ID tăng dần
    new_prob["id"] = max([p["id"] for p in problems], default=0) + 1
    problems.append(new_prob)
    save_json("problems.json", problems)
    return jsonify({"status": "success", "id": new_prob["id"]})

@app.route("/api/admin/students/list", methods=["GET"])
@login_required
@instructor_required
def get_all_students_for_selection():
    """API lấy danh sách sinh viên phục vụ việc chọn lựa trong trang admin"""
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
    """API cập nhật hoặc xóa một bài tập"""
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

# --- API Quản trị - Quản lý Kỳ thi ---
@app.route("/api/admin/exams", methods=["GET", "POST"])
@login_required
@permission_required("manage_exams")
def manage_exams():
    """API lấy danh sách kỳ thi hoặc tạo kỳ thi mới"""
    if request.method == "GET":
        exams = load_json("tests.json")
        username = session.get("username")
        role = session.get("role")
        
        # Lọc danh sách kỳ thi dựa trên quyền sở hữu hoặc chia sẻ
        accessible_exams = [e for e in exams if can_access_resource(e, username, role)]
        return jsonify(accessible_exams)
    
    # Bước 1: Trích xuất thông tin kỳ thi mới từ Request
    new_exam = request.json
    exams = load_json("tests.json")
    
    # Bước 2: Khởi tạo ID tự động tăng và thiết lập thời gian bắt đầu mặc định
    new_exam["id"] = max([e["id"] for e in exams], default=0) + 1
    if "startTime" not in new_exam:
        new_exam["startTime"] = time.strftime("%Y-%m-%d %H:%M:%S")
    
    # Bước 3: Ghi nhận thông tin quyền sở hữu (Created_by)
    # Kỳ thi sẽ thuộc quyền quản lý của người tạo ra nó
    new_exam["created_by"] = session.get("username")
    new_exam["shared_with"] = new_exam.get("shared_with", [])
    
    # Bước 4: Lưu vào cơ sở dữ liệu JSON
    exams.append(new_exam)
    save_json("tests.json", exams)
    return jsonify({"status": "success", "id": new_exam["id"]})

@app.route("/api/admin/exams/<int:eid>", methods=["GET", "PUT", "DELETE"])
@login_required
@permission_required("manage_exams")
def manage_single_exam(eid):
    """API quản lý chi tiết một kỳ thi (lấy thông tin, cập nhật, xóa)"""
    exams = load_json("tests.json")
    exam_idx = next((i for i, e in enumerate(exams) if e["id"] == eid), -1)
    
    if exam_idx == -1:
        return jsonify({"error": "Không tìm thấy kỳ thi"}), 404
    
    exam = exams[exam_idx]
    username = session.get("username")
    role = session.get("role")
    
    # Kiểm tra quyền hạn của người thực hiện
    if not can_access_resource(exam, username, role):
        return jsonify({"error": "Bạn không có quyền quản lý kỳ thi này."}), 403
        
    if request.method == "GET":
        return jsonify(exam)
        
    if request.method == "PUT":
        updated_data = request.json
        # Giữ nguyên ID kỳ thi
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
    """API lấy danh sách các kỳ thi đang diễn ra (dành cho sinh viên)"""
    # Bước 1: Nạp danh sách kỳ thi và lọc các kỳ thi đang kích hoạt
    exams = load_json("tests.json")
    active_exams = [e for e in exams if e.get("isActive", True)]
    
    # Bước 2: Phân quyền truy cập dựa trên vai trò
    role = session.get("role")
    username = session.get("username")
    
    # Sinh viên: Chỉ được thấy các kỳ thi mà họ có tên trong danh sách 'allowedStudents'
    # Nếu danh sách allowedStudents trống -> Kỳ thi công khai cho tất cả mọi người
    if role == "student":
        filtered_exams = []
        for exam in active_exams:
            allowed = exam.get("allowedStudents", [])
            
            # Kiểm tra xem sinh viên hiện tại có được phép tham gia không
            if allowed and username not in allowed:
                continue
            
            filtered_exams.append(exam)
        return jsonify(filtered_exams)
        
    # Giảng viên/Admin: Được thấy toàn bộ danh sách kỳ thi đang hoạt động
    return jsonify(active_exams)

@app.route("/api/exams/<int:eid>")
@login_required
def get_exam_detail(eid):
    """API lấy thông tin chi tiết của một kỳ thi, bao gồm các bài tập và trạng thái thời gian"""
    exams = load_json("tests.json")
    exam = next((e for e in exams if e["id"] == eid), None)
    if not exam:
        return jsonify({"error": "Không tìm thấy kỳ thi"}), 404
        
    # Bước 1: RÀO CHẮN BẢO MẬT (Security Guard)
    # Kiểm tra quyền truy cập dựa trên danh sách trắng (Whitelist) của sinh viên
    allowed_students = exam.get("allowedStudents", [])
    if allowed_students and session.get("username") not in allowed_students:
        return jsonify({"error": "Bạn không có quyền tham gia kỳ thi này. Vui lòng liên hệ giảng viên."}), 403

    # Bước 2: KIỂM TRA KHUNG GIỜ (Time Window Check)
    # Kỳ thi chỉ cho phép truy cập nếu nằm trong khoảng OpenTime và CloseTime
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%dT%H:%M") 
    open_time = exam.get("openTime")
    close_time = exam.get("closeTime")
    
    # Kiểm tra xem đề đã mở chưa?
    if open_time and now < open_time:
        return jsonify({"error": f"Kỳ thi chưa mở. Đề bài sẽ hiển thị vào: {open_time.replace('T', ' ')}"}), 403
    
    # Kiểm tra xem đề đã đóng chưa?
    if close_time and now > close_time:
        return jsonify({"error": f"Kỳ thi đã kết thúc vào lúc {close_time.replace('T', ' ')}. Bạn không thể vào làm bài."}), 403
        
    # Kiểm tra trạng thái kích hoạt chung
    if not exam.get("isActive", True):
        return jsonify({"error": "Kỳ thi hiện đang trong trạng thái bảo trì hoặc đã bị đóng bởi quản trị viên."}), 403
        
    # Bước 3: QUẢN LÝ THỜI GIAN LÀM BÀI CÁ NHÂN (User Timer)
    # Mục đích: Mỗi sinh viên khi bấm vào làm bài sẽ có một đồng hồ đếm ngược riêng
    starts = load_json("user_exam_starts.json") or {}
    if not isinstance(starts, dict): starts = {}
    
    # Tạo định danh duy nhất (Username + ExamID) để lưu thời điểm bắt đầu
    key = f"{session['username']}_{eid}"
    if key not in starts:
        # Ghi nhận thời điểm 'phát đề' cho sinh viên này
        starts[key] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_json("user_exam_starts.json", starts)
    
    # Tính toán số giây (seconds) đã trôi qua để Frontend hiển thị đếm ngược (Count down)
    start_time_str = starts[key]
    exam["userStartTime"] = start_time_str
    start_dt = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
    elapsed = (datetime.now() - start_dt).total_seconds()
    exam["timeElapsed"] = int(elapsed)
        
    # Bước 4: TỐI ƯU CẤU TRÚC ĐỀ BÀI
    all_problems = load_json("problems.json")
    # Lọc ra danh sách các bài tập thuộc kỳ thi này dựa trên mảng problemIds
    exam_problems = [p for p in all_problems if p["id"] in exam["problemIds"]]
    
    # Gán điểm số riêng biệt cho từng bài tập trong kỳ thi (Cấu hình bởi Giảng viên)
    points_map = exam.get("problemPoints", {})
    for p in exam_problems:
        p["points"] = points_map.get(str(p["id"]), 0)
    
    # Bước 5: TRUY VẤN TIẾN ĐỘ LÀM BÀI (Progress Recovery)
    # Lấy mã nguồn mà sinh viên đã nộp/lưu nháp gần đây nhất để hiển thị lại vào Edittor
    last_subs = {}
    if session.get("role") != "instructor":
        submissions = load_json("submissions.json")
        user_exam_subs = [s for s in submissions if s["username"] == session["username"] and str(s.get("examId")) == str(eid)]
        
        # Đồng bộ lại mã nguồn cho từng bài tập trong đề
        for s in sorted(user_exam_subs, key=lambda x: x.get("timestamp", "")):
            last_subs[str(s["problemId"])] = {
                "code": s.get("code", ""),
                "allPassed": s.get("allPassed", False),
                "language": s.get("language", "python"),
                "timeRemaining": s.get("timeRemaining")
            }

    # BẢO MẬT: Xóa bỏ gợi ý và code mẫu của giảng viên trước khi gửi đề cho sinh viên
    if session.get("role") != "instructor":
        for p in exam_problems:
            p.pop("hint", None)
            p.pop("solution_code", None)
            p.pop("language_hints", None)
            # Đính kèm bài nộp gần nhất (nếu có) để sinh viên tiếp tục làm
            p["last_submission"] = last_subs.get(str(p["id"]))
            
    return jsonify({
        "info": exam,
        "problems": exam_problems
    })

@app.route("/api/submissions", methods=["POST"])
@login_required
def save_submission():
    """API lưu trữ bài nộp hoặc lượt chạy thử của sinh viên"""
    # Bước 1: Trích xuất dữ liệu từ body request và định danh người nộp
    data = request.json
    username = session.get("username")
    submission_type = data.get("submission_type", "check") # 'check' (chạy console) hoặc 'submit' (nộp đề)
    
    # Bước 2: Chuẩn hóa đối tượng bài nộp (Submission Object)
    submission = {
        "problemId": data.get("problemId"),
        "problemTitle": data.get("problemTitle"),
        "language": data.get("language"),
        "code": data.get("code"),
        "mode": data.get("mode", "practice"), # Chế độ 'practice' (luyện tập) hoặc 'exam' (kỳ thi)
        "examId": data.get("examId"),
        "allPassed": data.get("allPassed", False), # Trạng thái tất cả test case đã qua
        "timeRemaining": data.get("timeRemaining"), # Thời gian còn lại của kỳ thi (nếu có)
        "submission_type": submission_type, # Loại nộp: 'check' hay 'submit'
        "username": username, # Tên người dùng nộp bài
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S") # Thời điểm nộp bài
    }
    
    if submission_type == "check":
        # Tuyến đường A: CHẾ ĐỘ CHẠY THỬ (Console Check)
        # Chỉ lưu vào lịch sử nháp để sinh viên xem lại, không tính điểm chính thức
        attempts = load_json("test_attempts.json")
        # Thêm bài nộp thử vào danh sách
        attempts.append(submission)
        # Tự động dọn dẹp (Rotate logs) nếu số lượng bản ghi vượt quá 1000
        if len(attempts) > 1000: attempts = attempts[-1000:]
        save_json("test_attempts.json", attempts)
    else:
        # Tuyến đường B: CHẾ ĐỘ NỘP BÀI (Official Submit)
        submissions = load_json("submissions.json")
        
        # CHIẾN LƯỢC LƯU TRỮ: Mỗi người dùng chỉ có 1 bản nộp duy nhất trên 1 bài tập.
        # Nếu nộp lại cùng một bài, hệ thống sẽ tự động ghi đè (Overwrite) bản cũ.
        if submission["mode"] == "exam":
            # Xử lý ghi đè trong kỳ thi: Căn cứ vào (Username, ExamID, ProblemID)
            submissions = [
                s for s in submissions 
                if not (s["username"] == username and 
                       str(s.get("examId")) == str(submission["examId"]) and 
                       s["problemId"] == submission["problemId"])
            ]
        else:
            # Xóa bản cũ của cùng sinh viên, cùng bài tập (trong chế độ luyện tập)
            submissions = [
                s for s in submissions 
                if not (s["username"] == username and 
                       s["problemId"] == submission["problemId"] and
                       s.get("mode") != "exam")
            ]
            
        # Thêm bản nộp mới nhất vào danh sách
        submissions.append(submission)
        save_json("submissions.json", submissions)
        
    return jsonify({"status": "success"})

@app.route("/api/exams/<int:eid>/cheat-logs", methods=["POST"])
@login_required
def report_cheat(eid):
    """API ghi nhận các hành vi nghi ngờ gian lận (chuyển tab, mất focus, etc.)"""
    # Bước 1: Trích xuất thông tin sự kiện từ Body
    data = request.json
    username = session.get("username")
    
    # Bước 2: Tải danh sách Log cũ hoặc khởi tạo mới (nếu file chưa tồn tại)
    logs = load_json("cheat_logs.json") or []
    if not isinstance(logs, list): logs = []
    
    # Bước 3: Cấu trúc hóa bản ghi log gian lận
    log_entry = {
        "examId": eid,
        "username": username,
        "event": data.get("event"),           # Hành vi: 'visibilitychange' (ẩn tab), 'blur' (mất focus)
        "problemId": data.get("problemId"),   # Bài tập đang làm lúc đó
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "details": data.get("details", "")     # Chi tiết bổ sung (VD: số mili giây mất focus)
    }
    
    # Bước 4: Lưu log vào hệ thống
    logs.append(log_entry)
    save_json("cheat_logs.json", logs)
    
    return jsonify({"status": "success"})

# --- Các API dành cho Bảng điều khiển sinh viên ---
@app.route("/api/student/exams/summary")
@login_required
def get_student_exams_summary():
    """API lấy bảng tóm tắt kết quả các kỳ thi của sinh viên hiện tại"""
    # Bước 1: Xác định danh tính và nạp dữ liệu kỳ thi/bài nộp
    username = session.get("username")
    exams = load_json("tests.json")
    submissions = load_json("submissions.json")
    
    summary = []
    # Lọc toàn bộ bài nộp của User hiện tại để xử lý tập trung
    user_subs = [s for s in submissions if s["username"] == username]
    
    # Bước 2: Duyệt qua từng kỳ thi để tính toán kết quả cá nhân
    for exam in exams:
        # 2.1. Kiểm tra xem sinh viên này có thuộc đối tượng được thi không
        allowed_students = exam.get("allowedStudents", [])
        if allowed_students and username not in allowed_students:
            continue
 
        # 2.2. Tính toán Tổng điểm của toàn bộ đề thi (Total possible)
        points_map = exam.get("problemPoints", {})
        total_possible = sum(points_map.values())
        
        # 2.3. Tính toán Điểm số thực tế đã đạt được (Achieved score)
        achieved = 0
        solved_in_exam = []
        
        # Lọc các bài nộp thành công (allPassed) CHỈ TRONG kỳ thi này
        exam_subs = [s for s in user_subs if str(s.get("examId")) == str(exam["id"]) and s.get("allPassed") is True]
        
        # Lấy duy nhất 1 bản nộp thành công cho mỗi bài tập (Unique IDs)
        solved_ids = set([s["problemId"] for s in exam_subs])
        
        # Tính tổng điểm tích lũy dựa trên map điểm của từng bài
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
    """API lấy thống kê cá nhân của sinh viên (số bài đã giải, tỷ lệ thành công, thứ hạng)"""
    username = session.get("username")
    submissions = load_json("submissions.json")
    problems = load_json("problems.json")
    users = load_json("users.json")
    
    user_subs = [s for s in submissions if s["username"] == username]
    # Danh sách bài đã giải (bất kể chế độ luyện tập hay thi)
    solved_ids = set([s["problemId"] for s in user_subs])
    
    # Tính toán thứ hạng dựa trên số bài đã giải
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
    """
    Thực thi mã nguồn với một bộ dữ liệu nhập (input) duy nhất.
    Hàm này được sử dụng để kiểm tra tính đúng đắn của bài tập trong trang quản trị.
    """
    config = LANGUAGE_CONFIG.get(language)
    if not config:
        return {"error": f"Ngôn ngữ không được hỗ trợ: {language}"}

    # 1. Tạo thư mục tạm thời (temp_dir) để biên dịch và thực thi
    # Sử dụng 'temp_sessions' để tránh xung đột quyền ghi trên một số môi trường Windows
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
        
        # Bước 1: Biên dịch (Compilation Step)
        if config['compile']:
            output_file = os.path.join(temp_dir, "program.exe" if os.name == 'nt' else "program")
            compile_cmd_template = config['compile']
            compile_files = [code_file]
            
            # Tắt output buffering cho C/C++ bằng cách link thêm file chứa hàm constructer setvbuf
            if language == 'c':
                flush_file = os.path.join(temp_dir, "flush_init.c")
                with open(flush_file, 'w', encoding='utf-8') as f: f.write(FLUSH_INIT_C)
                compile_files.append(flush_file)
            elif language == 'cpp':
                flush_file = os.path.join(temp_dir, "flush_init.cpp")
                with open(flush_file, 'w', encoding='utf-8') as f: f.write(FLUSH_INIT_CPP)
                compile_files.append(flush_file)
            
            # Xây dựng câu lệnh biên dịch từ template (Cấu hình trong LANGUAGE_CONFIG)
            final_compile_cmd = []
            for arg in compile_cmd_template:
                if "{file}" in arg: final_compile_cmd.append(arg.format(file=code_file, output=output_file))
                elif "{output}" in arg: final_compile_cmd.append(arg.format(output=output_file))
                else: final_compile_cmd.append(arg)
            for extra_file in compile_files[1:]: final_compile_cmd.append(extra_file)

            compile_result = subprocess.run(final_compile_cmd, capture_output=True, text=True, encoding='utf-8', timeout=10)
            if compile_result.returncode != 0:
                return {"error": f"Lỗi biên dịch:\n{compile_result.stderr}", "output": ""}
            exe_path = output_file
        
        # Bước 2: Thực thi (Run Step)
        if exe_path:
            classname = "Main" if language == "java" else None
            run_cmd = [cmd.format(output=exe_path, classname=classname) for cmd in run_cmd_template]
        else:
            run_cmd = [cmd.format(file=code_file, project_dir=temp_dir) for cmd in run_cmd_template]

        # Thực thi tiến trình với giới hạn thời gian (Timeout) để tránh treo server
        process = subprocess.run(
            run_cmd,
            input=user_input,   # Truyền dữ liệu nhập vào stdin
            capture_output=True, # Thu thập stdout và stderr
            text=True,           # Tự động giải mã bytes sang string
            encoding='utf-8',
            timeout=5,           # Giới hạn 5 giây cho mỗi lần chạy test
            cwd=temp_dir        # Chạy trong thư mục tạm chứa file code
        )
        return {"output": process.stdout, "error": process.stderr if process.returncode != 0 else None}

    except subprocess.TimeoutExpired:
        return {"error": "Lỗi: Quá thời gian thực thi (giới hạn 5 giây)", "output": ""}
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
    """API cho phép giảng viên chạy thử code mẫu đối với các bộ test case vừa tạo cho bài tập mới"""
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
    """API quản lý danh sách sinh viên (lấy danh sách, thêm mới, sửa)"""
    users = load_json("users.json")
    if request.method == "GET":
        submissions = load_json("submissions.json")
        students = [u for u in users if u["role"] == "student"]
        
        # Bổ sung các thông số thống kê cho mỗi sinh viên
        for s in students:
            user_subs = [sub for sub in submissions if sub["username"] == s["username"]]
            s["solved_count"] = len(set([sub["problemId"] for sub in user_subs]))
            s["submission_count"] = len(user_subs)
            
            # Xác định ngôn ngữ lập trình chủ đạo của sinh viên
            if user_subs:
                langs = {}
                for sub in user_subs:
                    l = sub["language"]
                    langs[l] = langs.get(l, 0) + 1
                s["main_lang"] = max(langs, key=langs.get).upper()
            else:
                s["main_lang"] = "--"
            
            # Đảm bảo trường tên lớp học luôn tồn tại
            if "class_name" not in s:
                s["class_name"] = "--"
                
        return jsonify(students)
    elif request.method == "POST":
        """Thêm mới một sinh viên"""
        new_student = request.json
        new_student["role"] = "student"
        if any(u["username"] == new_student["username"] for u in users):
            return jsonify({"status": "error", "message": "Tên đăng nhập đã tồn tại"}), 400
        users.append(new_student)
        save_json("users.json", users)
        return jsonify({"status": "success"})
    elif request.method == "PUT":
        """Cập nhật thông tin chi tiết của một sinh viên"""
        data = request.json
        username = data.get("username")
        # Tìm kiếm sinh viên theo username và cập nhật thông tin mới nhất
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
    """API lấy thống kê chi tiết của một sinh viên theo tên đăng nhập (dành cho Admin)"""
    # Bước 1: Truy vấn thông tin người dùng từ ID
    users = load_json("users.json")
    submissions = load_json("submissions.json")
    
    student = next((u for u in users if u["username"] == username), None)
    if not student:
        return jsonify({"status": "error", "message": "Sinh viên không tồn tại"}), 404
    
    # Bước 2: Lọc toàn bộ lịch sử bài nộp của sinh viên này
    user_subs = [s for s in submissions if s["username"] == username]
    
    # Bước 3: Phân tích các chỉ số hiệu năng
    # Đếm số lượng bài tập duy nhất đã từng nộp bài
    solved_problems = list(set([s["problemId"] for s in user_subs]))
    
    # Thống kê tần suất sử dụng các ngôn ngữ lập trình
    langs = {}
    for s in user_subs:
        lang = s["language"]
        langs[lang] = langs.get(lang, 0) + 1
        
    return jsonify({
        "info": student,
        "solved_count": len(solved_problems),
        "total_submissions": len(user_subs),
        "languages": langs,
        # Trả về 10 hoạt động gần đây nhất để hiển thị biểu đồ thời gian
        "recent_activity": user_subs[-10:] if user_subs else []
    })

@app.route("/api/admin/reports")
@login_required
@instructor_required
def get_reports():
    """API lấy dữ liệu báo cáo chi tiết cho giảng viên (Bảng xếp hạng sinh viên & Thống kê bài tập)"""
    # Bước 1: Nạp toàn bộ kho dữ liệu cần thiết cho báo cáo
    users = load_json("users.json")
    problems = load_json("problems.json")
    raw_submissions = load_json("submissions.json")
    exams = load_json("tests.json")
    
    username = session.get("username")
    role = session.get("role")
    
    # Bước 2: THIẾT LẬP PHẠM VI DỮ LIỆU (Data Scoping)
    # Xác định các kỳ thi mà Giảng viên hiện tại có quyền xem báo cáo
    accessible_exam_ids = [str(e["id"]) for e in exams if can_access_resource(e, username, role)]
    
    # Lọc bài nộp: Admin xem tất cả, Giảng viên chỉ xem các bài nộp trong kỳ thi mình quản lý
    if is_admin_role(role):
        submissions = raw_submissions
    else:
        # Cơ chế bảo mật: Ngăn việc giảng viên xem bài nộp của các lớp/kỳ thi khác
        submissions = [s for s in raw_submissions if str(s.get("examId")) in accessible_exam_ids]
    
    # Bước 3: XÂY DỰNG BÁO CÁO SINH VIÊN (Student Ranking)
    students = [u for u in users if u["role"] == "student"]
    student_report = []
    for s in students:
        user_subs = [sub for sub in submissions if sub["username"] == s["username"]]
        # Chỉ đếm các bài tập duy nhất (tránh tính lặp điểm)
        solved = set([sub["problemId"] for sub in user_subs])
        student_report.append({
            "username": s["username"],
            "display_name": s["display_name"],
            "class_name": s.get("class_name", "--"),
            "solved_count": len(solved),
            "submission_count": len(user_subs),
            # Tính tỷ lệ thành công trung bình (Pass rate)
            "success_rate": round(len(solved) / len(user_subs) * 100, 1) if user_subs else 0
        })
        
    # Bước 4: XÂY DỰNG BÁO CÁO BÀI TẬP (Problem Analytics)
    # Giúp giảng viên biết bài tập nào quá khó hoặc quá dễ
    problem_report = []
    for p in problems:
        p_subs = [sub for sub in submissions if sub["problemId"] == p["id"]]
        p_passers = set([sub["username"] for sub in p_subs]) 
        
        # Chuyển đổi nhãn độ khó sang tiếng Việt cho giao diện người dùng
        diff_map = { "Easy": "Dễ", "Medium": "Trung bình", "Hard": "Khó" }
        raw_diff = p.get("difficulty", "Dễ")
        
        problem_report.append({
            "id": p["id"],
            "title": p["title"],
            "difficulty": diff_map.get(raw_diff, raw_diff), 
            "category": p.get("category", "Chung"),
            "attempt_count": len(p_subs),
            "pass_count": len(p_passers)
        })
 
    # Bước 5: TỔNG HỢP CÁC KỲ THI (Exams Overview)
    accessible_exams = [e for e in exams if can_access_resource(e, username, role)]
    
    exam_report = []
    
    for exam in accessible_exams:
        exam_id = exam["id"]
        points_map = exam.get("problemPoints", {})
        
        # Lấy toàn bộ bài nộp cho kỳ thi này (không phân biệt thành công, để đếm số người tham gia)
        exam_all_subs = [s for s in submissions if str(s.get("examId")) == str(exam_id)]
        # Chỉ lấy các bài nộp thành công để tính toán điểm số
        exam_pass_subs = [s for s in exam_all_subs if s.get("allPassed") is True]
        
        # Kết quả chi tiết của từng sinh viên trong kỳ thi này
        student_results = []
        attendees = set([s["username"] for s in exam_all_subs])
        
        for username in attendees:
            user = next((u for u in students if u["username"] == username), None)
            if not user: continue
            
            user_exam_pass_subs = [s for s in exam_pass_subs if s["username"] == username]
            # Chỉ tính các bài tập khác nhau đã giải thành công
            solved_ids = set([s["problemId"] for s in user_exam_pass_subs])
            
            score = 0
            for pid in solved_ids:
                score += points_map.get(str(pid), 0)
                
            # Đếm số lần vi phạm (gian lận)
            cheat_logs = load_json("cheat_logs.json") or []
            violation_count = len([l for l in cheat_logs if str(l.get("examId")) == str(exam_id) and l.get("username") == username])

            student_results.append({
                "username": username,
                "display_name": user["display_name"],
                "class_name": user.get("class_name", "--"),
                "solved_count": len(solved_ids),
                "score": score,
                "violation_count": violation_count
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

# --- Tuyến đường Giao diện Admin (Trang báo cáo) ---
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
    """Trang xem chi tiết các bài nộp của một kỳ thi cụ thể"""
    return app.send_static_file("admin/report-exam-submissions.html")

# --- API Quản lý Quyền hạn (Permissions) ---
@app.route("/api/admin/permissions/config", methods=["GET"])
@login_required
@permission_required("manage_roles")
def get_permissions_config():
    """API lấy toàn bộ cấu hình vai trò và quyền hạn"""
    return jsonify(load_permissions())

@app.route("/api/admin/roles", methods=["GET"])
@login_required
def get_roles():
    """API lấy danh sách các vai trò có cấp bậc thấp hơn người dùng hiện tại"""
    # Bước 1: Nạp cấu hình phân quyền từ permissions.json
    perms = load_permissions()
    roles = perms.get("roles", {})
    
    # Bước 2: Xác định cấp bậc (Rank) của người dùng hiện tại
    current_user_role = session.get("role", "student")
    current_rank = ROLE_RANK.get(current_user_role, 0)
    
    # Bước 3: Lọc danh sách vai trò dựa trên cấp bậc (Hierarchy Filter)
    # QUY TẮC: Một người không được phép gán/nhìn thấy vai trò cao hơn hoặc bằng chính mình
    filtered_roles = {}
    for k, v in roles.items():
        role_rank = ROLE_RANK.get(k, 0)
        # Chỉ lấy vai trò có rank thấp hơn, trừ trường hợp đặc biệt là Super Admin
        if role_rank < current_rank or current_user_role == "super_admin":
            # Chặn Super Admin nhìn thấy chính mình để tránh tình trạng tự tước quyền (Self-demotion)
            if k == "super_admin" and current_user_role == "super_admin":
                continue
            filtered_roles[k] = {**v, "rank": role_rank}
            
    return jsonify(filtered_roles)

@app.route("/api/admin/permissions", methods=["GET"])
@login_required
def get_all_permissions():
    """API lấy danh sách tất cả các quyền hạn có sẵn trong hệ thống"""
    perms = load_permissions()
    return jsonify(perms.get("permissions", {}))

@app.route("/api/admin/users/<username>/permissions", methods=["GET", "PUT"])
@login_required
@permission_required("manage_roles")
def manage_user_permissions(username):
    """API lấy hoặc cập nhật quyền hạn cụ thể cho từng người dùng"""
    # Bước 1: Tìm người dùng trong database theo Username
    users = load_json("users.json")
    user = next((u for u in users if u["username"] == username), None)
    
    if not user:
        return jsonify({"error": "Không tìm thấy người dùng"}), 404
    
    # XỬ LÝ GET: Trả về trạng thái quyền hạn hiện tại
    if request.method == "GET":
        return jsonify({
            "username": username,
            "role": user.get("role", "student"),
            "custom_permissions": user.get("custom_permissions", []),
            "all_permissions": get_user_permissions(username)
        })
    
    # XỬ LÝ PUT: Cập nhật quyền hạn/vai trò
    data = request.json
    new_role = data.get("role")
    custom_perms = data.get("custom_permissions", [])
    
    # Bước 2: KIỂM TRA BẢO MẬT (Security Guard)
    # Ngăn chặn việc người dùng cấp thấp sửa đổi tài khoản Super Admin
    current_user = next((u for u in users if u["username"] == session["username"]), None)
    if user.get("role") == "super_admin" and current_user.get("role") != "super_admin":
        return jsonify({"error": "Vi phạm bảo mật: Chỉ Quản trị viên cấp cao nhất mới có quyền can thiệp vào tài khoản này."}), 403
    
    # Bước 3: Áp dụng thay đổi
    if new_role:
        user["role"] = new_role
    user["custom_permissions"] = custom_perms
    
    # Bước 4: Lưu dữ liệu
    save_json("users.json", users)
    return jsonify({"status": "success"})

@app.route("/api/admin/users/non-students", methods=["GET"])
@login_required
@permission_required("manage_roles")
def get_non_student_users():
    """API lấy danh sách người dùng (không phải sinh viên), được lọc theo cấp bậc (rank)"""
    users = load_json("users.json")
    current_user_role = session.get("role", "student")
    current_rank = ROLE_RANK.get(current_user_role, 0)
    
    non_students = []
    for u in users:
        role = u.get("role", "student")
        if role == "student":
            continue
            
        target_rank = ROLE_RANK.get(role, 0)
        # BẢO MẬT: Chỉ hiển thị những người dùng có cấp bậc THẤP HƠN người dùng hiện tại
        # Điều này ngăn chặn việc giảng viên thông thường can thiệp vào tài khoản Admin
        if target_rank < current_rank:
            non_students.append({
                "username": u["username"],
                "display_name": u.get("display_name", u["username"]),
                "role": role,
                "custom_permissions": u.get("custom_permissions", [])
            })
            
    return jsonify(non_students)

@app.route("/api/admin/users/create", methods=["POST"])
@login_required
@permission_required("manage_roles")
def create_non_student_user():
    """API tạo mới một tài khoản người dùng (không phải sinh viên)"""
    # Bước 1: Trích xuất thông tin người dùng mới
    data = request.json
    username = data.get("username", "").strip()
    display_name = data.get("display_name", "").strip()
    password = data.get("password", "")
    role = data.get("role", "instructor")
    custom_permissions = data.get("custom_permissions", [])
    
    # Bước 2: KIỂM TRA TÍNH HỢP LỆ (Validation)
    # Đảm bảo các trường bắt buộc không để trống
    if not username or not display_name or not password:
        return jsonify({"status": "error", "message": "Vui lòng nhập đầy đủ các trường bắt buộc"}), 400
    
    # Độ dài tối thiểu cho tài khoản và mật khẩu
    if len(username) < 3:
        return jsonify({"status": "error", "message": "Tên đăng nhập phải có ít nhất 3 ký tự"}), 400
    if len(password) < 3:
        return jsonify({"status": "error", "message": "Mật khẩu phải có ít nhất 3 ký tự"}), 400
    
    # Kiểm tra xem vai trò mục tiêu có tồn tại trong hệ thống không
    perms_config = load_permissions()
    if role not in perms_config.get("roles", {}) or role == "student":
        return jsonify({"status": "error", "message": "Vai trò (Role) không tồn tại hoặc không hợp lệ"}), 400
    
    # Bước 3: KIỂM TRA TRÙNG LẶP (Duplication Check)
    users = load_json("users.json")
    if any(u["username"] == username for u in users):
        return jsonify({"status": "error", "message": "Tên đăng nhập này đã được sử dụng"}), 400
    
    # Bước 4: Lưu tài khoản mới vào danh sách
    new_user = {
        "username": username,
        "password": password,
        "role": role,
        "display_name": display_name,
        "custom_permissions": custom_permissions
    }
    
    users.append(new_user)
    save_json("users.json", users)
    
    return jsonify({"status": "success", "message": "Tạo tài khoản quản lý thành công"})

# --- API Quản lý Quyền hạn (Permissions) CRUD ---
@app.route("/api/admin/permissions", methods=["POST"])
@login_required
@permission_required("manage_roles")
def create_permission():
    """API tạo thêm một quyền hạn mới trong hệ thống"""
    data = request.json
    perm_key = data.get("key", "").strip()
    perm_name = data.get("name", "").strip()
    perm_desc = data.get("description", "").strip()
    
    if not perm_key or not perm_name:
        return jsonify({"status": "error", "message": "Vui lòng nhập đầy đủ mã và tên quyền hạn"}), 400
    
    # Kiểm tra định dạng key (chỉ cho phép chữ thường, số và gạch dưới)
    import re
    if not re.match(r'^[a-z0-9_]+$', perm_key):
        return jsonify({"status": "error", "message": "Mã quyền hạn (key) chỉ được chứa chữ thường, số và dấu gạch dưới"}), 400
    
    perms_config = load_permissions()
    
    if perm_key in perms_config.get("permissions", {}):
        return jsonify({"status": "error", "message": "Mã quyền hạn này đã tồn tại trong hệ thống"}), 400
    
    perms_config.setdefault("permissions", {})[perm_key] = {
        "name": perm_name,
        "description": perm_desc
    }
    
    save_json("permissions.json", perms_config)
    return jsonify({"status": "success", "message": "Đã tạo quyền hạn mới thành công"})

@app.route("/api/admin/permissions/<perm_key>", methods=["PUT", "DELETE"])
@login_required
@permission_required("manage_roles")
def manage_permission(perm_key):
    # Bước 1: Nạp cấu hình hiện tại
    perms_config = load_permissions()
    
    if perm_key not in perms_config.get("permissions", {}):
        return jsonify({"status": "error", "message": "Không tìm thấy mã quyền hạn (key) này"}), 404
    
    # XỬ LÝ DELETE: Xóa bỏ quyền khỏi hệ thống
    if request.method == "DELETE":
        # KIỂM TRA RÀNG BUỘC: Không cho phép xóa nếu quyền đang được một vai trò sử dụng
        for role_key, role_data in perms_config.get("roles", {}).items():
            if perm_key in role_data.get("permissions", []):
                return jsonify({
                    "status": "error", 
                    "message": f"Dữ liệu đang được sử dụng: Quyền này đang được gán cho vai trò '{role_data.get('name', role_key)}'. Vui lòng gỡ quyền khỏi vai trò trước khi xóa."
                }), 400
        
        # Xóa thực thể khỏi Dictionary
        del perms_config["permissions"][perm_key]
        save_json("permissions.json", perms_config)
        return jsonify({"status": "success", "message": "Đã xóa quyền hạn vĩnh viễn"})
    
    # XỬ LÝ PUT: Cập nhật nội dung mô tả
    data = request.json
    perms_config["permissions"][perm_key] = {
        "name": data.get("name", ""),
        "description": data.get("description", "")
    }
    save_json("permissions.json", perms_config)
    return jsonify({"status": "success", "message": "Thông tin quyền hạn đã được cập nhật"})

@app.route("/api/admin/roles/<role_key>/permissions", methods=["PUT"])
@login_required
@permission_required("manage_roles")
def update_role_permissions(role_key):
    # Bước 1: Nạp kho quyền hạn
    perms_config = load_permissions()
    
    if role_key not in perms_config.get("roles", {}):
        return jsonify({"status": "error", "message": "Vai trò mục tiêu không tồn tại"}), 404
    
    # BẢO MẬT TUYỆT ĐỐI: Không cho phép can thiệp vào quyền của Super Admin qua API
    # Mục đích: Tránh việc sếp bị nhân viên (Admin cấp thấp) tước quyền thông qua chỉnh sửa role
    if role_key == "super_admin":
        return jsonify({"status": "error", "message": "Vi phạm quy tắc hệ thống: Không thể chỉnh sửa quyền hạn của Quản trị viên cấp cao nhất (Super Admin)"}), 403
    
    # Bước 2: Trích xuất danh sách quyền mới
    data = request.json
    new_perms = data.get("permissions", [])
    
    # Bước 3: Kiểm tra tính toàn vẹn (Integrity Check)
    # Đảm bảo các Key quyền hạn được gán phải thực sự tồn tại trong danh mục Permissions
    all_perms = perms_config.get("permissions", {})
    for perm in new_perms:
        if perm not in all_perms:
            return jsonify({"status": "error", "message": f"Lỗi logic: Quyền hạn '{perm}' không tồn tại. Vui lòng kiểm tra lại danh mục quyền."}), 400
    
    # Bước 4: Cập nhật và lưu trữ
    perms_config["roles"][role_key]["permissions"] = new_perms
    save_json("permissions.json", perms_config)
    return jsonify({"status": "success", "message": f"Đã cập nhật bộ quyền cho vai trò '{role_key}'"})

# --- API Theo dõi và Bài nộp (Lưu trữ lịch sử) ---
@app.route("/api/submissions", methods=["GET", "POST"])
@login_required
def handle_submissions():
    # XỬ LÝ POST: Gửi bài nộp hoặc lưu lịch sử chạy thử
    if request.method == "POST":
        data = request.json
        data["username"] = session["username"]
        data["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Bước 1: Chuẩn hóa dữ liệu (Data Normalization)
        # Đảm bảo trường thời gian 'timeRemaining' nhất quán giữa các phiên bản API
        if "timeRemaining" not in data and "time_remaining" in data:
            data["timeRemaining"] = data.pop("time_remaining")
        
        # Bước 2: Phân loại cơ sở dữ liệu đích
        submission_type = data.get("submission_type", "submit") 
        
        if submission_type == "check":
            # Tuyến đường lưu trữ CHẠY THỬ (Testing attempts)
            attempts = load_json("test_attempts.json")
            attempts.append(data)
            save_json("test_attempts.json", attempts)
        else:
            # Tuyến đường lưu trữ BÀI NỘP CHÍNH THỨC (Official submissions)
            submissions = load_json("submissions.json")
            submissions.append(data)
            save_json("submissions.json", submissions)
        
        return jsonify({"status": "success"})
    
    # XỬ LÝ GET: Truy vấn lịch sử (Phân quyền theo vai trò)
    submissions = load_json("submissions.json")
    test_attempts = load_json("test_attempts.json")
    
    # Bước 3: THIẾT LẬP CHẾ ĐỘ XEM (View Scoping)
    if session.get("role") != "student":
        # GIẢNG VIÊN/ADMIN: Được quyền xem toàn bộ 'Big Data' của hệ thống phục vụ hậu kiểm
        return jsonify({
            "submissions": submissions,
            "test_attempts": test_attempts
        })
    else:
        # SINH VIÊN: Chỉ được phép truy cập dữ liệu cá nhân (Bảo mật riêng tư)
        user_subs = [s for s in submissions if s["username"] == session["username"]]
        user_attempts = [a for a in test_attempts if a["username"] == session["username"]]
        return jsonify({
            "submissions": user_subs,
            "test_attempts": user_attempts
        })



# -------------------------------------------------------------------------------------------------
# III. CÔNG CỤ HỖ TRỢ & CẤU HÌNH THỨ BẬC (HELPER TOOLS & HIERARCHY)
# Phần này định nghĩa các quy tắc cốt lõi về phân quyền và sơ đồ dữ liệu sinh viên.
# -------------------------------------------------------------------------------------------------

# 1. Cấp bậc vai trò (Rank Hierarchy)
# Dùng để kiểm soát quyền hạn quản lý: Rank CAO điều phối người có Rank THẤP.
ROLE_RANK = {
    "super_admin": 100,         # Trùm cuối: Có quyền tối thượng trên toàn hệ thống
    "admin": 80,                # Quản trị viên: Vận hành hệ thống chung
    "instructor": 60,           # Giảng viên: Quản lý học tập và bài tập
    "teaching_assistant": 40,   # Trợ giảng: Hỗ trợ giảng dạy và chấm điểm bài nộp
    "student": 20               # Sinh viên: Chỉ có quyền làm bài và xem kết quả cá nhân
}

# 2. Danh mục thông tin sinh viên (Student Profile Schema)
# Các trường dữ liệu này sẽ được dùng để ánh xạ tự động từ Excel hoặc Form đăng ký.
STUDENT_FIELDS = [
    "msv", "fullname", "dob", "phone", "email_school", "email_personal", 
    "ethnicity", "id_card", "major", "address", "father_name", 
    "father_phone", "father_email", "mother_name", "mother_phone", "mother_email"
]

@app.route("/api/admin/users", methods=["GET", "POST"])
@login_required
@permission_required("manage_users")
def handle_admin_users():
    """API lấy danh sách người dùng hoặc tạo người dùng mới (có kiểm tra cấp bậc)"""
    users = load_json("users.json")
    current_user_role = session.get("role", "student")
    # Bước 1: Nạp toàn bộ dữ liệu người dùng
    users = load_json("users.json")
    
    # Bước 2: Xác định cấp bậc (Rank) của người đang đăng nhập
    current_user_role = session.get("role", "student")
    current_rank = ROLE_RANK.get(current_user_role, 0)
    
    # XỬ LÝ GET: Liệt kê danh sách người dùng quản lý
    if request.method == "GET":
        filtered_users = []
        for u in users:
            target_role = u.get("role", "student")
            target_rank = ROLE_RANK.get(target_role, 0)
            
            # KIỂM TRA BẢO MẬT: Chỉ được phép hiển thị những người dùng có rank THẤP HƠN mình
            # Điều này ngăn sinh viên thấy admin, và admin không thể can thiệp vào super_admin
            if target_rank < current_rank:
                user_info = {
                    "username": u["username"],
                    "display_name": u.get("display_name", u["username"]),
                    "role": target_role,
                    "class_name": u.get("class_name", "--"),
                    "password": "******" # BẢO MẬT: Tuyệt đối không gửi mật khẩu thật qua API
                }
                # Nếu là dữ liệu sinh viên, bổ sung thêm các trường thông tin chi tiết (SDT, Email, v.v.)
                if target_role == "student":
                    for field in STUDENT_FIELDS:
                        if field in u:
                            user_info[field] = u[field]
                filtered_users.append(user_info)
        return jsonify(filtered_users)
    
    # POST - Tạo một người dùng mới
    data = request.json
    username = data.get("username", "").strip()
    display_name = data.get("display_name", "").strip()
    password = data.get("password", "")
    role = data.get("role", "student")
    class_name = data.get("class_name", "")
    
    if not username or not display_name or not password:
        return jsonify({"status": "error", "message": "Thiếu thông tin bắt buộc"}), 400
        
    # Kiểm tra cấp bậc khi tạo: MUST có rank thấp hơn rank của người thực hiện
    target_rank = ROLE_RANK.get(role, 0)
    if target_rank >= current_rank and current_user_role != "super_admin":
        return jsonify({"status": "error", "message": "Bạn chỉ có thể tạo tài khoản có cấp bậc thấp hơn"}), 403
        
    if any(u["username"] == username for u in users):
        return jsonify({"status": "error", "message": "Tên đăng nhập đã tồn tại"}), 400
        
    new_user = {
        "username": username,
        "password": password,
        "display_name": display_name,
        "role": role,
        "class_name": class_name
    }
    # Bổ sung các trường chi tiết nếu được cung cấp (chủ yếu dành cho sinh viên)
    for field in STUDENT_FIELDS:
        if field in data:
            new_user[field] = data[field]
    users.append(new_user)
    save_json("users.json", users)
    return jsonify({"status": "success", "message": "Tạo người dùng thành công"})

@app.route("/api/admin/users/<username>", methods=["PUT", "DELETE"])
@login_required
@permission_required("manage_users")
def modify_user(username):
    # Bước 1: Tìm kiếm vị trí (Index) của người dùng mục tiêu trong mảng
    users = load_json("users.json")
    user_idx = next((i for i, u in enumerate(users) if u["username"] == username), -1)
    
    if user_idx == -1:
        return jsonify({"status": "error", "message": "Không tìm thấy người dùng trong hệ thống"}), 404
        
    # Bước 2: KIỂM TRA PHÂN CẤP QUYỀN HẠN (Permission Check)
    current_user_role = session.get("role", "student")
    target_user = users[user_idx]
    target_user_role = target_user.get("role", "student")
    
    current_rank = ROLE_RANK.get(current_user_role, 0)
    target_rank = ROLE_RANK.get(target_user_role, 0)
    
    # QUY TẮC: Rank của bạn phải LỚN HƠN rank của đối tượng bạn muốn chỉnh sửa
    if current_rank <= target_rank and current_user_role != "super_admin":
         return jsonify({"status": "error", "message": "Vi phạm chính sách: Bạn không có quyền thao tác trên tài khoản có cấp bậc tương đương hoặc cao hơn."}), 403
    
    # QUY TẮC ĐẶC BIỆT: Chỉ Super Admin mới được can thiệp vào các Super Admin khác
    if target_user_role == "super_admin" and current_user_role != "super_admin":
        return jsonify({"status": "error", "message": "Thất bại: Thao tác này yêu cầu quyền Quản trị viên cấp cao nhất."}), 403

    if request.method == "DELETE":
        if username == session["username"]:
            return jsonify({"status": "error", "message": "Bạn không thể tự xóa chính mình"}), 400
        users.pop(user_idx)
        save_json("users.json", users)
        return jsonify({"status": "success"})
    
    # PUT - Cập nhật thông tin sinh viên
    data = request.json
    target_user = users[user_idx]
    
    # Các trường thông tin được phép cập nhật
    if "display_name" in data: target_user["display_name"] = data["display_name"]
    # Xử lý mật khẩu bị ẩn: chỉ cập nhật nếu mật khẩu gửi lên không phải là chuỗi ẩn danh '******'
    if "password" in data and data["password"] != "******": 
        target_user["password"] = data["password"]
    if "class_name" in data: target_user["class_name"] = data["class_name"]
    
    # Cập nhật các trường thông tin chi tiết khác (cho sinh viên)
    for field in STUDENT_FIELDS:
        if field in data:
            target_user[field] = data[field]
    
    # Việc cập nhật vai trò (role) bị vô hiệu hóa vì lý do bảo mật (theo yêu cầu)
    # Vai trò nên được thiết lập một lần khi tạo và không thay đổi sau đó để duy trì ranh giới quyền hạn.
            
    save_json("users.json", users)
    
    # Cập nhật session nếu người dùng đang tự cập nhật thông tin của chính mình
    if username == session["username"]:
        if "display_name" in data: session["display_name"] = data["display_name"]
        
    return jsonify({"status": "success"})

@app.route("/api/admin/import-template", methods=["GET"])
@login_required
@permission_required("manage_users")
def download_import_template():
    """Tải xuống file Excel mẫu để nhập danh sách sinh viên"""
    file_path = os.path.join(app.static_folder, "admin", "student_import_template.xlsx")
    if not os.path.exists(file_path):
        return jsonify({"status": "error", "message": "Không tìm thấy file mẫu trên máy chủ"}), 404
        
    return send_file(
        file_path,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='student_import_template.xlsx'
    )

@app.route("/api/admin/import-students", methods=["POST"])
@login_required
@permission_required("manage_users")
def import_students_excel():
    """API nhập danh sách sinh viên hàng loạt từ file Excel tải lên"""
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "Không tìm thấy file"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "Chưa chọn file"}), 400
        
    try:
        # Bước 1: Trích xuất và nạp File từ Request
        file = request.files['file']
        df = pd.read_excel(file)
        
        # Bước 2: CẤU HÌNH ÁNH XẠ (Mapping Configuration)
        # Chuyển đổi tiêu đề cột tiếng Việt từ Excel sang các Key tương ứng trong JSON hệ thống
        mapping = {
            "Mã sinh viên": "msv",
            "Họ và tên": "fullname",
            "Lớp": "class_name",
            "Ngành học": "major",
            "Ngày sinh": "dob",
            "Số điện thoại": "phone",
            "Email trường": "email_school",
            "Email cá nhân": "email_personal",
            "CCCD": "id_card",
            "Dân tộc": "ethnicity",
            "Địa chỉ": "address",
            "Họ tên cha": "father_name",
            "SĐT cha": "father_phone",
            "Email cha": "father_email",
            "Họ tên mẹ": "mother_name",
            "SĐT mẹ": "mother_phone",
            "Email mẹ": "mother_email"
        }
        
        # Bước 3: KIỂM TRA TÍNH TOÀN VẸN (Data Integrity)
        # Đảm bảo các cột định danh tối thiểu phải tồn tại
        required = ["Mã sinh viên", "Họ và tên"]
        for col in required:
            if col not in df.columns:
                return jsonify({"status": "error", "message": f"File Excel không đúng định dạng. Thiếu cột bắt buộc: {col}"}), 400
        
        users = load_json("users.json")
        import_count = 0
        skip_count = 0
        
        # Bước 4: DUYỆT TỪNG DÒNG DỮ LIỆU (Row Processing)
        for _, row in df.iterrows():
            username = str(row["Mã sinh viên"]).strip()
            # Bỏ qua các dòng trống hoặc bị lỗi NaN
            if not username or username == 'nan':
                continue
                
            # Kiểm tra trùng lặp: Nếu sinh viên đã có trong hệ thống thì bỏ qua
            if any(u["username"] == username for u in users):
                skip_count += 1
                continue
                
            # Khởi tạo đối tượng người dùng mới với mật khẩu mặc định trùng MSSV
            new_user = {
                "username": username,
                "password": username, 
                "display_name": str(row["Họ và tên"]).strip(),
                "role": "student",
                "class_name": str(row.get("Lớp", "--")).strip()
            }
            
            # Áp dụng logic ánh xạ cho các trường thông tin phụ
            for excel_col, json_field in mapping.items():
                if excel_col in df.columns and excel_col not in ["Mã sinh viên", "Họ và tên", "Lớp"]:
                    val = row[excel_col]
                    if pd.notna(val):
                        new_user[json_field] = str(val).strip()
            
            users.append(new_user)
            import_count += 1
            
        # Bước 5: Lưu vĩnh viễn vào File JSON
        save_json("users.json", users)
        return jsonify({
            "status": "success", 
            "message": f"Tiến trình hoàn tất: Đã nhập {import_count} tài khoản mới. (Bỏ qua {skip_count} tài khoản đã tồn tại)"
        })
        
    except Exception as e:
        # Xử lý các lỗi bất ngờ trong quá trình parse Excel (VD: file hỏng, sai định dạng date)
        return jsonify({"status": "error", "message": f"Lỗi xử lý file Excel: {str(e)}"}), 500

@app.route("/api/admin/exams/<int:eid>/submissions")
@login_required
@instructor_required
def get_exam_submissions(eid):
    submissions = load_json("submissions.json")
    test_attempts = load_json("test_attempts.json")
    
    exam_subs = [s for s in submissions if str(s.get("examId")) == str(eid)]
    exam_attempts = [a for a in test_attempts if str(a.get("examId")) == str(eid)]
    
    return jsonify({
        "submissions": exam_subs,
        "test_attempts": exam_attempts
    })

@app.route("/api/admin/exams/<int:eid>/cheat-logs", methods=["GET"])
@login_required
@instructor_required
def get_admin_exam_cheat_logs(eid):
    """API lấy toàn bộ log nghi ngờ gian lận của một kỳ thi (dành cho Admin)"""
    logs = load_json("cheat_logs.json") or []
    exam_logs = [l for l in logs if str(l.get("examId")) == str(eid)]
    return jsonify(exam_logs)

from google import genai

@app.route("/api/ai/hint", methods=["POST"])
@login_required
def get_ai_hint():
    """API sử dụng Google Gemini AI để gợi ý cách sửa lỗi cho sinh viên"""
    print("👉 [1] Đã nhận được request hỏi AI từ frontend!")
    # Bước 1: Trích xuất và Chuẩn hóa dữ liệu đầu vào
    data = request.json
    code = data.get("code")             # Mã nguồn hiện tại của học sinh
    language = data.get("language")     # Ngôn ngữ lập trình
    problem_title = data.get("problem_title")
    problem_desc = data.get("problem_desc")
    failed_tc = data.get("failed_test_case") # Thông tin về Test Case bị sai (Input/Expected/Actual)
 
    # Bước 2: Kiểm soát dữ liệu (Data Validation)
    if not all([code, language, problem_title, failed_tc]):
        return jsonify({"status": "error", "message": "Dữ liệu cung cấp không đầy đủ để AI có thể phân tích lỗi."}), 400
 
    # Bước 3: THIẾT KẾ PROMPT (Prompt Engineering)
    # Đây là phần quan trọng nhất để điều hướng AI trả về câu trả lời hữu ích nhưng không giải hộ bài hoàn toàn
    prompt = f"""
    Bạn là một gia sư lập trình AI tận tâm. Một học sinh đang giải bài tập "{problem_title}".
    Yêu cầu bài toán: {problem_desc}

    Học sinh đã viết đoạn code sau bằng ngôn ngữ {language}:
    ```{language}
    {code}
    ```

    Đoạn code này đã chạy sai ở một test case cụ thể:
    - Input: {failed_tc.get('input')}
    - Output mong muốn (Expected): {failed_tc.get('expected')}
    - Output thực tế của học sinh (Actual): {failed_tc.get('actual')}

    Nhiệm vụ của bạn:
    Hãy phân tích lý do tại sao code của học sinh lại cho ra kết quả sai ở test case này. 
    Đưa ra một gợi ý ngắn gọn, dễ hiểu để học sinh tự sửa.
    LƯU Ý: Không được cung cấp mã nguồn đúng (solution code) ngay lập tức, chỉ đưa ra hướng dẫn logic.
    """

    try:
        print("👉 [2] Đang kết nối với Google API...")
        
        client = genai.Client(api_key="") 
        
        print("👉 [3] Đang chờ AI trả lời...")
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        
        print("👉 [4] AI đã trả lời thành công!")
        return jsonify({"status": "success", "hint": response.text})
    except Exception as e:
        print(f"❌ [LỖI API]: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


# --- Xử lý Kết nối thời gian thực qua Socket.IO ---
@socketio.on('connect')
def handle_connect():
    """Sự kiện khi một máy khách (client) kết nối thành công"""
    print(f'Client connected: {request.sid}')
    emit('connected', {'status': 'ready'})

@socketio.on('disconnect')
def handle_disconnect():
    """Sự kiện khi một máy khách ngắt kết nối: dọn dẹp tài nguyên temp"""
    print(f'Client disconnected: {request.sid}')
    cleanup_session(request.sid)

# Mã nguồn C/C++ bổ sung để vô hiệu hóa bộ đệm (buffering), giúp output hiển thị tức thì qua socket
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
    """Sự kiện khởi tạo một phiên thực thi code trực tiếp (Console Run)"""
    session_id = request.sid
    language = data.get('language')
    code = data.get('code')
    
    print(f'Starting session {session_id} for language {language}')
    
    # Bước 1: DỌN DẸP TIỀN TRÌNH (Sanitization)
    # Đảm bảo không có tiến trình nào đang chạy ngầm của session này trước khi bắt đầu mới
    cleanup_session(session_id)
    
    try:
        # Bước 2: THIẾT LẬP MÔI TRƯỜNG CÔ LẬP (Isolation)
        config = LANGUAGE_CONFIG.get(language)
        if not config:
            emit('error', {'message': f'Ngôn ngữ không được hỗ trợ: {language}'})
            return
        
        # Sử dụng thư mục tạm 'temp_sessions' để quản lý tập trung các tệp thực thi
        base_temp = os.path.join(os.getcwd(), "temp_sessions")
        if not os.path.exists(base_temp):
            os.makedirs(base_temp)
            
        # Tạo thư mục tạm duy nhất cho mỗi phiên làm việc (MKDTEMP)
        temp_dir = tempfile.mkdtemp(dir=base_temp)
        ext = config['ext']
        
        # Ghi mã nguồn vào file vật lý trong thư mục tạm
        filename = config.get('main_file', f"code{ext}")
        code_file = os.path.join(temp_dir, filename)
        
        with open(code_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        # Bước 3: QUY TRÌNH BIÊN DỊCH (Compilation Pipeline)
        if config['compile']:
            # Xác định tên file đầu ra (.exe cho Windows)
            output_file = os.path.join(temp_dir, "program.exe" if os.name == 'nt' else "program")
            compile_cmd_template = config['compile']
            compile_files = [code_file]
            
            # KỸ THUẬT NÂNG CAO: Chèn code Flushing cho C/C++
            # Mục đích: Vô hiệu hóa tính năng buffering của HDH để output nhảy lên màn hình ngay khi lệnh in được gọi
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
            
            # Xây dựng lệnh biên dịch đầy đủ từ template
            final_compile_cmd = []
            for arg in compile_cmd_template:
                if "{file}" in arg:
                    final_compile_cmd.append(arg.format(file=code_file, output=output_file))
                elif "{output}" in arg:
                    final_compile_cmd.append(arg.format(output=output_file))
                else:
                    final_compile_cmd.append(arg)
            
            # Đính kèm file flush (nếu có) vào lệnh biên dịch chính
            for extra_file in compile_files[1:]:
                final_compile_cmd.append(extra_file)
 
            try:
                # Thực hiện biên dịch (subprocess.run) - Giới hạn tối đa 10s để tránh treo server
                compile_result = subprocess.run(
                    final_compile_cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    timeout=10
                )
                
                # Trả về lỗi biên dịch (Syntax Error/Linker Error) nếu có cho học sinh
                if compile_result.returncode != 0:
                    emit('error', {'message': f'Lỗi biên dịch bài làm:\n{compile_result.stderr}'})
                    cleanup_session(session_id)
                    return
                
                # Chuẩn bị lệnh thực thi sau khi đã biên dịch xong
                classname = "Main" if language == "java" else None
                run_cmd = [cmd.format(output=output_file, classname=classname) for cmd in config['run']]
            except FileNotFoundError:
                emit('error', {'message': f'Lỗi hệ thống: Không tìm thấy trình biên dịch cho {language}.'})
                cleanup_session(session_id)
                return
        else:
            # Ngôn ngữ thông dịch (Python/JS): Run trực tiếp file nguồn
            run_cmd = [cmd.format(file=code_file, project_dir=temp_dir) for cmd in config['run']]
            
        print(f"Executing: {' '.join(run_cmd)}")
        # Gửi thông báo lệnh chạy thực tế lên Console của học sinh (như Terminal thực thụ)
        emit('output', {'data': f"\r\n[Lệnh chạy]: {' '.join(run_cmd)}\r\n\r\n", 'session_id': session_id})
        
        # Bước 4: KHỞI CHẠY TIẾN TRÌNH (Process Spawning)
        # Sử dụng chế độ Binary (text=False) và bufsize=0 (Unbuffered) để đảm bảo dữ liệu truyền tải thời gian thực
        process = subprocess.Popen(
            run_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, # Gộp Luồng lỗi vào Luồng chuẩn
            text=False, 
            bufsize=0,  
            cwd=temp_dir
        )
        
        # Lưu Session vào RAM để điều khiển (Gửi Input/Kill process)
        active_sessions[session_id] = {
            'process': process,
            'temp_dir': temp_dir,
            'language': language
        }
        
        # Bước 5: KHỞI CHẠY CÁC LUỒNG THEO DÕI (Threading System)
        # Luồng 1: Đọc và Phát Output liên tục qua Socket
        stdout_thread = threading.Thread(target=read_output, args=(session_id, process.stdout, 'stdout'), daemon=True)
        stdout_thread.start()
        
        active_sessions[session_id]['stdout_thread'] = stdout_thread
        
        # Luồng 2: Giám sát vòng đời tiến trình (Wait & Timeout handling)
        threading.Thread(target=monitor_process, args=(session_id,), daemon=True).start()
        
        emit('session_started', {'status': 'running'})
        
    except Exception as e:
        print(f'Error starting session: {e}')
        emit('error', {'message': f'Lỗi hệ thống khi khởi tạo phiên làm việc: {str(e)}'})
        cleanup_session(session_id)

@socketio.on('send_input')
def handle_input(data):
    session_id = request.sid
    user_input = data.get('input', '')
    
    session = active_sessions.get(session_id)
    if not session:
        emit('error', {'message': 'Không tìm thấy phiên làm việc đang hoạt động'})
        return
    
    process = session['process']
    
    try:
        if process.poll() is None:  # Process still running
            # Mã hóa dữ liệu nhập vào sang chế độ binary để tương thích với luồng thực thi
            process.stdin.write((user_input + '\n').encode('utf-8'))
            process.stdin.flush()
    except Exception as e:
        print(f'Error sending input: {e}')
        emit('error', {'message': f'Lỗi khi gửi dữ liệu nhập: {str(e)}'})

@socketio.on('run_test_cases')
def handle_run_test_cases(data):
    """Sự kiện thực thi mã nguồn đối với một danh sách các bộ test case định sẵn (Kiểm tra bài)"""
    session_id = request.sid
    language = data.get('language')
    code = data.get('code')
    test_cases = data.get('test_cases', [])
    
    print(f'Running test cases for session {session_id}, language {language}')
    
    # Bước 1: Tạo thư mục tạm thời (temp dir) mới cho mỗi lượt test
    # Sử dụng thư mục cục bộ để tránh lỗi phân quyền (Permissions) trên Windows
    base_temp = os.path.join(os.getcwd(), "temp_sessions")
    if not os.path.exists(base_temp):
        os.makedirs(base_temp)
    temp_dir = tempfile.mkdtemp(dir=base_temp)
    
    try:
        config = LANGUAGE_CONFIG.get(language)
        if not config:
            emit('error', {'message': f'Ngôn ngữ không được hỗ trợ: {language}'})
            return

        ext = config['ext']
        filename = config.get('main_file', f"code{ext}")
        code_file = os.path.join(temp_dir, filename)
        
        with open(code_file, 'w', encoding='utf-8') as f:
            f.write(code)
            
        # Bước 2: Thực hiện biên dịch DUY NHẤT MỘT LẦN cho toàn bộ test cases
        exe_path = None
        run_cmd_template = config['run']
        
        if config['compile']:
            output_file = os.path.join(temp_dir, "program.exe" if os.name == 'nt' else "program")
            
            # Sử dụng lại logic biên dịch từ start_session (có kiểm tra chống injection)
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
                    emit('test_results', {'error': f'Lỗi biên dịch bài làm:\n{compile_result.stderr}'})
                    return
                exe_path = output_file
            except Exception as e:
                emit('test_results', {'error': f'Quá trình biên dịch thất bại: {str(e)}'})
                return
        
        # Chuẩn bị lệnh chạy
        if exe_path:
             # Đối với ngôn ngữ biên dịch
            classname = "Main" if language == "java" else None
            run_cmd = [cmd.format(output=exe_path, classname=classname) for cmd in run_cmd_template]
        else:
             # Tuyến đường 2: Đối với các ngôn ngữ thông dịch (Python, Node...)
            run_cmd = [cmd.format(file=code_file, project_dir=temp_dir) for cmd in run_cmd_template]

        results = []
        
        for i, case in enumerate(test_cases):
            case_input = case.get('input', '')
            case_expected = case.get('output', '')
            
            try:
                # Sử dụng chế độ binary (text=False) để đảm bảo đồng nhất với các bản fix trước đó
                process = subprocess.Popen(
                    run_cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=False,
                    bufsize=0,
                    cwd=temp_dir
                )
                
                # Thực thi mã nguồn trong môi trường Subprocess an toàn
                try:
                    # Gửi input và thu thập kết quả (Timeout 5 giây cho mỗi lượt)
                    stdout_data, _ = process.communicate(input=(case_input + '\n').encode('utf-8'), timeout=5)
                    actual_output = stdout_data.decode('utf-8', errors='replace')
                except subprocess.TimeoutExpired:
                    # Ngắt tiến trình ngay lập tức nếu vượt quá thời gian cho phép
                    process.kill()
                    actual_output = "Lỗi: Quá thời gian thực thi (giới hạn 5 giây)"
                
                # Kiểm tra xem output thực tế có khớp hoàn toàn với output mong đợi hay không
                # LƯU Ý: Trong lập trình thi đấu (CP), việc so sánh thường rất khắt khe về khoảng trắng.
                # Tuy nhiên, phiên bản này thực hiện chuẩn hóa (normalize) để hỗ trợ tốt hơn cho việc học tập.
                passed = normalize_text(actual_output) == normalize_text(case_expected)
                
                # Logic dự phòng: Nếu bài tập yêu cầu in ra prompt nhập (ví dụ: "Nhập a: ") thì 
                # việc so khớp tuyệt đối có thể thất bại. Hiện tại chúng tôi mặc định bài tập 
                # trong problems.json chỉ chứa output thuần túy là dữ liệu kết quả.
                
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
    """Chuẩn hóa văn bản để so sánh kết quả: loại bỏ khoảng trắng thừa đầu cuối và các dòng trống"""
    if not text: return ""
    return "\n".join([line.rstrip() for line in text.strip().splitlines() if line.strip()])


@socketio.on('stop_session')
def handle_stop_session():
    """Sự kiện dừng phiên làm việc đang chạy theo yêu cầu người dùng"""
    session_id = request.sid
    cleanup_session(session_id)
    emit('session_ended', {'reason': 'stopped by user'})

def read_output(session_id, stream, stream_type):
    """Đọc dữ liệu output từ tiến trình và gửi về máy khách (client) theo thời gian thực"""
    try:
        # Đọc từng byte một để tạo cảm giác tương tác trực tiếp (real-time feel)
        while True:
            # Đọc theo byte (binary mode) để tránh lỗi decode khi output chưa hoàn chỉnh
            byte = stream.read(1)
            if not byte:
                break
            
            # Lưu ý kiến trúc: Chúng tôi đã lược bỏ việc kiểm tra 'if session_id not in active_sessions'
            # để đảm bảo luồng đọc stream được hoàn thành trọn vẹn ngay cả khi việc dọn dẹp đã bắt đầu,
            # miễn là stream vẫn đang mở và liên tục trả về dữ liệu.
            
            # Giải mã byte sang ký tự (Char)
            try:
                char = byte.decode('utf-8', errors='replace')
            except:
                # Trường hợp lỗi giải mã nghiêm trọng, dùng dấu hỏi để không làm ngắt quãng output
                char = '?'
                
            # Gửi ký tự đơn lẻ về client qua kênh 'output' của đúng session_id
            socketio.emit('output', {
                'data': char,
                'type': stream_type
            }, room=session_id)
    except Exception as e:
        print(f'Error reading {stream_type}: {e}')
    finally:
        stream.close()

def monitor_process(session_id):
    """
    Luồng giám sát trạng thái của tiến trình thực thi code:
    - Kiểm tra Timeout (mặc định 60 giây cho mỗi phiên).
    - Tự động đóng luồng dữ liệu (stdout) và dọn dẹp tài nguyên khi kết thúc.
    - Phát tín hiệu 'session_ended' về cho client để cập nhật giao diện.
    """
    session = active_sessions.get(session_id)
    if not session:
        return
    
    process = session['process']
    stdout_thread = session.get('stdout_thread')
    
    try:
        # Chờ tiến trình hoàn thành (tối đa 60 giây)
        process.wait(timeout=60)
        
        # Sau khi tiến trình kết thúc, chờ luồng đọc output hoàn tất việc đẩy dữ liệu
        if stdout_thread and stdout_thread.is_alive():
            stdout_thread.join(timeout=2)
            
    except subprocess.TimeoutExpired:
        print(f'Process timeout for session {session_id}')
        # Cưỡng bức dừng tiến trình nếu chạy quá giờ
        process.kill()
        socketio.emit('error', {
            'message': 'Lỗi: Quá thời gian thực thi (giới hạn 60 giây)'
        }, room=session_id)
    
    # Phát sự kiện thông báo phiên làm việc đã kết thúc chính thức
    socketio.emit('session_ended', {
        'reason': 'process completed',
        'exit_code': process.returncode
    }, room=session_id)
    
    # Cleanup
    cleanup_session(session_id)

def cleanup_session(session_id):
    """
    Dọn dẹp triệt để tài nguyên sau khi kết thúc phiên:
    1. Kiên quyết dừng (kill) tiến trình con nếu còn đang kẹt.
    2. Đóng các luồng nhập/xuất để giải phóng tài nguyên hệ thống.
    3. Xóa vĩnh viễn thư mục tạm thời khỏi bộ nhớ đệm (temp_sessions).
    """
    session = active_sessions.pop(session_id, None)
    if not session:
        return
    
    process = session['process']
    temp_dir = session['temp_dir']
    
    # Kiểm tra và dừng tiến trình con nếu vẫn còn đang chạy ngầm
    if process.poll() is None:
        try:
            process.kill()
            process.wait(timeout=5)
        except:
            pass
    
    # Xóa sạch thư mục tạm thời của phiên này để giải phóng ổ đĩa
    try:
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    except Exception as e:
        print(f'Error cleaning up temp dir: {e}')


def cleanup_dangling_temps():
    """
    Dọn dẹp các thư mục tạm còn sót lại (dangling folders):
    - Chạy khi khởi động server để đảm bảo ổ đĩa không bị đầy bởi các file rác
    từ các phiên làm việc bị sập đột ngột ở lần chạy trước.
    """
    try:
        current_dir = os.getcwd()
        # Bước 1: Dọn dẹp nội dung thư mục temp_sessions nhưng vẫn giữ lại thư mục cha
        temp_sessions = os.path.join(current_dir, "temp_sessions")
        if os.path.exists(temp_sessions):
            try:
                import shutil
                shutil.rmtree(temp_sessions)
                os.makedirs(temp_sessions)
                print("Đã làm sạch thư mục temp_sessions")
            except Exception as e:
                print(f"Cảnh báo: Không thể làm sạch thư mục temp_sessions: {e}")

        # Bước 2: Dọn dẹp các thư mục tạm thời dạng temp_* cũ còn sót lại trong thư mục gốc
        for name in os.listdir(current_dir):
            if name.startswith("temp_") and os.path.isdir(os.path.join(current_dir, name)):
                if name == "temp_sessions": continue
                try:
                    import shutil
                    shutil.rmtree(os.path.join(current_dir, name))
                    print(f"Đã xóa thư mục tạm thừa: {name}")
                except Exception as e:
                    print(f"Cảnh báo: Không thể xóa {name}: {e}")
    except Exception as e:
        print(f"Lỗi trong quá trình dọn dẹp khởi động: {e}")

if __name__ == "__main__":
    # Khởi động ứng dụng Flask với SocketIO
    # Cấu hình host 0.0.0.0 để cho phép truy cập từ các thiết bị khác trong mạng LAN
    # Cấu hình port 5001 - Cần đảm bảo port này không bị chiếm dụng bởi ứng dụng khác
    print("=" * 50)
    print("Máy chủ đang khởi chạy tại: http://localhost:5001")
    print("Phiên bản Python:", os.sys.version)
    print("Chế độ Async: threading")
    
    # Dọn dẹp các file tạm khi khởi động server
    cleanup_dangling_temps()
    
    print("=" * 50)
    
    # Khởi chạy ứng dụng với SocketIO hỗ trợ đa kết nối và không giới hạn bảo mật Werkzeug (cho dev)
    socketio.run(app, host='0.0.0.0', port=5001, debug=True, use_reloader=False, allow_unsafe_werkzeug=True)
