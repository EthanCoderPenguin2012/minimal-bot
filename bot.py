#!/usr/bin/env python3
import os
import json
import re
import time
from datetime import datetime, timedelta
from flask import Flask, request
import requests
from threading import Thread
import schedule

app = Flask(__name__)

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET')
OPENAI_KEY = os.environ.get('OPENAI_API_KEY', '')

def github_api(method, url, data=None):
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    response = requests.request(method, f'https://api.github.com{url}', headers=headers, json=data)
    return response.json() if response.content else {}

def ai_code_review(diff_text):
    if not OPENAI_KEY:
        return None
    try:
        response = requests.post('https://api.openai.com/v1/chat/completions',
            headers={'Authorization': f'Bearer {OPENAI_KEY}'},
            json={
                'model': 'gpt-3.5-turbo',
                'messages': [{'role': 'user', 'content': f'Review this code diff and suggest improvements:\n{diff_text[:2000]}'}],
                'max_tokens': 500
            })
        return response.json()['choices'][0]['message']['content']
    except:
        return None

def auto_label_pr(repo, pr_number, files):
    labels = set()
    lines_changed = 0
    
    for file in files:
        lines_changed += file.get('changes', 0)
        filename = file['filename'].lower()
        
        # Language detection
        if filename.endswith(('.py', '.pyx')): labels.add('python')
        elif filename.endswith(('.js', '.jsx', '.ts', '.tsx')): labels.add('javascript')
        elif filename.endswith(('.java', '.kt')): labels.add('java')
        elif filename.endswith(('.cpp', '.c', '.h')): labels.add('c++')
        elif filename.endswith(('.go')): labels.add('golang')
        elif filename.endswith(('.rs')): labels.add('rust')
        elif filename.endswith(('.rb')): labels.add('ruby')
        elif filename.endswith(('.php')): labels.add('php')
        elif filename.endswith(('.swift')): labels.add('swift')
        
        # File type detection
        if filename.endswith(('.md', '.txt', '.rst')): labels.add('documentation')
        elif 'test' in filename or filename.endswith(('.test.js', '_test.py')): labels.add('tests')
        elif filename.endswith(('.yml', '.yaml', '.json', '.toml')): labels.add('config')
        elif filename.endswith(('.css', '.scss', '.sass')): labels.add('styling')
        elif filename.endswith(('.html', '.htm')): labels.add('frontend')
        elif 'docker' in filename or filename == 'dockerfile': labels.add('docker')
        elif filename.endswith(('.sql')): labels.add('database')
        elif 'api' in filename or 'endpoint' in filename: labels.add('api')
        elif 'security' in filename or 'auth' in filename: labels.add('security')
        elif 'performance' in filename or 'optimize' in filename: labels.add('performance')
        
        # Directory-based labels
        if '/frontend/' in filename or '/ui/' in filename: labels.add('frontend')
        elif '/backend/' in filename or '/server/' in filename: labels.add('backend')
        elif '/mobile/' in filename or '/android/' in filename or '/ios/' in filename: labels.add('mobile')
        elif '/infra/' in filename or '/deploy/' in filename: labels.add('infrastructure')
    
    # Size labels
    if lines_changed > 500: labels.add('large')
    elif lines_changed > 100: labels.add('medium')
    else: labels.add('small')
    
    if labels:
        github_api('POST', f'/repos/{repo}/issues/{pr_number}/labels', {'labels': list(labels)})

def auto_assign_reviewers(repo, pr_number, files, author):
    # Smart reviewer assignment based on file ownership
    reviewers = set()
    
    for file in files:
        # Get file blame to find frequent contributors
        blame = github_api('GET', f'/repos/{repo}/contents/{file["filename"]}')
        if blame:
            commits = github_api('GET', f'/repos/{repo}/commits?path={file["filename"]}&per_page=5')
            for commit in commits[:3]:
                if commit['author'] and commit['author']['login'] != author:
                    reviewers.add(commit['author']['login'])
    
    if reviewers:
        github_api('POST', f'/repos/{repo}/pulls/{pr_number}/requested_reviewers', 
                  {'reviewers': list(reviewers)[:3]})

