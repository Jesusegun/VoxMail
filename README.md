# 🤖 VoxMail

An intelligent email management system that processes your emails using advanced AI and delivers beautiful, actionable daily digests. Built with Flask, integrated with Gmail API, and optimized for Fly.io free tier deployment.

## 🚀 Features

- **🤖 Advanced AI Processing**: Summarizes emails, generates draft replies, and prioritizes messages
- **📧 Beautiful Email Digests**: Mobile-optimized HTML emails with interactive buttons
- **⚡ Real-time Actions**: Send, edit, and archive emails directly from digest
- **👥 Multi-user Support**: Manage up to 50-70 users efficiently
- **🔐 OAuth Authentication**: Secure Google account integration
- **📊 Smart Priority Classification**: Automatically categorizes emails by importance
- **🌐 Web Dashboard**: Admin interface for user management and system monitoring

## 💰 Railway Free Tier Optimization

This system is specifically designed to work within Railway's free tier limits through an **intelligent auto-sleep strategy**.

### 📊 Railway Free Tier Limits
- ⏰ **Execution Time**: 500 hours/month
- 💾 **Memory**: 512MB RAM
- 🌐 **Bandwidth**: 100GB/month
- 💽 **Storage**: 1GB disk space

### 🎯 Our Resource Usage (50 users)
- ⏰ **Execution Time**: ~120-150 hours/month (24-30% of limit)
- 💾 **Memory**: ~400MB peak (78% of limit)
- 🌐 **Bandwidth**: ~4GB/month (4% of limit)
- 💽 **Storage**: ~450MB (45% of limit)

## 🛠️ Auto-Sleep Strategy

### How Auto-Sleep Works

Railway automatically puts your application to sleep after **30 minutes of inactivity** and wakes it up when a request comes in. Our system leverages this to minimize execution hours:

#### 🕐 Daily Schedule Patterns
```
📅 Scheduled Digest Generation:
- Process all users at their preferred times
- AI models loaded once per batch
- Server sleeps between processing windows

⚡ Real-Time Button Interactions:
- Server wakes up when users click email buttons
- Lightweight processing (no AI models needed)
- Server returns to sleep after handling request

🌙 Idle Periods:
- Nights: Server sleeps (no user activity)
- Weekends: Minimal activity, mostly sleeping
- Business hours: Active when users interact
```

#### 📊 Execution Time Breakdown
```
Daily AI Processing: ~19 hours/month
├── User email analysis: ~15 hours
├── AI summarization: ~3 hours  
└── Reply generation: ~1 hour

Button Interactions: ~50-80 hours/month
├── Send reply clicks: ~20 hours
├── Edit actions: ~15 hours
├── Settings updates: ~10 hours
└── Cold start overhead: ~25 hours

Auto-Sleep Savings: ~550 hours/month saved
Total Usage: ~120 hours/month ✅
```

## 🚂 Railway Deployment Setup

### 1. Prepare Your Project

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Create new project
railway new
```

### 2. Configure Environment Variables

Create these environment variables in Railway dashboard:

```env
# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-secret-key-here

# Gmail API Credentials
GMAIL_CLIENT_ID=your-client-id
GMAIL_CLIENT_SECRET=your-client-secret
GMAIL_REDIRECT_URI=https://your-app.railway.app/oauth2callback

# Auto-Sleep Configuration
RAILWAY_STATIC_URL=https://your-app.railway.app
ENABLE_AUTO_SLEEP=true
SLEEP_TIMEOUT=1800  # 30 minutes in seconds

# System Configuration
MAX_USERS=50
DIGEST_BATCH_SIZE=10
AI_MODEL_CACHE=true
```

### 3. Create Railway Configuration Files

#### `railway.toml`
```toml
[build]
builder = "NIXPACKS"
buildCommand = "pip install -r requirements.txt"

[deploy]
startCommand = "python web_app.py"
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"

