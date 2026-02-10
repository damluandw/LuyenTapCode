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
    limit: 10,
    search: "",
    sortKey: "solved_count",
    sortDir: "desc",
    filters: {},
  },
  reports_problems: {
    data: [],
    filtered: [],
    page: 1,
    limit: 10,
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
    limit: 10,
    search: "",
    sortKey: "score",
    sortDir: "desc",
    filters: {},
  },
};

if (typeof currentTab === 'undefined') {
  window.currentTab = "dashboard";
}
if (typeof examReportView === 'undefined') {
  window.examReportView = "exams";
}
if (typeof selectedExamId === 'undefined') {
  window.selectedExamId = null;
}
if (typeof selectedUsername === 'undefined') {
  window.selectedUsername = null;
}
if (typeof allExamSubmissions === 'undefined') {
  window.allExamSubmissions = [];
}

function showTab(tab, updateUrl = true) {
  // Mapping new page URLs to internal state keys
  const mapping = {
    'report-students': 'reports_students',
    'report-problems': 'reports_problems',
    'report-exams': 'reports_exams',
    'report-exam-detail': 'reports_exams',
    'report-exam-submissions': 'reports_exams',
    'report-students.html': 'reports_students',
    'report-problems.html': 'reports_problems',
    'report-exams.html': 'reports_exams',
    'report-exam-detail.html': 'reports_exams',
    'report-exam-submissions.html': 'reports_exams'
  };

  const internalTab = mapping[tab] || tab;
  currentTab = internalTab;

  // Hide all tabs
  document
    .querySelectorAll(".admin-tab")
    .forEach((t) => (t.style.display = "none"));

  // Show target tab
  const tabEl = document.getElementById(`tab-${internalTab}`);
  if (tabEl) tabEl.style.display = "block";

  // Handle active class for sidebar
  document
    .querySelectorAll(".admin-nav-item")
    .forEach((i) => i.classList.remove("active"));

  const navItems = document.querySelectorAll(".admin-nav-item");
  navItems.forEach(item => {
    const onclickHeader = item.getAttribute('onclick');
    const href = item.getAttribute('href');
    const isSubItem = item.classList.contains('admin-sub-item');

    if ((onclickHeader && (onclickHeader.includes(`'${tab}'`) || onclickHeader.includes(`"${tab}"`))) ||
      (href && (href.includes(`/${tab}`) || href === tab))) {
      item.classList.add("active");

      // If it's a sub-item, make sure parent is also active (optional but good)
      if (isSubItem) {
        const parentMenu = document.querySelector('[onclick*="toggleReportsMenu"]');
        if (parentMenu) parentMenu.classList.add('active');
      }
    }
  });

  // Toggle sub-nav visibility
  const subNav = document.getElementById('sub-nav-reports');
  if (subNav) {
    if (tab === 'reports' || tab.startsWith('report-') || tab === 'submissions' || tab.startsWith('reports_')) {
      subNav.style.display = 'block';

      if (tab === 'submissions') {
        document.querySelectorAll('.admin-sub-item').forEach(i => i.classList.remove('active'));
        const subItem = document.getElementById('sub-item-submissions');
        if (subItem) subItem.classList.add('active');

        document.querySelectorAll('.admin-nav-item').forEach(i => {
          if (i.textContent.trim() === 'Báo cáo & Nhật ký') i.classList.add('active');
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
  let tab = parts[parts.length - 1];

  if (tab.endsWith('.html')) {
    tab = tab.replace('.html', '');
  }

  const validTabs = ["dashboard", "problems", "students", "reports", "exams", "submissions", "report-students", "report-problems", "report-exams", "report-exam-detail", "report-exam-submissions"];
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
  examReportView = view;

  // Ensure we are on the reports tab or a specific report page
  if (currentTab !== 'reports' && !currentTab.startsWith('report-') && currentTab !== 'reports_exams') {
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

  // Swap data for reports_exams if needed
  if (view === "exams" && state.originalExamsReportData) {
    state.reports_exams.data = state.originalExamsReportData;
    updateFilteredData("reports_exams");
  } else if (view === "students_exam" && state.reports_exams_flat) { // Custom view for drill-down in reports.html if needed
    state.reports_exams.data = state.reports_exams_flat;
    updateFilteredData("reports_exams");
  }

  renderTable(`reports_${view}`);
}

async function loadData() {
  if (currentTab === "dashboard") {
    const res = await fetch("/api/admin/stats");
    const stats = await res.json();

    const statProblems = document.getElementById("stat-problems");
    if (statProblems) statProblems.textContent = stats.problem_count;

    const statStudents = document.getElementById("stat-students");
    if (statStudents) statStudents.textContent = stats.student_count;

    const statHits = document.getElementById("stat-hits");
    if (statHits) statHits.textContent = stats.student_logins;

    if (document.getElementById("stat-exams"))
      document.getElementById("stat-exams").textContent = stats.exam_count;
    if (document.getElementById("stat-active-exams"))
      document.getElementById("stat-active-exams").textContent = stats.active_exam_count;
    if (document.getElementById("stat-exam-subs"))
      document.getElementById("stat-exam-subs").textContent = stats.exam_submission_count;

    const langContainer = document.getElementById("lang-stats");
    if (langContainer) {
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
    }

    const activityBody = document.getElementById("recent-activity-body");
    if (activityBody) {
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
    }

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
  } else if (currentTab.startsWith("report") || currentTab === "reports" || currentTab.includes("exam-")) {
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
        (item.username || "").toLowerCase().includes(query) ||
        (item.display_name || "").toLowerCase().includes(query) ||
        (item.class_name && item.class_name.toLowerCase().includes(query));
      return matchesSearch;
    } else if (tab === "reports_problems") {
      matchesSearch =
        (item.title || "").toLowerCase().includes(query) ||
        (item.id || "").toString().includes(query);

      const matchesDiff =
        s.filters.difficulty === "all" ||
        item.difficulty === s.filters.difficulty;
      return matchesSearch && matchesDiff;
    } else if (tab === "reports_exams") {
      if (examReportView === "exams") {
        matchesSearch = (item.title || "").toLowerCase().includes(query) || (item.id || "").toString().includes(query);
        return matchesSearch;
      } else {
        matchesSearch = (item.display_name || "").toLowerCase().includes(query) || (item.username || "").toLowerCase().includes(query);
        const matchesExam = selectedExamId === null || item.examId == selectedExamId;
        return matchesSearch && matchesExam;
      }
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

// Exam reports drill-down state is now derived from URL and page context
// examReportView, selectedExamId, allExamSubmissions are initialized at top or in pages

// Pagination instances registry
const paginationInstances = {};

function renderTable(tab) {
  const s = state[tab];
  if (!s) return;

  // Initialize pagination if not exists
  if (!paginationInstances[tab]) {
    paginationInstances[tab] = new PaginationHelper(`pagination-${tab}`, {
      pageSize: s.limit || 10,
      renderCallback: (pageData) => renderTableBody(tab, pageData),
      pageSizeOptions: [5, 10, 20, 50, 100],
      instanceName: `window.paginationInstances['${tab}']`
    });
    // Store instance globally if needed for debugging or external access
    if (!window.paginationInstances) window.paginationInstances = {};
    window.paginationInstances[tab] = paginationInstances[tab];
  }

  // Update data for pagination
  // Note: PaginationHelper.setData() will trigger render() which calls renderTableBody()
  // It also resets page to 1, which is desired behavior when data/filter changes.
  // However, if we are just re-rendering existing data (e.g. after sort), we might want to stay on current page?
  // Current admin.js implementation for sort didn't reset page. 
  // PaginationHelper.setData resets page to 1.
  // To preserve page on sort, we'd need to modify PaginationHelper or handle it here.
  // For now, let's allow reset to page 1 on sort/filter for simplicity and consistency with search.

  // Actually, wait. onSort calls updateFilteredData -> renderTable.
  // If we just sorted, we usually want to see the *same* page but sorted, OR reset to 1.
  // Most grids reset to 1 on sort to avoid confusion if items move out of current page. 
  // Let's stick to reset to 1.

  paginationInstances[tab].setData(s.filtered);
}

function renderTableBody(tab, pageData) {
  const s = state[tab];
  const body = document.getElementById(`${tab}-body`);
  if (!body) return;

  // No longer need to slice data, pageData is already sliced
  // const start = (s.page - 1) * s.limit;
  // const end = start + s.limit;
  // const pageData = s.filtered.slice(start, end);

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
    updateSortUI(tab);
  } else if (tab === "reports_exams") {
    const head = document.getElementById("reports_exams-head");

    if (examReportView === "exams") {
      if (head) {
        head.innerHTML = `
              <tr>
                  <th class="px-4 py-3 border-secondary">Kỳ thi</th>
                  <th class="px-4 py-3 border-secondary text-center">Số SV tham gia</th>
                  <th class="px-4 py-3 border-secondary text-center">Số bài tập</th>
                  <th class="px-4 py-3 border-secondary text-center">Tổng điểm tối đa</th>
                  <th class="px-4 py-3 border-secondary text-end">Hành động</th>
              </tr>
          `;
      }

      body.innerHTML = pageData.map(ex => `
            <tr>
                <td><div class="fw-bold">${ex.title}</div><div class="text-muted small">ID: ${ex.id}</div></td>
                <td class="text-center">${ex.student_count}</td>
                <td class="text-center">${ex.problem_count}</td>
                <td class="text-center">${ex.total_points}</td>
                <td class="text-end">
                    <button class="secondary-btn" onclick="window.location.href='/admin/report-exam-detail.html?eid=${ex.id}'">Xem chi tiết</button>
                </td>
            </tr>
        `).join("") || '<tr><td colspan="5" class="text-center">Chưa có kỳ thi nào</td></tr>';
      updateSortUI(tab);
    } else if (examReportView === "students") {
      const titleEl = document.getElementById("exam-title-breadcrumb");
      const ex = state.originalExamsReportData.find(e => e.id == selectedExamId);
      if (ex && titleEl) {
        titleEl.textContent = ex.title;
        const h2 = document.getElementById("exam-detail-title");
        if (h2) h2.textContent = "Kết quả thi: " + ex.title;
      }

      if (head) {
        head.innerHTML = `
              <tr>
                  <th class="px-4 py-3 border-secondary">Sinh viên</th>
                  <th class="px-4 py-3 border-secondary text-center">Số bài giải</th>
                  <th class="px-4 py-3 border-secondary text-center">Tổng điểm</th>
                  <th class="px-4 py-3 border-secondary">Tiến độ</th>
                  <th class="px-4 py-3 border-secondary text-end">Bài nộp</th>
              </tr>
          `;
      }

      body.innerHTML = pageData.map(r => {
        const percent = r.total_possible > 0 ? (r.score / r.total_possible) * 100 : 0;
        return `
                <tr>
                    <td><div class="fw-bold">${r.display_name}</div><div class="text-muted small">@${r.username} | ${r.class_name}</div></td>
                    <td class="text-center">${r.solved_count} / ${r.problem_count}</td>
                    <td class="text-center"><span class="status-badge" style="background:rgba(88,166,255,0.1);color:var(--accent);font-weight:bold">${r.score}</span> / ${r.total_possible}</td>
                    <td>
                        <div style="display:flex; align-items:center; gap:10px">
                            <div class="progress-bg" style="flex:1; height:6px"><div class="progress-fill" style="width:${percent}%"></div></div>
                            <span class="small">${percent.toFixed(0)}%</span>
                        </div>
                    </td>
                    <td class="text-end">
                        <button class="secondary-btn" onclick="window.location.href='/admin/report-exam-submissions.html?eid=${selectedExamId}&user=${r.username}'">Xem bài</button>
                    </td>
                </tr>
            `;
      }).join("") || '<tr><td colspan="5" class="text-center">Chưa có sinh viên tham gia</td></tr>';
      updateSortUI(tab);
    }
  }
}

function showExamList() {
  examReportView = "exams";
  selectedExamId = null;
  updateFilteredData("reports_exams");
  renderTable("reports_exams");
}

async function viewExamStudents(eid) {
  window.location.href = `/admin/report-exam-detail.html?eid=${eid}`;
}

async function loadExamSubmissions(eid, username) {
  const list = document.getElementById("submissions-list");
  const breadcrumb = document.getElementById("student-name-breadcrumb");
  const headerTitle = document.getElementById("student-submissions-title");

  try {
    const res = await fetch(`/api/admin/exams/${eid}/submissions`);
    allExamSubmissions = await res.json();
    const studentSubs = allExamSubmissions.filter(s => s.username === username);

    if (breadcrumb) breadcrumb.textContent = "Bài nộp: " + username;
    if (headerTitle) headerTitle.textContent = "Bài nộp của " + username;

    if (studentSubs.length === 0) {
      list.innerHTML = '<div class="p-4 text-center text-muted">Sinh viên này chưa nộp bài nào.</div>';
      return;
    }

    let html = "";
    const problems = {};
    studentSubs.forEach(s => {
      if (!problems[s.problemId]) problems[s.problemId] = [];
      problems[s.problemId].push(s);
    });

    for (const pid in problems) {
      const subs = problems[pid];
      const latest = subs[subs.length - 1];
      html += `
                <div class="list-group-item bg-dark text-white border-secondary p-4">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <div>
                            <h5 class="mb-1">${latest.problemTitle}</h5>
                            <span class="badge bg-secondary">${latest.language}</span>
                            <span class="small text-muted ms-2">${latest.timestamp}</span>
                        </div>
                        <span class="status-badge ${latest.allPassed ? 'badge-success' : 'badge-danger'}">
                            ${latest.allPassed ? 'Đạt' : 'Chưa đạt'}
                        </span>
                    </div>
                    <div class="d-flex gap-2">
                        <button class="btn btn-sm btn-outline-accent" onclick="showSpecificCode(${allExamSubmissions.indexOf(latest)})">Xem mã nguồn</button>
                        ${subs.length > 1 ? `<small class="text-muted align-self-center">Có ${subs.length} lần nộp</small>` : ''}
                    </div>
                </div>
            `;
    }
    list.innerHTML = html;

    // Update the "Chi tiết kỳ thi" breadcrumb link title if possible
    const ex = state.originalExamsReportData.find(e => e.id == eid);
    if (ex) {
      const link = document.getElementById("exam-detail-link");
      if (link) link.textContent = "Kỳ thi: " + ex.title;
    }
  } catch (e) {
    console.error("Failed to load submissions:", e);
    if (list) list.innerHTML = '<div class="p-4 text-center text-danger">Lỗi khi tải bài nộp.</div>';
  }
}


function showSpecificCode(index) {
  const s = allExamSubmissions[index];
  const modalBody = document.querySelector("#codeModal .modal-body");

  modalBody.innerHTML = `
         <div class="p-3 border-bottom border-secondary bg-dark">
            <div class="row">
               <div class="col-md-6">
                  <div class="small text-muted">Sinh viên</div>
                  <div class="fw-bold">${s.username}</div>
               </div>
               <div class="col-md-6 text-md-end">
                  <div class="small text-muted">Bài tập</div>
                  <div class="fw-bold">${s.problemTitle} (${s.language})</div>
               </div>
            </div>
         </div>
         <pre id="code-display" class="m-0 p-3" style="max-height: 600px; overflow-y: auto; font-family: 'Fira Code', monospace; font-size: 0.9rem; background: #0d1117;">${document.createTextNode(s.code || "// Không có mã nguồn").wholeText}</pre>
    `;

  document.getElementById("code-timestamp").textContent = "Nộp lúc: " + s.timestamp;
}

// Old manual pagination functions removed
// function renderPagination(tab) { ... }
// function changePage(tab, page) { ... }

function onSearch(tab) {
  state[tab].search = document.getElementById(`search-${tab}`).value;
  // Page reset is handled by setData() in renderTable
  updateFilteredData(tab);
  renderTable(tab);
}

// ... rest of file


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
// examReportView is usually managed by individual pages

function toggleReportView(view) {
  switchReport(view);
}

async function loadReports() {
  try {
    const res = await fetch(`/api/admin/reports?t=${Date.now()}`);
    const data = await res.json();
    console.log("Reports data loaded:", data);

    // Assign ranks to students
    const students = data.students || [];
    students.forEach((s, i) => (s.rank = i + 1));

    state.reports_students.data = students;
    state.reports_problems.data = data.problems || [];
    state.originalExamsReportData = data.exams || [];
    console.log("Original Exams Report Data:", state.originalExamsReportData);

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
    state.reports_exams_flat = flatExamReports;

    // Assign data to active tab state based on view
    if (examReportView === "exams") {
      state.reports_exams.data = state.originalExamsReportData;
    } else {
      state.reports_exams.data = state.reports_exams_flat;
    }

    updateFilteredData("reports_students");
    updateFilteredData("reports_problems");
    updateFilteredData("reports_exams");

    if (currentTab === "reports_exams" || currentTab.includes("exam-")) {
      if (examReportView === "submissions") {
        loadExamSubmissions(selectedExamId, selectedUsername);
      } else {
        renderTable("reports_exams");
      }
    } else {
      renderTable(currentTab);
    }
  } catch (e) {
    console.error("CRITICAL error in loadReports:", e);
    const body = document.getElementById(`${currentTab}-body`) || document.getElementById("reports_exams-body");
    if (body) body.innerHTML = `<tr><td colspan="5" class="text-center text-danger">Lỗi tải dữ liệu: ${e.message}</td></tr>`;
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
