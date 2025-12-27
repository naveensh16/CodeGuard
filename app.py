from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
import os
import jwt
import datetime
from functools import wraps
import json
import subprocess
import tempfile
import ollama
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-this')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///codeguard.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Ollama Configuration
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama2')  # Default model
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')

ALLOWED_EXTENSIONS = {'py', 'java', 'js', 'jsx', 'ts', 'tsx', 'cpp', 'c', 'h', 'hpp', 'cs', 'go', 'rb', 'php', 'swift', 'kt', 'rs', 'scala', 'r', 'sql', 'sh', 'bat', 'ps1', 'html', 'css', 'xml', 'json', 'yaml', 'yml'}

# Comprehensive language configuration
LANGUAGE_CONFIGS = {
    'python': {'name': 'Python', 'compilers': ['python'], 'linters': ['pylint', 'flake8']},
    'java': {'name': 'Java', 'compilers': ['javac'], 'linters': ['checkstyle']},
    'javascript': {'name': 'JavaScript', 'compilers': ['node'], 'linters': ['eslint']},
    'typescript': {'name': 'TypeScript', 'compilers': ['tsc'], 'linters': ['eslint']},
    'cpp': {'name': 'C++', 'compilers': ['g++', 'clang++'], 'linters': ['cppcheck']},
    'c': {'name': 'C', 'compilers': ['gcc', 'clang'], 'linters': ['cppcheck']},
    'csharp': {'name': 'C#', 'compilers': ['csc'], 'linters': ['roslyn']},
    'go': {'name': 'Go', 'compilers': ['go'], 'linters': ['golint']},
    'ruby': {'name': 'Ruby', 'compilers': ['ruby'], 'linters': ['rubocop']},
    'php': {'name': 'PHP', 'compilers': ['php'], 'linters': ['phpcs']},
    'swift': {'name': 'Swift', 'compilers': ['swiftc'], 'linters': []},
    'kotlin': {'name': 'Kotlin', 'compilers': ['kotlinc'], 'linters': []},
    'rust': {'name': 'Rust', 'compilers': ['rustc'], 'linters': ['clippy']},
    'scala': {'name': 'Scala', 'compilers': ['scalac'], 'linters': []},
    'r': {'name': 'R', 'compilers': ['Rscript'], 'linters': []},
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='developer')  # developer, admin, reviewer
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    projects = db.relationship('Project', backref='owner', lazy=True)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    files = db.relationship('CodeFile', backref='project', lazy=True, cascade='all, delete-orphan')

class CodeFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    language = db.Column(db.String(50))
    content = db.Column(db.Text)
    analyzed = db.Column(db.Boolean, default=False)  # Track if analysis is complete
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    issues = db.relationship('Issue', backref='code_file', lazy=True, cascade='all, delete-orphan')