def welcome_contributor(repo, pr_number, author):
    prs = github_api('GET', f'/repos/{repo}/pulls?author={author}&state=all')
    if len(prs) == 1:
        repo_info = github_api('GET', f'/repos/{repo}')
        welcome_msg = f"""🎉 Welcome @{author}! Thanks for your first contribution to {repo_info.get('name', 'this project')}!

📋 **Quick checklist:**
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code follows project style

💡 **Tips:**
- Use `/help` to see available commands
- Tag maintainers with questions
- Check CI status below

Thanks for making this project better! 🚀"""
        github_api('POST', f'/repos/{repo}/issues/{pr_number}/comments', {'body': welcome_msg})

def check_pr_requirements(repo, pr_number, files):
    issues = []
    
    # Check for tests
    has_tests = any('test' in f['filename'].lower() for f in files)
    has_code = any(f['filename'].endswith(('.py', '.js', '.ts', '.java', '.go')) for f in files)
    
    if has_code and not has_tests:
        issues.append('⚠️ Consider adding tests for your code changes')
    
    # Check for large files
    large_files = [f['filename'] for f in files if f.get('changes', 0) > 300]
    if large_files:
        issues.append(f'📏 Large files detected: {", ".join(large_files[:3])} - consider splitting')
    
    # Check for documentation
    has_docs = any(f['filename'].endswith(('.md', '.rst', '.txt')) for f in files)
    if len(files) > 5 and not has_docs:
        issues.append('📚 Consider updating documentation for this change')
    
    if issues:
        comment = '🤖 **Automated PR Review:**\n\n' + '\n'.join(f'- {issue}' for issue in issues)
        github_api('POST', f'/repos/{repo}/issues/{pr_number}/comments', {'body': comment})

def auto_close_stale_issues():
    # This would run periodically to close stale issues
    pass

def generate_changelog(repo):
    # Generate changelog from recent PRs
    prs = github_api('GET', f'/repos/{repo}/pulls?state=closed&sort=updated&per_page=20')
    changelog = '# Recent Changes\n\n'
    
    for pr in prs[:10]:
        if pr.get('merged_at'):
            changelog += f"- {pr['title']} (#{pr['number']}) by @{pr['user']['login']}\n"
    
    return changelog

def security_scan_pr(files):
    security_issues = []
    
    for file in files:
        if file.get('patch'):
            patch = file['patch'].lower()
            
            # Basic security checks
            if 'password' in patch and '=' in patch:
                security_issues.append(f"⚠️ Potential hardcoded password in {file['filename']}")
            if 'api_key' in patch or 'secret' in patch:
                security_issues.append(f"🔐 Potential API key/secret in {file['filename']}")
            if 'eval(' in patch or 'exec(' in patch:
                security_issues.append(f"⚡ Dangerous eval/exec usage in {file['filename']}")
            if 'sql' in patch and ('drop' in patch or 'delete' in patch):
                security_issues.append(f"🗃️ Potential SQL injection risk in {file['filename']}")
    
    return security_issues

