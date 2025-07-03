# Utility functions for the GitHub bot
import re
import requests
from datetime import datetime, timedelta
from config import SECURITY_PATTERNS, JOKES, MOTIVATIONAL_QUOTES
import random

def analyze_code_complexity(files):
    """Analyze code complexity and provide insights"""
    total_lines = sum(f.get('changes', 0) for f in files)
    file_count = len(files)
    
    complexity_score = 0
    if total_lines > 500: complexity_score += 3
    elif total_lines > 200: complexity_score += 2
    elif total_lines > 50: complexity_score += 1
    
    if file_count > 10: complexity_score += 2
    elif file_count > 5: complexity_score += 1
    
    return {
        'score': complexity_score,
        'total_lines': total_lines,
        'file_count': file_count,
        'risk_level': 'high' if complexity_score >= 4 else 'medium' if complexity_score >= 2 else 'low'
    }

def detect_breaking_changes(files):
    """Detect potential breaking changes in code"""
    breaking_patterns = [
        r'def\s+\w+\([^)]*\)\s*->',  # Function signature changes
        r'class\s+\w+\([^)]*\):',     # Class inheritance changes
        r'import\s+\w+',              # Import changes
        r'from\s+\w+\s+import',       # Import changes
        r'@\w+',                      # Decorator changes
    ]
    
    breaking_files = []
    for file in files:
        if file.get('patch'):
            for pattern in breaking_patterns:
                if re.search(pattern, file['patch']):
                    breaking_files.append(file['filename'])
                    break
    
    return breaking_files

def generate_pr_summary(files, pr_title):
    """Generate intelligent PR summary"""
    complexity = analyze_code_complexity(files)
    breaking_files = detect_breaking_changes(files)
    
    summary = f"📊 **PR Analysis:**\n\n"
    summary += f"- **Files changed:** {complexity['file_count']}\n"
    summary += f"- **Lines changed:** {complexity['total_lines']}\n"
    summary += f"- **Complexity:** {complexity['risk_level'].title()}\n"
    
    if breaking_files:
        summary += f"- ⚠️ **Potential breaking changes in:** {', '.join(breaking_files[:3])}\n"
    
    # Language breakdown
    languages = set()
    for file in files:
        ext = '.' + file['filename'].split('.')[-1] if '.' in file['filename'] else ''
        if ext in ['.py', '.js', '.ts', '.java', '.go', '.rs', '.rb']:
            languages.add(ext[1:])
    
    if languages:
        summary += f"- **Languages:** {', '.join(sorted(languages))}\n"
    
    return summary

def scan_for_vulnerabilities(files):
    """Enhanced security vulnerability scanning"""
    vulnerabilities = []
    
    for file in files:
        if not file.get('patch'):
            continue
            
        patch_content = file['patch'].lower()
        filename = file['filename']
        
        # Check each security pattern category
        for category, patterns in SECURITY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, patch_content, re.IGNORECASE):
                    vulnerabilities.append({
                        'type': category,
                        'file': filename,
                        'severity': 'high' if category == 'hardcoded_secrets' else 'medium'
                    })
    
    return vulnerabilities

def get_contributor_stats(github_api_func, repo):
    """Get contributor statistics"""
    try:
        contributors = github_api_func('GET', f'/repos/{repo}/contributors?per_page=10')
        stats = []
        
        for contributor in contributors[:5]:
            stats.append({
                'login': contributor['login'],
                'contributions': contributor['contributions'],
                'avatar': contributor['avatar_url']
            })
        
        return stats
    except:
        return []

def format_time_ago(timestamp):
    """Format timestamp to human readable 'time ago' format"""
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        now = datetime.now(dt.tzinfo)
        diff = now - dt
        
        if diff.days > 0:
            return f"{diff.days} days ago"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600} hours ago"
        else:
            return f"{diff.seconds // 60} minutes ago"
    except:
        return "recently"

def get_random_joke():
    """Get a random programming joke"""
    return random.choice(JOKES)

def get_random_quote():
    """Get a random motivational quote"""
    return random.choice(MOTIVATIONAL_QUOTES)

def extract_mentioned_users(text):
    """Extract @mentioned users from text"""
    return re.findall(r'@(\w+)', text)

def is_maintainer(github_api_func, repo, username):
    """Check if user is a maintainer/collaborator"""
    try:
        response = github_api_func('GET', f'/repos/{repo}/collaborators/{username}')
        return 'login' in response
    except:
        return False

def generate_issue_template_suggestion(issue_title, issue_body):
    """Suggest issue template improvements"""
    suggestions = []
    
    if not issue_body or len(issue_body) < 50:
        suggestions.append("Consider providing more details about the issue")
    
    if 'bug' in issue_title.lower() and 'reproduce' not in issue_body.lower():
        suggestions.append("For bug reports, please include steps to reproduce")
    
    if 'feature' in issue_title.lower() and 'why' not in issue_body.lower():
        suggestions.append("For feature requests, please explain the use case")
    
    return suggestions