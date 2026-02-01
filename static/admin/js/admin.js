// Global state for each management tab
const state = {
  problems: {
    data: [],
    filtered: [],
    page: 1,
    limit: 10,
    search: "",
    sortKey: "id",
    sortDir: "desc",
    filters: { category: "all", difficulty: "all" },
  },
  students: {
    data: [],
    filtered: [],
    page: 1,
    limit: 10,
    search: "",
    sortKey: "username",
    sortDir: "asc",
    filters: {},
  },
  submissions: {
    data: [],
    filtered: [],
    page: 1,
    limit: 15,
    search: "",
    sortKey: "timestamp",
    sortDir: "desc",
    filters: { lang: "all" },
  },
  reports_students: {
    data: [],
    filtered: [],
    page: 1,
    limit: 100,
    search: "",
    sortKey: "solved_count",
    sortDir: "desc",
    filters: {},
  },
  reports_problems: {
    data: [],
    filtered: [],
    page: 1,
    limit: 100,
    search: "",
    sortKey: "attempt_count",
    sortDir: "desc",
    filters: { difficulty: "all" },
  },
  exams: {
    data: [],
    filtered: [],
    page: 1,
    limit: 10,
    search: "",
    sortKey: "id",
    sortDir: "desc",
    filters: {},
  },
  reports_exams: {
    data: [],
    filtered: [],
    page: 1,
    limit: 100,
    search: "",
    sortKey: "score",
    sortDir: "desc",
    filters: {},
  },
};

if (typeof currentTab === 'undefined') {
    window.currentTab = "dashboard";
}

function showTab(tab, updateUrl = true) {
  currentTab = tab;
  
  // Hide all tabs
  document
    .querySelectorAll(".admin-tab")
    .forEach((t) => (t.style.display = "none"));
    
  // Show target tab
  const tabEl = document.getElementById(`tab-${tab}`);
  if (tabEl) tabEl.style.display = "block";

  // Handle active class for sidebar
  document
    .querySelectorAll(".admin-nav-item")
    .forEach((i) => i.classList.remove("active"));
  
  const navItems = document.querySelectorAll(".admin-nav-item");
  navItems.forEach(item => {
      const onclickHeader = item.getAttribute('onclick');
      // match 'tab' precisely
      if (onclickHeader && (onclickHeader.includes(`'${tab}'`) || onclickHeader.includes(`"${tab}"`))) {
          item.classList.add("active");
      }
  });

  // Toggle sub-nav visibility
  const subNav = document.getElementById('sub-nav-reports');
  if (subNav) {
      if (tab === 'reports' || tab === 'submissions' || tab.startsWith('reports_')) {
          subNav.style.display = 'block';
          
          if (tab === 'submissions') {
              document.querySelectorAll('.admin-sub-item').forEach(i => i.classList.remove('active'));
              const subItem = document.getElementById('sub-item-submissions');
              if (subItem) subItem.classList.add('active');
              
              document.querySelectorAll('.admin-nav-item').forEach(i => {
                if(i.textContent.trim() === 'Báo cáo') i.classList.add('active');
              });
          }
      } else {
          subNav.style.display = 'none';
      }
  }

  // Update URL if requested
  if (updateUrl && window.location.pathname !== `/admin/${tab}`) {
      const path = tab === 'dashboard' ? '/admin' : `/admin/${tab}`;
      history.pushState({ tab }, "", path);
  }

  loadData();
}

// Initial load based on URL
function initRouting() {
    const path = window.location.pathname;
    const parts = path.split('/');
    const tab = parts[parts.length - 1];
    
    const validTabs = ["dashboard", "problems", "students", "reports", "exams", "submissions"];
    if (validTabs.includes(tab)) {
        showTab(tab, false);
    } else if (path === "/admin") {
        showTab("dashboard", false);
    }
}

window.onpopstate = (event) => {
    if (event.state && event.state.tab) {
        showTab(event.state.tab, false);
    } else {
        initRouting();
    }
};

