#!/usr/bin/env python3
import os
import json
import jwt
import time
import requests
from datetime import datetime, timedelta
from flask import Flask, request
from utils import *
from config import *

app = Flask(__name__)

# GitHub App credentials
APP_ID = os.environ.get('GITHUB_APP_ID')
PRIVATE_KEY = os.environ.get('GITHUB_PRIVATE_KEY', '').replace('\\n', '\n')
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET')

def generate_jwt():
    """Generate JWT for GitHub App authentication"""
    payload = {
        'iat': int(time.time()),
        'exp': int(time.time()) + 600,  # 10 minutes
        'iss': APP_ID
    }
    return jwt.encode(payload, PRIVATE_KEY, algorithm='RS256')

def get_installation_token(installation_id):
    """Get installation access token"""
    jwt_token = generate_jwt()
    headers = {
        'Authorization': f'Bearer {jwt_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    response = requests.post(
        f'https://api.github.com/app/installations/{installation_id}/access_tokens',
        headers=headers
    )
    return response.json().get('token')

def github_api(method, url, installation_id, data=None):
    """Make GitHub API request with installation token"""
    token = get_installation_token(installation_id)
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    response = requests.request(method, f'https://api.github.com{url}', headers=headers, json=data)
    return response.json() if response.content else {}

def auto_label_pr(repo, pr_number, files, installation_id):
    """Enhanced PR labeling with GitHub App"""
    labels = set()
    lines_changed = sum(f.get('changes', 0) for f in files)
    
    # Language and content detection
    for file in files:
        filename = file['filename'].lower()
        ext = '.' + filename.split('.')[-1] if '.' in filename else ''
        
        if ext in LANGUAGE_LABELS:
            labels.add(LANGUAGE_LABELS[ext])
        
        for label, extensions in CONTENT_LABELS.items():
            if any(filename.endswith(e) or e in filename for e in extensions):
                labels.add(label)
    
    # Size labels
    if lines_changed > 500: labels.add('size/large')
    elif lines_changed > 100: labels.add('size/medium')
    else: labels.add('size/small')
    
    if labels:
        github_api('POST', f'/repos/{repo}/issues/{pr_number}/labels', 
                  installation_id, {'labels': list(labels)})

def security_scan_and_comment(repo, pr_number, files, installation_id):
    """Security scan with detailed reporting"""
    vulnerabilities = scan_for_vulnerabilities(files)
    
    if vulnerabilities:
        comment = "🔒 **Security Scan Results:**\n\n"
        for vuln in vulnerabilities:
            severity_emoji = "🚨" if vuln['severity'] == 'high' else "⚠️"
            comment += f"{severity_emoji} **{vuln['type'].replace('_', ' ').title()}** in `{vuln['file']}`\n"
        
        comment += "\n💡 Please review these potential security issues before merging."
        github_api('POST', f'/repos/{repo}/issues/{pr_number}/comments', 
                  installation_id, {'body': comment})

def ai_code_review(files, installation_id, repo, pr_number):
    """AI-powered code review"""
    if not os.environ.get('OPENAI_API_KEY') or len(files) > 5:
        return
    
    diff_text = '\n'.join([f.get('patch', '')[:1000] for f in files[:3]])
    
    try:
        response = requests.post('https://api.openai.com/v1/chat/completions',
            headers={'Authorization': f'Bearer {os.environ.get("OPENAI_API_KEY")}'},
            json={
                'model': 'gpt-3.5-turbo',
                'messages': [{'role': 'user', 'content': f'Review this code diff briefly:\n{diff_text}'}],
                'max_tokens': 300
            })
        
        review = response.json()['choices'][0]['message']['content']
        comment = f"🤖 **AI Code Review:**\n\n{review}"
        github_api('POST', f'/repos/{repo}/issues/{pr_number}/comments', 
                  installation_id, {'body': comment})
    except:
        pass

