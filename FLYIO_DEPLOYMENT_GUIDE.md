# =============================================================================
# FLY.IO DEPLOYMENT GUIDE - Complete Beginner Tutorial
# =============================================================================
# 🎓 Learning Objectives:
# - Understand server deployment concepts
# - Deploy Python app to production
# - Manage environment variables and secrets
# - Run multiple processes (web + scheduler)
# - Monitor and debug production apps
# =============================================================================

## 📚 PART 1: UNDERSTANDING THE BASICS

### What is Fly.io?
Fly.io is a platform that:
- Runs your Python code on servers around the world
- Keeps your app running 24/7 (even when your laptop is off)
- Provides a web address so people can access your app
- Handles SSL certificates (HTTPS) automatically
- Scales your app if you get more users

Think of it like: **Airbnb for server computers**
- You don't own the computer
- You just rent space to run your code
- They handle maintenance, security, electricity, etc.

---

### Key Terms Explained:

**1. Container (Docker)**
- A "box" that contains your app + all dependencies
- Like a portable computer that works the same everywhere
- Ensures your code runs identically on your laptop and on Fly.io

**2. Process**
- A running program
- Your app has 2 processes:
  * Web process: Flask app (handles button clicks)
  * Scheduler process: Background job (sends digests)

**3. Environment Variables**
- Secret settings stored separately from code
- Like having a "settings.txt" file that doesn't go to GitHub
- Examples: BASE_URL, ADMIN_EMAIL, API keys