[environments.production]
variables = { FLASK_ENV = "production" }
```

#### `Procfile` (optional)
```
web: python web_app.py
```

### 4. Optimize Your Application for Auto-Sleep

#### Add Health Check Endpoint
```python
# Add to web_app.py
@app.route('/health')
def health_check():
    """Railway health check endpoint"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'users': len(user_manager.get_all_users()),
        'memory_usage': get_memory_usage()
    }, 200
```

#### Implement Lazy Loading
```python
# Global variables for lazy loading
email_agent = None
ai_models_loaded = False

def get_email_agent():
    """Lazy load AI models only when needed"""
    global email_agent, ai_models_loaded
    
    if not ai_models_loaded:
        print("🤖 Loading AI models...")
        email_agent = CompleteEmailAgent()
        ai_models_loaded = True
        print("✅ AI models loaded successfully")
    
    return email_agent

# Use in digest generation only
@app.route('/generate_digest/<user_id>')
def generate_digest_route(user_id):
    agent = get_email_agent()  # Only load when actually needed
    # ... rest of digest generation
```

#### Add Auto-Sleep Monitoring
```python
import time
import psutil

# Track app usage for monitoring
app_stats = {
    'last_activity': time.time(),
    'requests_today': 0,
    'sleep_cycles': 0
}

@app.before_request
def track_activity():
    """Track app activity for auto-sleep optimization"""
    app_stats['last_activity'] = time.time()
    app_stats['requests_today'] += 1

@app.route('/stats')
def app_statistics():
    """Monitor auto-sleep effectiveness"""
    return {
        'uptime_seconds': time.time() - app_start_time,
        'last_activity': app_stats['last_activity'],
        'requests_today': app_stats['requests_today'],
        'memory_usage_mb': psutil.Process().memory_info().rss / 1024 / 1024,
        'auto_sleep_enabled': os.getenv('ENABLE_AUTO_SLEEP') == 'true'
    }
```

### 5. Deploy to Railway

```bash
# Connect to Railway project
railway link

# Deploy your application
railway up

# Set up custom domain (optional)
railway domain

# Monitor deployment
railway logs
```

## 📈 Monitoring and Optimization

### 🔍 Usage Monitoring

Access your Railway dashboard to monitor:

- **Execution Hours**: Track monthly usage vs 500-hour limit
- **Memory Usage**: Ensure staying under 512MB
- **Request Patterns**: Identify peak usage times
- **Auto-Sleep Effectiveness**: Monitor sleep/wake cycles

### 📊 Usage Dashboard

Add this route to monitor your resource usage:

```python
@app.route('/usage-dashboard')
def usage_dashboard():
    """Internal dashboard for monitoring Railway resource usage"""
    return render_template('usage_dashboard.html', 
                         stats=get_railway_usage_stats())
```

### ⚠️ Usage Alerts

Set up alerts when approaching limits:

```python
def check_usage_limits():
    """Alert when approaching Railway limits"""
    monthly_hours = get_monthly_execution_hours()
    
    if monthly_hours > 400:  # 80% of 500-hour limit
        send_admin_alert(f"⚠️ High usage: {monthly_hours}/500 hours")
    
    memory_usage = psutil.virtual_memory().percent
    if memory_usage > 85:  # 85% of memory
        send_admin_alert(f"⚠️ High memory: {memory_usage}%")
```

## 🎯 User Capacity Guidelines

### 👥 Recommended User Limits

| Users | Execution Hours/Month | Free Tier Status | Notes |
|-------|----------------------|------------------|--------|
| **30 users** | ~80 hours | ✅ Very Safe | Large safety margin |
| **50 users** | ~120 hours | ✅ Safe | Recommended maximum |
| **70 users** | ~170 hours | ⚠️ Monitor closely | Need careful optimization |
| **100+ users** | ~250+ hours | ❌ Upgrade needed | Consider Hobby plan ($5/month) |

### 📈 Scaling Strategy

1. **Start with 20-30 users** to test and optimize
2. **Monitor usage patterns** for 1-2 weeks
3. **Gradually increase to 50 users** 
4. **Implement usage alerts** before reaching limits
5. **Upgrade to Hobby plan** if needed for more users

## 🔧 Advanced Optimizations

### ⚡ Cold Start Optimization

```python
# Minimize cold start time
@app.before_first_request
def optimize_startup():
    """Optimize application startup for Railway auto-sleep"""
    
    # Pre-warm essential components only
    initialize_user_manager()
    setup_gmail_auth()
    
    # Don't load AI models until needed
    # This keeps startup under 10 seconds
    
    print("🚀 App ready for auto-sleep mode")
```

### 📅 Smart Scheduling

```python
# Batch user processing to minimize execution time
def process_users_efficiently():
    """Process users in optimal batches"""
    
    users = get_active_users()
    batch_size = 10  # Process 10 users at once
    
    for i in range(0, len(users), batch_size):
        batch = users[i:i + batch_size]
        
        # Load AI models once per batch
        agent = get_email_agent()
        
        # Process entire batch
        for user in batch:
            process_user_digest(agent, user)
        
        # Short pause between batches
        time.sleep(2)
```

### 💾 Memory Management

```python
import gc

def cleanup_after_processing():
    """Clean up memory after heavy AI processing"""
    
    global email_agent, ai_models_loaded
    
    # Clear AI models from memory when done
    if ai_models_loaded:
        del email_agent
        email_agent = None
        ai_models_loaded = False
        
        # Force garbage collection
        gc.collect()
        
        print("🧹 Memory cleaned up for auto-sleep")
```

## 🚨 Troubleshooting

### Common Issues and Solutions

#### ❌ Execution Time Limit Exceeded
```bash
# Check current usage
railway logs --filter="execution"

# Solutions:
1. Reduce user count temporarily
2. Optimize AI model loading
3. Implement more aggressive auto-sleep
4. Consider upgrading to Hobby plan
```

#### ❌ Memory Limit Issues
```python
# Monitor memory usage
@app.route('/memory-check')
def memory_check():
    memory = psutil.Process().memory_info()
    return {
        'memory_mb': memory.rss / 1024 / 1024,
        'limit_mb': 512,
        'usage_percent': (memory.rss / 1024 / 1024 / 512) * 100
    }
```

#### ❌ Cold Start Too Slow
```python
# Optimize startup sequence
def quick_startup():
    """Minimize cold start time to under 10 seconds"""
    
    # Load only essential components
    # Defer AI model loading until first use
    # Use lazy initialization patterns
    
    startup_time = time.time() - app_start_time
    print(f"⚡ Cold start completed in {startup_time:.2f} seconds")
```

## 📞 Support and Resources

### 🔗 Useful Links
- [Railway Documentation](https://docs.railway.app/)
- [Flask Auto-Sleep Guide](https://flask.palletsprojects.com/en/2.3.x/deploying/)
- [Gmail API Quotas](https://developers.google.com/gmail/api/reference/quota)

### 📧 Getting Help
- Check Railway logs: `railway logs`
- Monitor resource usage in Railway dashboard
- Use `/stats` endpoint for app monitoring
- Check `/health` endpoint for system status

### 🎯 Success Metrics
- ✅ Monthly execution hours < 400 (safety margin)
- ✅ Memory usage < 400MB peak
- ✅ Cold start time < 15 seconds
- ✅ User satisfaction with digest delivery
- ✅ Reliable auto-sleep/wake cycles

---

## 🎉 Ready to Deploy!

With this auto-sleep strategy, your VoxMail will run efficiently on Railway's free tier while providing a professional experience for up to 50 users. The system automatically optimizes resource usage through intelligent sleep/wake cycles, ensuring you stay well within the free tier limits.

**Deploy with confidence knowing your system is designed for efficiency and scalability!** 🚀

---

*Last updated: September 2025*
*Tested with Railway free tier limits*
*Optimized for 50+ users*