@app.route('/webhook', methods=['POST'])
def webhook():
    event = request.headers.get('X-GitHub-Event')
    payload = request.json
    installation_id = payload.get('installation', {}).get('id')
    
    if not installation_id:
        return '', 400
    
    if event == 'pull_request':
        action = payload['action']
        repo = payload['repository']['full_name']
        pr = payload['pull_request']
        pr_number = pr['number']
        author = pr['user']['login']
        
        if action == 'opened':
            files = github_api('GET', f'/repos/{repo}/pulls/{pr_number}/files', installation_id)
            
            # All automations
            auto_label_pr(repo, pr_number, files, installation_id)
            security_scan_and_comment(repo, pr_number, files, installation_id)
            
            # Welcome new contributors
            prs = github_api('GET', f'/repos/{repo}/pulls?author={author}&state=all', installation_id)
            if len(prs) == 1:
                welcome_msg = f"""🎉 Welcome @{author}! Thanks for your first contribution!

📋 **Quick checklist:**
- [ ] Tests added/updated
- [ ] Documentation updated  
- [ ] Code follows project style

💡 Use `/help` for available commands. Thanks for contributing! 🚀"""
                github_api('POST', f'/repos/{repo}/issues/{pr_number}/comments', 
                          installation_id, {'body': welcome_msg})
            
            # AI review for small PRs
            ai_code_review(files, installation_id, repo, pr_number)
            
            # PR summary
            summary = generate_pr_summary(files, pr['title'])
            github_api('POST', f'/repos/{repo}/issues/{pr_number}/comments', 
                      installation_id, {'body': summary})
        
        elif action == 'closed' and pr.get('merged'):
            thank_msg = f"🎉 Thanks @{author}! Your contribution has been merged. Great work! 🚀"
            github_api('POST', f'/repos/{repo}/issues/{pr_number}/comments', 
                      installation_id, {'body': thank_msg})
    
    elif event == 'issues' and payload['action'] == 'opened':
        issue = payload['issue']
        repo = payload['repository']['full_name']
        title = issue['title'].lower()
        
        # Auto-label issues
        labels = []
        if any(word in title for word in ['bug', 'error', 'broken', 'crash']):
            labels.append('bug')
        if any(word in title for word in ['feature', 'enhancement', 'add']):
            labels.append('enhancement')
        if any(word in title for word in ['question', '?', 'how']):
            labels.append('question')
        if any(word in title for word in ['urgent', 'critical', 'important']):
            labels.append('priority: high')
        
        if labels:
            github_api('POST', f'/repos/{repo}/issues/{issue["number"]}/labels', 
                      installation_id, {'labels': labels})
    
    elif event == 'issue_comment' and payload['action'] == 'created':
        comment = payload['comment']['body'].strip()
        repo = payload['repository']['full_name']
        issue_number = payload['issue']['number']
        
        if comment.startswith('/'):
            cmd = comment.lower().split()[0]
            
            if cmd == '/help':
                help_text = """🤖 **Available Commands:**

**Management:**
• `/assign @user` - Assign to user
• `/label <name>` - Add label  
• `/close` - Close issue/PR
• `/priority high` - Set priority

**Info:**
• `/changelog` - Recent changes
• `/contributors` - Top contributors
• `/status` - Current status

**Fun:**
• `/joke` - Programming humor
• `/motivate` - Inspiration"""
                github_api('POST', f'/repos/{repo}/issues/{issue_number}/comments', 
                          installation_id, {'body': help_text})
            
            elif cmd.startswith('/assign') and '@' in comment:
                assignee = comment.split('@')[1].split()[0]
                github_api('POST', f'/repos/{repo}/issues/{issue_number}/assignees', 
                          installation_id, {'assignees': [assignee]})
            
            elif cmd.startswith('/label'):
                label = comment.split('/label ')[1].strip()
                github_api('POST', f'/repos/{repo}/issues/{issue_number}/labels', 
                          installation_id, {'labels': [label]})
            
            elif cmd == '/close':
                github_api('PATCH', f'/repos/{repo}/issues/{issue_number}', 
                          installation_id, {'state': 'closed'})
            
            elif cmd == '/changelog':
                prs = github_api('GET', f'/repos/{repo}/pulls?state=closed&sort=updated&per_page=10', installation_id)
                changelog = '# Recent Changes\n\n'
                for pr in prs[:5]:
                    if pr.get('merged_at'):
                        changelog += f"• {pr['title']} (#{pr['number']}) by @{pr['user']['login']}\n"
                github_api('POST', f'/repos/{repo}/issues/{issue_number}/comments', 
                          installation_id, {'body': changelog})
            
            elif cmd == '/joke':
                github_api('POST', f'/repos/{repo}/issues/{issue_number}/comments', 
                          installation_id, {'body': f'😄 {get_random_joke()}'})
            
            elif cmd == '/motivate':
                github_api('POST', f'/repos/{repo}/issues/{issue_number}/comments', 
                          installation_id, {'body': f'💪 {get_random_quote()}'})
    
    return '', 200

@app.route('/setup', methods=['GET'])
def setup_info():
    """Setup instructions endpoint"""
    return f"""
    <h1>GitHub App Setup</h1>
    <p>Your GitHub App is running!</p>
    <p>App ID: {APP_ID}</p>
    <p>Install this app on your repositories to enable automation.</p>
    """

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)