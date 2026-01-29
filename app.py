import os
import json
import sys
import subprocess
import threading
import time
import tempfile
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app, resources={r"/*": {"origins": "*"}})
# Use threading mode for maximum compatibility on Python 3.13 / Windows
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', logger=True, engineio_logger=True)

# Store active sessions
active_sessions = {}

# Language configurations for local execution
# Resolve real path for Python to avoid Windows App Execution Alias issues
REAL_PYTHON = os.path.realpath(sys.executable)

LANGUAGE_CONFIG = {
    "python": {
        "compile": None,
        "run": [REAL_PYTHON, "-u", "{file}"],
        "ext": ".py"
    },
    "c": {
        "compile": ["gcc", "-o", "{output}", "{file}"],
        "run": ["{output}"],
        "ext": ".c"
    },
    "cpp": {
        "compile": ["g++", "-o", "{output}", "{file}"],
        "run": ["{output}"],
        "ext": ".cpp"
    },
    "java": {
        "compile": ["javac", "{file}"],
        "run": ["java", "{classname}"],
        "ext": ".java",
        "main_file": "Main.java"
    },
    "csharp": {
        "compile": [r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe", "/out:{output}", "{file}"],
        "run": ["{output}"],
        "ext": ".cs"
    }
}

@app.route("/")
def index():
    response = app.send_static_file("index.html")
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route("/<path:path>")
def serve_static(path):
    response = app.send_static_file(path)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route("/problems")
def get_problems():
    try:
        with open("problems.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')
    emit('connected', {'status': 'ready'})

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected: {request.sid}')
    cleanup_session(request.sid)

# C code to disable buffering
FLUSH_INIT_C = r"""
#include <stdio.h>
#include <stdlib.h>

#ifdef _WIN32
#include <windows.h>
#endif

void __attribute__((constructor)) flush_init() {
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);
}
"""

# C++ code to disable buffering
FLUSH_INIT_CPP = r"""
#include <iostream>
#include <stdio.h>

class FlushInit {
public:
    FlushInit() {
        std::setvbuf(stdout, NULL, _IONBF, 0);
        std::setvbuf(stderr, NULL, _IONBF, 0);
        std::cout.setf(std::ios::unitbuf);
        std::cerr.setf(std::ios::unitbuf);
    }
};

static FlushInit flush_init_obj;
"""

@socketio.on('start_session')
def handle_start_session(data):
    session_id = request.sid
    language = data.get('language')
    code = data.get('code')
    
    print(f'Starting session {session_id} for language {language}')
    
    # Cleanup any existing session
    cleanup_session(session_id)
    
    try:
        # Create temp directory for this session
        config = LANGUAGE_CONFIG.get(language)
        if not config:
            emit('error', {'message': f'Unsupported language: {language}'})
            return
        
         # Use a local temp directory to avoid path/permission issues on Windows
        base_temp = os.path.join(os.getcwd(), "temp_sessions")
        if not os.path.exists(base_temp):
            os.makedirs(base_temp)
            
        temp_dir = tempfile.mkdtemp(dir=base_temp)
        ext = config['ext']
        
        # Java needs specific filename
        filename = config.get('main_file', f"code{ext}")
        code_file = os.path.join(temp_dir, filename)
        
        with open(code_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        # Compile if needed
        if config['compile']:
            output_file = os.path.join(temp_dir, "program.exe" if os.name == 'nt' else "program")
            
            # Prepare compilation command
            compile_cmd_template = config['compile']
            compile_files = [code_file]
            
            # Inject flushing code for C/C++
            if language == 'c':
                flush_file = os.path.join(temp_dir, "flush_init.c")
                with open(flush_file, 'w', encoding='utf-8') as f:
                    f.write(FLUSH_INIT_C)
                compile_files.append(flush_file)
            elif language == 'cpp':
                flush_file = os.path.join(temp_dir, "flush_init.cpp")
                with open(flush_file, 'w', encoding='utf-8') as f:
                    f.write(FLUSH_INIT_CPP)
                compile_files.append(flush_file)
            
            # Construct the compile command
            # The template usually looks like ["gcc", "-o", "{output}", "{file}"]
            # We need to replace "{file}" with all source files
            
            # Simplistic approach: replace "{file}" in the template with the primary file,
            # and append the extra files to the end of the command (before -o if possible, or just append)
            # GCC/G++ allows input files anywhere.
            
            final_compile_cmd = []
            for arg in compile_cmd_template:
                if "{file}" in arg:
                    # Replace {file} with the main code file
                    final_compile_cmd.append(arg.format(file=code_file, output=output_file))
                elif "{output}" in arg:
                    final_compile_cmd.append(arg.format(output=output_file))
                else:
                    final_compile_cmd.append(arg)
            
            # Append extra source files (flushing logic)
            # We skip the first file in compile_files because it was likely handled by {file} replacement
            # actually we should be careful. let's just append the extra files to the command list.
            for extra_file in compile_files[1:]:
                final_compile_cmd.append(extra_file)

            try:
                compile_result = subprocess.run(
                    final_compile_cmd,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if compile_result.returncode != 0:
                    emit('error', {'message': f'Compilation error:\n{compile_result.stderr}'})
                    cleanup_session(session_id)
                    return
                
                # For compiled languages, classname/classname might still be needed (e.g. Java)
                classname = "Main" if language == "java" else None
                run_cmd = [cmd.format(output=output_file, classname=classname) for cmd in config['run']]
            except FileNotFoundError:
                emit('error', {'message': f'System error: Compiler not found for {language}. Please install it to run code locally.'})
                cleanup_session(session_id)
                return
        else:
            # For interpreted languages
            run_cmd = [cmd.format(file=code_file, project_dir=temp_dir) for cmd in config['run']]
            
        print(f"Executing: {' '.join(run_cmd)}")
        # Send the command to the terminal so user knows what's happening
        emit('output', {'data': f"\r\n[Lệnh chạy]: {' '.join(run_cmd)}\r\n\r\n", 'session_id': session_id})
        
        # Start the process - Redirect stderr to stdout to see all errors
        process = subprocess.Popen(
            run_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=False, # Use binary mode for unbuffered I/O
            bufsize=0,  # Unbuffered
            cwd=temp_dir
        )
        
        # Store session info
        active_sessions[session_id] = {
            'process': process,
            'temp_dir': temp_dir,
            'language': language
        }
        
        # Start threads to read output
        stdout_thread = threading.Thread(target=read_output, args=(session_id, process.stdout, 'stdout'), daemon=True)
        stdout_thread.start()
        
        # Store thread in session so we can join it later
        active_sessions[session_id]['stdout_thread'] = stdout_thread
        
        # threading.Thread(target=read_output, args=(session_id, process.stderr, 'stderr'), daemon=True).start() # Stderr is redirected to stdout
        threading.Thread(target=monitor_process, args=(session_id,), daemon=True).start()
        
        emit('session_started', {'status': 'running'})
        
    except Exception as e:
        print(f'Error starting session: {e}')
        emit('error', {'message': f'Error: {str(e)}'})
        cleanup_session(session_id)

@socketio.on('send_input')
def handle_input(data):
    session_id = request.sid
    user_input = data.get('input', '')
    
    session = active_sessions.get(session_id)
    if not session:
        emit('error', {'message': 'No active session'})
        return
    
    process = session['process']
    
    try:
        if process.poll() is None:  # Process still running
            # Encode input for binary mode
            process.stdin.write((user_input + '\n').encode('utf-8'))
            process.stdin.flush()
    except Exception as e:
        print(f'Error sending input: {e}')
        emit('error', {'message': f'Error sending input: {str(e)}'})

@socketio.on('run_test_cases')
def handle_run_test_cases(data):
    session_id = request.sid
    language = data.get('language')
    code = data.get('code')
    test_cases = data.get('test_cases', [])
    
    print(f'Running test cases for session {session_id}, language {language}')
    
    # Create temp directory
    # Use a local temp directory to avoid path/permission issues on Windows
    # We use a new temp dir per test run to keep things clean
    base_temp = os.path.join(os.getcwd(), "temp_sessions")
    if not os.path.exists(base_temp):
        os.makedirs(base_temp)
    temp_dir = tempfile.mkdtemp(dir=base_temp)
    
    try:
        config = LANGUAGE_CONFIG.get(language)
        if not config:
            emit('error', {'message': f'Unsupported language: {language}'})
            return

        ext = config['ext']
        filename = config.get('main_file', f"code{ext}")
        code_file = os.path.join(temp_dir, filename)
        
        with open(code_file, 'w', encoding='utf-8') as f:
            f.write(code)
            
        # Compile ONCE
        exe_path = None
        run_cmd_template = config['run']
        
        if config['compile']:
            output_file = os.path.join(temp_dir, "program.exe" if os.name == 'nt' else "program")
            
            # Re-use the compilation logic from start_session (checking for injection)
            compile_cmd_template = config['compile']
            compile_files = [code_file]
            
            if language == 'c':
                flush_file = os.path.join(temp_dir, "flush_init.c")
                with open(flush_file, 'w', encoding='utf-8') as f:
                    f.write(FLUSH_INIT_C)
                compile_files.append(flush_file)
            elif language == 'cpp':
                flush_file = os.path.join(temp_dir, "flush_init.cpp")
                with open(flush_file, 'w', encoding='utf-8') as f:
                    f.write(FLUSH_INIT_CPP)
                compile_files.append(flush_file)
            
            final_compile_cmd = []
            for arg in compile_cmd_template:
                if "{file}" in arg:
                    final_compile_cmd.append(arg.format(file=code_file, output=output_file))
                elif "{output}" in arg:
                    final_compile_cmd.append(arg.format(output=output_file))
                else:
                    final_compile_cmd.append(arg)
            for extra_file in compile_files[1:]:
                final_compile_cmd.append(extra_file)

            try:
                compile_result = subprocess.run(
                    final_compile_cmd,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if compile_result.returncode != 0:
                    emit('test_results', {'error': f'Compilation error:\n{compile_result.stderr}'})
                    return
                exe_path = output_file
            except Exception as e:
                emit('test_results', {'error': f'Compilation failed: {str(e)}'})
                return
        
        # Prepare run command
        if exe_path:
             # For compiled
            classname = "Main" if language == "java" else None
            run_cmd = [cmd.format(output=exe_path, classname=classname) for cmd in run_cmd_template]
        else:
             # For interpreted
            run_cmd = [cmd.format(file=code_file, project_dir=temp_dir) for cmd in run_cmd_template]

        results = []
        
        for i, case in enumerate(test_cases):
            case_input = case.get('input', '')
            case_expected = case.get('output', '')
            
            try:
                # Use binary mode (text=False) for consistent behavior with our fix
                process = subprocess.Popen(
                    run_cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=False,
                    bufsize=0,
                    cwd=temp_dir
                )
                
                try:
                    stdout_data, _ = process.communicate(input=(case_input + '\n').encode('utf-8'), timeout=5)
                    actual_output = stdout_data.decode('utf-8', errors='replace')
                except subprocess.TimeoutExpired:
                    process.kill()
                    actual_output = "Error: Timeout (5s)"
                
                # Normalize text for comparison (ignore trailing whitespace/newlines differences)
                passed = normalize_text(actual_output) == normalize_text(case_expected)
                
                # Check if actual output merely CONTAINS the expected output (sometimes prompts are included)
                # But for competitive programming style, typically we want clean output.
                # However, since we forced prompts to appear immediateley, they are part of stdout.
                # If the problem asks for "Sum: 8", but user prints "Input a: Input b: Sum: 8", we might need smarter matching.
                # For now, let's try strict normalization, but maybe strip prompts if we could identify them?
                # Actually, standard CP problems usually don't print prompts like "Input a:". 
                # But this is a learning app. Users write prompts.
                # Let's trust the logic: existing test cases in problems.json for "A+B" only show numbers.
                # If the user code prints prompts, it will fail current test cases. 
                # We should probably modify the usage instructions or the test cases to include prompts?
                # Or invalid solution?
                # Let's stick to standard strict comparison for now.
                
                results.append({
                    'input': case_input,
                    'expected': case_expected,
                    'actual': actual_output,
                    'passed': passed
                })
                
            except Exception as e:
                 results.append({
                    'input': case_input,
                    'expected': case_expected,
                    'actual': f"Error: {str(e)}",
                    'passed': False
                })

        emit('test_results', {'results': results})

    except Exception as e:
        print(f"Error in run_test_cases: {e}")
        emit('test_results', {'error': str(e)})
        
    finally:
        # Cleanup
        try:
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except:
            pass

def normalize_text(text):
    """Normalize text for comparison: strip whitespace, unify newlines"""
    if not text: return ""
    return "\n".join([line.rstrip() for line in text.strip().splitlines() if line.strip()])


@socketio.on('stop_session')
def handle_stop_session():
    session_id = request.sid
    cleanup_session(session_id)
    emit('session_ended', {'reason': 'stopped by user'})

def read_output(session_id, stream, stream_type):
    """Read output from process and emit to client"""
    try:
        # Read character by character for a more interactive feel
        while True:
            # Read bytes in binary mode
            byte = stream.read(1)
            if not byte:
                break
            
            # Note: We removed the check 'if session_id not in active_sessions'
            # to ensure we finish reading the stream even if cleanup has started,
            # provided the stream is still open and yielding data.
            
            # Decode byte to string
            try:
                char = byte.decode('utf-8', errors='replace')
            except:
                char = '?'
                
            socketio.emit('output', {
                'data': char,
                'type': stream_type
            }, room=session_id)
    except Exception as e:
        print(f'Error reading {stream_type}: {e}')
    finally:
        stream.close()

def monitor_process(session_id):
    """Monitor process and cleanup when it exits"""
    session = active_sessions.get(session_id)
    if not session:
        return
    
    process = session['process']
    stdout_thread = session.get('stdout_thread')
    
    try:
        # Wait for process to complete (with timeout)
        process.wait(timeout=60)
        
        # After process finishes, wait for the output reader to finish flushing
        if stdout_thread and stdout_thread.is_alive():
            stdout_thread.join(timeout=2)
            
    except subprocess.TimeoutExpired:
        print(f'Process timeout for session {session_id}')
        process.kill()
        socketio.emit('error', {
            'message': 'Process timeout (60s limit)'
        }, room=session_id)
    
    # Emit session ended
    socketio.emit('session_ended', {
        'reason': 'process completed',
        'exit_code': process.returncode
    }, room=session_id)
    
    # Cleanup
    cleanup_session(session_id)

def cleanup_session(session_id):
    """Clean up session resources"""
    session = active_sessions.pop(session_id, None)
    if not session:
        return
    
    process = session['process']
    temp_dir = session['temp_dir']
    
    # Kill process if still running
    if process.poll() is None:
        try:
            process.kill()
            process.wait(timeout=5)
        except:
            pass
    
    # Clean up temp directory
    try:
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    except Exception as e:
        print(f'Error cleaning up temp dir: {e}')


def cleanup_dangling_temps():
    """Clean up any dangling temporary directories from previous runs"""
    try:
        current_dir = os.getcwd()
        # Clean up temp_sessions directory content but keep the directory
        temp_sessions = os.path.join(current_dir, "temp_sessions")
        if os.path.exists(temp_sessions):
            try:
                import shutil
                shutil.rmtree(temp_sessions)
                os.makedirs(temp_sessions)
                print("Cleaned up temp_sessions directory")
            except Exception as e:
                print(f"Warning: Could not clean temp_sessions: {e}")

        # Clean up legacy temp_* directories in root
        for name in os.listdir(current_dir):
            if name.startswith("temp_") and os.path.isdir(os.path.join(current_dir, name)):
                if name == "temp_sessions": continue
                try:
                    import shutil
                    shutil.rmtree(os.path.join(current_dir, name))
                    print(f"Removed dangling temp dir: {name}")
                except Exception as e:
                    print(f"Warning: Could not remove {name}: {e}")
    except Exception as e:
        print(f"Error during cleanup: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("Server starting on http://localhost:5001")
    print("Python version:", os.sys.version)
    print("Async mode: threading")
    
    # Clean up temp files on startup
    cleanup_dangling_temps()
    
    print("=" * 50)
    
    socketio.run(app, host='0.0.0.0', port=5001, debug=True, use_reloader=False)
