let editor;
let allProblems = [];
let currentProblem = null;
let terminal;
let socket;
let examId = new URLSearchParams(window.location.search).get('id') || 1;
let examDuration = 60 * 60; // Default 60 mins
let isSubmitting = false; // Flag to trigger submission after test completion
let currentTimeRemaining = 0;
let timeElapsedFromServer = 0;

// Monaco Loading
require.config({
    paths: { vs: "https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.44.0/min/vs" },
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
    });

    window.addEventListener("resize", () => editor.layout());

    socket = io({
        transports: ['websocket', 'polling']
    });

    socket.on('connect', () => {
        const orb = document.getElementById('connection-status');
        if (orb) {
            orb.className = 'status-orb connected';
            orb.title = 'Đã kết nối máy chủ';
        }
    });

    socket.on('disconnect', () => {
        const orb = document.getElementById('connection-status');
        if (orb) {
            orb.className = 'status-orb disconnected';
            orb.title = 'Mất kết nối máy chủ';
        }
    });

    socket.on('error', (data) => {
        const runBtn = document.getElementById("run-btn");
        if (runBtn) {
            runBtn.disabled = false;
            runBtn.innerHTML = '<i class="bi bi-play-fill me-1"></i> Kiểm tra';
        }
        const consoleBtn = document.getElementById("console-run-btn");
        if (consoleBtn) {
            consoleBtn.disabled = false;
            consoleBtn.innerHTML = '<i class="bi bi-terminal"></i>';
        }

        if (terminal) {
            terminal.xterm.write(`\r\n\x1b[31m[LỖI]: ${data.message || 'Có lỗi xảy ra'}\x1b[0m\r\n`);
        } else {
            alert("Lỗi: " + (data.message || "Có lỗi xảy ra"));
        }

        // If we're in results tab, show the error
        const resultsPanel = document.getElementById('tab-results');
        if (resultsPanel && resultsPanel.classList.contains('active')) {
            resultsPanel.innerHTML = `<div class="p-4 text-danger small" style="font-family: monospace; white-space: pre-wrap;">${data.message || 'Lỗi không xác định'}</div>`;
        }
    });

    terminal = new Terminal();
    await fetchExamData(); // Wait for data to get correct time
    checkUser();
    setupTabs();
    setupEventListeners();
    startTimer();
    setupSidebarToggles();
});

function setupSidebarToggles() {
    const sidebar = document.getElementById('sidebar');

    // Desktop Toggle
    const toggle = document.getElementById('sidebar-toggle');
    const icon = document.getElementById('toggle-icon');
    if (toggle && sidebar) {
        toggle.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
            if (sidebar.classList.contains('collapsed')) {
                icon.classList.replace('bi-chevron-left', 'bi-chevron-right');
            } else {
                icon.classList.replace('bi-chevron-right', 'bi-chevron-left');
            }
            setTimeout(() => editor.layout(), 300);
        });
    }

    // Mobile Toggle
    const mobileToggle = document.getElementById('mobile-sidebar-toggle');
    const mobileOverlay = document.getElementById('mobile-overlay');
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
}

function setupTabs() {
    document.querySelectorAll(".tab-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            const type = btn.dataset.content ? 'content' : 'tab';
            if (type === 'content') {
                // Left pane tabs (Problem Info)
                document.querySelectorAll(".problem-pane .tab-btn").forEach(b => b.classList.remove('active'));
                document.querySelectorAll(".pane-content").forEach(p => p.classList.remove('active'));
                btn.classList.add('active');
                const targetId = `problem-${btn.dataset.content}`;
                if (document.getElementById(targetId)) {
                    document.getElementById(targetId).classList.add('active');
                }
            } else {
                // Bottom pane tabs (Console/Results)
                switchTab(btn.dataset.tab);
            }
        });
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
        }, 100);
    }
}

async function checkUser() {
    try {
        const res = await fetch('/api/auth/me');
        if (!res.ok) { window.location.href = '/login'; return; }
        const data = await res.json();
        const navDisplayEl = document.getElementById('nav-user-display');
        if (navDisplayEl) navDisplayEl.textContent = data.display_name;
    } catch (e) {
        window.location.href = '/login';
    }
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
        timeElapsedFromServer = data.info.timeElapsed || 0;
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
        updateMonacoLanguage(firstAllowed);
    }
}

function updateMonacoLanguage(lang) {
    const monacoLang = (lang === 'c' || lang === 'cpp') ? 'cpp' : (lang === 'csharp' ? 'csharp' : lang);
    if (editor) monaco.editor.setModelLanguage(editor.getModel(), monacoLang);
}