function switchReport(view) {
    currentReportView = view;
    
    // Ensure we are on the reports tab
    if (currentTab !== 'reports') {
        showTab('reports');
    }

    // Update sub-item active state
    document.querySelectorAll('.admin-sub-item').forEach(item => {
        item.classList.remove('active');
        if (item.id === `sub-item-reports_${view}`) {
            item.classList.add('active');
        }
    });

    // Update title
    const titleMap = {
        'students': 'Bảng xếp hạng SV',
        'problems': 'Thống kê bài tập',
        'exams': 'Lịch sử thi'
    };
    const titleEl = document.getElementById('report-title');
    if (titleEl) titleEl.textContent = titleMap[view];

    // Show/hide sub-tabs
    const reportsStudents = document.getElementById("tab-reports_students");
    const reportsProblems = document.getElementById("tab-reports_problems");
    const reportsExams = document.getElementById("tab-reports_exams");

    if (reportsStudents) reportsStudents.style.display = view === "students" ? "block" : "none";
    if (reportsProblems) reportsProblems.style.display = view === "problems" ? "block" : "none";
    if (reportsExams) reportsExams.style.display = view === "exams" ? "block" : "none";

    renderTable(`reports_${view}`);
}

async function loadData() {
  if (currentTab === "dashboard") {
    const res = await fetch("/api/admin/stats");
    const stats = await res.json();

    document.getElementById("stat-problems").textContent = stats.problem_count;
    document.getElementById("stat-students").textContent = stats.student_count;
    document.getElementById("stat-hits").textContent = stats.student_logins;
    
    if (document.getElementById("stat-exams"))
        document.getElementById("stat-exams").textContent = stats.exam_count;
    if (document.getElementById("stat-active-exams"))
        document.getElementById("stat-active-exams").textContent = stats.active_exam_count;
    if (document.getElementById("stat-exam-subs"))
        document.getElementById("stat-exam-subs").textContent = stats.exam_submission_count;

    const langContainer = document.getElementById("lang-stats");
    langContainer.innerHTML = "";
    const total = Object.values(stats.languages).reduce((a, b) => a + b, 0);

    for (const [lang, count] of Object.entries(stats.languages)) {
      const percent = total > 0 ? ((count / total) * 100).toFixed(1) : 0;
      langContainer.innerHTML += `
                <div class="lang-bar-item">
                    <div class="lang-label">
                        <span>${lang.toUpperCase()}</span>
                        <span>${count} (${percent}%)</span>
                    </div>
                    <div class="progress-bg"><div class="progress-fill" style="width: ${percent}%"></div></div>
                </div>
            `;
    }

    const activityBody = document.getElementById("recent-activity-body");
    activityBody.innerHTML =
      stats.recent_activity
        .reverse()
        .map(
          (s) => `
            <tr>
                <td>${s.username}</td>
                <td>${s.problemTitle}</td>
                <td>${s.language}</td>
                <td style="font-size:0.8rem">${s.timestamp}</td>
            </tr>
        `,
        )
        .join("") ||
      '<tr><td colspan="4" style="text-align:center">Chưa có hoạt động nào</td></tr>';

    const examActivityBody = document.getElementById("recent-exam-activity-body");
    if (examActivityBody) {
        examActivityBody.innerHTML =
        stats.recent_exam_activity
            .reverse()
            .map(
            (s) => `
                <tr>
                    <td>${s.username}</td>
                    <td>${s.examTitle}</td>
                    <td>${s.problemTitle}</td>
                    <td style="font-size:0.8rem">${s.timestamp}</td>
                </tr>
            `,
            )
            .join("") ||
        '<tr><td colspan="4" style="text-align:center">Chưa có hoạt động nào</td></tr>';
    }
} else if (currentTab === "reports") {
    loadReports();
  } else {
    const endpoints = {
      problems: "/problems",
      students: "/api/admin/students",
      submissions: "/api/submissions",
      exams: "/api/admin/exams",
    };

    try {
      const res = await fetch(endpoints[currentTab]);
      let data = await res.json();

      // Map English difficulty to Vietnamese for Problems tab
      if (currentTab === "problems") {
        const diffMap = { Easy: "Dễ", Medium: "Trung bình", Hard: "Khó" };
        data = data.map((p) => ({
          ...p,
          difficulty: diffMap[p.difficulty] || p.difficulty,
        }));
      }

      state[currentTab].data = data;
      state[currentTab].page = 1; // Reset to first page on reload
      updateFilteredData(currentTab);
      renderTable(currentTab);
    } catch (e) {
      console.error(`Failed to load ${currentTab}:`, e);
    }
  }
}