class Issue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('code_file.id'), nullable=False)
    issue_type = db.Column(db.String(50))  # security, quality, style, performance
    severity = db.Column(db.String(20))  # critical, high, medium, low
    line_number = db.Column(db.Integer)
    message = db.Column(db.Text)
    suggestion = db.Column(db.Text)
    fixed_code = db.Column(db.Text)  # AI-generated fix
    source = db.Column(db.String(50))  # static_analysis, ai
    status = db.Column(db.String(20), default='open')  # open, resolved, ignored
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# Authentication Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Static Analysis Functions
def run_pylint_analysis(filepath):
    """Run Pylint static analysis on Python files"""
    issues = []
    try:
        result = subprocess.run(
            ['pylint', filepath, '--output-format=json'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.stdout:
            pylint_results = json.loads(result.stdout)
            for item in pylint_results:
                issues.append({
                    'issue_type': item.get('type', 'quality'),
                    'severity': map_pylint_severity(item.get('type')),
                    'line_number': item.get('line', 0),
                    'message': item.get('message', ''),
                    'suggestion': f"Check: {item.get('symbol', '')}",
                    'source': 'pylint'
                })
    except Exception as e:
        print(f"Pylint analysis error: {e}")
    
    return issues

def map_pylint_severity(msg_type):
    """Map Pylint message types to severity levels"""
    mapping = {
        'error': 'critical',
        'fatal': 'critical',
        'warning': 'high',
        'refactor': 'medium',
        'convention': 'low',
        'info': 'low'
    }
    return mapping.get(msg_type, 'medium')

def run_java_compilation_check(filepath, content):
    """Check Java file for compilation errors"""
    issues = []
    try:
        # Try to compile the Java file
        result = subprocess.run(
            ['javac', '-Xlint:all', filepath],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Parse compilation errors
        if result.returncode != 0:
            error_output = result.stderr
            for line in error_output.split('\n'):
                if filepath in line or '.java:' in line:
                    # Parse error format: filename.java:line: error: message
                    parts = line.split(':')
                    if len(parts) >= 3:
                        try:
                            line_num = int(parts[1])
                            error_type = parts[2].strip()
                            message = ':'.join(parts[3:]).strip() if len(parts) > 3 else error_type
                            
                            issues.append({
                                'issue_type': 'syntax',
                                'severity': 'critical',
                                'line_number': line_num,
                                'message': f'Compilation error: {message}',
                                'suggestion': 'Fix syntax error to allow compilation',
                                'source': 'javac'
                            })
                        except (ValueError, IndexError):
                            pass
        
        # Clean up compiled class file if it exists
        class_file = filepath.replace('.java', '.class')
        if os.path.exists(class_file):
            os.remove(class_file)
            
    except FileNotFoundError:
        print("Java compiler (javac) not found. Install JDK for Java analysis.")
    except Exception as e:
        print(f"Java compilation check error: {e}")
    
    return issues

def analyze_javascript_bugs(content, lines):
    """Dedicated analyzer for JavaScript/TypeScript async and closure bugs"""
    issues = []
    
    for line_num, line in enumerate(lines, 1):
        line_stripped = line.strip()
        
        # 1. Missing await on .json(), .text(), .blob()
        if 'response.json()' in line or 'response.text()' in line or 'response.blob()' in line:
            if 'await' not in line:
                issues.append({
                    'issue_type': 'async',
                    'severity': 'critical',
                    'line_number': line_num,
                    'message': 'Missing await on Promise - response.json() returns a Promise',
                    'suggestion': 'Add await before response.json()',
                    'fixed_code': line.replace('response.json()', 'await response.json()').replace('response.text()', 'await response.text()').strip(),
                    'source': 'js_analyzer'
                })
        
        # 2. var in for loops (closure bug)
        if 'for' in line and 'var ' in line and ('i = 0' in line or 'j = 0' in line):
            # Check if setTimeout/setInterval exists in nearby lines
            context_start = max(0, line_num - 1)
            context_end = min(len(lines), line_num + 15)
            context = '\n'.join(lines[context_start:context_end])
            
            if 'setTimeout' in context or 'setInterval' in context or 'async' in context:
                issues.append({
                    'issue_type': 'closure',
                    'severity': 'critical',
                    'line_number': line_num,
                    'message': 'Closure bug: var in loop with async/setTimeout causes wrong variable capture',
                    'suggestion': 'Replace var with let or const to fix closure scope',
                    'fixed_code': line.replace('var ', 'let ').strip(),
                    'source': 'js_analyzer'
                })
        
        # 3. Async function but returning before completion
        if 'setTimeout' in line and 'async function' in line:
            issues.append({
                'issue_type': 'async',
                'severity': 'high',
                'line_number': line_num,
                'message': 'Anti-pattern: setTimeout with async function - timing issues likely',
                'suggestion': 'Remove setTimeout and use await, or use Promise.all()',
                'source': 'js_analyzer'
            })
        
        # 4. Function returns value but has async operations
        if line_stripped.startswith('return ') and 'results' in line:
            # Check if there's setTimeout/async in previous lines
            prev_context = '\n'.join(lines[max(0, line_num-10):line_num])
            if 'setTimeout' in prev_context or 'setInterval' in prev_context:
                issues.append({
                    'issue_type': 'async',
                    'severity': 'critical',
                    'line_number': line_num,
                    'message': 'Function returns before async operations complete - will return empty/incomplete data',
                    'suggestion': 'Use async/await pattern or return Promise',
                    'source': 'js_analyzer'
                })
    
    return issues

def analyze_cpp_bugs(content, lines):
    """Comprehensive C/C++ analyzer for memory, concurrency, and design defects"""
    issues = []
    total_lines = len(lines)

    # Track class info for design pattern analysis
    class_info = {}
    current_class = None
    has_virtual_destructor = {}
    has_manual_memory = {}
    
    for line_num, line in enumerate(lines, 1):
        line_stripped = line.strip()

        # Track class definitions
        if line_stripped.startswith('class ') and '{' in line:
            class_name = line_stripped.split()[1].rstrip(':').rstrip('{')
            current_class = class_name
            class_info[class_name] = {'start': line_num, 'has_virtual': False, 'has_manual_mem': False}
        
        # Track virtual functions
        if current_class and 'virtual ' in line:
            class_info[current_class]['has_virtual'] = True
        
        # Check for non-virtual destructor in polymorphic class
        if current_class and line_stripped.startswith('~') and 'virtual' not in line:
            # Check if class has virtual methods (is polymorphic)
            if class_info.get(current_class, {}).get('has_virtual', False):
                issues.append({
                    'issue_type': 'design',
                    'severity': 'critical',
                    'line_number': line_num,
                    'message': 'Non-virtual destructor in polymorphic class causes undefined behavior',
                    'suggestion': 'Make destructor virtual: virtual ~ClassName()',
                    'fixed_code': line.replace('~', 'virtual ~').strip(),
                    'source': 'cpp_analyzer'
                })

        # Manual memory management (new/new[])
        if 'new ' in line or 'new[' in line:
            if current_class:
                class_info[current_class]['has_manual_mem'] = True
            issues.append({
                'issue_type': 'memory',
                'severity': 'high',
                'line_number': line_num,
                'message': 'Manual memory allocation - prefer RAII with smart pointers',
                'suggestion': 'Use std::unique_ptr or std::shared_ptr instead of raw new',
                'source': 'cpp_analyzer'
            })

        # Dangling pointer: taking address of stack variable
        if 'push_back(&' in line or 'emplace_back(&' in line:
            issues.append({
                'issue_type': 'memory',
                'severity': 'critical',
                'line_number': line_num,
                'message': 'Dangling pointer: storing address of stack object causes use-after-free',
                'suggestion': 'Store by value or use heap allocation with smart pointers',
                'source': 'cpp_analyzer'
            })

        # Off-by-one: loop with <= size()
        if 'for' in line and '.size()' in line and '<=' in line:
            issues.append({
                'issue_type': 'logic',
                'severity': 'critical',
                'line_number': line_num,
                'message': 'Off-by-one error: loop <= size() causes out-of-bounds access',
                'suggestion': 'Use < container.size() for valid indices (0 to size-1)',
                'fixed_code': line.replace('<=', '<').strip(),
                'source': 'cpp_analyzer'
            })

        # Data race: unprotected access to shared container
        if ('map<' in line or 'vector<' in line or 'unordered_map<' in line) and '&' in line:
            # Check if this is shared between threads
            context = '\n'.join(lines[line_num:min(line_num+20, len(lines))])
            if 'thread' in context and 'lock_guard' not in context:
                issues.append({
                    'issue_type': 'concurrency',
                    'severity': 'critical',
                    'line_number': line_num,
                    'message': 'Data race: shared container accessed by multiple threads without synchronization',
                    'suggestion': 'Protect with mutex or use thread-safe data structures',
                    'source': 'cpp_analyzer'
                })

        # Iterator invalidation with erase
        if '.erase(' in line and 'it' in line:
            issues.append({
                'issue_type': 'logic',
                'severity': 'critical',
                'line_number': line_num,
                'message': 'Iterator invalidation: erasing invalidates current iterator',
                'suggestion': 'Use it = container.erase(it); or erase-remove idiom',
                'source': 'cpp_analyzer'
            })

        # Raw delete on element (double-free risk)
        if 'delete ' in line and ('[' in line or '->' in line):
            issues.append({
                'issue_type': 'memory',
                'severity': 'high',
                'line_number': line_num,
                'message': 'Deleting element with unclear ownership - risk of double-free',
                'suggestion': 'Use smart pointers to manage ownership automatically',
                'source': 'cpp_analyzer'
            })

        # Detached thread with lambda capture
        if 'detach()' in line:
            prev_context = '\n'.join(lines[max(0, line_num-8):line_num])
            if '[&]' in prev_context:
                issues.append({
                    'issue_type': 'concurrency',
                    'severity': 'critical',
                    'line_number': line_num,
                    'message': 'Detached thread captures by reference - causes dangling references and crashes',
                    'suggestion': 'Join threads or capture by value with proper lifetime',
                    'source': 'cpp_analyzer'
                })

        # Busy-wait spin loop
        if 'while' in line and '.load()' in line and '{}' in line:
            issues.append({
                'issue_type': 'performance',
                'severity': 'medium',
                'line_number': line_num,
                'message': 'Busy-wait spin loop wastes CPU cycles',
                'suggestion': 'Use std::condition_variable for efficient waiting',
                'source': 'cpp_analyzer'
            })

        # Multiple lock acquisition (deadlock risk)
        if 'lock_guard' in line:
            # Check for second lock in nearby lines
            context_window = '\n'.join(lines[line_num:min(line_num+10, len(lines))])
            if context_window.count('lock_guard') > 1:
                issues.append({
                    'issue_type': 'concurrency',
                    'severity': 'high',
                    'line_number': line_num,
                    'message': 'Multiple locks acquired - potential deadlock if order inconsistent',
                    'suggestion': 'Use std::scoped_lock or std::lock with adoption',
                    'source': 'cpp_analyzer'
                })

        # Capture iterator by reference in lambda
        if 'thread' in line or 'async' in line:
            next_lines = '\n'.join(lines[line_num:min(line_num+5, len(lines))])
            if '[&]' in next_lines and '->second' in next_lines:
                issues.append({
                    'issue_type': 'concurrency',
                    'severity': 'critical',
                    'line_number': line_num,
                    'message': 'Lambda captures iterator by reference - iterator invalidates before execution',
                    'suggestion': 'Capture necessary values explicitly, not references',
                    'source': 'cpp_analyzer'
                })

    # Check for Rule of 5 violations
    for class_name, info in class_info.items():
        if info.get('has_manual_mem'):
            issues.append({
                'issue_type': 'design',
                'severity': 'high',
                'line_number': info['start'],
                'message': f'Class {class_name} manages memory but may lack Rule of 5 special members',
                'suggestion': 'Implement copy constructor, copy assignment, move constructor, move assignment, and destructor',
                'source': 'cpp_analyzer'
            })

    return issues

def analyze_python_bugs(content, lines):
    """Comprehensive Python analyzer for security, resource management, and common bugs"""
    issues = []
    
    for line_num, line in enumerate(lines, 1):
        line_stripped = line.strip()
        
        # SQL Injection vulnerabilities
        if ('execute(' in line or 'executemany(' in line) and (f'f"' in line or "f'" in line or '%' in line or '+' in line):
            if 'SELECT' in line.upper() or 'INSERT' in line.upper() or 'UPDATE' in line.upper() or 'DELETE' in line.upper():
                issues.append({
                    'issue_type': 'security',
                    'severity': 'critical',
                    'line_number': line_num,
                    'message': 'SQL Injection vulnerability: string formatting in SQL query',
                    'suggestion': 'Use parameterized queries with ? or %s placeholders',
                    'fixed_code': 'cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))',
                    'source': 'python_analyzer'
                })
        
        # Hardcoded credentials
        if any(keyword in line.lower() for keyword in ['password', 'api_key', 'secret', 'token', 'apikey']):
            if '=' in line and ('"' in line or "'" in line):
                if not line_stripped.startswith('#'):
                    issues.append({
                        'issue_type': 'security',
                        'severity': 'critical',
                        'line_number': line_num,
                        'message': 'Hardcoded credentials detected - security risk',
                        'suggestion': 'Use environment variables or secure vault (os.getenv, config files)',
                        'source': 'python_analyzer'
                    })
        
        # Unclosed file handles
        if 'open(' in line and 'with' not in line:
            issues.append({
                'issue_type': 'resource',
                'severity': 'high',
                'line_number': line_num,
                'message': 'File opened without context manager - resource leak risk',
                'suggestion': 'Use "with open(...) as f:" to ensure file is closed',
                'fixed_code': 'with open(filename, "r") as f:',
                'source': 'python_analyzer'
            })
        
        # ThreadPoolExecutor without context manager
        if 'ThreadPoolExecutor(' in line and 'with' not in line:
            issues.append({
                'issue_type': 'resource',
                'severity': 'high',
                'line_number': line_num,
                'message': 'ThreadPoolExecutor created without context manager - resource leak',
                'suggestion': 'Use "with ThreadPoolExecutor(...) as executor:" or ensure shutdown() is called',
                'fixed_code': 'with ThreadPoolExecutor(max_workers=4) as executor:',
                'source': 'python_analyzer'
            })
        
        # asyncio.new_event_loop() in non-main thread (dangerous)
        if 'asyncio.new_event_loop()' in line or 'new_event_loop(' in line:
            issues.append({
                'issue_type': 'concurrency',
                'severity': 'high',
                'line_number': line_num,
                'message': 'Creating new event loop can cause issues in threads',
                'suggestion': 'Use asyncio.run() or ensure proper event loop management',
                'source': 'python_analyzer'
            })
        
        # Global mutable dictionary/list (shared state)
        if line_stripped.startswith(tuple(chr(c) for c in range(ord('A'), ord('Z')+1))) and '=' in line:
            if any(pattern in line for pattern in ['{}', '[]', 'dict(', 'list(', 'set(']):
                issues.append({
                    'issue_type': 'concurrency',
                    'severity': 'high',
                    'line_number': line_num,
                    'message': 'Global mutable state detected - consider encapsulating or using thread-safe design',
                    'suggestion': 'Wrap global state access with locks or move into TaskManager class with synchronization',
                    'source': 'python_analyzer'
                })

        # Reinitializing ThreadPoolExecutor after shutdown (resource churn)
        if 'ThreadPoolExecutor' in line and '=' in line and line.strip().startswith('self.executor'):
            # Look back few lines for shutdown
            context_prev = '\n'.join(lines[max(0, line_num-5):line_num])
            if 'self.executor.shutdown' in context_prev:
                issues.append({
                    'issue_type': 'resource',
                    'severity': 'medium',
                    'line_number': line_num,
                    'message': 'ThreadPoolExecutor is recreated after shutdown without protective locking',
                    'suggestion': 'Create executors inside context manager or guard reinitialization with lock',
                    'source': 'python_analyzer'
                })

        # Iterating shared list without copy/lock
        if 'for' in line and 'self.tasks' in line and 'list(self.tasks)' in line:
            issues.append({
                'issue_type': 'concurrency',
                'severity': 'medium',
                'line_number': line_num,
                'message': 'Concurrent iteration over shared task list without lock',
                'suggestion': 'Protect iteration with lock or use copy guarded by synchronization',
                'source': 'python_analyzer'
            })
        
        # Global variable modification without lock
        if line_stripped.startswith('GLOBAL_') and '=' in line:
            # Check if lock is acquired in context
            context_before = '\n'.join(lines[max(0, line_num-5):line_num])
            if 'with lock' not in context_before and 'lock.acquire' not in context_before:
                issues.append({
                    'issue_type': 'concurrency',
                    'severity': 'critical',
                    'line_number': line_num,
                    'message': 'Global variable modified without lock - data race',
                    'suggestion': 'Acquire lock before modifying shared data: with lock:',
                    'source': 'python_analyzer'
                })
        
        # Dict/List access without lock when global
        if ('GLOBAL_' in line or 'shared_' in line.lower()) and any(op in line for op in ['.get(', '[', '.pop(', '.append(', 'del ']):
            context_before = '\n'.join(lines[max(0, line_num-5):line_num])
            if 'with lock' not in context_before:
                issues.append({
                    'issue_type': 'concurrency',
                    'severity': 'high',
                    'line_number': line_num,
                    'message': 'Shared data structure accessed without synchronization',
                    'suggestion': 'Protect access with lock or use thread-safe data structures',
                    'source': 'python_analyzer'
                })
        
        # list() or dict() on shared data (shallow copy race condition)
        if ('list(' in line or 'dict(' in line) and any(var in line for var in ['self.', 'GLOBAL_', 'shared_']):
            issues.append({
                'issue_type': 'concurrency',
                'severity': 'medium',
                'line_number': line_num,
                'message': 'Shallow copy of shared data - potential race condition',
                'suggestion': 'Use copy.deepcopy() or acquire lock during copy',
                'source': 'python_analyzer'
            })
        
        # eval() usage (code injection)
        if 'eval(' in line:
            issues.append({
                'issue_type': 'security',
                'severity': 'critical',
                'line_number': line_num,
                'message': 'eval() allows arbitrary code execution - severe security risk',
                'suggestion': 'Use ast.literal_eval() for safe evaluation or avoid eval',
                'source': 'python_analyzer'
            })
        
        # Bare except clause
        if line_stripped == 'except:':
            issues.append({
                'issue_type': 'quality',
                'severity': 'medium',
                'line_number': line_num,
                'message': 'Bare except clause catches all exceptions including system exit',
                'suggestion': 'Catch specific exceptions: except ValueError, TypeError:',
                'fixed_code': 'except Exception:',
                'source': 'python_analyzer'
            })
        
        # Mutable default arguments
        if 'def ' in line and ('=[]' in line.replace(' ', '') or '={}' in line.replace(' ', '')):
            issues.append({
                'issue_type': 'logic',
                'severity': 'high',
                'line_number': line_num,
                'message': 'Mutable default argument - shared between function calls',
                'suggestion': 'Use None as default and initialize inside function',
                'fixed_code': 'def func(data=None): data = data if data is not None else []',
                'source': 'python_analyzer'
            })
        
        # os.system() usage (command injection)
        if 'os.system(' in line or 'subprocess.call(' in line:
            if '+' in line or f'f"' in line or "f'" in line:
                issues.append({
                    'issue_type': 'security',
                    'severity': 'critical',
                    'line_number': line_num,
                    'message': 'Command injection risk: unsanitized input in system command',
                    'suggestion': 'Use subprocess.run() with shell=False and argument list',
                    'source': 'python_analyzer'
                })
        
        # pickle.loads on untrusted data
        if 'pickle.loads(' in line or 'pickle.load(' in line:
            issues.append({
                'issue_type': 'security',
                'severity': 'high',
                'line_number': line_num,
                'message': 'Pickle deserialization can execute arbitrary code',
                'suggestion': 'Use JSON or validate pickle source',
                'source': 'python_analyzer'
            })
        
        # Missing await on async function call
        if '=' in line and 'async_' in line and '(' in line and 'await' not in line:
            issues.append({
                'issue_type': 'async',
                'severity': 'critical',
                'line_number': line_num,
                'message': 'Missing await on async function - returns coroutine object',
                'suggestion': 'Add await keyword: result = await async_function()',
                'source': 'python_analyzer'
            })
        
        # Thread without join() - daemon thread issues
        if 'threading.Thread(' in line and 'daemon' not in line:
            # Check if .join() is called within next 10 lines
            context_after = '\n'.join(lines[line_num:min(line_num+10, len(lines))])
            if '.join()' not in context_after:
                issues.append({
                    'issue_type': 'concurrency',
                    'severity': 'medium',
                    'line_number': line_num,
                    'message': 'Thread created without join() - may cause premature exit',
                    'suggestion': 'Call thread.join() or set daemon=True',
                    'source': 'python_analyzer'
                })
    
    return issues

def analyze_java_bugs(content, lines):
    """Comprehensive Java analyzer for null safety, resources, and security"""
    issues = []
    
    for line_num, line in enumerate(lines, 1):
        line_stripped = line.strip()
        
        # Null pointer dereference risk
        if '= null' in line:
            # Check if dereferenced in next lines
            context = '\n'.join(lines[line_num:min(line_num+10, len(lines))])
            var_name = line.split('=')[0].strip().split()[-1]
            if f'{var_name}.' in context:
                issues.append({
                    'issue_type': 'logic',
                    'severity': 'high',
                    'line_number': line_num,
                    'message': f'Variable {var_name} set to null then dereferenced - NullPointerException',
                    'suggestion': 'Check for null before use or use Optional<>',
                    'source': 'java_analyzer'
                })
        
        # SQL Injection
        if ('executeQuery(' in line or 'executeUpdate(' in line) and ('+' in line or 'String.format' in line):
            issues.append({
                'issue_type': 'security',
                'severity': 'critical',
                'line_number': line_num,
                'message': 'SQL Injection vulnerability: string concatenation in query',
                'suggestion': 'Use PreparedStatement with ? placeholders',
                'fixed_code': 'PreparedStatement pstmt = conn.prepareStatement("SELECT * FROM users WHERE id = ?");',
                'source': 'java_analyzer'
            })
        
        # Resource leak: missing try-with-resources
        if any(keyword in line for keyword in ['FileInputStream', 'FileOutputStream', 'Connection', 'Statement', 'ResultSet']):
            if 'new ' in line and 'try' not in line:
                issues.append({
                    'issue_type': 'resource',
                    'severity': 'high',
                    'line_number': line_num,
                    'message': 'Resource not managed with try-with-resources - potential leak',
                    'suggestion': 'Use try-with-resources: try (Resource r = new Resource()) {...}',
                    'source': 'java_analyzer'
                })
        
        # Empty catch block
        if line_stripped == 'catch' or (line_stripped.startswith('catch') and '{' in line):
            next_line_idx = line_num
            if next_line_idx < len(lines) and lines[next_line_idx].strip() == '}':
                issues.append({
                    'issue_type': 'quality',
                    'severity': 'medium',
                    'line_number': line_num,
                    'message': 'Empty catch block silently swallows exceptions',
                    'suggestion': 'Log the exception or rethrow',
                    'source': 'java_analyzer'
                })
        
        # Hardcoded password
        if any(keyword in line.lower() for keyword in ['password', 'passwd', 'pwd', 'secret', 'apikey']):
            if '= "' in line or "= '" in line:
                if not line_stripped.startswith('//'):
                    issues.append({
                        'issue_type': 'security',
                        'severity': 'critical',
                        'line_number': line_num,
                        'message': 'Hardcoded credential - security vulnerability',
                        'suggestion': 'Load from environment variable or properties file',
                        'source': 'java_analyzer'
                    })
    
    return issues

def run_basic_syntax_check(content, language):
    """Enhanced syntax validation for multiple languages - avoiding false positives"""
    issues = []
    lines = content.split('\n')

    # JavaScript/TypeScript specific analysis
    if language in ['javascript', 'typescript']:
        issues.extend(analyze_javascript_bugs(content, lines))

    # C/C++ specific analysis
    if language in ['cpp', 'c']:
        issues.extend(analyze_cpp_bugs(content, lines))
    
    # Python specific analysis
    if language == 'python':
        issues.extend(analyze_python_bugs(content, lines))
    
    # Java specific analysis
    if language == 'java':
        issues.extend(analyze_java_bugs(content, lines))
    
    return issues

def run_basic_security_checks(content, language):
    """Basic security pattern matching"""
    issues = []
    security_patterns = {
        'python': [
            ('eval(', 'Dangerous use of eval()', 'critical'),
            ('exec(', 'Dangerous use of exec()', 'critical'),
            ('pickle.loads', 'Unsafe pickle deserialization', 'high'),
            ('os.system(', 'Command injection risk', 'high'),
            ('subprocess.call(', 'Potential command injection', 'medium'),
        ],
        'javascript': [
            ('eval(', 'Dangerous use of eval()', 'critical'),
            ('innerHTML', 'XSS vulnerability risk', 'high'),
            ('document.write(', 'XSS vulnerability risk', 'high'),
        ],
        'java': [
            ('Runtime.getRuntime().exec', 'Command injection risk', 'high'),
            ('Statement.execute', 'SQL injection risk', 'high'),
        ]
    }
    
    patterns = security_patterns.get(language, [])
    lines = content.split('\n')
    
    for line_num, line in enumerate(lines, 1):
        for pattern, message, severity in patterns:
            if pattern in line:
                issues.append({
                    'issue_type': 'security',
                    'severity': severity,
                    'line_number': line_num,
                    'message': message,
                    'suggestion': f'Avoid using {pattern}. Use safer alternatives.',
                    'source': 'security_scanner'
                })
    
    return issues

def run_ai_analysis(content, language):
    """Enhanced AI-powered code analysis with fix generation using Ollama"""
    issues = []
    
    try:
        language_name = LANGUAGE_CONFIGS.get(language, {}).get('name', language)
        
        # Language-specific focus areas
        focus_areas = {
            'javascript': """
CRITICAL JavaScript issues to detect:
- var vs let/const closure bugs in loops
- Missing await on Promises (response.json(), fetch(), etc.)
- Async functions returning before async operations complete
- setTimeout/setInterval with async functions (timing bugs)
- Promise chains without proper error handling
- Race conditions and event loop issues
- Callback hell and unhandled promise rejections""",
            'typescript': """
CRITICAL TypeScript issues to detect:
- Type safety violations and 'any' usage
- Missing await on Promises
- Async/await patterns
- Generic type misuse""",
            'python': """
CRITICAL Python issues to detect:
- SQL injection vulnerabilities
- Unvalidated user input
- Hardcoded credentials
- Resource leaks (unclosed files/connections)""",
            'java': """
CRITICAL Java issues to detect:
- Missing semicolons
- Null pointer dereferences
- Resource leaks (unclosed streams)
- SQL injection vulnerabilities"""
        }
        
        specific_focus = focus_areas.get(language, "")
        
        prompt = f"""You are an expert {language_name} developer and code analyzer.

{specific_focus}

Analyze this {language_name} code for REAL issues:

```{language}
{content[:3000]}
```

Provide detailed analysis as a JSON array with objects containing:
- "type": Issue category (async/closure/security/performance/logic/quality)
- "severity": critical/high/medium/low
- "line": Line number where issue occurs
- "message": Clear description of the ACTUAL problem
- "suggestion": Specific fix recommendation
- "fixed_code": The corrected code snippet (single line only)

IMPORTANT:
1. Detect async/await bugs (missing await, wrong return timing)
2. Find closure bugs (var in loops, scope issues)
3. Identify security vulnerabilities
4. Flag performance issues
5. NO false positives - only report REAL problems

Return ONLY valid JSON array, no additional text."""

        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {
                    'role': 'system',
                    'content': f'You are an expert {language_name} code analyzer. Always return valid JSON arrays with actionable fixes. Be thorough and precise.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            options={
                'temperature': 0.3,
                'top_p': 0.9,
            }
        )
        
        # Parse the response
        response_content = response['message']['content']
        
        # Extract JSON from markdown code blocks
        if '```json' in response_content:
            response_content = response_content.split('```json')[1].split('```')[0].strip()
        elif '```' in response_content:
            response_content = response_content.split('```')[1].split('```')[0].strip()
        
        # Handle case where response is just text
        if not response_content.strip().startswith('['):
            # Try to find JSON in the response
            import re
            json_match = re.search(r'\[.*\]', response_content, re.DOTALL)
            if json_match:
                response_content = json_match.group(0)
        
        ai_issues = json.loads(response_content)
        
        for issue in ai_issues:
            issues.append({
                'issue_type': issue.get('type', 'quality'),
                'severity': issue.get('severity', 'medium'),
                'line_number': issue.get('line', 0),
                'message': issue.get('message', ''),
                'suggestion': issue.get('suggestion', ''),
                'fixed_code': issue.get('fixed_code', ''),
                'source': 'ai_analysis'
            })
            
    except json.JSONDecodeError as e:
        print(f"Ollama JSON parsing error: {e}")
        print(f"Response was: {response_content[:500]}")
    except Exception as e:
        print(f"Ollama AI analysis error: {e}")
        print("Make sure Ollama is running: ollama serve")
        print("For better code analysis, try: ollama pull codellama")
    
    return issues

def analyze_code_file(file_id):
    """Main analysis orchestrator - thread-safe version with comprehensive error handling"""
    try:
        with app.app_context():
            code_file = db.session.get(CodeFile, file_id)
            if not code_file:
                print(f"❌ File {file_id} not found in database")
                return
            
            # Normalize content to avoid carriage-return issues and ensure consistent newline endings
            normalized_content = code_file.content.replace('\r\n', '\n').replace('\r', '\n') if code_file.content else ''
            if normalized_content and not normalized_content.endswith('\n'):
                normalized_content += '\n'
            if normalized_content != code_file.content:
                code_file.content = normalized_content
                db.session.commit()
            # Ensure file on disk matches normalized content
            try:
                with open(code_file.filepath, 'w', encoding='utf-8', newline='\n') as f:
                    f.write(normalized_content)
            except Exception as file_err:
                print(f"⚠ Could not rewrite file with normalized newlines: {file_err}")
            
            print(f"\n🔍 Starting analysis for {code_file.filename} (ID: {file_id}, Language: {code_file.language})")
            all_issues = []
            
            # Run static analysis based on language
            try:
                if code_file.language == 'python':
                    # Try pylint if available
                    try:
                        pylint_issues = run_pylint_analysis(code_file.filepath)
                        if pylint_issues:
                            all_issues.extend(pylint_issues)
                            print(f"  ✓ Pylint found {len(pylint_issues)} issues")
                    except Exception as e:
                        print(f"  ⚠ Pylint not available: {e}")
                    
                    # Always run comprehensive Python bug detection
                    syntax_issues = run_basic_syntax_check(code_file.content, code_file.language)
                    all_issues.extend(syntax_issues)
                    print(f"  ✓ Python analysis found {len(syntax_issues)} issues")
                    
                elif code_file.language == 'java':
                    # Try Java compilation check first
                    java_issues = run_java_compilation_check(code_file.filepath, code_file.content)
                    all_issues.extend(java_issues)
                    # If no compilation errors found, run basic syntax check
                    if not java_issues:
                        all_issues.extend(run_basic_syntax_check(code_file.content, code_file.language))
                else:
                    # For other languages, run basic syntax check
                    all_issues.extend(run_basic_syntax_check(code_file.content, code_file.language))
                
                print(f"  📊 After syntax check: {len(all_issues)} total issues")
            except Exception as e:
                print(f"  ❌ Error during syntax analysis: {e}")
            
            # Run security checks
            try:
                security_issues = run_basic_security_checks(code_file.content, code_file.language)
                all_issues.extend(security_issues)
                print(f"  🔒 Security check found {len(security_issues)} issues (Total: {len(all_issues)})")
            except Exception as e:
                print(f"  ❌ Error during security check: {e}")
            
            # Run AI analysis with Ollama
            try:
                ai_issues = run_ai_analysis(code_file.content, code_file.language)
                all_issues.extend(ai_issues)
                print(f"  🤖 AI analysis found {len(ai_issues)} issues (Total: {len(all_issues)})")
            except Exception as e:
                print(f"  ⚠ AI analysis skipped: {e}")
            
            # Save issues to database
            try:
                # Clear previous analysis results
                Issue.query.filter_by(file_id=file_id).delete(synchronize_session=False)
                
                for issue_data in all_issues:
                    issue = Issue(
                        file_id=file_id,
                        issue_type=issue_data['issue_type'],
                        severity=issue_data['severity'],
                        line_number=issue_data['line_number'],
                        message=issue_data['message'],
                        suggestion=issue_data['suggestion'],
                        fixed_code=issue_data.get('fixed_code', ''),
                        source=issue_data['source']
                    )
                    db.session.add(issue)
                
                code_file.analyzed = True
                db.session.commit()
                print(f"\n✅ Analysis complete: {len(all_issues)} issues saved for {code_file.filename}\n")
                
            except Exception as e:
                print(f"  ❌ Error saving issues to database: {e}")
                db.session.rollback()
                try:
                    fresh_file = db.session.get(CodeFile, file_id)
                    if fresh_file:
                        fresh_file.analyzed = True
                        db.session.commit()
                except Exception as inner_err:
                    print(f"  ❌ Unable to mark file as analyzed due to: {inner_err}")
                    db.session.rollback()
    except Exception as e:
        print(f"\n❌ Fatal error in analyze_code_file: {e}\n")
        import traceback
        traceback.print_exc()

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('register'))
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    user = db.session.get(User, session['user_id'])
    projects = Project.query.filter_by(user_id=user.id).all()
    
    # Get statistics
    total_projects = len(projects)
    total_files = sum(len(p.files) for p in projects)
    total_issues = sum(sum(len(f.issues) for f in p.files) for p in projects)
    critical_issues = sum(sum(1 for i in f.issues if i.severity == 'critical') 
                         for p in projects for f in p.files)
    
    stats = {
        'total_projects': total_projects,
        'total_files': total_files,
        'total_issues': total_issues,
        'critical_issues': critical_issues
    }
    
    return render_template('dashboard.html', projects=projects, stats=stats)

@app.route('/project/create', methods=['POST'])
@login_required
def create_project():
    name = request.form.get('name')
    description = request.form.get('description', '')
    
    project = Project(
        name=name,
        description=description,
        user_id=session['user_id']
    )
    db.session.add(project)
    db.session.commit()
    
    flash('Project created successfully!', 'success')
    return redirect(url_for('project_detail', project_id=project.id))

@app.route('/project/<int:project_id>')
@login_required
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    
    if project.user_id != session['user_id']:
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('project.html', project=project)

@app.route('/project/<int:project_id>/upload', methods=['POST'])
@login_required
def upload_file(project_id):
    project = Project.query.get_or_404(project_id)
    
    if project.user_id != session['user_id']:
        return jsonify({'error': 'Access denied'}), 403
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        
        # Read file content first (before saving to uploads folder)
        content = file.read().decode('utf-8', errors='ignore')
        # Normalize newlines to avoid pylint invalid-carriage-return spam and ensure trailing newline
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        if not content.endswith('\n'):
            content += '\n'
        
        # Detect language
        ext = filename.rsplit('.', 1)[1].lower()
        language_map = {
            'py': 'python', 'java': 'java', 'js': 'javascript', 
            'jsx': 'javascript', 'ts': 'typescript', 'tsx': 'typescript',
            'cpp': 'cpp', 'c': 'c', 'h': 'c', 'hpp': 'cpp',
            'cs': 'csharp', 'go': 'go', 'rb': 'ruby', 'php': 'php'
        }
        language = language_map.get(ext, 'unknown')
        
        # Create temporary filepath
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{project_id}_{filename}")
        
        # Save to database first (without saving file to disk yet)
        code_file = CodeFile(
            filename=filename,
            filepath=filepath,
            language=language,
            content=content,
            project_id=project_id,
            analyzed=False
        )
        db.session.add(code_file)
        db.session.commit()
        file_id = code_file.id
        
        # Prepare response
        response_data = jsonify({
            'success': True,
            'file_id': file_id,
            'filename': filename,
            'language': language
        })
        
        # Save file and run analysis in background thread (after response is ready)
        def save_and_analyze():
            with app.app_context():
                # Mark file as pending analysis
                pending_file = db.session.get(CodeFile, file_id)
                if pending_file:
                    pending_file.analyzed = False
                    db.session.commit()
                
                # Save the file to disk
                normalized = content.replace('\r\n', '\n').replace('\r', '\n')
                if not normalized.endswith('\n'):
                    normalized += '\n'
                with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
                    f.write(normalized)
                # Run analysis
                analyze_code_file(file_id)
        
        import threading
        bg_thread = threading.Thread(target=save_and_analyze)
        bg_thread.daemon = True
        bg_thread.start()
        
        return response_data
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/file/<int:file_id>')
@login_required
def file_detail(file_id):
    code_file = CodeFile.query.get_or_404(file_id)
    project = code_file.project
    
    if project.user_id != session['user_id']:
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('file.html', code_file=code_file, project=project)

@app.route('/api/file/<int:file_id>/status')
@login_required
def get_file_status(file_id):
    """Check if file analysis is complete"""
    code_file = CodeFile.query.get_or_404(file_id)
    
    if code_file.project.user_id != session['user_id']:
        return jsonify({'error': 'Access denied'}), 403
    
    # If analysis not complete, attempt a synchronous analysis pass as a fallback
    if not code_file.analyzed:
        try:
            analyze_code_file(file_id)
            # Refresh state
            db.session.refresh(code_file)
        except Exception as e:
            print(f"⚠ Status-triggered analysis failed for file {file_id}: {e}")
            db.session.rollback()
        finally:
            # Prevent stale session state
            db.session.expire_all()
    
    # Check analysis status and issue count
    issue_count = Issue.query.filter_by(file_id=file_id).count()
    analyzed = bool(code_file.analyzed)
    
    return jsonify({
        'file_id': file_id,
        'analyzed': analyzed,
        'issue_count': issue_count,
        'status': 'complete' if analyzed else 'pending'
    })

@app.route('/api/file/<int:file_id>/issues')
@login_required
def get_file_issues(file_id):
    code_file = CodeFile.query.get_or_404(file_id)
    
    if code_file.project.user_id != session['user_id']:
        return jsonify({'error': 'Access denied'}), 403
    
    issues = Issue.query.filter_by(file_id=file_id).all()
    
    return jsonify({
        'issues': [{
            'id': issue.id,
            'type': issue.issue_type,
            'severity': issue.severity,
            'line': issue.line_number,
            'message': issue.message,
            'suggestion': issue.suggestion,
            'fixed_code': issue.fixed_code,
            'source': issue.source,
            'status': issue.status
        } for issue in issues]
    })

@app.route('/api/issue/<int:issue_id>/status', methods=['POST'])
@login_required
def update_issue_status(issue_id):
    issue = Issue.query.get_or_404(issue_id)
    
    if issue.code_file.project.user_id != session['user_id']:
        return jsonify({'error': 'Access denied'}), 403
    
    new_status = request.json.get('status')
    if new_status in ['open', 'resolved', 'ignored']:
        issue.status = new_status
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'error': 'Invalid status'}), 400