**4. Region**
- Physical location of the server
- Closer to users = faster response
- Fly.io has servers worldwide (we'll use one close to you)

**5. Volume**
- Persistent storage for files
- Your `data/` folder that survives restarts
- Like a USB drive attached to the server

---

## 🛠️ PART 2: PREPARING YOUR APP FOR DEPLOYMENT

### Files We Need to Create:

1. **Dockerfile** - Instructions to build your app container
2. **fly.toml** - Fly.io configuration file
3. **.dockerignore** - Files to exclude from deployment
4. **start.sh** - Script to run both web + scheduler
5. **requirements.txt** - Already exists, we'll verify it

Let me explain each file as we create it...

---

## 📝 PART 3: FILE EXPLANATIONS

### 1. Dockerfile (The Recipe)
```dockerfile
# This file tells Fly.io how to build your app

# Start with Python 3.11 base image (pre-installed Python)
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Copy requirements first (for caching - faster rebuilds)
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model for NLP
RUN python -m spacy download en_core_web_sm

# Copy all your code into the container
COPY . .

# Create data directory for storing files
RUN mkdir -p data credentials

# Expose port 8080 (Flask will listen on this)
EXPOSE 8080

# Run the start script
CMD ["sh", "start.sh"]
```

**What this does:**
- Line 1-2: Use Python 3.11 as base (like installing Python on a fresh computer)
- Line 4-5: Set working directory to `/app` folder
- Line 7-10: Install all dependencies from `requirements.txt`
- Line 12-13: Download spaCy AI model
- Line 15-16: Copy your code files
- Line 18-19: Create folders for data storage
- Line 21-22: Tell it what port to use
- Line 24-25: Run your app

---

### 2. fly.toml (Configuration)
```toml
# Fly.io configuration file

app = "email-digest-assistant"  # Your app name (will be email-digest-assistant.fly.dev)

[build]
  # Use Dockerfile to build the app

[env]
  # Environment variables (non-secret)
  PORT = "8080"

[http_service]
  internal_port = 8080  # Port Flask listens on
  force_https = true     # Always use HTTPS
  auto_stop_machines = false  # Keep running 24/7
  auto_start_machines = true
  min_machines_running = 1    # Always have 1 server running

[[vm]]
  memory = '512mb'  # Allocate 512MB RAM (enough for your app)
  cpu_kind = 'shared'  # Use shared CPU (cheaper)
  cpus = 1
```

**What this does:**
- Defines your app name
- Sets memory/CPU resources
- Keeps your app running 24/7 (no sleep)
- Forces HTTPS for security
- Uses 1 virtual machine (stays in free tier)

---

### 3. start.sh (Process Manager)
```bash
#!/bin/bash
# This script starts both Flask and Scheduler

# Start scheduler in background
python scheduler.py &

# Start Flask web app in foreground
python web_app.py
```

**What this does:**
- Runs scheduler.py in background (the `&` means "run in background")
- Runs web_app.py in foreground
- Both processes run simultaneously in one container
- **This is the trick to use only 1 VM instead of 2!**

---

### 4. .dockerignore (Exclusions)
```
# Files to not copy to production
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
venv/
.env
.git/
.gitignore
*.log
test_*.py
docs/
.vscode/
```

**What this does:**
- Excludes unnecessary files from deployment
- Makes deployment faster (smaller container)
- Keeps secrets safe (doesn't copy `.env` file)

---

## 🎯 PART 4: DEPLOYMENT STEPS

### Step 1: Install Fly.io CLI

**Windows (PowerShell):**
```powershell
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

**What happens:**
- Downloads Fly.io command-line tool
- Installs it on your computer
- Allows you to run `fly` commands

**Verify installation:**
```powershell
fly version
```

You should see: `flyctl v0.x.x ...`

---

### Step 2: Sign Up for Fly.io

```powershell
fly auth signup
```

**What happens:**
- Opens browser
- Create account (email + password)
- **NO credit card required** for free tier!
- You get 3 free VMs

---

### Step 3: Login

```powershell
fly auth login
```

**What happens:**
- Opens browser
- Confirms you're logged in
- Saves authentication token on your computer

---

### Step 4: Create App

```powershell
fly launch --no-deploy
```

**What happens:**
- Fly.io scans your code
- Suggests app name: `email-digest-assistant-XXXX`
- Asks: "Choose a region" → Pick closest to you (e.g., `ewr` for US East)
- Creates `fly.toml` configuration file
- **--no-deploy** means "don't deploy yet" (we need to set secrets first)

**Interactive questions:**
```
? App Name: email-digest-assistant-yourname
? Choose a region: ewr (US East)
? Would you like to set up a database? No
? Would you like to set up monitoring? No (for now)
```

---

### Step 5: Set Environment Variables (Secrets)

```powershell
# Set base URL (your app's web address)
fly secrets set BASE_URL="https://email-digest-assistant-yourname.fly.dev"

# Set admin email for error notifications
fly secrets set ADMIN_EMAIL="jesusegunadewunmi@gmail.com"

# If you have other secrets, add them:
# fly secrets set GMAIL_API_KEY="your-key"
```

**What happens:**
- Secrets stored encrypted on Fly.io
- Your code can access them via `os.environ.get('BASE_URL')`
- Never visible in logs or code
- Can't be stolen even if someone sees your GitHub

---

### Step 6: Upload Gmail Credentials

**Important:** Your `credentials/` folder has sensitive files:
- `credentials.json` - Gmail OAuth credentials
- `token.pickle` - Authentication token

**How to handle:**

**Option A: Use Fly.io Volumes (Recommended)**
```powershell
# Create a volume (persistent storage)
fly volumes create email_digest_data --size 1

# SSH into your app and upload files manually (after first deploy)
fly ssh console
# Then upload files
```

**Option B: Include in deployment (Less secure but easier)**
```powershell
# They'll be copied during deployment
# Make sure .dockerignore doesn't exclude them
```

**For learning, let's use Option B** (easier for now).

---

### Step 7: Deploy!

```powershell
fly deploy
```

**What happens (step-by-step):**

1. **Building (2-3 minutes):**
   ```
   ==> Building image
   [+] Building 1.2s (10/10) FINISHED
   ```
   - Fly.io creates container from your Dockerfile
   - Installs all dependencies
   - Packages your code

2. **Pushing (30 seconds):**
   ```
   ==> Pushing image to registry
   ```
   - Uploads container to Fly.io's servers

3. **Deploying (30 seconds):**
   ```
   ==> Deploying to production
   ```
   - Starts your container
   - Runs `start.sh` script
   - Both Flask and Scheduler start

4. **Health Checks:**
   ```
   ==> Monitoring deployment
   ```
   - Fly.io checks if app is responding
   - Makes sure it's running correctly

5. **Success!**
   ```
   ✅ Deployed successfully!
   Visit: https://email-digest-assistant-yourname.fly.dev
   ```

---

### Step 8: Verify Deployment

```powershell
# Check if app is running
fly status

# View logs (real-time)
fly logs

# Check processes
fly ssh console
# Inside: ps aux
```

**Expected output:**
```
Status: running
Health: healthy
Instances: 1
  ID: xxx Region: ewr Process: app
```

---

## 🔍 PART 5: TESTING YOUR DEPLOYED APP

### Test 1: Web Interface
```
Visit: https://email-digest-assistant-yourname.fly.dev
```

You should see your admin dashboard!

### Test 2: Send Digest
```
Visit: https://email-digest-assistant-yourname.fly.dev/send_all_digests
```

Should send digests to all active users.

### Test 3: Scheduler Running
```powershell
fly logs --follow
```

Watch for hourly scheduler checks:
```
⏰ Hourly Check - 2025-10-06 14:00:00
👥 Checking 1 active users
```

---

## 📊 PART 6: MONITORING & DEBUGGING

### View Live Logs
```powershell
# All logs
fly logs

# Follow logs (live stream)
fly logs --follow

# Filter by search term
fly logs --search "ERROR"

# Last 100 lines
fly logs --lines 100
```

### SSH into Server
```powershell
fly ssh console
```

**Inside the container:**
```bash
# Check running processes
ps aux

# Check files
ls -la

# Check data directory
ls data/

# Test Python
python -c "print('Hello from Fly.io!')"

# Exit
exit
```

### Check Resource Usage
```powershell
fly scale show
```

Shows memory/CPU usage.

### Restart App
```powershell
fly deploy --force
```

Redeploys and restarts everything.

---

## 🐛 PART 7: TROUBLESHOOTING

### Problem 1: App Won't Start

**Check logs:**
```powershell
fly logs --lines 200
```

**Common issues:**
- Missing dependencies → Add to `requirements.txt`
- Import errors → Check file paths
- Port mismatch → Verify Flask uses port 8080

### Problem 2: Scheduler Not Running

**Check if both processes started:**
```powershell
fly ssh console
ps aux | grep python
```

Should see 2 Python processes:
- `python scheduler.py`
- `python web_app.py`

### Problem 3: Gmail API Fails

**Check credentials exist:**
```powershell
fly ssh console
ls credentials/
```

Should see:
- `credentials.json`
- `token.pickle`

**If missing:**
Upload them using `fly ssh console` and manually copy.

### Problem 4: Out of Memory

**Check memory usage:**
```powershell
fly scale show
```

**If near limit:**
```powershell
# Increase memory to 1GB
fly scale memory 1024
```

**Note:** This might exceed free tier. First try optimizing code.

---

## 💰 PART 8: STAYING IN FREE TIER

### Free Tier Limits:
- **3 shared-cpu-1x VMs** with 256MB RAM each
- **160GB outbound transfer/month**
- **Up to 3GB persistent storage**

### Your Usage (50 users):
- **1 VM** (combined web + scheduler) ✅
- **~256-512MB RAM** ✅
- **~5GB transfer/month** (1500 emails) ✅

**Verdict: ✅ Easily within free tier!**

### Monitor Usage:
```powershell
fly dashboard
```

Opens browser showing:
- Current usage
- Costs (should be $0)
- Resource graphs

---

## 🎓 PART 9: LEARNING CONCEPTS EXPLAINED

### Why Docker/Containers?

**Without containers:**
- "It works on my laptop but not on server" 😭
- Different Python versions cause issues
- Missing dependencies
- Hard to reproduce environment

**With containers:**
- Same environment everywhere ✅
- All dependencies included ✅
- Works identically on laptop and production ✅
- Easy to move between servers ✅

### Why Environment Variables?

**Bad practice (hardcoding):**
```python
BASE_URL = "https://my-app.fly.dev"  # In code!
ADMIN_EMAIL = "admin@email.com"      # Public in GitHub!
```

**Good practice (env vars):**
```python
BASE_URL = os.environ.get('BASE_URL')  # Stored securely
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')  # Not in code
```

**Benefits:**
- Different values for dev vs production
- Secrets not in GitHub
- Easy to change without redeploying

### Why Multiple Processes in One Container?

**Option 1 (separate containers - costs more):**
```
Container 1: Flask web app
Container 2: Scheduler
Total: 2 VMs = 2x cost
```

**Option 2 (combined - FREE!):**
```
Container 1: Flask + Scheduler
Total: 1 VM = FREE tier
```

We're using Option 2 with `start.sh` script!

---

## 📋 PART 10: MAINTENANCE

### Update Your App

**After making code changes:**
```powershell
# Commit changes to git
git add .
git commit -m "Updated feature X"

# Deploy new version
fly deploy
```

### View App Info
```powershell
fly info
```

Shows:
- App name
- Region
- URL
- Status

### Scale Resources
```powershell
# Show current scale
fly scale show

# Increase memory if needed
fly scale memory 512

# Add more VMs (will exceed free tier)
fly scale count 2
```

### Backup Data
```powershell
# SSH in and download data
fly ssh console
# Inside: tar -czf backup.tar.gz data/
# Exit and download
fly sftp get backup.tar.gz
```

---

## 🎉 PART 11: SUCCESS CHECKLIST

After deployment, verify:

✅ **Web app accessible:**
- Visit: `https://your-app.fly.dev`
- Admin dashboard loads
- User settings page works

✅ **Scheduler running:**
- Check logs for hourly checks
- Wait for scheduled digest time
- Verify digest arrives in email

✅ **Button endpoints work:**
- Click "Send" button in digest email
- Click "Edit" button
- Verify replies are sent

✅ **Within free tier:**
- Check `fly dashboard`
- Usage shows $0.00
- Only 1 VM running

---

## 📚 PART 12: NEXT LEARNING STEPS

Now that you understand:
- Server deployment
- Environment variables
- Docker containers
- Process management
- Monitoring & debugging

**Level up with:**
1. **Custom domains** - Use your own domain name
2. **Database integration** - PostgreSQL on Fly.io
3. **Auto-scaling** - Handle traffic spikes
4. **Multi-region** - Servers worldwide
5. **CI/CD** - Auto-deploy from GitHub

---

## 🆘 GET HELP

**Fly.io Community:**
- Forum: https://community.fly.io
- Docs: https://fly.io/docs
- Discord: https://fly.io/discord

**Your Questions:**
- Ask me anything!
- I'll explain every concept
- No question is too basic

---

## 📝 SUMMARY

**What you learned:**
✅ Server deployment fundamentals
✅ Docker containers and why they matter
✅ Environment variables and secrets
✅ Running multiple processes efficiently
✅ Monitoring and debugging production apps
✅ Staying within free tier limits
✅ Best practices for production deployment

**What you achieved:**
✅ 50-user email digest system running 24/7
✅ Professional deployment on real servers
✅ Completely free (Fly.io free tier)
✅ Production-ready, scalable architecture

**You're now a deployment engineer!** 🚀

---

Ready to create the deployment files?