function updateFilteredData(tab) {
  const s = state[tab];
  const query = s.search.toLowerCase();

  // Filter
  s.filtered = s.data.filter((item) => {
    // Search matches
    let matchesSearch = true;
    if (tab === "problems") {
      matchesSearch =
        item.title.toLowerCase().includes(query) ||
        item.category.toLowerCase().includes(query) ||
        item.id.toString().includes(query);

      // Dropdown filters
      const matchesCategory =
        s.filters.category === "all" ||
        (item.category &&
          item.category
            .toLowerCase()
            .includes(s.filters.category.toLowerCase()));
      const matchesDifficulty =
        s.filters.difficulty === "all" ||
        item.difficulty === s.filters.difficulty;

      return matchesSearch && matchesCategory && matchesDifficulty;
    } else if (tab === "students") {
      matchesSearch =
        item.username.toLowerCase().includes(query) ||
        item.display_name.toLowerCase().includes(query) ||
        (item.class_name && item.class_name.toLowerCase().includes(query));
      return matchesSearch;
    } else if (tab === "submissions") {
      matchesSearch =
        item.username.toLowerCase().includes(query) ||
        item.problemTitle.toLowerCase().includes(query) ||
        item.language.toLowerCase().includes(query);

      const matchesLang =
        s.filters.lang === "all" || item.language === s.filters.lang;

      return matchesSearch && matchesLang;
    } else if (tab === "reports_students") {
      matchesSearch =
        item.username.toLowerCase().includes(query) ||
        item.display_name.toLowerCase().includes(query) ||
        (item.class_name && item.class_name.toLowerCase().includes(query));
      return matchesSearch;
    } else if (tab === "reports_problems") {
      matchesSearch =
        item.title.toLowerCase().includes(query) ||
        item.id.toString().includes(query);

      const matchesDiff =
        s.filters.difficulty === "all" ||
        item.difficulty === s.filters.difficulty;
      return matchesSearch && matchesDiff;
    } else if (tab === "reports_exams") {
      matchesSearch =
        item.examTitle.toLowerCase().includes(query) ||
        item.display_name.toLowerCase().includes(query) ||
        item.username.toLowerCase().includes(query);
      return matchesSearch;
    }
    return true;
  });

  // Sort
  s.filtered.sort((a, b) => {
    let valA = a[s.sortKey];
    let valB = b[s.sortKey];

    if (typeof valA === "string") valA = valA.toLowerCase();
    if (typeof valB === "string") valB = valB.toLowerCase();

    if (valA < valB) return s.sortDir === "asc" ? -1 : 1;
    if (valA > valB) return s.sortDir === "asc" ? 1 : -1;
    return 0;
  });
}

