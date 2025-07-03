# GitHub App Setup Guide

## 1. Create GitHub App

1. Go to GitHub → Settings → Developer settings → GitHub Apps
2. Click **"New GitHub App"**
3. Fill in details:
   - **App name**: `your-repo-bot` (must be unique)
   - **Homepage URL**: `https://your-domain.com`
   - **Webhook URL**: `https://your-domain.com/webhook`
   - **Webhook secret**: Generate a random string

## 2. Set Permissions

**Repository permissions:**
- Contents: Read
- Issues: Write
- Metadata: Read
- Pull requests: Write
- Commit statuses: Write

**Subscribe to events:**
- [x] Issues
- [x] Issue comments  
- [x] Pull requests
- [x] Pull request reviews

## 3. Generate Private Key

1. Scroll down to **"Private keys"**
2. Click **"Generate a private key"**
3. Download the `.pem` file

## 4. Configure Environment

```bash
# Copy template
cp .env.example .env

# Edit .env with your values:
GITHUB_APP_ID=123456
GITHUB_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\nYOUR_KEY_HERE\n-----END RSA PRIVATE KEY-----"
WEBHOOK_SECRET=your_webhook_secret
OPENAI_API_KEY=optional_for_ai_reviews
```

## 5. Install & Run

```bash
pip install -r requirements.txt
python github_app.py
```

## 6. Install App on Repositories

1. Go to your GitHub App settings
2. Click **"Install App"**
3. Choose repositories to install on
4. Grant permissions

## 7. Deploy (Production)

### Heroku:
```bash
git add .
git commit -m "GitHub App setup"
git push heroku main
```

### Railway/DigitalOcean:
- Connect your GitHub repo
- Set environment variables in dashboard
- Deploy automatically

## 8. Test Installation

1. Create a PR in an installed repository
2. Watch for auto-labels and comments
3. Try commands like `/help` in issue comments
4. Check security scanning and AI reviews

Your GitHub App is now ready to automate repositories! 🚀