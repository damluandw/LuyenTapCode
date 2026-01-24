let editor;
let problems = [];
let currentProblem = null;
let terminal;

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
    descEl.innerHTML = p.description.replace(/\n/g, "<br>");
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
    const manualInput = document.getElementById('custom-stdin').value;

    if (!currentProblem) return;

    btn.disabled = true;
    const originalText = btn.textContent;
    btn.textContent = "Đang chạy...";

    switchTab('console');
    if (terminal) {
        terminal.clear();
        terminal.print("Đang chạy với dữ liệu nhập tay...", "status");
        await terminal.execute_with_input(editor.getValue(), manualInput);
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
    if (terminal) {
        terminal.clear();
        terminal.print("Đang chạy toàn bộ code với test cases...", "status");
    }

    try {
        const response = await fetch("/execute", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                language: document.getElementById("language-select").value,
                code: editor.getValue(),
                test_cases: currentProblem.test_cases,
            }),
        });
        const data = await response.json();
        renderResults(data.results);
    } catch (err) {
        if (terminal) terminal.print("Lỗi kết nối server: " + err.message, "error");
        switchTab("console");
    } finally {
        btn.disabled = false;
        btn.textContent = originalText;
    }
}

function updateEditorLanguage(lang) {
  if (!editor) return;
  let monacoLang = "python";
  let prompt = ">>>";
  if (lang === "c" || lang === "cpp") { monacoLang = "cpp"; prompt = "$"; }
  else if (lang === "csharp" || lang === "java") { monacoLang = lang; prompt = ">"; }

  monaco.editor.setModelLanguage(editor.getModel(), monacoLang);
  if (terminal) terminal.setPrompt(prompt);
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
}

function renderResults(results) {
    const panel = document.getElementById('results-list');
    panel.innerHTML = '';
    let allPassed = true;
    let errorLog = '';

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
        if (res.error) errorLog += `Test Case #${index + 1} Error:\n${res.error}\n\n`;
        panel.appendChild(card);
        if (!res.passed) allPassed = false;
    });

    if (allPassed) {
        if (terminal) terminal.print("Chúc mừng! Tất cả test case đã vượt qua.", "status");
    } else if (errorLog && terminal) {
        terminal.print(errorLog, 'error');
        switchTab('console');
    }
}

class Terminal {
    constructor() {
        this.container = document.getElementById('terminal-container');
        this.outputArea = document.getElementById('terminal-output');
        this.inputArea = document.getElementById('terminal-input');
        this.promptEl = document.getElementById('terminal-prompt');
        this.history = [];
        this.historyIndex = -1;
        this.isExecuting = false;
        this.init();
    }
    init() {
        this.inputArea.addEventListener('keydown', (e) => this.handleKeydown(e));
        this.container.addEventListener('click', () => this.inputArea.focus());
        this.print("Sẵn sàng. Nhập lệnh và nhấn Enter để chạy.", "status");
    }
    setPrompt(prompt) { this.promptEl.textContent = prompt; }
    print(text, type = 'default') {
        const line = document.createElement('div');
        line.className = `line ${type}-line`;
        line.textContent = text;
        this.outputArea.appendChild(line);
        this.outputArea.scrollTop = this.outputArea.scrollHeight;
    }
    async handleKeydown(e) {
        if (this.isExecuting) return e.preventDefault();
        if (e.key === 'Enter') {
            const command = this.inputArea.value.trim();
            if (!command) return;
            this.print(`${this.promptEl.textContent} ${command}`, 'command');
            this.history.push(command);
            this.historyIndex = this.history.length;
            this.inputArea.value = '';
            await this.execute(command);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            if (this.historyIndex > 0) { this.historyIndex--; this.inputArea.value = this.history[this.historyIndex]; }
        } else if (e.key === 'ArrowDown') {
            e.preventDefault();
            if (this.historyIndex < this.history.length - 1) { this.historyIndex++; this.inputArea.value = this.history[this.historyIndex]; }
            else { this.historyIndex = this.history.length; this.inputArea.value = ''; }
        }
    }
    async execute(command) {
        this.isExecuting = true;
        this.inputArea.disabled = true;
        try {
            const response = await fetch('/execute_console', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    language: document.getElementById('language-select').value,
                    code: editor.getValue(),
                    command: command,
                    stdin: document.getElementById('custom-stdin').value
                })
            });
            const data = await response.json();
            if (data.output) this.print(data.output.trim());
            if (data.error) this.print(data.error.trim(), 'error');
            if (!data.output && !data.error) this.print("(Không có kết quả trả về)");
        } catch (err) { this.print("Lỗi kết nối: " + err.message, 'error'); }
        finally { this.isExecuting = false; this.inputArea.disabled = false; this.inputArea.focus(); }
    }
    async execute_with_input(code, stdin) {
        this.isExecuting = true;
        this.inputArea.disabled = true;
        try {
            const response = await fetch('/execute_console', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    language: document.getElementById('language-select').value,
                    code: code,
                    command: "",
                    stdin: stdin
                })
            });
            const data = await response.json();
            if (data.output) { this.print("Output:"); this.print(data.output.trim()); }
            if (data.error) { this.print("Error:", "error"); this.print(data.error.trim(), 'error'); }
        } catch (err) { this.print("Lỗi hệ thống: " + err.message, 'error'); }
        finally { this.isExecuting = false; this.inputArea.disabled = false; this.inputArea.focus(); }
    }
    clear() { this.outputArea.innerHTML = ''; }
}