function renderTable(tab) {
  const s = state[tab];
  if (!s) return;

  const body = document.getElementById(`${tab}-body`);
  if (!body) return;

  const start = (s.page - 1) * s.limit;
  const end = start + s.limit;
  const pageData = s.filtered.slice(start, end);

  if (tab === "problems") {
    body.innerHTML = pageData
      .map(
        (p) => `
            <tr>
                <td>${p.id}</td>
                <td>${p.title}</td>
                <td><span class="difficulty-badge">${p.difficulty}</span></td>
                <td>${p.category}</td>
                <td>
                    <button class="secondary-btn" onclick="editProblem(${p.id})">Sửa</button>
                    <button class="secondary-btn" style="color:#ff7b72" onclick="deleteProblem(${p.id})">Xóa</button>
                </td>
            </tr>
        `,
      )
      .join("");
  } else if (tab === "students") {
    body.innerHTML = pageData
      .map(
        (s) => `
            <tr>
                <td>${s.username}</td>
                <td>${s.display_name}</td>
                <td style="text-align:center">${s.class_name || "--"}</td>
                <td style="text-align:center"><b>${s.solved_count}</b></td>
                <td style="text-align:center">${s.submission_count}</td>
                <td><span class="status-badge" style="background:rgba(88,166,255,0.1);color:var(--accent)">${s.main_lang}</span></td>
                <td><code>${s.password}</code></td>
                <td>
                    <button class="secondary-btn" onclick="viewStudentStats('${s.username}')">Thống kê</button>
                    <button class="secondary-btn" onclick="editStudent('${s.username}')">Sửa</button>
                </td>
            </tr>
        `,
      )
      .join("");
  } else if (tab === "submissions") {
    body.innerHTML = pageData
      .map(
        (s) => `
            <tr>
                <td>${s.username}</td>
                <td>ID: ${s.problemId} - ${s.problemTitle}</td>
                <td>${s.language}</td>
                <td style="font-size:0.8rem">${s.timestamp}</td>
                <td><span class="status-badge badge-success">SỐNG</span></td>
            </tr>
        `,
      )
      .join("");
  } else if (tab === "reports_students") {
    body.innerHTML =
      pageData
        .map(
          (s, i) => `
            <tr>
                <td style="font-weight:bold; color:${(s.rank || i + 1) <= 3 ? "var(--accent)" : "inherit"}">#${s.rank || i + 1}</td>
                <td>${s.display_name} (@${s.username})</td>
                <td style="text-align:center">${s.class_name || "--"}</td>
                <td><b>${s.solved_count}</b></td>
                <td>${s.submission_count}</td>
                <td>
                    <div style="display:flex; align-items:center; gap:10px">
                        <div class="progress-bg" style="flex:1; height:6px"><div class="progress-fill" style="width:${s.success_rate}%"></div></div>
                        <span style="font-size:0.8rem">${s.success_rate}%</span>
                    </div>
                </td>
            </tr>
        `,
        )
        .join("") ||
      '<tr><td colspan="5" style="text-align:center">Chưa có dữ liệu</td></tr>';
  } else if (tab === "reports_problems") {
    body.innerHTML =
      pageData
        .map(
          (p) => `
            <tr>
                <td>${p.id}</td>
                <td>${p.title}</td>
                <td><span class="difficulty-badge">${p.difficulty}</span></td>
                <td>${p.attempt_count}</td>
                <td><b>${p.pass_count} SV</b></td>
            </tr>
        `,
        )
        .join("") ||
      '<tr><td colspan="5" style="text-align:center">Chưa có dữ liệu</td></tr>';
    renderPagination(tab);
    updateSortUI(tab);
  } else if (tab === "exams") {
    body.innerHTML = pageData
      .map(
        (e) => `
        <tr>
            <td>
                <div style="font-weight:600">${e.title}</div>
                <div style="font-size:0.75rem; color:var(--text-secondary)">
                    ${e.openTime ? "Bắt đầu: " + e.openTime.replace("T", " ") : ""}
                    ${e.closeTime ? "<br>Kết thúc: " + e.closeTime.replace("T", " ") : ""}
                </div>
            </td>
            <td>${e.startTime || "--"}</td>
            <td>${(e.problemIds || []).length}</td>
            <td>${e.duration}p</td>
            <td><span class="status-badge" style="background:${e.isActive ? "rgba(63,185,80,0.1);color:#3fb950" : "rgba(248,81,73,0.1);color:#f85149"}">${e.isActive ? "Đang mở" : "Đã đóng"}</span></td>
            <td>
                <button class="secondary-btn" onclick="location.href='/admin/create-exam?id=${e.id}'">Sửa</button>
                <button class="secondary-btn" style="color:#ff7b72" onclick="deleteExam(${e.id})">Xóa</button>
                <button class="secondary-btn" onclick="location.href='/exam?id=${e.id}'" title="Xem trước trang thi">👁️</button>
            </td>
        </tr>
    `
      )
      .join("");
    renderPagination(tab);
    updateSortUI(tab);
  } else if (tab === "reports_exams") {
    body.innerHTML =
      pageData
        .map((r) => {
          const percent = r.total_possible > 0 ? (r.score / r.total_possible) * 100 : 0;
          return `
            <tr>
                <td><div style="font-weight:600">${r.examTitle}</div><div style="font-size:0.75rem;color:var(--text-secondary)">ID: ${r.examId}</div></td>
                <td><div style="font-weight:600">${r.display_name}</div><div style="font-size:0.75rem;color:var(--text-secondary)">@${r.username} | ${r.class_name}</div></td>
                <td style="text-align:center">${r.solved_count} / ${r.problem_count}</td>
                <td><span class="status-badge" style="background:rgba(88,166,255,0.1);color:var(--accent);font-weight:bold;font-size:1rem">${r.score}</span> <small>/ ${r.total_possible}</small></td>
                <td>
                    <div style="display:flex; align-items:center; gap:10px; min-width:120px">
                        <div class="progress-bg" style="flex:1; height:8px"><div class="progress-fill" style="width:${percent}%"></div></div>
                        <span style="font-size:0.8rem">${percent.toFixed(0)}%</span>
                    </div>
                </td>
            </tr>
        `;
        })
        .join("") || '<tr><td colspan="5" style="text-align:center">Chưa có kết quả thi nào</td></tr>';
  }
}

