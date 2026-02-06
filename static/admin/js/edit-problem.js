let editors = {};
let currentProblemId = new URLSearchParams(window.location.search).get('id');

// Monaco Config
require.config({ paths: { vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.44.0/min/vs' } });

require(['vs/editor/editor.main'], function () {
    const langConfigs = [
        { id: 'editor-python', lang: 'python' },
        { id: 'solution-python', lang: 'python' },
        { id: 'editor-c', lang: 'cpp' },
        { id: 'solution-c', lang: 'cpp' },
        { id: 'editor-cpp', lang: 'cpp' },
        { id: 'solution-cpp', lang: 'cpp' },
        { id: 'editor-java', lang: 'java' },
        { id: 'solution-java', lang: 'java' },
        { id: 'editor-csharp', lang: 'csharp' },
        { id: 'solution-csharp', lang: 'csharp' }
    ];

    langConfigs.forEach(conf => {
        editors[conf.id] = monaco.editor.create(document.getElementById(conf.id), {
            value: '',
            language: conf.lang,
            theme: 'vs-dark',
            automaticLayout: true,
            minimap: { enabled: false },
            fontSize: 14
        });
    });

    setupLivePreview();

    if (currentProblemId) {
        loadProblemData(currentProblemId);
    } else {
        initializeDefaultNewProblem();
    }
});

function initializeDefaultNewProblem() {
    document.getElementById('page-title').textContent = "Thêm bài tập mới";
    addTestCase(); // Start with one empty test case

    // Fill basic templates
    editors['editor-python'].setValue("# Viết code của bạn ở đây\n");
    editors['editor-c'].setValue("// Tính toán...\n#include <stdio.h>\n\nint main() {\n    // Viết code của bạn ở đây\n    \n    return 0;\n}");
    editors['editor-cpp'].setValue("// Tính toán...\n#include <iostream>\nusing namespace std;\n\nint main() {\n    // Viết code của bạn ở đây\n    \n    return 0;\n}");
    editors['editor-java'].setValue("// Tính toán...\nimport java.util.Scanner;\n\npublic class Main {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        // Viết code của bạn ở đây\n    }\n}");
    editors['editor-csharp'].setValue("// Tính toán...\nusing System;\n\nclass Program {\n    static void Main() {\n        // Viết code của bạn ở đây\n    }\n}");

    updatePreview();
}

function setupLivePreview() {
    ['p-title', 'p-diff', 'p-desc', 'p-hint'].forEach(id => {
        document.getElementById(id).addEventListener('input', updatePreview);
    });
}

function updatePreview() {
    const title = document.getElementById('p-title').value || "Tiêu đề bài tập";
    const diff = document.getElementById('p-diff').value;
    const desc = document.getElementById('p-desc').value || "Mô tả sẽ hiển thị ở đây...";
    const hint = document.getElementById('p-hint').value || "Chưa có gợi ý.";

    document.getElementById('pre-title').textContent = title;
    document.getElementById('pre-diff').textContent = diff;
    
    // Bootstrap badge colors
    let badgeClass = 'bg-success';
    if (diff === 'Medium') badgeClass = 'bg-warning text-dark';
    if (diff === 'Hard') badgeClass = 'bg-danger';
    document.getElementById('pre-diff').className = `badge ${badgeClass} mb-3`;

    // Use marked for markdown rendering
    if (window.marked) {
        document.getElementById('pre-desc').innerHTML = marked.parse(desc);
        document.getElementById('pre-hint').innerHTML = marked.parse(hint);
    } else {
        document.getElementById('pre-desc').innerText = desc;
        document.getElementById('pre-hint').innerText = hint;
    }
}

function addTestCase(input = '', output = '') {
    const container = document.getElementById('testcase-list');
    const div = document.createElement('div');
    div.className = 'card bg-dark bg-opacity-25 border-secondary border-opacity-25 p-4 mb-3 position-relative shadow-sm testcase-item';
    div.innerHTML = `
        <button class="btn btn-sm btn-outline-danger position-absolute top-0 end-0 m-2 border-0" onclick="this.parentElement.remove()" title="Xóa bộ test">
            <i class="bi bi-trash"></i>
        </button>
        <div class="row g-3">
            <div class="col-md-6">
                <label class="form-label-custom">Đầu vào (Input)</label>
                <textarea class="form-control bg-dark border-secondary text-light tc-input tc-in" style="font-family: 'Fira Code', monospace; font-size: 0.85rem;" rows="3">${input}</textarea>
            </div>
            <div class="col-md-6">
                <label class="form-label-custom">Đầu ra mong đợi (Output)</label>
                <textarea class="form-control bg-dark border-secondary text-light tc-input tc-out" style="font-family: 'Fira Code', monospace; font-size: 0.85rem;" rows="3">${output}</textarea>
            </div>
        </div>
    `;
    container.appendChild(div);
}

async function loadProblemData(id) {
    document.getElementById('page-title').textContent = `Chỉnh sửa bài tập #${id}`;
    const res = await fetch(`/api/problems/${id}`);
    const p = await res.json();

    document.getElementById('p-title').value = p.title;
    document.getElementById('p-diff').value = p.difficulty;
    document.getElementById('p-cat').value = p.category;
    document.getElementById('p-desc').value = p.description;
    document.getElementById('p-hint').value = p.hint || '';

    // Test cases
    document.getElementById('testcase-list').innerHTML = '';
    p.test_cases.forEach(tc => addTestCase(tc.input, tc.output));

    // Starter codes
    if (p.starter_code) {
        if (p.starter_code.python) editors['editor-python'].setValue(p.starter_code.python);
        if (p.starter_code.c) editors['editor-c'].setValue(p.starter_code.c);
        if (p.starter_code.cpp) editors['editor-cpp'].setValue(p.starter_code.cpp);
        if (p.starter_code.java) editors['editor-java'].setValue(p.starter_code.java);
        if (p.starter_code.csharp) editors['editor-csharp'].setValue(p.starter_code.csharp);
    }

    // Solutions
    if (p.solution_code) {
        if (p.solution_code.python) editors['solution-python'].setValue(p.solution_code.python);
        if (p.solution_code.c) editors['solution-c'].setValue(p.solution_code.c);
        if (p.solution_code.cpp) editors['solution-cpp'].setValue(p.solution_code.cpp);
        if (p.solution_code.java) editors['solution-java'].setValue(p.solution_code.java);
        if (p.solution_code.csharp) editors['solution-csharp'].setValue(p.solution_code.csharp);
    }

    updatePreview();
}

async function saveProblem() {
    const testCases = [];
    document.querySelectorAll('.testcase-item').forEach(item => {
        const inp = item.querySelector('.tc-in').value;
        const out = item.querySelector('.tc-out').value;
        if (inp || out) testCases.push({ input: inp, output: out });
    });

    const data = {
        title: document.getElementById('p-title').value,
        difficulty: document.getElementById('p-diff').value,
        category: document.getElementById('p-cat').value,
        description: document.getElementById('p-desc').value,
        hint: document.getElementById('p-hint').value,
        test_cases: testCases,
        starter_code: {
            python: editors['editor-python'].getValue(),
            c: editors['editor-c'].getValue(),
            cpp: editors['editor-cpp'].getValue(),
            java: editors['editor-java'].getValue(),
            csharp: editors['editor-csharp'].getValue()
        },
        solution_code: {
            python: editors['solution-python'].getValue(),
            c: editors['solution-c'].getValue(),
            cpp: editors['solution-cpp'].getValue(),
            java: editors['solution-java'].getValue(),
            csharp: editors['solution-csharp'].getValue()
        }
    };

    const url = currentProblemId ? `/api/admin/problems/${currentProblemId}` : '/api/admin/problems';
    const method = currentProblemId ? 'PUT' : 'POST';

    const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });

    if (res.ok) {
        alert("Lưu bài tập thành công!");
        window.location.href = '/admin';
    } else {
        alert("Lỗi khi lưu bài tập!");
    }
}

function generateDescriptionFromTests() {
    const testCases = [];
    document.querySelectorAll('.testcase-item').forEach(item => {
        const input = item.querySelector('.tc-in').value;
        const output = item.querySelector('.tc-out').value;
        if (input || output) testCases.push({ input, output });
    });

    if (testCases.length === 0) {
        alert("Cần ít nhất một Test Case để tạo ví dụ!");
        return;
    }

    const tc = testCases[0];
    const exampleMd = `\n\n### Ví dụ:\n**Đầu vào:**\n<div class='example-box'>${tc.input}</div>\n**Đầu ra:**\n<div class='example-box'>${tc.output}</div>`;

    const descArea = document.getElementById('p-desc');
    descArea.value = descArea.value.trim() + exampleMd;
    updatePreview();
}

function copyFromSolution(lang) {
    let sourceId = `solution-${lang}`;
    let destId = `editor-${lang}`;
    if (editors[sourceId] && editors[destId]) {
        editors[destId].setValue(editors[sourceId].getValue());
        alert(`Đã sao chép lời giải ${lang} vào code mẫu!`);
    }
}

async function testSolution(lang) {
    const btn = event.target;
    const originalText = btn.textContent;
    btn.textContent = "Đang chạy...";
    btn.disabled = true;

    // Show result panel
    document.getElementById('preview-results-panel').style.display = 'block';
    document.getElementById('preview-lang-display').textContent = lang;

    const testCases = [];
    document.querySelectorAll('.testcase-item').forEach(item => {
        testCases.push({
            input: item.querySelector('.tc-in').value,
            output: item.querySelector('.tc-out').value
        });
    });

    try {
        const res = await fetch('/api/admin/test-problem', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                language: lang,
                code: editors[`solution-${lang}`].getValue(),
                test_cases: testCases
            })
        });
        const result = await res.json();

        const listContainer = document.getElementById('test-results-list');
        listContainer.innerHTML = '';

        result.results.forEach((r, i) => {
            const card = document.createElement('div');
            const statusColor = r.passed ? 'success' : 'danger';
            card.className = `card bg-dark bg-opacity-25 border-${statusColor} border-opacity-50 border-start border-4 mb-2 p-3 shadow-sm`;

            const inText = (r.input || "").substring(0, 15);
            const outText = (r.actual || "").substring(0, 15);

            card.innerHTML = `
                <div class="d-flex justify-content-between align-items-start mb-1">
                    <strong class="text-${statusColor} small text-uppercase fw-bold">Test #${i + 1}: ${r.passed ? 'PASSED' : 'FAILED'}</strong>
                    ${r.passed ? '<i class="bi bi-check-circle-fill text-success h6 mb-0"></i>' : '<i class="bi bi-x-circle-fill text-danger h6 mb-0"></i>'}
                </div>
                <div class="small text-muted font-monospace">
                    <span class="opacity-50">In:</span> ${inText}${r.input && r.input.length > 15 ? '...' : ''} 
                    <span class="mx-1 opacity-25">|</span>
                    <span class="opacity-50">Out:</span> ${outText}${r.actual && r.actual.length > 15 ? '...' : ''}
                </div>
                ${r.error ? `<div class="mt-2 small text-danger bg-danger bg-opacity-10 p-2 rounded border border-danger border-opacity-25" style="white-space: pre-wrap;">Error: ${r.error}</div>` : ''}
            `;
            listContainer.appendChild(card);
        });
    } catch (e) {
        alert("Lỗi kết nối server!");
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
}

// Simple Scroll Spy
document.querySelector('.editor-main').addEventListener('scroll', () => {
    const sections = document.querySelectorAll('.edit-section');
    const navItems = document.querySelectorAll('.editor-nav .nav-item');

    let currentId = "sec-basic";
    sections.forEach(sec => {
        if (document.querySelector('.editor-main').scrollTop >= sec.offsetTop - 120) {
            currentId = sec.id;
        }
    });

    navItems.forEach(item => {
        item.classList.toggle('active', item.getAttribute('href') === `#${currentId}`);
    });
});
