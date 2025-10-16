# VPS OAuth Fix - Upload Pre-Authenticated Token

## Problem
The VPS can't open a browser for OAuth authentication. We need to upload the pre-authenticated `token.pickle` file.

## Solution

### Step 1: On Your Local Machine (Windows PowerShell)

```powershell
# Navigate to your project
cd C:\Users\PC\Desktop\email-digest-assistant

# Check if token.pickle exists
ls credentials\token.pickle
```

### Step 2: Upload token.pickle to VPS

Since you're using the DigitalOcean console (not SSH), you have two options:

#### Option A: Use SCP (if you can access SSH)
```powershell
# From your local machine
scp credentials/token.pickle root@46.101.177.154:/root/VoxMail/credentials/
```

#### Option B: Use Base64 Transfer (works in console)
```powershell
# On your LOCAL machine - encode the file
[Convert]::ToBase64String([IO.File]::ReadAllBytes("credentials\token.pickle")) | Out-File -FilePath token_base64.txt -Encoding ASCII

# Then copy the contents of token_base64.txt
Get-Content token_base64.txt | Set-Clipboard
```

Then on the VPS console:
```bash
# Create a file with the base64 content (paste the content you copied)
cat > /root/VoxMail/credentials/token_base64.txt << 'EOF'
[PASTE YOUR BASE64 CONTENT HERE]
EOF

# Decode and save as token.pickle
base64 -d /root/VoxMail/credentials/token_base64.txt > /root/VoxMail/credentials/token.pickle

# Verify the file exists
ls -lh /root/VoxMail/credentials/token.pickle

# Restart the container
cd /root/VoxMail
docker-compose restart

# Check logs
docker-compose logs -f
```

### Step 3: Verify

Visit `http://46.101.177.154:8080/oauth_login` in your browser. It should now work without prompting for browser authentication!

---

## Alternative: Multi-User Setup

If you need multiple users (your 70 users scenario), each user needs their own token. The current setup uses a single shared token. For true multi-user support, you'd need to modify the architecture to:

1. Store per-user tokens in `credentials/user_{user_id}_token.pickle`
2. Each user goes through OAuth individually
3. Or use a service account with domain-wide delegation (enterprise Google Workspace only)

For now, the single token approach will work for testing and single-user deployment.