function renderPagination(tab) {
  const s = state[tab];
  if (!s) return;

  const container = document.getElementById(`pagination-${tab}`);
  if (!container) return;

  const totalPages = Math.ceil(s.filtered.length / s.limit);
  if (totalPages <= 1) {
    container.innerHTML = "";
    return;
  }

  let html = `
        <div class="pagination-info">Hiển thị ${Math.min(s.filtered.length, (s.page - 1) * s.limit + 1)}-${Math.min(s.filtered.length, s.page * s.limit)} trong số ${s.filtered.length}</div>
        <div class="pagination-controls">
            <button class="page-btn" onclick="changePage('${tab}', 1)" ${s.page === 1 ? "disabled" : ""}>&laquo;</button>
            <button class="page-btn" onclick="changePage('${tab}', ${s.page - 1})" ${s.page === 1 ? "disabled" : ""}>Trước</button>
    `;

  // Show few pages around current
  const startPage = Math.max(1, s.page - 2);
  const endPage = Math.min(totalPages, s.page + 2);

  for (let i = startPage; i <= endPage; i++) {
    html += `<button class="page-btn ${i === s.page ? "active" : ""}" onclick="changePage('${tab}', ${i})">${i}</button>`;
  }

  html += `
            <button class="page-btn" onclick="changePage('${tab}', ${s.page + 1})" ${s.page === totalPages ? "disabled" : ""}>Sau</button>
            <button class="page-btn" onclick="changePage('${tab}', ${totalPages})" ${s.page === totalPages ? "disabled" : ""}>&raquo;</button>
        </div>
    `;
  container.innerHTML = html;
}

function changePage(tab, page) {
  state[tab].page = page;
  renderTable(tab);
}

function onSearch(tab) {
  state[tab].search = document.getElementById(`search-${tab}`).value;
  state[tab].page = 1;
  updateFilteredData(tab);
  renderTable(tab);
}

function onSort(tab, key) {
  if (state[tab].sortKey === key) {
    state[tab].sortDir = state[tab].sortDir === "asc" ? "desc" : "asc";
  } else {
    state[tab].sortKey = key;
    state[tab].sortDir = "asc";
  }
  updateFilteredData(tab);
  renderTable(tab);
}

function updateSortUI(tab) {
  const container = document.getElementById(`tab-${tab}`);
  if (!container) return;

  const headers = container.querySelectorAll("th[onclick]");
  headers.forEach((h) => {
    h.classList.remove("sort-asc", "sort-desc");
    if (h.getAttribute("onclick").includes(`'${state[tab].sortKey}'`)) {
      h.classList.add(`sort-${state[tab].sortDir}`);
    }
  });
}

function onFilter(tab) {
  if (tab === "problems") {
    state.problems.filters.category = document.getElementById(
      "filter-problems-category",
    ).value;
    state.problems.filters.difficulty = document.getElementById(
      "filter-problems-difficulty",
    ).value;
  } else if (tab === "submissions") {
    state.submissions.filters.lang = document.getElementById(
      "filter-submissions-lang",
    ).value;
  } else if (tab === "reports_problems") {
    state.reports_problems.filters.difficulty = document.getElementById(
      "filter-reports_problems-difficulty",
    ).value;
  }
  state[tab].page = 1;
  updateFilteredData(tab);
  renderTable(tab);
}

function openProblemModal() {
  window.location.href = "/admin/edit-problem";
}

function editProblem(id) {
  window.location.href = `/admin/edit-problem?id=${id}`;
}

async function deleteProblem(id) {
  if (!confirm("Bạn có chắc chắn muốn xóa bài tập này?")) return;
  await fetch(`/api/admin/problems/${id}`, { method: "DELETE" });
  loadData();
}

