# CodeGuard - AI-Powered Code Analysis Platform

CodeGuard is an intelligent code quality and security analysis platform that combines static analysis tools with AI-powered insights to help developers maintain high-quality, secure codebases.

## 🚀 Features

### Core Features
- **🔐 Secure Authentication** - JWT-based user authentication with role-based access control
- **📁 Project Management** - Organize code files into projects with version tracking
- **🔍 Comprehensive Code Analysis** - Multi-layer analysis with syntax checking, compilation validation, and AI insights
- **🛡️ Advanced Security Scanning** - Detect SQL injection, XSS, hardcoded secrets, and 20+ vulnerability types
- **🤖 AI-Powered Analysis & Auto-Fix** - Intelligent issue detection with one-click fixes using local LLM (Ollama)
- **⚡ Bulk Auto-Fix** - Apply all AI-suggested fixes with a single click
- **📊 Analytics Dashboard** - Visualize code health metrics with interactive charts
- **💡 Smart Fix Suggestions** - See proposed fixes before applying them
- **🎯 Multi-Language Support** - 30+ programming languages including Python, Java, JavaScript, C/C++, Go, Rust, and more

### Analysis Capabilities
- **Syntax Error Detection** - Missing semicolons, brackets, indentation issues
- **Compilation Checking** - Java, C/C++, Go compiler integration
- **Security Vulnerabilities** - SQL injection, XSS, CSRF, insecure cryptography
- **Performance Issues** - Inefficient algorithms, memory leaks, optimization opportunities
- **Code Quality** - Code smells, design patterns, SOLID principles
- **Best Practices** - Language-specific modern idioms and conventions

### Supported Languages
Python, Java, JavaScript, TypeScript, C, C++, C#, Go, Ruby, PHP, Swift, Kotlin, Rust, Scala, R, SQL, Shell (sh/bash/ps1), HTML, CSS, XML, JSON, YAML

## 🛠️ Tech Stack

- **Backend**: Python Flask
- **Frontend**: HTML, CSS, JavaScript
- **Database**: SQLite
- **Static Analysis**: Pylint
- **AI Integration**: Ollama (local LLM)
- **Charts**: Chart.js

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git

## 🔧 Installation & Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd CodeGuard-app
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
```bash
# Copy the example environment file
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac

# Edit .env and set your configuration
# SECRET_KEY - Change this to a random secret key
# OLLAMA_MODEL - Set your preferred Ollama model (default: llama2)
```

### 5. Install and Start Ollama (for AI analysis)
```bash
# Download Ollama from https://ollama.ai
# After installation, pull a model:
ollama pull llama2

# Start Ollama server (in a separate terminal)
ollama serve
```

### 6. Run the Application
```bash
python app.py
```

The application will be available at: `http://localhost:5000`

## 📖 Usage Guide

### Getting Started

1. **Register an Account**
   - Navigate to `http://localhost:5000`
   - Click "Get Started" or "Register"
   - Fill in your details and create an account

2. **Create a Project**
   - After login, click "New Project" on the dashboard
   - Enter project name and description
   - Click "Create Project"

3. **Upload Code Files**
   - Open your project
   - Click "Upload File"
   - Select a code file from your computer
   - The system will automatically analyze the code

4. **View Analysis Results**
   - Click on any uploaded file to view detailed analysis
   - See issues categorized by severity (Critical, High, Medium, Low)
   - Get line-by-line code review with suggestions
   - View AI-generated fixes for each issue

5. **Apply Fixes**
   - **Single Fix**: Click "Apply Fix" button on any issue with a suggested fix
   - **Bulk Fix**: Click "Auto-Fix All" button to apply all available fixes at once
   - Review proposed changes before confirming
   - File is automatically updated and saved

6. **Monitor Progress**
   - Track issue resolution in the Analytics dashboard
   - View code quality metrics over time
   - Monitor security score and improvements

5. **Check Analytics**
   - Navigate to the Analytics page from the top menu
   - View charts showing:
     - Issues by severity
     - Issues by type (security, quality, performance)
     - Issues across projects

## 🔑 Key Features Explained

