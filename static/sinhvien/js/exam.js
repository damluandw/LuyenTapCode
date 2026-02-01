let editor;
let allProblems = [];
let currentProblem = null;
let terminal;
let socket;
let examId = new URLSearchParams(window.location.search).get('id') || 1;
let examDuration = 60 * 60; // Default 60 mins

// Monaco Loading
require.config({
  paths: { vs: "https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.44.0/min/vs" },
});

require(["vs/editor/editor.main"], async function () {
  editor = monaco.editor.create(document.getElementById("editor-container"), {
    value: "",
    language: "python",
    theme: "vs-dark",
    fontSize: 16,
    automaticLayout: true,
    minimap: { enabled: false }
  });

  socket = io();
  socket.on('connect', () => document.getElementById('connection-status').className = 'status-orb connected');
  
  terminal = new Terminal();
  fetchExamData();
  checkUser();
  setupEventListeners();
  startTimer();
});

async function checkUser() {
  const res = await fetch('/api/auth/me');
  if (!res.ok) { window.location.href = '/login'; return; }
  const data = await res.json();
  document.getElementById('user-name').textContent = data.display_name;
}

async function fetchExamData() {
  try {
    const res = await fetch(`/api/exams/${examId}`);
    const data = await res.json();
    if (data.error) {
        alert("Không tìm thấy kỳ thi hoặc bạn không có quyền truy cập.");
        window.location.href = "/";
        return;
    }
    
    document.getElementById('exam-title').textContent = data.info.title;
    examDuration = (data.info.duration || 60) * 60;
    allProblems = data.problems;
    
    // Filter languages if restricted
    filterLanguages(data.info.allowedLanguages);
    
    renderProblems();

    if (allProblems.length > 0) loadProblemDetail(allProblems[0].id);
  } catch (err) {
    console.error("Failed to load exam:", err);
  }
}

function filterLanguages(allowed) {
    const select = document.getElementById("language-select");
    if (!select || !allowed || allowed.length === 0) return;
    
    const options = Array.from(select.options);
    let firstAllowed = null;
    
    options.forEach(opt => {
        if (allowed.includes(opt.value)) {
            opt.style.display = "";
            opt.disabled = false;
            if (!firstAllowed) firstAllowed = opt.value;
        } else {
            opt.style.display = "none";
            opt.disabled = true;
        }
    });
    
    if (firstAllowed) {
        select.value = firstAllowed;
        // Trigger monaco update
        const monacoLang = (firstAllowed === 'c' || firstAllowed === 'cpp') ? 'cpp' : firstAllowed;
        if(editor) monaco.editor.setModelLanguage(editor.getModel(), monacoLang);
    }
}

function renderProblems() {
  const listContainer = document.getElementById("problem-list");
  listContainer.innerHTML = "";

  allProblems.forEach((p) => {
    const item = document.createElement("div");
    item.className = `problem-item ${currentProblem && currentProblem.id === p.id ? "active" : ""}`;
    item.innerHTML = `<div class="p-title">${p.title}</div><div class="p-diff">${p.difficulty}</div>`;
    item.addEventListener("click", () => {
      document.querySelectorAll(".problem-item").forEach((el) => el.classList.remove("active"));
      item.classList.add("active");
      loadProblemDetail(p.id);
    });
    listContainer.appendChild(item);
  });
}

function loadProblemDetail(id) {
    const p = allProblems.find(item => item.id == id);
    if (!p) return;
    currentProblem = p;
    document.getElementById("current-problem-title").textContent = p.title;
    document.getElementById("current-difficulty").textContent = p.difficulty;
    document.getElementById("current-points").textContent = `${p.points || 0} điểm`;
    document.getElementById("problem-desc").innerHTML = marked.parse(p.description);
    
    if (editor) {
        // Exam doesn't show sample code buttons, but we can set a basic boiler plate if needed
        editor.setValue("");
    }
}

