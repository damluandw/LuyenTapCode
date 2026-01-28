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
  loadProblems();
  setupTabs();
  setupEventListeners();
});

// Sidebar & Problem Loading
async function loadProblems() {
  try {
    const response = await fetch("/problems");
    const data = await response.json();
    if (data.error) return console.error("Server error:", data.error);

    problems = Array.isArray(data) ? data : [];
    const listContainer = document.getElementById("problem-list");
    listContainer.innerHTML = "";

    problems.forEach((p) => {
      const item = document.createElement("div");
      item.className = "problem-item";
      item.dataset.id = p.id;
      item.innerHTML = `
                <div class="p-title">${p.title}</div>
                <div class="p-diff" style="font-size: 0.7rem; color: #8b949e">${p.difficulty}</div>
            `;
      item.addEventListener("click", () => {
        document.querySelectorAll(".problem-item").forEach((el) => el.classList.remove("active"));
        item.classList.add("active");
        setProblem(p);
      });
      listContainer.appendChild(item);
    });

    if (problems.length > 0) listContainer.firstChild.click();
  } catch (err) {
    console.error("Lỗi tải bài tập:", err);
  }
}

function setProblem(p) {
  currentProblem = p;
  document.getElementById("current-problem-title").textContent = p.title;

  const descEl = document.getElementById("problem-desc");
  if (typeof marked !== 'undefined') {
    descEl.innerHTML = marked.parse(p.description);
  } else {
    descEl.innerHTML = p.description.replace(/\\n/g, "<br>");
  }

  document.getElementById("current-difficulty").textContent = p.difficulty;
  if (editor) editor.setValue("");
  switchTab("desc");

  const lang = document.getElementById("language-select").value;
  updateEditorLanguage(lang);
  updateHintTab(p, lang);
}

function updateHintTab(p, lang) {
  if (!p) return;
  const hintEl = document.getElementById("problem-hint");
  const syntaxTips = {
    python: "<strong>Cú pháp Python:</strong> <code>print()</code>, <code>input()</code>",
    c: "<strong>Cú pháp C:</strong> <code>printf()</code>, <code>scanf()</code>",
    cpp: "<strong>Cú pháp C++:</strong> <code>cout <<</code>, <code>cin >></code>",
    java: "<strong>Cú pháp Java:</strong> <code>System.out.println()</code>",
    csharp: "<strong>Cú pháp C#:</strong> <code>Console.WriteLine()</code>"
  };

  let hintText = p.hint;
  if (p.language_hints && p.language_hints[lang]) hintText = p.language_hints[lang];

  let hintHtml = typeof marked !== 'undefined' ? marked.parse(hintText || "Không có gợi ý.") : (hintText || "Không có gợi ý.");
  hintHtml = `<div class="syntax-tip" style="margin-bottom: 15px; padding: 10px; background: rgba(88, 166, 255, 0.1); border-radius: 6px; font-size: 0.9rem; border: 1px solid rgba(88, 166, 255, 0.2);">${syntaxTips[lang] || ""}</div>` + hintHtml;

  if (p.starter_code && p.starter_code[lang]) {
    hintHtml += `<br><strong>Code mẫu (${lang}):</strong><pre class="console-box" style="margin-top: 10px; background: #1c2128; border: 1px solid #30363d; padding: 10px; border-radius: 4px; font-family: 'Fira Code', monospace; font-size: 0.85rem;">${p.starter_code[lang]}</pre>`;
  }
  hintEl.innerHTML = hintHtml;
}

function setupEventListeners() {
    document.getElementById("language-select").addEventListener("change", (e) => {
        const lang = e.target.value;
        updateEditorLanguage(lang);
        if (currentProblem) updateHintTab(currentProblem, lang);
    });

    document.getElementById("run-btn").addEventListener("click", handleRunClick);
    document.getElementById("console-run-btn").addEventListener("click", handleConsoleRunClick);
}

async function handleConsoleRunClick() {
    const btn = document.getElementById("console-run-btn");

    if (!currentProblem) return;

    btn.disabled = true;
    const originalText = btn.textContent;
    btn.textContent = "Đang chạy...";

    switchTab('console');
    if (terminal) {
        await terminal.startSession(editor.getValue());
    }
    btn.disabled = false;
    btn.textContent = originalText;
}

async function handleRunClick() {
    const btn = document.getElementById("run-btn");
    const resultsPanel = document.getElementById("results-list");

    if (!currentProblem) return;

    btn.disabled = true;
    const originalText = btn.textContent;
    btn.textContent = "Đang chạy...";

    switchTab("results");
    resultsPanel.innerHTML = '<div class="loading">Đang thực thi các test case...</div>';

    // For test cases, we'll still use the old Piston API temporarily
    // You can implement batch testing later if needed
    
    btn.disabled = false;
    btn.textContent = originalText;
    resultsPanel.innerHTML = '<div>Chức năng test case đang được cập nhật. Vui lòng sử dụng "Chạy console" để kiểm tra code.</div>';
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
    btn.addEventListener("click", () => switchTab(btn.dataset.tab));
  });

  document.getElementById("template-btn").addEventListener("click", () => {
    if (!currentProblem) return;
    const lang = document.getElementById("language-select").value;
    if (currentProblem.starter_code && currentProblem.starter_code[lang]) {
      editor.setValue(currentProblem.starter_code[lang]);
      switchTab("desc");
    } else alert("Bài tập này không có code mẫu cho ngôn ngữ này.");
  });
}

function switchTab(tabId) {
  document.querySelectorAll(".tab-btn").forEach((btn) => btn.classList.toggle("active", btn.dataset.tab === tabId));
  document.querySelectorAll(".tab-pane").forEach((pane) => pane.classList.toggle("active", pane.id === `tab-${tabId}`));
  
  if (tabId === 'console' && terminal) {
    setTimeout(() => {
        terminal.fitAddon.fit();
        terminal.xterm.focus();
    }, 50);
  }
}

function renderResults(results) {
    const panel = document.getElementById('results-list');
    panel.innerHTML = '';
    let allPassed = true;

    results.forEach((res, index) => {
        const card = document.createElement('div');
        card.className = `result-card ${res.passed ? 'passed' : 'failed'}`;
        card.innerHTML = `
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                <strong>Test Case #${index + 1}</strong>
                <span style="color: ${res.passed ? '#3fb950' : '#f85149'}">${res.passed ? 'PASS' : 'FAIL'}</span>
            </div>
            <div style="font-size: 0.8rem; color: #8b949e">
                <div>Input: <code>${res.input}</code></div>
                <div>Expected: <code>${res.expected}</code></div>
                <div>Actual: <code>${res.actual.trim() || '(empty)'}</code></div>
            </div>
        `;
        panel.appendChild(card);
        if (!res.passed) allPassed = false;
    });
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
                this.fitAddon.fit();
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
