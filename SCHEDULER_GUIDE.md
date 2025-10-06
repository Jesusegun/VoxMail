# 📅 Email Digest Scheduler Guide

## Overview

The `scheduler.py` file provides **automated daily digest delivery** for all users in your email digest system. Instead of manually triggering digests through the web interface, the scheduler runs continuously in the background and automatically sends digests to users at their preferred times.

---

## 🎯 What Problem Does It Solve?

### **Before (Manual System):**
- ❌ You had to manually visit `/send_digest/<user_id>` for each user
- ❌ No automatic daily execution
- ❌ `/send_all_digests` was just a skeleton (didn't actually work)
- ❌ Users couldn't receive digests at their preferred times automatically

### **After (Automated Scheduler):**
- ✅ Runs continuously 24/7
- ✅ Automatically checks every hour if any user needs their digest
- ✅ Respects each user's timezone and preferred delivery time
- ✅ Handles weekend preferences and vacation mode
- ✅ Logs all activities for monitoring
- ✅ Sends error notifications to admin if something fails

---

## 🚀 How It Works

### **Workflow:**

```
Every Hour:
  ↓
Check all active users
  ↓
For each user, check:
  - Is it their preferred hour? (e.g., 8 AM in their timezone)
  - Are they in vacation mode? (Skip if yes)
  - Is it a weekend and they have weekend preferences?
  ↓
If conditions met:
  1. Generate digest using CompleteEmailAgent (AI processing)
  2. Create beautiful HTML email using email_templates.py
  3. Send via Gmail API
  4. Store email data for button actions (Send/Edit/Archive)
  5. Record statistics and success/failure
  ↓
Continue to next user
  ↓
Sleep for 60 seconds and repeat check
```

### **Example Timeline:**

```
7:00 AM UTC - Scheduler checks
  → No users scheduled for 7 AM
  → Waits for next hour

8:00 AM UTC - Scheduler checks
  → User1 (timezone: UTC, digest_time: 8) ✓ Send digest
  → User2 (timezone: PST, digest_time: 8) → Still 12 AM for them, skip
  → User3 (vacation_mode: true) → Skip
  → Sends digest to User1

9:00 AM UTC - Scheduler checks
  → User4 (timezone: EST, digest_time: 9) → It's 4 AM EST, skip
  → No digests to send

... continues 24/7
```

---

## 📋 Features

### **1. User Preferences Respected:**
- ⏰ **Preferred Time**: Each user sets their preferred hour (0-23)
- 🌍 **Timezone Support**: Uses `pytz` to handle different timezones
- 📅 **Weekend Modes**:
  - `full`: Send normal digest on weekends
  - `urgent_only`: Only urgent emails on weekends
  - `off`: No digests on weekends
- ✈️ **Vacation Mode**: Skip users who are on vacation

### **2. AI Processing:**
- Uses your `CompleteEmailAgent` for sophisticated email analysis
- Generates AI summaries, priority scoring, and smart replies
- No dumbing down - full AI power for each digest

### **3. Error Handling:**
- Catches and logs all errors
- Continues to other users if one fails
- Sends admin notification emails when digests fail
- Records failures in digest history

### **4. Monitoring & Logging:**
- Logs to console with emojis for easy reading
- Writes to `data/scheduler.log` for persistent records
- Tracks statistics:
  - Total digests sent
  - Total emails processed
  - Failed digests
  - Uptime

### **5. Production Ready:**
- Can run as standalone process
- Handles rate limiting (2-second delay between users)
- Graceful shutdown on Ctrl+C
- Compatible with Heroku/Railway deployment

---

## 🛠️ Setup Instructions

### **1. Install Required Dependencies**

Make sure you have all required packages:

```powershell
# Activate virtual environment first
venv\Scripts\activate

# Install scheduler dependency (if not already installed)
pip install schedule pytz

# Verify all dependencies
pip install -r requirements.txt
```

### **2. Verify Your System Files**

Make sure these files exist:
- ✅ `scheduler.py` (just created)
- ✅ `web_app.py` (for user/digest management logic)
- ✅ `complete_advanced_ai_processor.py` (AI system)
- ✅ `email_templates.py` (HTML email generation)
- ✅ `auth_test.py` (Gmail authentication)
- ✅ `data/users.json` (user data)
- ✅ `credentials/credentials.json` (Gmail OAuth)
- ✅ `credentials/token.pickle` (Gmail token)

### **3. Test Users Configuration**

Check your `data/users.json`:

```json
{
  "test_user": {
    "email": "jesusegunadewunmi@gmail.com",
    "digest_time": 8,
    "timezone": "UTC",
    "weekend_digests": "urgent_only",
    "vacation_mode": false,
    "created_at": "2025-10-06T10:00:00"
  }
}
```

### **4. Run the Scheduler**

#### **Testing Mode (Local):**

```powershell
# Make sure you're in the project directory
cd C:\Users\PC\Desktop\email-digest-assistant

# Activate virtual environment
venv\Scripts\activate

# Run scheduler
python scheduler.py
```

You should see:
```
✅ Successfully imported system components
============================================================
🚀 Initializing Email Digest Scheduler
============================================================
📊 Loaded 1 users
⏰ Scheduler ready to run
============================================================
🤖 Email Digest Scheduler Starting
============================================================
⏰ Will check every hour for scheduled digests
👥 Managing 1 users
📧 Base URL: http://localhost:5000
============================================================
🚀 Running immediate check on startup...
```

#### **Production Mode (Background Process):**

For deployment platforms like **Heroku** or **Railway**, add to `Procfile`:

```
web: python web_app.py
scheduler: python scheduler.py
```

This runs both processes simultaneously.

---

## 🧪 Testing the Scheduler

### **Option 1: Immediate Test**

Temporarily modify your test user's `digest_time` to the current hour:

```json
{
  "test_user": {
    "digest_time": 14,  // If it's currently 2 PM (14:00)
    "timezone": "UTC"
  }
}
```

Save the file and run the scheduler - it will send immediately!

### **Option 2: Manual Trigger**

You can also test digest generation without the scheduler:

```powershell
python
```

```python
from scheduler import DigestScheduler

scheduler = DigestScheduler()
scheduler.check_and_send_digests()  # Force check now
```

### **Option 3: Web Interface Test**

While scheduler is running, you can still use web interface:
- Visit `http://localhost:5000/preview_digest/test_user`
- Check what digest would look like without sending

---

## 📊 Monitoring

### **1. Live Console Output**

The scheduler shows live status:

```
ℹ️ [2025-10-06 08:00:00] [INFO] ⏰ Hourly Check - 2025-10-06 08:00:00
ℹ️ [2025-10-06 08:00:01] [INFO] 👥 Checking 5 active users
ℹ️ [2025-10-06 08:00:01] [INFO] 📋 User john@example.com scheduled for digest
ℹ️ [2025-10-06 08:00:02] [INFO] 🤖 Generating digest for john@example.com
✅ [2025-10-06 08:00:15] [SUCCESS] ✅ Digest generated: 25 emails
✅ [2025-10-06 08:00:18] [SUCCESS] ✅ Digest sent successfully
```

### **2. Log Files**

Check `data/scheduler.log` for persistent records:

```powershell
# View last 50 lines of log
Get-Content data\scheduler.log -Tail 50

# Watch log in real-time
Get-Content data\scheduler.log -Wait
```

### **3. Statistics**

The scheduler prints stats after each hourly run:

```
============================================================
📊 Scheduler Statistics:
   Total digests sent: 142
   Total emails processed: 3,567
   Failed digests: 2
   Running since: 2025-10-01T08:00:00
============================================================
```

### **4. Error Notifications**

If a digest fails, admin receives email:

```
Subject: 🚨 Email Digest Error - user@example.com

Failed to send digest to user@example.com

Error: Gmail API authentication failed

Time: 2025-10-06 10:30:00

Please check the scheduler logs for more details.
```

---

## 🔧 Configuration

### **Environment Variables:**

```powershell
# Set base URL for production
$env:BASE_URL = "https://your-app.railway.app"

# Set admin email for error notifications
$env:ADMIN_EMAIL = "admin@yourdomain.com"
```

### **User Settings (per user in `data/users.json`):**

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `digest_time` | int (0-23) | 8 | Hour to send digest (24-hour format) |
| `timezone` | string | "UTC" | User's timezone (e.g., "America/New_York") |
| `weekend_digests` | string | "urgent_only" | Options: "full", "urgent_only", "off" |
| `vacation_mode` | boolean | false | Skip digests when on vacation |
| `vacation_delegate` | string | "" | (Future) Forward to delegate |

---

## 🐛 Troubleshooting

### **Problem: Scheduler doesn't send digests**

**Check:**
1. Is the current hour matching a user's `digest_time`?
2. Is the user in `vacation_mode: false`?
3. Are there new emails to process?
4. Check logs in `data/scheduler.log`

**Solution:**
```powershell
# Test with current hour
python
from scheduler import SimplifiedUserManager
um = SimplifiedUserManager()
user = um.get_user('test_user')
print(f"Digest time: {user['digest_time']}")
print(f"Current hour: {datetime.now().hour}")
```

### **Problem: Gmail authentication fails**

**Check:**
1. Does `credentials/token.pickle` exist?
2. Is it expired?

**Solution:**
```powershell
# Delete old token and re-authenticate
rm credentials\token.pickle
python auth_test.py
```

### **Problem: Scheduler crashes**

**Check:**
1. View error in console or `data/scheduler.log`
2. Common issues:
   - Missing dependencies
   - Invalid user data in `users.json`
   - Gmail API rate limits

**Solution:**
```powershell
# Validate JSON files
python -m json.tool data\users.json

# Test AI system separately
python test_ai_integration.py
```

---

## 🚀 Deployment

### **Heroku:**

1. Create `Procfile`:
```
web: python web_app.py
scheduler: python scheduler.py
```

2. Deploy:
```bash
heroku create your-app-name
git push heroku main
heroku ps:scale web=1 scheduler=1
```

3. View logs:
```bash
heroku logs --tail --ps scheduler
```

### **Railway:**

1. Connect GitHub repo
2. Add environment variables (BASE_URL, ADMIN_EMAIL)
3. Railway auto-detects Procfile
4. Both processes run automatically

### **Local (Development):**

Run in separate terminals:

**Terminal 1 (Web App):**
```powershell
venv\Scripts\activate
python web_app.py
```

**Terminal 2 (Scheduler):**
```powershell
venv\Scripts\activate
python scheduler.py
```

---

## 📈 Next Steps

Now that scheduler is working:

1. ✅ **Fix `/send_all_digests` route** in `web_app.py` (if you want manual bulk send)
2. ✅ **Implement Archive functionality** (actually archive in Gmail, not just record)
3. ✅ **Add more users** via OAuth: `/oauth_login`
4. ✅ **Monitor performance** using scheduler statistics
5. ✅ **Set up alerts** for failed digests
6. ✅ **Deploy to production** (Heroku/Railway)

---

## ❓ FAQ

**Q: Can I change how often it checks?**  
A: Yes! In `scheduler.py`, change:
```python
schedule.every().hour.at(":00").do(self.check_and_send_digests)
# To check every 30 minutes:
schedule.every(30).minutes.do(self.check_and_send_digests)
```

**Q: Can I send digests at specific times like 8:30 AM?**  
A: Currently supports hourly (8:00, 9:00, etc.). For 8:30, you'd need to enhance the scheduler to check minutes as well.

**Q: What happens if scheduler crashes?**  
A: On platforms like Heroku/Railway, it auto-restarts. For local/VPS, use a process manager like `pm2` or `systemd`.

**Q: Does it handle daylight saving time?**  
A: Yes! The `pytz` library handles DST transitions automatically.

**Q: Can I see which users will receive digest next hour?**  
A: Add this debug script:
```python
from scheduler import DigestScheduler
from datetime import datetime, timedelta

scheduler = DigestScheduler()
next_hour = datetime.now() + timedelta(hours=1)

for user_id, user_data in scheduler.user_manager.users.items():
    if scheduler.user_manager.should_send_digest(user_data, next_hour):
        print(f"📧 {user_data['email']} scheduled for next hour")
```

---

## 📝 Summary

The scheduler is now **fully implemented and production-ready**! It:

✅ Automatically sends digests at user-preferred times  
✅ Respects timezones, weekends, and vacation mode  
✅ Uses your full AI system (no compromises)  
✅ Logs everything for monitoring  
✅ Handles errors gracefully  
✅ Ready for deployment to Heroku/Railway  

**To start using it:**
```powershell
venv\Scripts\activate
python scheduler.py
```

That's it! Your email digest system is now fully automated! 🎉
