# Configuration for advanced bot features
import os

# Bot behavior settings
AUTO_ASSIGN_REVIEWERS = os.environ.get('AUTO_ASSIGN_REVIEWERS', 'true').lower() == 'true'
ENABLE_AI_REVIEWS = os.environ.get('ENABLE_AI_REVIEWS', 'true').lower() == 'true'
SECURITY_SCANNING = os.environ.get('SECURITY_SCANNING', 'true').lower() == 'true'
WELCOME_NEW_CONTRIBUTORS = os.environ.get('WELCOME_NEW_CONTRIBUTORS', 'true').lower() == 'true'

# Label mappings for different file types and patterns
LANGUAGE_LABELS = {
    '.py': 'python', '.pyx': 'python',
    '.js': 'javascript', '.jsx': 'javascript', '.ts': 'typescript', '.tsx': 'typescript',
    '.java': 'java', '.kt': 'kotlin',
    '.cpp': 'c++', '.c': 'c++', '.h': 'c++',
    '.go': 'golang',
    '.rs': 'rust',
    '.rb': 'ruby',
    '.php': 'php',
    '.swift': 'swift',
    '.cs': 'c#',
    '.scala': 'scala',
    '.r': 'r'
}

CONTENT_LABELS = {
    'documentation': ['.md', '.txt', '.rst', '.adoc'],
    'config': ['.yml', '.yaml', '.json', '.toml', '.ini', '.cfg'],
    'styling': ['.css', '.scss', '.sass', '.less'],
    'frontend': ['.html', '.htm', '.vue', '.svelte'],
    'database': ['.sql', '.db', '.sqlite'],
    'docker': ['dockerfile', 'docker-compose'],
    'ci/cd': ['.github', '.gitlab-ci', '.travis', '.circleci']
}

# Security patterns to scan for
SECURITY_PATTERNS = {
    'hardcoded_secrets': [
        r'password\s*=\s*["\'][^"\']+["\']',
        r'api_key\s*=\s*["\'][^"\']+["\']',
        r'secret\s*=\s*["\'][^"\']+["\']',
        r'token\s*=\s*["\'][^"\']+["\']'
    ],
    'dangerous_functions': [
        r'eval\s*\(',
        r'exec\s*\(',
        r'system\s*\(',
        r'shell_exec\s*\('
    ],
    'sql_injection': [
        r'execute\s*\(\s*["\'].*\+.*["\']',
        r'query\s*\(\s*["\'].*\+.*["\']'
    ]
}

# Fun responses
JOKES = [
    "Why do programmers prefer dark mode? Because light attracts bugs! 🐛",
    "How many programmers does it take to change a light bulb? None, that's a hardware problem! 💡",
    "Why do Java developers wear glasses? Because they don't C# 👓",
    "There are only 10 types of people: those who understand binary and those who don't 🤖",
    "A SQL query goes into a bar, walks up to two tables and asks: 'Can I join you?' 🍺",
    "Why did the programmer quit his job? He didn't get arrays! 📊"
]

MOTIVATIONAL_QUOTES = [
    "Code is like humor. When you have to explain it, it's bad. 💭",
    "First, solve the problem. Then, write the code. 🎯",
    "The best error message is the one that never shows up. ✨",
    "Programming isn't about what you know; it's about what you can figure out. 🧠",
    "Clean code always looks like it was written by someone who cares. 💎",
    "Any fool can write code that a computer can understand. Good programmers write code that humans can understand. 👥"
]