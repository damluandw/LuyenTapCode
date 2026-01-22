import os
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

PISTON_API_URL = "https://emkc.org/api/v2/piston/execute"

# Language mapping for Piston API
LANGUAGE_MAP = {
    "python": {"language": "python", "version": "*"},
    "c": {"language": "c", "version": "*"},
    "cpp": {"language": "cpp", "version": "*"},
    "java": {"language": "java", "version": "*"},
    "csharp": {"language": "csharp", "version": "*"}
}

@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/<path:path>")
def serve_static(path):
    return app.send_static_file(path)

@app.route("/problems")
def get_problems():
    try:
        with open("problems.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def run_code_online(language, code, input_data=""):
    lang_info = LANGUAGE_MAP.get(language)
    if not lang_info:
        return "", f"Unsupported language: {language}"

    payload = {
        "language": lang_info["language"],
        "version": lang_info["version"],
        "files": [{"content": code}],
        "stdin": input_data
    }

    try:
        print(f"Sending request to Piston: {language}")
        response = requests.post(PISTON_API_URL, json=payload, timeout=10)
        print(f"Piston Status Code: {response.status_code}")
        
        if response.status_code != 200:
            return "", f"API Error: {response.text}"
            
        data = response.json()
        run = data.get("run", {})
        stdout = run.get("stdout", "")
        stderr = run.get("stderr", "")
        
        if stderr:
            print(f"Piston Stderr: {stderr}")
            
        return stdout, stderr
    except Exception as e:
        print(f"Piston Exception: {str(e)}")
        return "", f"Piston API Error: {str(e)}"

@app.route("/execute", methods=["POST"])
def execute():
    data = request.json
    language = data.get("language")
    code = data.get("code")
    test_cases = data.get("test_cases", [])
    
    results = []
    for tc in test_cases:
        actual_output, error = run_code_online(language, code, tc.get("input", ""))
        
        passed = False
        if not error:
            actual_clean = " ".join(actual_output.split())
            expected_clean = " ".join(tc.get("output", "").split())
            passed = actual_clean == expected_clean
            
        results.append({
            "input": tc.get("input"),
            "expected": tc.get("output"),
            "actual": actual_output,
            "error": error,
            "passed": passed
        })
        
    return jsonify({"results": results})

@app.route("/execute_console", methods=["POST"])
def execute_console():
    data = request.json
    language = data.get("language")
    main_code = data.get("code", "")
    console_command = data.get("command", "")
    stdin_data = data.get("stdin", "") # New: check for explicit stdin
    
    # Combine code. For Python, we can just append. 
    # For C/C++/Java/C#, it's trickier but we'll try to append it after the main code.
    # Note: This is an approximation of stateful execution.
    if language == "python":
        combined_code = f"{main_code}\n\n{console_command}"
    else:
        # For compiled languages, we assume the console_command might be a full snippet 
        # or we just try to run it. For now, we'll just append it to the end.
        combined_code = f"{main_code}\n{console_command}"
        
    actual_output, error = run_code_online(language, combined_code, stdin_data)
    
    return jsonify({
        "output": actual_output,
        "error": error
    })

if __name__ == "__main__":
    app.run(port=5000, debug=True)
