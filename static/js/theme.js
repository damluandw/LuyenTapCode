/**
 * Theme Toggle - Dark / Light Mode
 * Shared across all pages. Saved to localStorage.
 */

(function () {
  var saved = localStorage.getItem('theme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
})();

function initThemeIcon() {
  var btn = document.getElementById('theme-toggle-btn');
  var icon = document.getElementById('theme-icon');
  var theme = document.documentElement.getAttribute('data-theme');
  
  if (icon) {
    if (theme === 'light') {
      icon.className = 'bi bi-moon-fill';
      if (btn) btn.title = 'Chuyển giao diện tối';
    } else {
      icon.className = 'bi bi-sun-fill';
      if (btn) btn.title = 'Chuyển giao diện sáng';
    }
  }

  // Notify other components (Monaco, Xterm)
  window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme: theme } }));
}

function toggleTheme() {
  var current = document.documentElement.getAttribute('data-theme');
  var next = current === 'light' ? 'dark' : 'light';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
  initThemeIcon();
}

document.addEventListener('DOMContentLoaded', initThemeIcon);