### Static Analysis
- **Pylint Integration**: Automatically runs Pylint on Python files
- **Custom Rules**: Built-in security pattern matching for common vulnerabilities
- **Multi-language Support**: Extensible architecture for adding more analyzers

### Security Scanning
Detects common security issues:
- Use of dangerous functions (eval, exec)
- Command injection vulnerabilities
- SQL injection risks
- XSS vulnerabilities
- Unsafe deserialization

### AI-Powered Analysis (Optional)
When OpenAI API key is configured:
- Context-aware code review
- Intelligent suggestions
- Best practice recommendations
- Performance optimization tips
llama)
When Ollama is running locally:
- Context-aware code review using local LLMs
- Intelligent suggestions
- Best practice recommendations
- Performance optimization tips
- Privacy-focused (all analysis done locally)
- Supports multiple models (llama2, codellama, mistral, etc.)s to problematic code

## 📁 Project Structure

```
CodeGuard-app/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── .gitignore            # Git ignore rules
├── README.md             # This file
├── templates/            # HTML templates
│   ├── base.html         # Base template
│   ├── index.html        # Landing page
│   ├── login.html        # Login page
│   ├── register.html     # Registration page
│   ├── dashboard.html    # Main dashboard
│   ├── project.html      # Project detail view
│   ├── file.html         # File analysis view
│   └── analytics.html    # Analytics dashboard
├── static/               # Static assets
│   ├── css/
│   │   └── style.css     # Main stylesheet
│   └── js/
│       ├── main.js       # Common utilities
│       ├── dashboard.js  # Dashboard functionality
│       ├── project.js    # Project page scripts
│       ├── file.js       # File viewer scripts
│       └── analytics.js  # Chart visualizations
└── uploads/              # Uploaded files (created automatically)
```

## 🔒 Security Considerations

1. **Change Default Secret Key**: Update `SECRET_KEY` in `.env` file
2. **Use Strong Passwords**: Passwords are hashed using bcrypt
3. **Local AI**: Ollama runs locally, keeping your code private and secur
4. **Allowed File Types**: Only specific code file extensions are allowed
5. **API Keys**: Keep your OpenAI API key secure in `.env` file

## 🚀 Production Deployment

For production deployment:

1. Set `FLASK_ENV=production` in `.env`
2. Use a production-grade WSGI server (gunicorn, uWSGI)
3. Use PostgreSQL or MySQL instead of SQLite
4. Set up proper logging and monitoring
5. Use environment variables for sensitive configuration
6. Enable HTTPS with SSL certificates
7. Configure firewall and security groups

### Example with Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 📊 Database Schema

### Users Table
- id, username, email, password (hashed), role, created_at

### Projects Table
- id, name, description, user_id, created_at, updated_at

### CodeFiles Table
- id, filename, filepath, language, content, project_id, uploaded_at

### Issues Table
- id, file_id, issue_type, severity, line_number, message, suggestion, source, status, created_at

## 🤝 Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/YourFeature`)
3. Commit your changes (`git commit -m 'Add YourFeature'`)
4. Push to the branch (`git push origin feature/YourFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Troubleshooting

### Database Issues
```bash
# Reset database
rm codeguard.db
python app.py
```

### Port Already in Use
```python
# In app.py, change the port:
app.run(debug=True, host='0.0.0.0', port=5001)
```

### Pylint Not Found
```bash
pip install pylint
```llama Issues
```bash
# Check if Ollama is running
curl http://localhost:11434

# Start Ollama server
ollama serve

# Pull a model if not already downloaded
ollama pull llama2
# or for better code analysis
ollama pull codellama
```
- Ensure you have API credits
- The app works without OpenAI, it's optional

## 📧 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Contact the development team

## 🎯 Future Enhancements

- [ ] CI/CD integration (GitHub Actions, GitLab CI)
- [ ] Team collaboration features
- [ ] Slack/Discord notifications
- [ ] Code diff analysis
- [llama for local rule configuration
- [ ] API endpoints for programmatic access
- [ ] Docker containerization
- [ ] More language support

## ⭐ Acknowledgments

- Flask framework
- Pylint static analyzer
- OpenAI for AI capabilities
- Chart.js for visualizations
- Font Awesome for icons

---

**Made with ❤️ for better code quality**
