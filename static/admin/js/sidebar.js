function injectSidebar() {
    const sidebar = document.querySelector('.admin-sidebar');
    if (!sidebar) return;

    const path = window.location.pathname;
    const search = window.location.search;

    sidebar.innerHTML = `
        <div class="sidebar-header p-4 border-bottom border-secondary border-opacity-25 mb-3">
            <h1 class="h5 fw-bold text-white mb-0">
                <i class="bi bi-shield-lock me-2 text-primary"></i>Admin<span class="text-primary text-opacity-75">Panel</span>
            </h1>
        </div>
        
        <div class="px-3 overflow-y-auto">
            <a href="/admin" class="admin-nav-item ${path === '/admin' || path === '/admin/dashboard' ? 'active' : ''}">
                <i class="bi bi-speedometer2"></i> Thống kê chung
            </a>
            
            <a href="/admin/problems" class="admin-nav-item ${path === '/admin/problems' ? 'active' : ''}">
                <i class="bi bi-code-square"></i> Quản lý bài tập
            </a>
            
            <a href="/admin/students" class="admin-nav-item ${path === '/admin/students' ? 'active' : ''}">
                <i class="bi bi-people"></i> Quản lý sinh viên
            </a>
            
            <div class="admin-nav-item ${path.includes('/reports') || path.includes('/submissions') ? 'active' : ''}" style="cursor: pointer" onclick="toggleReportsMenu(event)">
                <i class="bi bi-file-earmark-bar-graph"></i> Báo cáo & Nhật ký
                <i class="bi bi-chevron-down ms-auto small transition-transform" id="reports-chevron"></i>
            </div>
            
            <div id="sub-nav-reports" class="admin-sub-nav" style="display: ${path.includes('/report') || path.includes('/submissions') ? 'block' : 'none'}">
                <a href="/admin/report-students.html" class="admin-sub-item ${path.includes('report-students') ? 'active' : ''}">
                    Bảng xếp hạng SV
                </a>
                <a href="/admin/report-problems.html" class="admin-sub-item ${path.includes('report-problems') ? 'active' : ''}">
                    Thống kê bài tập
                </a>
                <a href="/admin/report-exams.html" class="admin-sub-item ${path.includes('report-exam') ? 'active' : ''}">
                    Lịch sử thi
                </a>
                <a href="/admin/submissions" class="admin-sub-item ${path === '/admin/submissions' ? 'active' : ''}">
                    Nhật ký nộp bài
                </a>
            </div>
            
            <a href="/admin/exams" class="admin-nav-item ${path === '/admin/exams' || path.includes('create-exam') ? 'active' : ''}">
                <i class="bi bi-journal-text"></i> Quản lý kỳ thi
            </a>
        </div>
        
        <div class="mt-auto p-3 border-top border-secondary border-opacity-25">
            <a href="/" class="admin-nav-item text-muted">
                <i class="bi bi-arrow-left-circle"></i> Về trang Student
            </a>
            <a href="/api/auth/logout" class="admin-nav-item text-danger">
                <i class="bi bi-box-arrow-right"></i> Đăng xuất
            </a>
        </div>
    `;

    // Rotate chevron if menu is open
    if (path.includes('/reports') || path.includes('/submissions')) {
        const chev = document.getElementById('reports-chevron');
        if (chev) chev.style.transform = 'rotate(180deg)';
    }
}

function toggleReportsMenu(e) {
    const subNav = document.getElementById('sub-nav-reports');
    const chev = document.getElementById('reports-chevron');
    if (subNav) {
        const isOpen = subNav.style.display !== 'none';
        subNav.style.display = isOpen ? 'none' : 'block';
        if (chev) {
            chev.style.transform = isOpen ? 'rotate(0deg)' : 'rotate(180deg)';
        }
    }
}

document.addEventListener('DOMContentLoaded', injectSidebar);
