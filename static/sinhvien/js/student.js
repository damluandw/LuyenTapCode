let editor;
let problems = [];
let currentProblem = null;
let terminal;
let socket;

// Monaco Loading
require.config({
  paths: {
    vs: "https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.44.0/min/vs",
  },
});

require(["vs/editor/editor.main"], async function () {
  if (document.fonts) {
    await document.fonts.ready;
  }

  editor = monaco.editor.create(document.getElementById("editor-container"), {
    value: "",
    language: "python",
    theme: "vs-dark",
    fontSize: 16,
    fontFamily: "'Fira Code', monospace",
    fontLigatures: true,
    automaticLayout: true,
    minimap: { enabled: false },
    padding: { top: 10, bottom: 10 },
    roundedSelection: true,
    scrollBeyondLastLine: false,
    lineNumbers: "on",
    renderLineHighlight: "all",
    suggestOnTriggerCharacters: true,
    quickSuggestions: { other: true, comments: false, strings: true },
    acceptSuggestionOnEnter: "on",
    tabCompletion: "on",
    wordBasedSuggestions: "all",
  });

  window.addEventListener("resize", () => editor.layout());
  setTimeout(() => editor.layout(), 100);

  // Initialize Socket.IO - connect to same server as webpage
  // If io is not defined, it might be because Monaco's loader (AMD) intercepted it
  if (typeof io === 'undefined' && typeof require === 'function' && require.defined && require.defined('io')) {
    io = require('io');
  }

  // Final check for io
  if (typeof io === 'undefined') {
    console.error('Socket.IO (io) is still not defined. Trying to recover...');
    // If it's still missing, it's a critical error for terminal functionality
  }

  socket = io({
    transports: ['websocket', 'polling']
  });

  socket.on('connect', () => {
    console.log('Connected to server');
    const orb = document.getElementById('connection-status');
    if (orb) {
      orb.className = 'status-orb connected';
      orb.title = 'Đã kết nối';
    }
  });

  socket.on('connect_error', (error) => {
    console.error('Connection error:', error);
    const orb = document.getElementById('connection-status');
    if (orb) {
      orb.className = 'status-orb disconnected';
      orb.title = 'Lỗi kết nối: ' + error.message;
    }
  });

  socket.on('disconnect', () => {
    console.log('Disconnected from server');
    const orb = document.getElementById('connection-status');
    if (orb) {
      orb.className = 'status-orb disconnected';
      orb.title = 'Đã mất kết nối';
    }
  });

  terminal = new Terminal();
  fetchProblems();
  checkUser();
  setupTabs();
  setupEventListeners();

  // Add filter/search listeners
  const filterEl = document.getElementById('level-filter');
  if (filterEl) {
    filterEl.addEventListener('change', () => renderProblems());
  }
  const diffEl = document.getElementById('difficulty-filter');
  if (diffEl) {
    diffEl.addEventListener('change', () => renderProblems());
  }
  const searchEl = document.getElementById('problem-search');
  if (searchEl) {
    searchEl.addEventListener('input', () => renderProblems());
  }

  // Mobile Sidebar Toggle
  const mobileToggle = document.getElementById('mobile-sidebar-toggle');
  const mobileOverlay = document.getElementById('mobile-overlay');
  const sidebar = document.getElementById('sidebar');

  if (mobileToggle) {
    mobileToggle.addEventListener('click', () => {
      sidebar.classList.toggle('mobile-show');
      mobileOverlay.classList.toggle('active');
    });
  }

  if (mobileOverlay) {
    mobileOverlay.addEventListener('click', () => {
      sidebar.classList.remove('mobile-show');
      mobileOverlay.classList.remove('active');
    });
  }

  // Desktop Sidebar Toggle
  const deskToggle = document.getElementById('sidebar-toggle');
  const toggleIcon = document.getElementById('toggle-icon');

  if (deskToggle) {
    deskToggle.addEventListener('click', () => {
      sidebar.classList.toggle('collapsed');
      if (sidebar.classList.contains('collapsed')) {
        toggleIcon.classList.replace('bi-chevron-left', 'bi-chevron-right');
      } else {
        toggleIcon.classList.replace('bi-chevron-right', 'bi-chevron-left');
      }

      // Trigger editor layout recalculation
      if (editor) {
        setTimeout(() => editor.layout(), 300); // Wait for CSS transition
      }
    });
  }
});

