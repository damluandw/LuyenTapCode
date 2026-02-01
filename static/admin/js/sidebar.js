function injectSidebar() {
    const sidebar = document.querySelector('.admin-sidebar');
    if (!sidebar) return;

    const path = window.location.pathname;
    
    sidebar.innerHTML = `
        <div class="logo" style="margin-bottom: 2rem">
          Admin<span>Panel</span>
        </div>
        <a href="/admin/dashboard" class="admin-nav-link ${path === '/admin' || path === '/admin/dashboard' ? 'active' : ''}">
          <div class="admin-nav-item">Thống kê chung</div>
        </a>
        <a href="/admin/problems" class="admin-nav-link ${path === '/admin/problems' ? 'active' : ''}">
          <div class="admin-nav-item">Quản lý bài tập</div>
        </a>
        <a href="/admin/students" class="admin-nav-link ${path === '/admin/students' ? 'active' : ''}">
          <div class="admin-nav-item">Sinh viên</div>
        </a>
        
        <div class="admin-nav-item ${path.includes('/reports') || path.includes('/submissions') ? 'active' : ''}" onclick="toggleReportsMenu(event)">Báo cáo</div>
        <div id="sub-nav-reports" class="admin-sub-nav" style="display: ${path.includes('/reports') || path.includes('/submissions') ? 'block' : 'none'}">
          <a href="/admin/reports?t=students" class="admin-sub-item ${path.includes('/reports') && window.location.search.includes('t=students') ? 'active' : ''}">
            Bảng xếp hạng SV
          </a>
          <a href="/admin/reports?t=problems" class="admin-sub-item ${path.includes('/reports') && window.location.search.includes('t=problems') ? 'active' : ''}">
            Thống kê bài tập
          </a>
          <a href="/admin/reports?t=exams" class="admin-sub-item ${path.includes('/reports') && window.location.search.includes('t=exams') ? 'active' : ''}">
            Lịch sử thi
          </a>
          <a href="/admin/submissions" class="admin-sub-item ${path === '/admin/submissions' ? 'active' : ''}">
            Nhật ký nộp bài
          </a>
        </div>
        
        <a href="/admin/exams" class="admin-nav-link ${path === '/admin/exams' ? 'active' : ''}">
          <div class="admin-nav-item">Kỳ thi</div>
        </a>
        
        <div style="margin-top: auto; padding-top: 2rem; border-top: 1px solid #30363d;">
          <a href="/api/auth/logout" style="text-decoration: none; color: #ff7b72; font-size: 0.9rem">Đăng xuất</a>
        </div>
    `;
}

function toggleReportsMenu(e) {
    const subNav = document.getElementById('sub-nav-reports');
    if (subNav) {
        subNav.style.display = subNav.style.display === 'none' ? 'block' : 'none';
    }
}

document.addEventListener('DOMContentLoaded', injectSidebar);