function renderProblems() {
    const listContainer = document.getElementById("problem-list");
    listContainer.innerHTML = "";

    allProblems.forEach((p) => {
        const item = document.createElement("div");
        item.className = `problem-item ${currentProblem && currentProblem.id === p.id ? "active" : ""}`;
        item.innerHTML = `
        <div class="p-title">${p.title}</div>
        <div class="p-meta">
            <span class="text-info">${p.difficulty}</span>
            <span>• ${p.points || 0}đ</span>
        </div>
    `;
        item.addEventListener("click", () => {
            document.querySelectorAll(".problem-item").forEach((el) => el.classList.remove("active"));
            item.classList.add("active");
            loadProblemDetail(p.id);

            // Close mobile sidebar if open
            const sidebar = document.getElementById('sidebar');
            const overlay = document.getElementById('mobile-overlay');
            if (sidebar.classList.contains('mobile-show')) {
                sidebar.classList.remove('mobile-show');
                overlay.classList.remove('active');
            }
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

    // Restore previous code if available
    if (p.last_submission && p.last_submission.code) {
        editor.setValue(p.last_submission.code);
        if (p.last_submission.language) {
            document.getElementById("language-select").value = p.last_submission.language;
            updateMonacoLanguage(p.last_submission.language);
        }
    } else {
        editor.setValue("");
    }

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
        // Fallback to plain text if marked is totally unavailable
        descEl.innerHTML = `<pre style="white-space: pre-wrap; font-family: inherit;">${p.description}</pre>`;
    }
}

function setupEventListeners() {
    const langSelect = document.getElementById("language-select");
    if (langSelect) {
        langSelect.addEventListener("change", (e) => {
            updateMonacoLanguage(e.target.value);
        });
    }

    const runBtn = document.getElementById("run-btn");
    if (runBtn) {
        runBtn.addEventListener("click", handleRunClick);
    }

    const consoleBtn = document.getElementById("console-run-btn");
    if (consoleBtn) {
        consoleBtn.addEventListener("click", handleConsoleRunClick);
    }

    const submitBtn = document.getElementById("submit-btn");
    if (submitBtn) {
        submitBtn.addEventListener("click", handleSubmitClick);
    }

    const finishBtn = document.getElementById("finish-exam-btn");
    if (finishBtn) {
        finishBtn.addEventListener("click", () => {
            if (confirm("Bạn có chắc chắn muốn nộp bài và kết thúc kỳ thi?")) {
                window.location.href = "/";
            }
        });
    }

    socket.on('test_results', (data) => {
        const btn = document.getElementById("run-btn");
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-play-fill me-1"></i> Kiểm tra';
        }
        if (data.results) {
            renderResults(data.results);

            // Save test attempt when checking (not submitting)
            if (!isSubmitting) {
                const allPassed = data.results.every(r => r.passed);
                saveTestAttempt(allPassed);
            }

            // Handle actual submission if this was triggered by submit button
            if (isSubmitting) {
                isSubmitting = false;
                const allPassed = data.results.every(r => r.passed);
                performActualSubmission(allPassed);
            }
        } else if (data.error) {
            isSubmitting = false;
            const panel = document.getElementById('tab-results');
            if (panel) panel.innerHTML = `<div class="p-4 text-danger small" style="font-family: monospace; white-space: pre-wrap;">${data.error}</div>`;
        }
    });
}

function startTimer() {
    const timerEl = document.getElementById('timer');

    // We calculate the start time based on when the server says we started
    // If the student reloads, we subtract the elapsed time from now to get a consistent "start" point
    const startTime = Date.now() - (timeElapsedFromServer * 1000);

    const interval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        const remaining = examDuration - elapsed;
        currentTimeRemaining = remaining;

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

        if (remaining < 300) {
            timerEl.style.background = "linear-gradient(135deg, #ff4444 0%, #cc0000 100%)";
        }
    }, 1000);
}

class Terminal {
    constructor() {
        this.container = document.getElementById('terminal-container');
        this.fitAddon = new window.FitAddon.FitAddon();
        this.xterm = new window.Terminal({
            cursorBlink: true,
            theme: {
                background: '#0d1117',
                foreground: '#d1d5db',
                cursor: '#58a6ff',
                selection: 'rgba(58, 150, 221, 0.3)'
            },
            fontFamily: '"Fira Code", monospace',
            fontSize: 14,
            convertEol: true
        });

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
            if (data === '\r') {
                this.xterm.write('\r\n');
                socket.emit('send_input', { input: this.inputBuffer });
                this.inputBuffer = '';
            } else if (data === '\u007F') {
                if (this.inputBuffer.length > 0) {
                    this.inputBuffer = this.inputBuffer.slice(0, -1);
                    this.xterm.write('\b \b');
                }
            } else {
                this.inputBuffer += data;
                this.xterm.write(data);
            }
        });

        socket.on('output', (data) => this.xterm.write(data.data));
        socket.on('session_started', () => {
            this.isSessionActive = true;
            const consoleBtn = document.getElementById("console-run-btn");
            if (consoleBtn) {
                consoleBtn.disabled = false;
                consoleBtn.innerHTML = '<i class="bi bi-terminal"></i>';
            }
        });
        socket.on('session_ended', () => {
            this.isSessionActive = false;
            this.xterm.write('\r\n[Phiên đã kết thúc]\r\n');
        });

        window.addEventListener('resize', () => {
            if (document.getElementById('tab-console').classList.contains('active')) {
                this.fitAddon.fit();
            }
        });
    }

    async startSession(code) {
        this.xterm.reset();
        this.xterm.write('Đang khởi động terminal...\r\n');
        socket.emit('start_session', {
            language: document.getElementById('language-select').value,
            code: code
        });
    }
}