@app.route('/api/issue/<int:issue_id>/apply-fix', methods=['POST'])
@login_required
def apply_fix(issue_id):
    """Apply AI-generated fix to the code file"""
    issue = Issue.query.get_or_404(issue_id)
    code_file = issue.code_file
    
    if code_file.project.user_id != session['user_id']:
        return jsonify({'error': 'Access denied'}), 403
    
    if not issue.fixed_code:
        return jsonify({'error': 'No fix available for this issue'}), 400
    
    try:
        # Read current file content
        lines = code_file.content.split('\n')
        
        # Apply the fix
        if issue.line_number > 0 and issue.line_number <= len(lines):
            # Replace the problematic line with the fixed version
            lines[issue.line_number - 1] = issue.fixed_code
            
            # Update file content
            code_file.content = '\n'.join(lines)
            
            # Update file on disk
            with open(code_file.filepath, 'w', encoding='utf-8') as f:
                f.write(code_file.content)
            
            # Mark issue as resolved
            issue.status = 'resolved'
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Fix applied successfully',
                'new_content': code_file.content
            })
        else:
            return jsonify({'error': 'Invalid line number'}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to apply fix: {str(e)}'}), 500

@app.route('/api/file/<int:file_id>/auto-fix-all', methods=['POST'])
@login_required
def auto_fix_all(file_id):
    """Automatically apply all available fixes for a file"""
    code_file = CodeFile.query.get_or_404(file_id)
    
    if code_file.project.user_id != session['user_id']:
        return jsonify({'error': 'Access denied'}), 403
    
    # Get all issues with fixes
    issues_with_fixes = [i for i in code_file.issues if i.fixed_code and i.status == 'open']
    
    if not issues_with_fixes:
        return jsonify({'message': 'No fixable issues found'}), 200
    
    try:
        lines = code_file.content.split('\n')
        fixed_count = 0
        
        # Sort issues by line number in descending order to avoid offset issues
        issues_with_fixes.sort(key=lambda x: x.line_number, reverse=True)
        
        for issue in issues_with_fixes:
            if issue.line_number > 0 and issue.line_number <= len(lines):
                lines[issue.line_number - 1] = issue.fixed_code
                issue.status = 'resolved'
                fixed_count += 1
        
        # Update file content
        code_file.content = '\n'.join(lines)
        
        # Update file on disk
        with open(code_file.filepath, 'w', encoding='utf-8') as f:
            f.write(code_file.content)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Applied {fixed_count} fixes successfully',
            'fixed_count': fixed_count,
            'new_content': code_file.content
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to apply fixes: {str(e)}'}), 500

@app.route('/analytics')
@login_required
def analytics():
    user = db.session.get(User, session['user_id'])
    projects = Project.query.filter_by(user_id=user.id).all()
    
    # Aggregate data for charts
    severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
    type_counts = {}
    
    for project in projects:
        for file in project.files:
            for issue in file.issues:
                severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1
                type_counts[issue.issue_type] = type_counts.get(issue.issue_type, 0) + 1
    
    return render_template('analytics.html', 
                         severity_counts=severity_counts,
                         type_counts=type_counts,
                         projects=projects)

@app.route('/project/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    
    if project.user_id != session['user_id']:
        return jsonify({'error': 'Access denied'}), 403
    
    # Delete associated files
    for file in project.files:
        if os.path.exists(file.filepath):
            os.remove(file.filepath)
    
    db.session.delete(project)
    db.session.commit()
    
    flash('Project deleted successfully', 'success')
    return redirect(url_for('dashboard'))

# Initialize database and uploads folder
with app.app_context():
    db.create_all()
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    try:
        column_info = db.session.execute(text("PRAGMA table_info(code_file)")).all()
        columns = {row[1] for row in column_info}
        if 'analyzed' not in columns:
            db.session.execute(text("ALTER TABLE code_file ADD COLUMN analyzed BOOLEAN DEFAULT 0"))
            db.session.execute(text("UPDATE code_file SET analyzed = 0 WHERE analyzed IS NULL"))
            db.session.commit()
    except Exception as migration_error:
        db.session.rollback()
        print(f"⚠ Database migration warning: {migration_error}")

if __name__ == '__main__':
    # Disable Flask reloader to prevent restarts when uploads are written
    import sys
    sys.dont_write_bytecode = True

    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000,
        use_reloader=False
    )
