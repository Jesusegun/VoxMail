#!/bin/bash
# =============================================================================
# VPS Deployment Script for Multi-User OAuth System
# =============================================================================
# Run this script on your VPS: ssh root@46.101.177.154
# Or copy-paste commands one by one
# =============================================================================

echo "🚀 Starting VoxMail Multi-User OAuth Deployment"
echo "================================================"
echo ""

# Step 1: Navigate to project directory
echo "📂 Step 1: Navigating to project directory..."
cd /root/VoxMail || { echo "❌ Directory not found"; exit 1; }
echo "✅ Current directory: $(pwd)"
echo ""

# Step 2: Check current status
echo "📊 Step 2: Checking current status..."
echo "Git branch:"
git branch
echo ""
echo "Docker containers:"
docker ps -a | grep voxmail
echo ""

# Step 3: Pull latest code from GitHub
echo "⬇️  Step 3: Pulling latest code from GitHub..."
git pull origin main
if [ $? -eq 0 ]; then
    echo "✅ Code pulled successfully"
else
    echo "❌ Git pull failed - check for conflicts"
    exit 1
fi
echo ""

# Step 4: Update .env file with ADMIN_EMAIL
echo "🔧 Step 4: Updating .env file..."
if grep -q "ADMIN_EMAIL" .env; then
    echo "⚠️  ADMIN_EMAIL already exists in .env"
else
    echo "ADMIN_EMAIL=jesusegunadewunmi@gmail.com" >> .env
    echo "✅ Added ADMIN_EMAIL to .env"
fi
echo ""
echo "Current .env contents:"
cat .env
echo ""

# Step 5: Rebuild Docker image
echo "🔨 Step 5: Building new Docker image..."
docker build -t voxmail:latest . || { echo "❌ Docker build failed"; exit 1; }
echo "✅ Docker image built successfully"
echo ""

# Step 6: Stop and remove old container
echo "🛑 Step 6: Stopping old container..."
docker stop voxmail 2>/dev/null
docker rm voxmail 2>/dev/null
echo "✅ Old container removed"
echo ""

# Step 7: Start new container
echo "🚀 Step 7: Starting new container..."
docker run -d --name voxmail -p 8080:8080 \
  -v /root/VoxMail/data:/app/data \
  -v /root/VoxMail/ai_data:/app/ai_data \
  -v /root/VoxMail/credentials:/app/credentials \
  --env-file .env --restart unless-stopped voxmail:latest

if [ $? -eq 0 ]; then
    echo "✅ Container started successfully"
else
    echo "❌ Container start failed"
    exit 1
fi
echo ""

# Step 8: Wait for container to initialize
echo "⏳ Step 8: Waiting for container to initialize (10 seconds)..."
sleep 10
echo ""

# Step 9: Check container status
echo "📊 Step 9: Checking container status..."
docker ps | grep voxmail
echo ""

# Step 10: Show recent logs
echo "📋 Step 10: Showing recent logs..."
echo "================================================"
docker logs --tail 50 voxmail
echo "================================================"
echo ""

# Step 11: Look for migration message
echo "🔍 Step 11: Checking for token migration..."
if docker logs voxmail 2>&1 | grep -q "Token migrated"; then
    echo "✅ Token migration completed successfully"
    docker logs voxmail 2>&1 | grep -A 3 "Migrating existing OAuth"
else
    echo "⚠️  No migration detected - check if old token exists"
fi
echo ""

# Step 12: Verify new files exist
echo "📁 Step 12: Verifying new files..."
if [ -f "auth_multiuser.py" ]; then
    echo "✅ auth_multiuser.py exists"
else
    echo "❌ auth_multiuser.py NOT found"
fi

if [ -f "MULTIUSER_OAUTH_DEPLOYMENT.md" ]; then
    echo "✅ MULTIUSER_OAUTH_DEPLOYMENT.md exists"
else
    echo "❌ Documentation NOT found"
fi
echo ""

# Step 13: Check token files
echo "🔑 Step 13: Checking token files..."
ls -lh credentials/*.pickle 2>/dev/null || echo "⚠️  No token files found yet"
echo ""

# Final summary
echo "================================================"
echo "✅ DEPLOYMENT COMPLETE!"
echo "================================================"
echo ""
echo "📋 Next Steps:"
echo "1. Visit: http://46.101.177.154:8080/admin/login"
echo "2. Login with: ben / Taiwoben123$"
echo "3. Test existing admin user works"
echo ""
echo "4. Open INCOGNITO browser window"
echo "5. Visit: http://46.101.177.154:8080/oauth_login"
echo "6. Sign in with DIFFERENT Gmail account"
echo "7. Verify new user created"
echo ""
echo "📊 Monitoring Commands:"
echo "  docker logs -f voxmail           # Watch logs in real-time"
echo "  docker logs voxmail | grep OAuth # Check OAuth activity"
echo "  docker ps                        # Check container status"
echo "  docker restart voxmail           # Restart if needed"
echo ""
echo "🎉 Deployment script finished!"