// Sidebar & Problem Loading
// Auth
async function checkUser() {
  try {
    const res = await fetch('/api/auth/me');
    if (!res.ok) {
      window.location.href = '/login';
      return;
    }
    const data = await res.json();
    const nameEl = document.getElementById('user-name');
    const navDisplayEl = document.getElementById('nav-user-display');
    if (nameEl) nameEl.textContent = data.display_name;
    if (navDisplayEl) navDisplayEl.textContent = data.display_name;
  } catch (e) {
    window.location.href = '/login';
  }
}

let allProblems = []; // Store basic problem list

async function fetchProblems() {
  try {
    const res = await fetch("/problems");
    allProblems = await res.json();
    renderProblems();

    // Select first problem if available
    if (allProblems.length > 0) {
      loadProblemDetail(allProblems[0].id);
    }
  } catch (err) {
    console.error("Failed to load problems:", err);
  }
}

function renderProblems() {
  const filterCategory = document.getElementById('level-filter').value;
  const filterDifficulty = document.getElementById('difficulty-filter').value;
  const searchQuery = document.getElementById('problem-search').value.toLowerCase();

  const listContainer = document.getElementById("problem-list");
  listContainer.innerHTML = "";

  const filtered = allProblems.filter(p => {
    // Level filter
    const matchesLevel = filterCategory === "all" ||
      (p.category && p.category.startsWith(filterCategory));

    // Difficulty filter
    const matchesDifficulty = filterDifficulty === "all" || p.difficulty === filterDifficulty;

    // Search filter
    const matchesSearch = p.title.toLowerCase().includes(searchQuery) ||
      p.id.toString().includes(searchQuery);

    return matchesLevel && matchesDifficulty && matchesSearch;
  });

  filtered.forEach((p) => {
    const item = document.createElement("div");
    item.className = `problem-item ${currentProblem && currentProblem.id === p.id ? "active" : ""} ${p.solved ? "solved" : ""}`;
    item.dataset.id = p.id;
    item.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: start;">
            <div class="p-title">${p.title}</div>
            ${p.solved ? '<div class="solved-icon" title="Đã thực hành">✅</div>' : ''}
        </div>
        <div class="p-diff" style="font-size: 0.7rem; color: #8b949e">${p.difficulty}</div>
    `;
    item.addEventListener("click", () => {
      document.querySelectorAll(".problem-item").forEach((el) => el.classList.remove("active"));
      item.classList.add("active");
      loadProblemDetail(p.id);
    });
    listContainer.appendChild(item);
  });
}

async function loadProblemDetail(id) {
  try {
    // Close mobile sidebar on selection
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('mobile-overlay');
    if (window.innerWidth < 992) {
      if (sidebar) sidebar.classList.remove('mobile-show');
      if (overlay) overlay.classList.remove('active');
    }

    const res = await fetch(`/api/problems/${id}`);
    const p = await res.json();
    setProblem(p);
  } catch (err) {
    console.error("Error loading problem detail:", err);
  }
}

function setProblem(p) {
  currentProblem = p;
  document.getElementById("current-problem-title").textContent = p.title;

  const descEl = document.getElementById("problem-desc");

  // Robustly handle marked being potentially intercepted by Monaco's AMD loader
  let markedObj;
  if (typeof window.marked !== 'undefined') {
    markedObj = window.marked;
  } else if (typeof require === 'function' && require.defined && require.defined('marked')) {
    markedObj = require('marked');
  }

  if (markedObj) {
    if (markedObj.setOptions) {
      markedObj.setOptions({
        breaks: true,
        gfm: true,
        headerIds: false,
        mangle: false
      });
    }
    const htmlContent = markedObj.parse ? markedObj.parse(p.description) : markedObj(p.description);
    descEl.innerHTML = htmlContent;
  } else {
    // Better fallback if marked is totally unavailable
    descEl.innerHTML = p.description
      .replace(/### (.*)/g, '<h3 class="fallback-h3">$1</h3>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/\n\n/g, '<p></p>')
      .replace(/\n/g, '');
  }

  document.getElementById("current-difficulty").textContent = p.difficulty;
  if (editor) {
    // Default to empty or specific comment
    let startCode = "";
    if (p.starter_code && p.starter_code[document.getElementById("language-select").value]) {
      startCode = p.starter_code[document.getElementById("language-select").value];
    }
    editor.setValue(startCode);
  }
  switchTab("desc");

  const lang = document.getElementById("language-select").value;
  updateEditorLanguage(lang);
  updateHintTab(p, lang);
}

function updateHintTab(p, lang) {
  const hintEl = document.getElementById("problem-hint");
  if (!p) {
    hintEl.innerHTML = "Chọn bài tập để xem gợi ý.";
    return;
  }

  // Syntax tips
  const syntaxTips = {
    c: "<strong>Cú pháp C:</strong> <code>printf()</code>, <code>scanf()</code>",
    cpp: "<strong>Cú pháp C++:</strong> <code>cout <<</code>, <code>cin >></code>",
    java: "<strong>Cú pháp Java:</strong> <code>System.out.println()</code>",
    csharp: "<strong>Cú pháp C#:</strong> <code>Console.WriteLine()</code>"
  };

  let hintText = p.hint;
  if (p.language_hints && p.language_hints[lang]) hintText = p.language_hints[lang];

  let hintHtml = typeof marked !== 'undefined' ? marked.parse(hintText || "Không có gợi ý.") : (hintText || "Không có gợi ý.");
  hintHtml = `<div class="syntax-tip" style="margin-bottom: 15px; padding: 10px; background: rgba(88, 166, 255, 0.1); border-radius: 6px; font-size: 0.9rem; border: 1px solid rgba(88, 166, 255, 0.2);">${syntaxTips[lang] || ""}</div>` + hintHtml;

  // Use SOLUTION CODE for hints if available, otherwise template
  const codeToShow = (p.solution_code && p.solution_code[lang]) ? p.solution_code[lang] : (p.starter_code && p.starter_code[lang] ? p.starter_code[lang] : "");

  if (codeToShow) {
    hintHtml += `<br><strong>Bài giải mẫu (${lang}):</strong>
    <div style="position: relative;">
        <pre class="console-box" style="margin-top: 10px; background: #1c2128; border: 1px solid #30363d; padding: 10px; border-radius: 4px; font-family: 'Fira Code', monospace; font-size: 0.85rem; user-select: text;">${escapeHtml(codeToShow)}</pre>
        <button id="use-sample-btn" style="margin-top: 5px; padding: 5px 10px; background: #238636; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 0.8rem;">Sử dụng code này</button>
    </div>`;
  }
  hintEl.innerHTML = hintHtml;

  if (document.getElementById("use-sample-btn")) {
    document.getElementById("use-sample-btn").addEventListener("click", () => {
      if (editor) {
        editor.setValue(codeToShow);
        // Switch back to code tab if needed, but current layout shows editor always.
        // If there's a specific 'code' tab processing (like hiding/showing), we might need it.
        // But standard layout usually has Editor always visible or in a split. 
        // Assuming this app layout has tabs for "Description/Hint/Result" separate from Editor? 
        // Looking at index.html, yes, tabs control the right panel (Desc/Hint). Editor is Left (or center)?
        // Wait, index.html structure: Sidebar (Left) - Main (Editor + Terminal) - Right Panel (Desc/Hint)?
        // Let's check tab names. "console" is a tab. "desc", "hint", "results".
        // So Editor is always visible? No, let's assume it updates the editor content is enough.
        // User sees code change immediately.
      }
    });
  }
}



function setupEventListeners() {
  document.getElementById("language-select").addEventListener("change", (e) => {
    const lang = e.target.value;
    updateEditorLanguage(lang);
    if (currentProblem) updateHintTab(currentProblem, lang);
  });

  document.getElementById("run-btn").addEventListener("click", handleRunClick);
  document.getElementById("console-run-btn").addEventListener("click", handleConsoleRunClick);

  // Add listener for test results
  socket.on('test_results', (data) => {
    const btn = document.getElementById("run-btn");
    btn.disabled = false;
    btn.innerHTML = '<i class="bi bi-lightning-fill"></i> Kiểm tra';

    const resultsPanel = document.getElementById("tab-results");
    if (!resultsPanel) return;

    if (data.error) {
      resultsPanel.innerHTML = `<div class="p-3 w-100"><div class="result-card failed"><div style="color: #f85149; font-weight: bold; margin-bottom: 5px;">Lỗi thực thi:</div><pre style="white-space: pre-wrap; margin: 0; font-family: 'Fira Code', monospace; font-size: 0.85rem; color: #f85149;">${escapeHtml(data.error)}</pre></div></div>`;
      return;
    }

    if (data.results) {
      renderResults(data.results);
    }
  });

  socket.on('session_started', () => {
    const btn = document.getElementById("console-run-btn");
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<i class="bi bi-play"></i> Console';
    }
  });
}

function escapeHtml(text) {
  if (!text) return "";
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

async function handleConsoleRunClick() {
  const btn = document.getElementById("console-run-btn");

  if (!currentProblem) return;

  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Khởi động...';

  switchTab('console');
  if (terminal) {
    await terminal.startSession(editor.getValue());
  }
}

async function handleRunClick() {
  const btn = document.getElementById("run-btn");
  const resultsPanel = document.getElementById("tab-results");

  if (!currentProblem) return;

  // Stop any active console session first
  if (terminal && terminal.isSessionActive) {
    socket.emit('stop_session');
    terminal.isSessionActive = false;
  }

  btn.disabled = true;
  const originalHtml = btn.innerHTML;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Đang kiểm tra...';

  switchTab("results");
  resultsPanel.innerHTML = '<div class="p-4 w-100 text-center text-muted">Đang thực thi các test case... <div class="spinner-border spinner-border-sm ms-2" role="status"></div></div>';

  const code = editor.getValue();
  const language = document.getElementById('language-select').value;
  const testCases = currentProblem.test_cases || [];

  socket.emit('run_test_cases', {
    language: language,
    code: code,
    test_cases: testCases
  });

  // Safety timeout
  setTimeout(() => {
    if (btn.textContent === "Đang kiểm tra...") {
      btn.disabled = false;
      btn.textContent = "Kiểm tra";
    }
  }, 15000);
}

function updateEditorLanguage(lang) {
  if (!editor) return;
  let monacoLang = "python";
  if (lang === "c" || lang === "cpp") { monacoLang = "cpp"; }
  else if (lang === "csharp" || lang === "java") { monacoLang = lang; }

  monaco.editor.setModelLanguage(editor.getModel(), monacoLang);
}

function setupTabs() {
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const type = btn.dataset.content ? 'content' : 'tab';
      if (type === 'content') {
        // Left pane tabs
        document.querySelectorAll(".problem-pane .tab-btn").forEach(b => b.classList.remove('active'));
        document.querySelectorAll(".pane-content").forEach(p => p.classList.add('d-none'));
        btn.classList.add('active');
        document.getElementById(`problem-${btn.dataset.content}`).classList.remove('d-none');
      } else {
        // Bottom pane tabs (Console/Results)
        switchTab(btn.dataset.tab);
      }
    });
  });

  document.getElementById("template-btn").addEventListener("click", () => {
    if (!currentProblem) return;
    const lang = document.getElementById("language-select").value;
    if (currentProblem.starter_code && currentProblem.starter_code[lang]) {
      editor.setValue(currentProblem.starter_code[lang]);
    } else alert("Bài tập này không có code mẫu cho ngôn ngữ này.");
  });
}

function switchTab(tabId) {
  // Sync tabs in the console section
  document.querySelectorAll(".console-section .tab-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.tab === tabId);
  });

  // Sync panes in the console section
  document.querySelectorAll(".console-section .tab-pane").forEach((pane) => {
    pane.classList.toggle("active", pane.id === `tab-${tabId}`);
  });

  if (tabId === 'console' && terminal) {
    setTimeout(() => {
      terminal.fitAddon.fit();
      terminal.xterm.focus();
      terminal.xterm.scrollToBottom();
    }, 100);
  }
}

function renderResults(results) {
  const panel = document.getElementById('tab-results');
  if (!panel) return;
  panel.innerHTML = '';

  if (!results || results.length === 0) {
    panel.innerHTML = '<div class="p-4 w-100 text-center text-muted">Không tìm thấy test case nào cho bài này.</div>';
    return;
  }

  let allPassed = results.length > 0;

  results.forEach((res, index) => {
    const card = document.createElement('div');
    card.className = `result-card ${res.passed ? 'passed' : 'failed'}`;
    const actualText = (res.actual || "").toString().trim() || '(không có đầu ra)';

    card.innerHTML = `
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                <strong>Test Case #${index + 1}</strong>
                <span style="color: ${res.passed ? '#3fb950' : '#f85149'}">${res.passed ? 'PASS' : 'FAIL'}</span>
            </div>
            <div style="font-size: 0.8rem; color: #8b949e">
                <div>Input: <code>${res.input}</code></div>
                <div>Expected: <code>${res.expected}</code></div>
                <div class="text-truncate" title="${escapeHtml(actualText)}">Actual: <code>${escapeHtml(actualText)}</code></div>
            </div>
        `;
    panel.appendChild(card);
    if (!res.passed) allPassed = false;
  });

  if (allPassed && currentProblem) {
    // Save as test attempt (not final submission) for exercise mode
    fetch('/api/submissions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        problemId: currentProblem.id,
        problemTitle: currentProblem.title,
        language: document.getElementById('language-select').value,
        code: editor.getValue(),
        mode: 'practice',
        allPassed: true,
        submission_type: 'check'  // Mark as test attempt, not final submission
      })
    });
  }
}

class Terminal {
  constructor() {
    this.container = document.getElementById('terminal-container');
    this.xterm = new window.Terminal({
      cursorBlink: true,
      theme: {
        background: '#0d1117',
        foreground: '#c9d1d9',
        cursor: '#58a6ff',
        selectionBackground: 'rgba(88, 166, 255, 0.3)',
      },
      fontFamily: '"Fira Code", monospace',
      fontSize: 15,
      lineHeight: 1.4,
      scrollback: 1000,
      convertEol: true,
      cursorStyle: 'block'
    });

    this.fitAddon = new window.FitAddon.FitAddon();
    this.xterm.loadAddon(this.fitAddon);
    this.xterm.open(this.container);
    this.fitAddon.fit();

    this.inputBuffer = '';
    this.isSessionActive = false;

    this.init();
  }

  init() {
    this.xterm.onData(data => this.handleData(data));
    window.addEventListener('resize', () => {
      if (document.getElementById('tab-console').classList.contains('active')) {
        setTimeout(() => this.fitAddon.fit(), 100);
      }
    });

    this.xterm.writeln("\x1b[1;34m=== INTERACTIVE TERMINAL ===\x1b[0m");
    this.xterm.writeln("\x1b[90mViết code và bấm 'Chạy console' để bắt đầu.\x1b[0m");

    // Setup Socket.IO listeners
    socket.on('output', (data) => {
      this.xterm.write(data.data);
    });

    socket.on('error', (data) => {
      this.xterm.writeln(`\n\x1b[1;31m[LỖI]: ${data.message}\x1b[0m`);
      this.isSessionActive = false;
    });

    socket.on('session_started', () => {
      this.isSessionActive = true;
      this.xterm.writeln("\x1b[1;32m[Chương trình đang chạy - Nhập dữ liệu và Enter]\x1b[0m");
    });

    socket.on('session_ended', (data) => {
      this.isSessionActive = false;
      this.xterm.writeln(`\n\x1b[1;33m[Kết thúc: ${data.reason}]\x1b[0m`);
    });
  }

  handleData(data) {
    if (!this.isSessionActive) return;

    switch (data) {
      case '\r': // Enter
        this.xterm.write('\r\n');
        this.handleEnter();
        break;
      case '\u007F': // Backspace
        if (this.inputBuffer.length > 0) {
          this.inputBuffer = this.inputBuffer.slice(0, -1);
          this.xterm.write('\b \b');
        }
        break;
      default:
        if (data >= ' ' && data <= '~') {
          this.inputBuffer += data;
          this.xterm.write(data);
        }
    }
  }

  handleEnter() {
    const input = this.inputBuffer;
    this.inputBuffer = '';

    socket.emit('send_input', { input: input });
  }

  async startSession(code) {
    this.xterm.reset();
    this.inputBuffer = '';

    const language = document.getElementById('language-select').value;

    this.xterm.writeln("\x1b[1;34m[Đang khởi động...]\x1b[0m");

    socket.emit('start_session', {
      language: language,
      code: code
    });
  }

  clear() {
    this.xterm.reset();
    this.inputBuffer = '';
    this.isSessionActive = false;
  }
}