// Student Stats & Detail
async function viewStudentStats(username) {
  showTab("student-detail");
  const res = await fetch(`/api/admin/students/${username}/stats`);
  const data = await res.json();

  document.getElementById("student-detail-name").textContent =
    `Thống kê chi tiết: ${data.info.display_name} (@${username})`;
  document.getElementById("student-stat-solved").textContent =
    data.solved_count;
  document.getElementById("student-stat-subs").textContent =
    data.total_submissions;

  // Find main language
  let mainLang = "--";
  let max = 0;
  for (const [l, c] of Object.entries(data.languages)) {
    if (c > max) {
      max = c;
      mainLang = l.toUpperCase();
    }
  }
  document.getElementById("student-stat-lang").textContent = mainLang;

  // Language chart
  const langContainer = document.getElementById("student-lang-stats");
  langContainer.innerHTML = "";
  for (const [lang, count] of Object.entries(data.languages)) {
    const percent =
      data.total_submissions > 0
        ? ((count / data.total_submissions) * 100).toFixed(1)
        : 0;
    langContainer.innerHTML += `
            <div class="lang-bar-item">
                <div class="lang-label"><span>${lang.toUpperCase()}</span><span>${count} (${percent}%)</span></div>
                <div class="progress-bg"><div class="progress-fill" style="width: ${percent}%"></div></div>
            </div>
        `;
  }

  // Activity body
  const activityBody = document.getElementById("student-activity-body");
  activityBody.innerHTML =
    data.recent_activity
      .reverse()
      .map(
        (s) => `
        <tr>
            <td>${s.problemTitle}</td>
            <td>${s.language}</td>
            <td style="font-size:0.8rem">${s.timestamp}</td>
        </tr>
    `,
      )
      .join("") ||
    '<tr><td colspan="3" style="text-align:center">Chưa có hoạt động nào</td></tr>';
}

let editingUsername = null;

function editStudent(username) {
  editingUsername = username;
  const student = state.students.data.find((s) => s.username === username);
  if (!student) return;

  document.getElementById("student-modal-title").textContent =
    "Sửa tài khoản sinh viên";
  document.getElementById("s-user").value = student.username;
  document.getElementById("s-user").disabled = true; // Cannot change username
  document.getElementById("s-name").value = student.display_name;
  document.getElementById("s-class").value = student.class_name || "";
  document.getElementById("s-pass").value = student.password;

  document.getElementById("student-modal").style.display = "flex";
}

function openStudentModal() {
  editingUsername = null;
  document.getElementById("student-modal-title").textContent =
    "Thêm sinh viên mới";
  document.getElementById("s-user").value = "";
  document.getElementById("s-user").disabled = false;
  document.getElementById("s-name").value = "";
  document.getElementById("s-class").value = "";
  document.getElementById("s-pass").value = "";
  document.getElementById("student-modal").style.display = "flex";
}

function closeModals() {
  document
    .querySelectorAll(".modal")
    .forEach((m) => (m.style.display = "none"));
}

async function saveStudent() {
  const data = {
    username: document.getElementById("s-user").value,
    display_name: document.getElementById("s-name").value,
    class_name: document.getElementById("s-class").value,
    password: document.getElementById("s-pass").value,
  };

  if (!data.username || !data.display_name || !data.password) {
    alert("Vui lòng điền đầy đủ thông tin");
    return;
  }

  const method = editingUsername ? "PUT" : "POST";
  const res = await fetch("/api/admin/students", {
    method: method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (res.ok) {
    closeModals();
    loadData();
  } else {
    const err = await res.json();
    alert(err.message || "Lỗi khi lưu thông tin");
  }
}

// Reports logic
let currentReportView = "students";

function toggleReportView(view) {
    switchReport(view);
}

async function loadReports() {
  try {
    const res = await fetch(`/api/admin/reports?t=${Date.now()}`);
    const data = await res.json();

    // Assign ranks to students before filtering so ranks stay consistent with leaderboard
    const students = data.students || [];
    students.forEach((s, i) => (s.rank = i + 1));

    state.reports_students.data = students;
    state.reports_problems.data = data.problems || [];

    // Flatten Exam Reports for the table
    const flatExamReports = [];
    (data.exams || []).forEach((ex) => {
      (ex.results || []).forEach((res) => {
        flatExamReports.push({
          examId: ex.id,
          examTitle: ex.title,
          problem_count: ex.problem_count,
          total_possible: ex.total_points,
          ...res,
        });
      });
    });
    state.reports_exams.data = flatExamReports;

    updateFilteredData("reports_students");
    updateFilteredData("reports_problems");
    updateFilteredData("reports_exams");

    toggleReportView(currentReportView);
  } catch (e) {
    console.error("Failed to load reports:", e);
  }
}

async function deleteExam(id) {
  if (!confirm("Bạn có chắc chắn muốn xóa kỳ thi này?")) return;
  const res = await fetch(`/api/admin/exams/${id}`, { method: "DELETE" });
  if (res.ok) {
    loadData();
  } else {
    alert("Không thể xóa kỳ thi.");
  }
}

// Init
initRouting();