async function handleRunClick() {
    const btn = document.getElementById("run-btn");
    if (!currentProblem) return;

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Đang chạy...';

    switchTab("results");
    const panel = document.getElementById("tab-results");
    panel.innerHTML = '<div class="p-4 w-100 text-center text-muted">Đang chấm bài... <div class="spinner-border spinner-border-sm ms-2" role="status"></div></div>';

    socket.emit('run_test_cases', {
        language: document.getElementById('language-select').value,
        code: editor.getValue(),
        test_cases: currentProblem.test_cases || []
    });

    setTimeout(() => {
        if (btn.disabled && btn.textContent.includes("Đang chạy")) {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-play-fill me-1"></i> Kiểm tra';
        }
    }, 15000);
}

function handleConsoleRunClick() {
    const btn = document.getElementById("console-run-btn");
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';

    switchTab('console');
    terminal.startSession(editor.getValue());

    // Safety timeout to re-enable button if session_started never arrives
    setTimeout(() => {
        if (btn.disabled && btn.innerHTML.includes("spinner-border")) {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-terminal"></i>';
        }
    }, 15000);
}

async function handleSubmitClick() {
    if (!currentProblem) return;
    // if (!confirm("Bạn muốn nộp bài tập này? (Hệ thống sẽ chạy kiểm tra trước khi nộp)")) return;

    isSubmitting = true;
    handleRunClick(); // This will trigger renderResults -> performActualSubmission
}

async function performActualSubmission(allPassed) {
    const btn = document.getElementById("submit-btn");
    const originalContent = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Đang lưu...';

    try {
        const response = await fetch('/api/submissions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                problemId: currentProblem.id,
                problemTitle: currentProblem.title,
                language: document.getElementById('language-select').value,
                code: editor.getValue(),
                mode: 'exam',
                examId: examId,
                allPassed: allPassed,
                timeRemaining: currentTimeRemaining,
                submission_type: 'submit'  // Mark as final submission
            })
        });

        const data = await response.json();
        if (data.status === 'success') {
            // Update local state so if they switch back, the code remains
            currentProblem.last_submission = {
                code: editor.getValue(),
                allPassed: allPassed,
                language: document.getElementById('language-select').value,
                timeRemaining: currentTimeRemaining
            };

            btn.classList.replace('btn-success', 'btn-outline-success');
            btn.innerHTML = '<i class="bi bi-check-lg me-1"></i> Đã nộp thành công';
            setTimeout(() => {
                btn.classList.replace('btn-outline-success', 'btn-success');
                btn.innerHTML = originalContent;
                btn.disabled = false;
            }, 3000);
        } else {
            throw new Error(data.message || "Lỗi nộp bài");
        }
    } catch (error) {
        console.error("Submission error:", error);
        alert("Lỗi khi nộp bài: " + error.message);
        btn.disabled = false;
        btn.innerHTML = originalContent;
    }
}

// Save test attempt when student clicks "Check" button
async function saveTestAttempt(allPassed) {
    try {
        await fetch('/api/submissions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                problemId: currentProblem.id,
                problemTitle: currentProblem.title,
                language: document.getElementById('language-select').value,
                code: editor.getValue(),
                mode: 'exam',
                examId: examId,
                allPassed: allPassed,
                timeRemaining: currentTimeRemaining,
                submission_type: 'check'  // Mark as test attempt
            })
        });
    } catch (error) {
        console.error("Error saving test attempt:", error);
        // Don't show error to user, this is just for tracking
    }
}


function renderResults(results) {
    const panel = document.getElementById('tab-results');
    panel.innerHTML = '';

    if (results.length === 0) {
        panel.innerHTML = '<div class="p-4 text-center text-muted">Không có dữ liệu test case.</div>';
        return;
    }

    let passedCount = 0;
    results.forEach((res, index) => {
        if (res.passed) passedCount++;
        const card = document.createElement('div');
        // ... (rest of the card generation remains same)
        card.className = `result-card ${res.passed ? 'passed' : 'failed'}`;
        card.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-1">
            <span class="fw-bold small">Test case #${index + 1}</span>
            <span class="badge ${res.passed ? 'bg-success' : 'bg-danger'} rounded-pill" style="font-size: 0.6rem">
                ${res.passed ? 'PASSED' : 'FAILED'}
            </span>
        </div>
        ${!res.passed && res.error ? `<div class="text-danger small mt-1" style="font-family: monospace; font-size: 0.75rem">${res.error}</div>` : ''}
    `;
        panel.appendChild(card);
    });
}