@app.route('/webhook', methods=['POST'])
def webhook():
    event = request.headers.get('X-GitHub-Event')
    payload = request.json
    
    if event == 'pull_request':
        action = payload['action']
        repo = payload['repository']['full_name']
        pr = payload['pull_request']
        pr_number = pr['number']
        author = pr['user']['login']
        
        if action == 'opened':
            files = github_api('GET', f'/repos/{repo}/pulls/{pr_number}/files')
            
            # All the automation
            auto_label_pr(repo, pr_number, files)
            auto_assign_reviewers(repo, pr_number, files, author)
            welcome_contributor(repo, pr_number, author)
            check_pr_requirements(repo, pr_number, files)
            
            # Security scan
            security_issues = security_scan_pr(files)
            if security_issues:
                security_comment = '🔒 **Security Scan Results:**\n\n' + '\n'.join(f'- {issue}' for issue in security_issues)
                github_api('POST', f'/repos/{repo}/issues/{pr_number}/comments', {'body': security_comment})
            
            # AI code review (if OpenAI key provided)
            if OPENAI_KEY and len(files) <= 5:
                diff_text = '\n'.join([f.get('patch', '') for f in files[:3]])
                ai_review = ai_code_review(diff_text)
                if ai_review:
                    github_api('POST', f'/repos/{repo}/issues/{pr_number}/comments', 
                              {'body': f'🤖 **AI Code Review:**\n\n{ai_review}'})
        
        elif action == 'closed' and pr.get('merged'):
            # Thank contributor
            thank_msg = f"🎉 Thanks @{author}! Your contribution has been merged. Great work! 🚀"
            github_api('POST', f'/repos/{repo}/issues/{pr_number}/comments', {'body': thank_msg})
    
    elif event == 'issues':
        if payload['action'] == 'opened':
            issue = payload['issue']
            repo = payload['repository']['full_name']
            
            # Auto-label issues
            title = issue['title'].lower()
            body = issue['body'].lower() if issue['body'] else ''
            labels = []
            
            if 'bug' in title or 'error' in title or 'broken' in title:
                labels.append('bug')
            if 'feature' in title or 'enhancement' in title:
                labels.append('enhancement')
            if 'question' in title or '?' in title:
                labels.append('question')
            if 'help' in title or 'support' in title:
                labels.append('help wanted')
            if 'urgent' in title or 'critical' in title:
                labels.append('priority: high')
            
            if labels:
                github_api('POST', f'/repos/{repo}/issues/{issue["number"]}/labels', {'labels': labels})
    
    elif event == 'issue_comment' and payload['action'] == 'created':
        comment = payload['comment']['body'].strip()
        repo = payload['repository']['full_name']
        issue_number = payload['issue']['number']
        commenter = payload['comment']['user']['login']
        
        # Command processing
        if comment.startswith('/'):
            cmd = comment.lower().split()[0]
            
            if cmd == '/help':
                help_text = """🤖 **Available Commands:**

**Assignment & Labels:**
- `/assign @user` - Assign to user
- `/unassign @user` - Remove assignment
- `/label bug` - Add label
- `/unlabel bug` - Remove label
- `/priority high` - Set priority

**Actions:**
- `/close` - Close issue/PR
- `/reopen` - Reopen issue/PR
- `/lock` - Lock conversation
- `/unlock` - Unlock conversation

**Info:**
- `/status` - Show issue/PR status
- `/changelog` - Generate recent changes
- `/contributors` - List top contributors

**Fun:**
- `/joke` - Random dev joke
- `/motivate` - Motivational quote"""
                github_api('POST', f'/repos/{repo}/issues/{issue_number}/comments', {'body': help_text})
            
            elif cmd.startswith('/assign'):
                if '@' in comment:
                    assignee = comment.split('@')[1].split()[0]
                    github_api('POST', f'/repos/{repo}/issues/{issue_number}/assignees', {'assignees': [assignee]})
                    github_api('POST', f'/repos/{repo}/issues/{issue_number}/comments', 
                              {'body': f'✅ Assigned to @{assignee}'})
            
            elif cmd.startswith('/label'):
                label = comment.split('/label ')[1].strip()
                github_api('POST', f'/repos/{repo}/issues/{issue_number}/labels', {'labels': [label]})
                github_api('POST', f'/repos/{repo}/issues/{issue_number}/comments', 
                          {'body': f'🏷️ Added label: `{label}`'})
            
            elif cmd == '/close':
                github_api('PATCH', f'/repos/{repo}/issues/{issue_number}', {'state': 'closed'})
                github_api('POST', f'/repos/{repo}/issues/{issue_number}/comments', 
                          {'body': f'🔒 Closed by @{commenter}'})
            
            elif cmd == '/changelog':
                changelog = generate_changelog(repo)
                github_api('POST', f'/repos/{repo}/issues/{issue_number}/comments', {'body': changelog})
            
            elif cmd == '/joke':
                jokes = [
                    "Why do programmers prefer dark mode? Because light attracts bugs! 🐛",
                    "How many programmers does it take to change a light bulb? None, that's a hardware problem! 💡",
                    "Why do Java developers wear glasses? Because they don't C# 👓",
                    "There are only 10 types of people: those who understand binary and those who don't 🤖"
                ]
                import random
                github_api('POST', f'/repos/{repo}/issues/{issue_number}/comments', 
                          {'body': f'😄 {random.choice(jokes)}'})
            
            elif cmd == '/motivate':
                quotes = [
                    "Code is like humor. When you have to explain it, it's bad. 💭",
                    "First, solve the problem. Then, write the code. 🎯",
                    "The best error message is the one that never shows up. ✨",
                    "Programming isn't about what you know; it's about what you can figure out. 🧠"
                ]
                import random
                github_api('POST', f'/repos/{repo}/issues/{issue_number}/comments', 
                          {'body': f'💪 {random.choice(quotes)}'})
    
    return '', 200

# Scheduled tasks
def run_scheduled_tasks():
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    # Start scheduled tasks in background
    scheduler_thread = Thread(target=run_scheduled_tasks, daemon=True)
    scheduler_thread.start()
    
    app.run(host='0.0.0.0', port=5000, debug=True)