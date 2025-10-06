# 🚀 Quick Deployment Commands - Fly.io

## 📋 Pre-Deployment Checklist

Before deploying, verify:

- [ ] `requirements.txt` exists and is complete
- [ ] `Dockerfile` created
- [ ] `fly.toml` created  
- [ ] `start.sh` created
- [ ] `.dockerignore` created
- [ ] `credentials/credentials.json` exists (Gmail OAuth)
- [ ] `credentials/token.pickle` exists (Gmail token)
- [ ] `data/users.json` exists with at least one test user

---

## 🛠️ Installation

### 1. Install Fly.io CLI (Windows)

```powershell
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

### 2. Verify Installation

```powershell
fly version
```

---

## 🔐 Setup & Authentication

### 3. Sign Up (First Time Only)

```powershell
fly auth signup
```

**What happens:** Opens browser, create account (NO credit card required)

### 4. Login

```powershell
fly auth login
```

**What happens:** Opens browser, confirms authentication

---

## 🚀 Initial Deployment

### 5. Initialize App (First Time Only)

```powershell
# Navigate to project directory
cd C:\Users\PC\Desktop\email-digest-assistant

# Launch (but don't deploy yet)
fly launch --no-deploy
```

**Interactive questions:**
- **App Name:** `email-digest-assistant-yourname` (must be unique)
- **Region:** `ewr` (US East) or choose closest to you
- **PostgreSQL database?** No
- **Redis?** No

**What happens:** Creates `fly.toml` configuration file

### 6. Set Environment Variables (Secrets)

```powershell
# Set your app's web address (replace with your actual app name)
fly secrets set BASE_URL="https://email-digest-assistant-yourname.fly.dev"

# Set admin email for error notifications
fly secrets set ADMIN_EMAIL="jesusegunadewunmi@gmail.com"

# Optional: Set Flask environment
fly secrets set FLASK_ENV="production"
```

**What happens:** Stores secrets encrypted on Fly.io servers

### 7. Deploy!

```powershell
fly deploy
```

**What happens:**
1. Builds Docker image (2-3 minutes first time)
2. Pushes to Fly.io registry (30 seconds)
3. Deploys to production (30 seconds)
4. Starts your app

**Expected output:**
```
==> Building image
==> Pushing image to registry
==> Deploying
✅ Deployed successfully!
Visit: https://email-digest-assistant-yourname.fly.dev
```

---

## ✅ Verification

### 8. Check Status

```powershell
fly status
```

**Expected output:**
```
Status: running
Health: healthy
Instances: 1 running
```

### 9. View Logs (Real-Time)

```powershell
fly logs --follow
```

**What to look for:**
```
🚀 Starting Email Digest Assistant...
📅 Starting scheduler process...
✅ Scheduler started
🌐 Starting Flask web app on port 8080...
 * Running on http://0.0.0.0:8080
```

Press `Ctrl+C` to stop watching logs.

### 10. Test Web Interface

```
Visit: https://email-digest-assistant-yourname.fly.dev
```

Should show your admin dashboard!

---

## 🔄 Updates & Maintenance

### Redeploy After Code Changes

```powershell
# After editing code:
fly deploy
```

### View App Information

```powershell
fly info
```

### Open App in Browser

```powershell
fly open
```

### SSH into Server

```powershell
fly ssh console
```

**Useful commands inside:**
```bash
# Check running processes
ps aux | grep python

# View files
ls -la

# Check data directory
ls data/

# Check logs
tail -f data/scheduler.log

# Exit
exit
```

---

## 📊 Monitoring

### View Dashboard

```powershell
fly dashboard
```

**Opens browser showing:**
- Current usage
- Costs (should be $0.00)
- Resource graphs
- Deployment history

### Check Logs (Last 100 Lines)

```powershell
fly logs --lines 100
```

### Search Logs

```powershell
# Find errors
fly logs --search "ERROR"

