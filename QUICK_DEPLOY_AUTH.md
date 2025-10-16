# Quick Deploy: Admin Authentication

## 🚀 Fast Deployment to VPS

### 1️⃣ On Your Local Machine (Windows)

```powershell
# Commit and push changes
git add .
git commit -m "Add admin authentication"
git push origin main
```

### 2️⃣ On DigitalOcean VPS

```bash
# SSH into VPS
ssh root@46.101.177.154

# Navigate to project
cd /root/VoxMail

# Update .env file (add admin credentials)
nano .env
```

**Add these lines to `.env`:**
```env
ADMIN_USERNAME=ben
ADMIN_PASSWORD=Taiwoben123$
```

**Save:** `Ctrl+X` → `Y` → `Enter`

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker build -t voxmail:latest .
docker stop voxmail && docker rm voxmail
docker run -d --name voxmail -p 8080:8080 \
  -v /root/VoxMail/data:/app/data \
  -v /root/VoxMail/ai_data:/app/ai_data \
  -v /root/VoxMail/credentials:/app/credentials \
  --env-file .env --restart unless-stopped voxmail:latest

# Check logs
docker logs -f voxmail
```

### 3️⃣ Test in Browser

Navigate to: **http://46.101.177.154:8080**

**Login:**
- Username: `ben`
- Password: `Taiwoben123$`

---

## 🔐 Admin Credentials

- **Username:** `ben`
- **Password:** `Taiwoben123$`
- **Session Timeout:** 30 minutes

## 📝 Password Recovery

If you forget credentials:

```bash
ssh root@46.101.177.154
cd /root/VoxMail
nano .env  # Update ADMIN_USERNAME and ADMIN_PASSWORD
docker restart voxmail
```

---

**That's it!** Your admin dashboard is now protected. 🎉

