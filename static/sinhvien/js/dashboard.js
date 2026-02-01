async function initDashboard() {
    try {
        // Fetch user info
        const userRes = await fetch('/api/auth/me');
        if (!userRes.ok) {
            window.location.href = '/login';
            return;
        }
        const userData = await userRes.json();
        document.getElementById('user-display').textContent = userData.display_name;
        document.getElementById('welcome-msg').textContent = `Chào mừng trở lại, ${userData.display_name}!`;

        // Fetch stats
        const statsRes = await fetch('/api/student/stats');
        const stats = await statsRes.json();

        // Update stats cards
        document.getElementById('stat-solved').textContent = `${stats.solved_count}/${stats.total_problems}`;
        document.getElementById('stat-subs').textContent = stats.submission_count;
        document.getElementById('stat-rank').textContent = `#${stats.rank}`;
        document.getElementById('stat-rate').textContent = `${stats.success_rate}%`;

        // Render recent activity
        const activityList = document.getElementById('activity-list');
        activityList.innerHTML = stats.recent_activity.map(act => `
            <div class="activity-item">
                <div class="activity-info">
                    <h4>${act.problemTitle}</h4>
                    <span>${act.timestamp} • Ngôn ngữ: ${act.language.toUpperCase()}</span>
                </div>
                <div class="status-pill success">PASS</div>
            </div>
        `).join('') || '<p style="text-align: center; color: var(--text-secondary); margin-top: 20px;">Chưa có hoạt động nào gần đây.</p>';

    } catch (e) {
        console.error("Dashboard error:", e);
    }
}

document.addEventListener('DOMContentLoaded', initDashboard);
