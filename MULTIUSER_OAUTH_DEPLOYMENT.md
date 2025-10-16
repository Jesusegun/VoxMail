# Multi-User OAuth Deployment Guide

## Overview

This guide walks you through deploying the multi-user OAuth system that allows each user to sign up with their own Gmail account and receive personalized email digests.

## Architecture Changes

### Before (Single User)
- One token file (`credentials/token.pickle`)
- All users see the same emails (from jesusegunadewunmi@gmail.com)
- OAuth used `run_local_server()` (doesn't work on VPS)

### After (Multi-User)
- Per-user token files (`credentials/user_<id>_token.pickle`)
- Each user sees their own Gmail inbox
- Web-based OAuth flow (works on VPS)
- CSRF protection with state tokens

---

## Step 1: Update Google Cloud Console

### 1.1 Access OAuth Settings
1. Go to: https://console.cloud.google.com
2. Select your project: **"VoxMail"** or **"Email Digest Assistant"**
3. Navigate to: **APIs & Services** → **Credentials**
4. Find your OAuth 2.0 Client ID (the one you downloaded as `credentials.json`)
5. Click **Edit** (pencil icon)

### 1.2 Add Authorized Redirect URIs
Scroll down to **"Authorized redirect URIs"** section and add:

**Production URI:**
```
http://46.101.177.154:8080/oauth_callback
```

**Local Testing URI:**
```
http://localhost:8080/oauth_callback
```

Click **"Save"** at the bottom.

### 1.3 Verify OAuth Consent Screen
1. Go to **APIs & Services** → **OAuth consent screen**
2. Verify the following:
   - **User Type**: External (or Internal if Google Workspace)
   - **App Name**: VoxMail or Email Digest Assistant
   - **User support email**: Your email
   - **Scopes**: Should include:
     - `https://www.googleapis.com/auth/gmail.readonly`
     - `https://www.googleapis.com/auth/gmail.send`
   - **Test users** (if in Testing mode): Add test emails here

3. If app is in **"Testing"** mode, you can only add up to 100 test users
4. To go public: Click **"Publish App"** (Google may require verification for large user bases)

---

## Step 2: Update Environment Variables on VPS

### 2.1 SSH into Your VPS
```bash
ssh root@46.101.177.154
```

### 2.2 Update .env File
```bash
cd /root/VoxMail
nano .env
```

Add the following line:
```bash
ADMIN_EMAIL=jesusegunadewunmi@gmail.com
```

Your complete `.env` should look like:
```bash
BASE_URL=http://46.101.177.154:8080
AI_MAX_CONCURRENCY=2
RUN_SCHEDULER=true
ADMIN_USERNAME=ben
ADMIN_PASSWORD=Taiwoben123$
ADMIN_EMAIL=jesusegunadewunmi@gmail.com
```

Save with `Ctrl+X`, then `Y`, then `Enter`.

---

## Step 3: Deploy Updated Code

### 3.1 From Your Local Machine (Windows PowerShell)

```powershell
# Navigate to project directory
cd C:\Users\PC\Desktop\email-digest-assistant

# Commit all changes
git add .
git commit -m "Implement multi-user OAuth system"
git push origin main
```

### 3.2 On Your VPS

```bash
# Pull latest code
cd /root/VoxMail
git pull origin main

# Rebuild Docker image with new code
docker build -t voxmail:latest .

# Stop and remove old container
docker stop voxmail
docker rm voxmail

# Start new container with updated code
docker run -d --name voxmail -p 8080:8080 \
  -v /root/VoxMail/data:/app/data \
  -v /root/VoxMail/ai_data:/app/ai_data \
  -v /root/VoxMail/credentials:/app/credentials \
  --env-file .env --restart unless-stopped voxmail:latest

# Watch logs to verify startup
docker logs -f voxmail
```

### 3.3 Watch for Migration Messages

In the logs, you should see:
```
🔄 Migrating existing OAuth token to multi-user system...
📧 Old token belongs to: jesusegunadewunmi@gmail.com
✅ Token migrated to: credentials/user_jesusegunadewunmi_at_gmail_dot_com_token.pickle
✅ Updated user record for jesusegunadewunmi_at_gmail_dot_com
✅ Token migration complete!
```

This means your existing token was successfully migrated!

---

## Step 4: Test Multi-User OAuth

### 4.1 Test Existing Admin User

1. Visit: `http://46.101.177.154:8080/admin/login`
2. Login with: `ben` / `Taiwoben123$`
3. You should see the dashboard with your existing user

### 4.2 Test New User Registration

**Important**: Use a different Google account (not jesusegunadewunmi@gmail.com)

1. **Open an Incognito/Private browser window**
2. Visit: `http://46.101.177.154:8080/oauth_login`
3. **Expected flow:**
   - Redirects to Google OAuth consent screen
   - Shows: "VoxMail wants to access your Google Account"
   - Lists permissions: Read, compose, and send emails
4. **Click "Allow"**
5. **Should redirect back to:**
   - `http://46.101.177.154:8080/oauth_callback?code=...&state=...`
   - Then to: `http://46.101.177.154:8080/user_settings/<new_user_id>`
6. **Verify:**
   - You see the settings page for the NEW user
   - User ID matches the new email (e.g., `newuser_at_gmail_dot_com`)

### 4.3 Test Digest Generation for New User

1. From the new user's settings page, click **"Generate Test Digest"**
2. Or visit: `http://46.101.177.154:8080/preview_digest/<new_user_id>`
3. **Expected result:**
   - Digest shows emails from the NEW user's Gmail inbox
   - NOT from jesusegunadewunmi@gmail.com's inbox

---

## Step 5: Verify Multi-User Isolation

### 5.1 Check Token Files

On VPS:
```bash
cd /root/VoxMail/credentials
ls -la user_*.pickle
```

You should see:
```
user_jesusegunadewunmi_at_gmail_dot_com_token.pickle
user_newuser_at_gmail_dot_com_token.pickle
```

### 5.2 Check Users JSON

```bash
cat /root/VoxMail/data/users.json
```

You should see both users with their own `token_path` values.

### 5.3 Test Digest Isolation

Generate digests for both users and verify:
- Admin user sees their own emails
- New user sees their own emails
- No cross-contamination

---

## Troubleshooting

### Problem: "OAuth error: redirect_uri_mismatch"

**Cause**: Redirect URI not added to Google Cloud Console

**Fix**:
1. Go to Google Cloud Console → Credentials
2. Edit your OAuth 2.0 Client
3. Add: `http://46.101.177.154:8080/oauth_callback`
4. Save and wait 5 minutes for propagation
5. Try again

### Problem: "Invalid state token - possible CSRF attack"

**Cause**: State token mismatch (session cleared or expired)

**Fix**:
1. Clear browser cookies
2. Start fresh from `/oauth_login`

### Problem: "User has no token_path - needs to complete OAuth"

**Cause**: User record exists but token file is missing

**Fix**:
1. Have the user visit `/oauth_login` to re-authenticate
2. Or manually delete the user from `users.json`

### Problem: Old user still using old token

**Cause**: Migration didn't update user record

**Fix**:
1. SSH into VPS
2. Edit `/root/VoxMail/data/users.json`
3. Update `token_path` to: `credentials/user_<id>_token.pickle`
4. Restart container: `docker restart voxmail`

---

## Security Considerations

### CSRF Protection
- State tokens are generated using `secrets.token_hex(16)`
- Validated on callback to prevent CSRF attacks
- Tokens stored in Flask session (server-side)

### Token Storage
- Each user's token stored separately
- Tokens not exposed to other users
- File permissions: Only root can read token files

### Admin Privileges
- Only users with email matching `ADMIN_EMAIL` have admin access
- Admin can manage all users via dashboard
- Regular users only see their own data

---

## OAuth Flow Diagram

```
User visits /oauth_login
         ↓
Server generates state token
         ↓
Server redirects to Google
         ↓
User grants permissions
         ↓
Google redirects to /oauth_callback
         ↓
Server validates state token
         ↓
Server exchanges code for access token
         ↓
Server saves token to user_<id>_token.pickle
         ↓
Server creates/updates user record
         ↓
User redirected to settings page
```

---

## Monitoring and Logs

### Check OAuth Activity

```bash
# Watch real-time logs
docker logs -f voxmail

# Search for OAuth events
docker logs voxmail 2>&1 | grep "OAuth"

# Check for errors
docker logs voxmail 2>&1 | grep "❌"
```

### Key Log Messages

**Successful OAuth:**
```
🔐 Starting OAuth flow for new user...
✅ Authorization URL generated
🔄 Processing OAuth callback...
✅ State token validated
✅ OAuth successful for: user@example.com
✅ New user created: user@example.com
```

**Failed OAuth:**
```
❌ OAuth error from Google: access_denied
❌ OAuth callback validation failed: Invalid state token
❌ OAuth flow failed: <error details>
```

---

## Next Steps

Once multi-user OAuth is working:

1. **Share the signup link**: `http://46.101.177.154:8080/oauth_login`
2. **Monitor user registrations** via admin dashboard
3. **Set up custom domain** (optional):
   - Register domain (e.g., voxmail.example.com)
   - Point to VPS IP: 46.101.177.154
   - Set up Nginx with Let's Encrypt for HTTPS
   - Update Google Cloud Console with HTTPS redirect URI
4. **Publish OAuth App** if you need >100 users
5. **Enable scheduler** for automatic daily digests

---

## Rollback Plan

If something goes wrong, you can rollback:

### Option 1: Revert to Previous Code

```bash
# On VPS
cd /root/VoxMail
git log --oneline -5  # Find previous commit
git checkout <previous-commit-hash>
docker build -t voxmail:latest .
docker restart voxmail
```

### Option 2: Restore Old Token

```bash
# If you kept the old token.pickle
cp credentials/token.pickle.backup credentials/token.pickle
```

---

## Support

If you encounter issues:

1. Check logs: `docker logs voxmail`
2. Verify Google Cloud Console settings
3. Check `.env` file has correct values
4. Verify token files exist and are readable
5. Test with a fresh incognito browser session

---

## Summary

You've successfully implemented:

✅ Web-based OAuth flow for VPS deployment
✅ Per-user token management
✅ CSRF protection with state tokens
✅ Automatic token migration for existing users
✅ Admin privileges for jesusegunadewunmi@gmail.com
✅ Multi-user isolation (each user sees their own emails)

Users can now sign up at: `http://46.101.177.154:8080/oauth_login`