# Find specific user
fly logs --search "test_user"
```

### Check Resource Usage

```powershell
fly scale show
```

**Shows:**
- Memory usage
- CPU type
- Number of machines

---

## 🐛 Troubleshooting

### App Won't Start

```powershell
# View detailed logs
fly logs --lines 200

# Check if processes are running
fly ssh console
ps aux
```

### Reset Everything

```powershell
# Delete and recreate
fly destroy email-digest-assistant-yourname
fly launch
```

### Increase Memory (if needed)

```powershell
fly scale memory 1024
```

**Note:** Might exceed free tier

### Force Restart

```powershell
fly deploy --force
```

---

## 💰 Free Tier Management

### Check Current Usage

```powershell
fly dashboard
```

Look for:
- Machines: Should show 1
- Cost: Should show $0.00
- Memory: Should show 512MB

### Verify Free Tier

Your setup uses:
- ✅ 1 VM (free tier includes 3)
- ✅ 512MB RAM (free tier includes up to 256MB × 3)
- ✅ Minimal bandwidth (well under 160GB limit)

**You're well within free tier limits!**

---

## 🔐 Security Best Practices

### Never Commit Secrets

```powershell
# Make sure .gitignore includes:
credentials/
*.pickle
.env
```

### Rotate Secrets

```powershell
# Update a secret
fly secrets set ADMIN_EMAIL="newemail@example.com"

# List secrets (values hidden)
fly secrets list
```

### Secure Gmail Credentials

After first deployment, verify:
```powershell
fly ssh console
ls credentials/
# Should see: credentials.json, token.pickle
```

---

## 🎯 Common Tasks

### Send Test Digest

```
Visit: https://your-app.fly.dev/send_digest/test_user
```

### Check Scheduler

```powershell
fly logs --follow | grep "Hourly Check"
```

### Preview Digest

```
Visit: https://your-app.fly.dev/preview_digest/test_user
```

### Add New User

```
Visit: https://your-app.fly.dev/oauth_login
```

---

## 📱 Mobile Testing

### Test on Mobile

1. Visit your app URL on phone
2. Admin dashboard should be responsive
3. Receive digest email
4. Click buttons - should work on mobile

---

## 🆘 Emergency Commands

### Stop App

```powershell
fly scale count 0
```

### Restart App

```powershell
fly scale count 1
```

### View All Apps

```powershell
fly apps list
```

### Delete App Completely

```powershell
fly destroy email-digest-assistant-yourname
```

---

## 📈 Scaling (Beyond Free Tier)

### Add More Machines

```powershell
# Add a second machine (exceeds free tier)
fly scale count 2
```

### Increase Memory

```powershell
# Increase to 1GB (might exceed free tier)
fly scale memory 1024
```

### Dedicated CPU

```powershell
# Use dedicated CPU (exceeds free tier)
fly scale vm dedicated-cpu-1x
```

---

## 🎓 Learning Resources

### Official Docs
- Getting Started: https://fly.io/docs/getting-started/
- Python Guide: https://fly.io/docs/languages-and-frameworks/python/
- Fly.io CLI Reference: https://fly.io/docs/flyctl/

### Community
- Forum: https://community.fly.io
- Discord: https://fly.io/discord

---

## ✅ Success Criteria

After deployment, verify:

- [ ] `fly status` shows "running"
- [ ] Web interface accessible at your-app.fly.dev
- [ ] Logs show both Flask and Scheduler running
- [ ] Can send test digest
- [ ] Buttons in email work
- [ ] Scheduler checks every hour
- [ ] Usage shows $0.00 (free tier)

---

## 🎉 You're Deployed!

Your email digest system is now running 24/7 on production servers!

**Your app URL:** `https://email-digest-assistant-yourname.fly.dev`

**What's happening right now:**
- Scheduler checking every hour
- Flask web server handling requests
- Ready to send digests to 50 users
- Completely free!

---

## 📞 Need Help?

If anything goes wrong:

1. Check logs: `fly logs`
2. SSH in: `fly ssh console`
3. Ask me! I'm here to help
4. Check Fly.io docs: https://fly.io/docs

Happy deploying! 🚀
