# minimal-bot
A comprehensive GitHub bot that does A LOT of repository automation.

## 🚀 Features

### 🤖 Smart PR Automation
- **Auto-labels** PRs by language, file type, size, and directory
- **Smart reviewer assignment** based on file ownership
- **Security scanning** for hardcoded secrets, SQL injection risks
- **AI code reviews** (with OpenAI integration)
- **PR requirement checks** (tests, docs, file sizes)
- **Welcome messages** for first-time contributors

### 🏷️ Intelligent Issue Management
- **Auto-labels** issues based on title/content keywords
- **Priority detection** from urgent/critical keywords
- **Bug/feature/question classification**

### 💬 Powerful Commands
- `/help` - Complete command reference
- `/assign @user` - Smart assignment
- `/label <name>` - Add labels
- `/close` / `/reopen` - Issue management
- `/changelog` - Generate recent changes
- `/joke` - Developer humor
- `/motivate` - Coding inspiration

### 🔍 Language Detection
Supports: Python, JavaScript, TypeScript, Java, Go, Rust, Ruby, PHP, Swift, C++

### 🛡️ Security Features
- Scans for hardcoded passwords/API keys
- Detects dangerous eval/exec usage
- SQL injection risk detection

### 📊 Analytics & Insights
- Contributor statistics
- Automated changelog generation
- File ownership tracking

## ⚡ Quick Setup
1. Get GitHub token: Settings → Developer settings → Personal access tokens
2. Copy `.env.example` to `.env` and add your tokens
3. Install: `pip install -r requirements.txt`
4. Run: `python bot.py`
5. Add webhook URL to repo settings: `your-domain.com/webhook`

## 🎯 Advanced Features
- **AI Integration**: Add OpenAI key for intelligent code reviews
- **Multi-language**: Detects 10+ programming languages
- **Smart Labeling**: 20+ automatic label categories
- **Security First**: Built-in vulnerability scanning
- **Contributor Friendly**: Welcomes and guides new contributors

## 🔧 Configuration
Optional environment variables:
- `OPENAI_API_KEY` - Enable AI code reviews
- `WEBHOOK_SECRET` - Secure webhook endpoint

---
*This bot does A LOT to make your repository management effortless!* 🎉