function setupEventListeners() {
    document.getElementById("language-select").addEventListener("change", (e) => {
        const monacoLang = e.target.value === 'c' || e.target.value === 'cpp' ? 'cpp' : e.target.value;
        monaco.editor.setModelLanguage(editor.getModel(), monacoLang);
    });

    document.getElementById("run-btn").addEventListener("click", handleRunClick);
    document.getElementById("console-run-btn").addEventListener("click", handleConsoleRunClick);
    document.getElementById("finish-exam-btn").addEventListener("click", () => {
        if(confirm("Bạn có chắc chắn muốn nộp bài và kết thúc kỳ thi?")) {
            window.location.href = "/";
        }
    });

    socket.on('test_results', (data) => {
        const btn = document.getElementById("run-btn");
        btn.disabled = false;
        btn.textContent = "Kiểm tra";
        if (data.results) renderResults(data.results);
    });
}

function startTimer() {
    const timerEl = document.getElementById('timer');
    const startTime = Date.now();
    
    const interval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        const remaining = examDuration - elapsed;
        
        if (remaining <= 0) {
            clearInterval(interval);
            timerEl.textContent = "HẾT GIỜ";
            alert("Đã hết thời gian làm bài!");
            window.location.href = "/";
            return;
        }
        
        const h = Math.floor(remaining / 3600);
        const m = Math.floor((remaining % 3600) / 60);
        const s = remaining % 60;
        timerEl.textContent = `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
        
        if (remaining < 300) timerEl.style.background = "#ff4444";
    }, 1000);
}

// Reuse Terminal class logic from student.js
class Terminal {
  constructor() {
    this.container = document.getElementById('terminal-container');
    this.xterm = new window.Terminal({
      cursorBlink: true,
      theme: { background: '#0d1117' },
      fontFamily: '"Fira Code", monospace',
      convertEol: true
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
    this.xterm.onData(data => {
        if (!this.isSessionActive) return;
        if (data === '\r') { this.xterm.write('\r\n'); socket.emit('send_input', { input: this.inputBuffer }); this.inputBuffer = ''; }
        else if (data === '\u007F') { if (this.inputBuffer.length > 0) { this.inputBuffer = this.inputBuffer.slice(0, -1); this.xterm.write('\b \b'); } }
        else { this.inputBuffer += data; this.xterm.write(data); }
    });
    socket.on('output', (data) => this.xterm.write(data.data));
    socket.on('session_started', () => this.isSessionActive = true);
    socket.on('session_ended', () => this.isSessionActive = false);
  }

  async startSession(code) {
    this.xterm.reset();
    socket.emit('start_session', { language: document.getElementById('language-select').value, code: code });
  }
}

async function handleRunClick() {
  const btn = document.getElementById("run-btn");
  btn.disabled = true;
  btn.textContent = "Đang chạy...";
  document.querySelector('.tab-btn[data-tab="results"]').click();
  socket.emit('run_test_cases', {
    language: document.getElementById('language-select').value,
    code: editor.getValue(),
    test_cases: currentProblem.test_cases || []
  });
}

function handleConsoleRunClick() {
    document.querySelector('.tab-btn[data-tab="console"]').click();
    terminal.startSession(editor.getValue());
}

function renderResults(results) {
  const panel = document.getElementById('results-list');
  panel.innerHTML = '';
  results.forEach((res, index) => {
    const card = document.createElement('div');
    card.className = `result-card ${res.passed ? 'passed' : 'failed'}`;
    card.innerHTML = `<div>Test #${index + 1}: ${res.passed ? 'PASS' : 'FAIL'}</div>`;
    panel.appendChild(card);
  });
  
  // Also log the exam submission
  fetch('/api/submissions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        problemId: currentProblem.id,
        problemTitle: currentProblem.title,
        language: document.getElementById('language-select').value,
        mode: 'exam',
        examId: examId
      })
  });
}

document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove('active'));
        document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById(`tab-${btn.dataset.tab}`).classList.add('active');
        if (btn.dataset.tab === 'console') {
            setTimeout(() => terminal.fitAddon.fit(), 50);
        }
    });
});
