function injectSidebar() {
    const sidebar = document.querySelector('.admin-sidebar');
    if (!sidebar) return;

    const path = window.location.pathname;
    const isReports = path.includes('/report') || path.includes('/submissions');

    sidebar.innerHTML = `
        <a href="/admin" class="sidebar-brand">
            <h1 class="h5 fw-bold mb-0">
                <i class="bi bi-shield-lock me-2 text-primary"></i>Admin<span style="color: var(--accent)">Panel</span>
            </h1>
        </a>
        
        <div class="sidebar-navigation">
            <div class="nav-header">Dashboard</div>
            <a href="/admin" class="nav-item ${path === '/admin' || path === '/admin/dashboard' ? 'active' : ''}">
                <i class="bi bi-speedometer2"></i>
                <span>Thống kê chung</span>
            </a>
            
            <div class="nav-header">Management</div>
            <a href="/admin/problems" class="nav-item ${path === '/admin/problems' ? 'active' : ''}">
                <i class="bi bi-code-square"></i>
                <span>Quản lý bài tập</span>
            </a>
            
            <a href="/admin/students" class="nav-item ${path === '/admin/students' ? 'active' : ''}">
                <i class="bi bi-people"></i>
                <span>Quản lý sinh viên</span>
            </a>

            <a href="/admin/exams" class="nav-item ${path === '/admin/exams' || path.includes('create-exam') ? 'active' : ''}">
                <i class="bi bi-journal-text"></i>
                <span>Quản lý kỳ thi</span>
            </a>

            <a href="/admin/users.html" class="nav-item ${path.includes('/admin/users') ? 'active' : ''}">
                <i class="bi bi-person-workspace"></i>
                <span>Quản lý người dùng</span>
            </a>

            <div class="nav-header">Reports & Logs</div>
            <div class="nav-item ${isReports ? 'active' : ''}" style="cursor: pointer" onclick="toggleTreeview('reports-menu', event)">
                <i class="bi bi-file-earmark-bar-graph"></i>
                <span>Báo cáo & Nhật ký</span>
                <i class="bi bi-chevron-left nav-chevron" id="reports-chevron" style="transform: ${isReports ? 'rotate(-90deg)' : 'rotate(0deg)'}"></i>
            </div>
            
            <div id="reports-menu" class="nav-treeview ${isReports ? 'show' : ''}">
                <a href="/admin/report-students.html" class="nav-item nav-link-sub ${path.includes('report-students') ? 'active' : ''}">
                    <i class="bi bi-circle"></i> Bảng xếp hạng SV
                </a>
                <a href="/admin/report-problems.html" class="nav-item nav-link-sub ${path.includes('report-problems') ? 'active' : ''}">
                    <i class="bi bi-circle"></i> Thống kê bài tập
                </a>
                <a href="/admin/report-exams.html" class="nav-item nav-link-sub ${path.includes('report-exam') ? 'active' : ''}">
                    <i class="bi bi-circle"></i> Lịch sử thi
                </a>
                <a href="/admin/submissions" class="nav-item nav-link-sub ${path === '/admin/submissions' ? 'active' : ''}">
                    <i class="bi bi-circle"></i> Nhật ký nộp bài
                </a>
            </div>

            <div class="sidebar-divider"></div>
            
            <div class="nav-header">Security</div>
            <a href="/admin/roles" class="nav-item ${path === '/admin/roles' ? 'active' : ''}">
                <i class="bi bi-shield-check"></i>
                <span>Quản lý vai trò</span>
            </a>
            
            <a href="/admin/user-permissions" class="nav-item ${path === '/admin/user-permissions' ? 'active' : ''}">
                <i class="bi bi-person-gear"></i>
                <span>Phân quyền</span>
            </a>

            <div class="sidebar-divider"></div>
            
            <div class="nav-header">System</div>
            <a href="/profile" class="nav-item ${path === '/profile' ? 'active' : ''}">
                <i class="bi bi-person-circle"></i>
                <span>Hồ sơ cá nhân</span>
            </a>
            <a href="/" class="nav-item">
                <i class="bi bi-arrow-left-circle"></i>
                <span>Về trang Sinh viên</span>
            </a>
            <a href="/api/auth/logout" class="nav-item text-danger">
                <i class="bi bi-box-arrow-right"></i>
                <span>Đăng xuất</span>
            </a>

            <div class="sidebar-divider"></div>

            <div class="px-2 py-2">
                <button onclick="toggleTheme()" id="theme-toggle-btn"
                    class="nav-item w-100 border-0 text-start"
                    style="cursor:pointer; background:none;">
                    <i class="bi bi-sun-fill" id="theme-icon"></i>
                    <span id="theme-label">Giao diện sáng</span>
                </button>
            </div>
        </div>
    `;

    // sync label after sidebar inject
    (function syncThemeLabel() {
        var theme = document.documentElement.getAttribute('data-theme');
        var label = document.getElementById('theme-label');
        var icon = document.getElementById('theme-icon');
        if (label) label.textContent = theme === 'light' ? 'Giao diện tối' : 'Giao diện sáng';
        if (icon) icon.className = theme === 'light' ? 'bi bi-moon-fill' : 'bi bi-sun-fill';
    })();
}

function toggleTreeview(menuId, event) {
    const menu = document.getElementById(menuId);
    const chevron = event.currentTarget.querySelector('.nav-chevron');

    if (menu) {
        const isShowing = menu.classList.contains('show');
        if (isShowing) {
            menu.classList.remove('show');
            if (chevron) chevron.style.transform = 'rotate(0deg)';
        } else {
            menu.classList.add('show');
            if (chevron) chevron.style.transform = 'rotate(-90deg)';
        }
    }
}

document.addEventListener('DOMContentLoaded', injectSidebar);
