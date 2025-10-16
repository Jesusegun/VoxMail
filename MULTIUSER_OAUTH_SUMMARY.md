# Multi-User OAuth Implementation Summary

## What Was Implemented

### 1. New Files Created

**`auth_multiuser.py`** - Multi-user OAuth authentication module
- `authenticate_gmail_multiuser(token_path)` - Authenticate with per-user tokens
- `get_oauth_authorization_url(redirect_uri, state)` - Generate Google OAuth URL
- `handle_oauth_callback(auth_code, redirect_uri, token_path)` - Exchange code for token
- `generate_state_token()` - Generate CSRF protection tokens

### 2. Modified Files

**`web_app.py`** - Core application updates
- Added `ADMIN_EMAIL` constant for admin privileges
- Updated `UserManager.start_oauth_flow()` - Start web-based OAuth
- Updated `UserManager.complete_oauth_flow()` - Complete OAuth with state validation
- Updated `UserManager.get_user_gmail_service()` - Use per-user tokens
- Updated `/oauth_login` route - Redirect to Google OAuth
- Added `/oauth_callback` route - Handle Google callback
- Added `migrate_existing_user_token()` - Migrate old token to new system
- Added lazy loading for `auth_multiuser` module

### 3. Key Features

#### Multi-User Support
- Each user has their own OAuth token: `credentials/user_<id>_token.pickle`
- Users authenticate with their own Gmail account
- Each user sees only their own emails in digests
- Token refresh handled automatically per user

#### Security
- CSRF protection using state tokens (cryptographically secure)
- State validation on OAuth callback
- Session-based token storage
- Admin privileges based on email address

#### Migration
- Automatic migration of existing token on startup
- Preserves jesusegunadewunmi@gmail.com as admin user
- No manual intervention required

---

## How It Works

### OAuth Flow

```
1. User visits /oauth_login
   ↓
2. Server generates state token, stores in session
   ↓
3. Server redirects to Google OAuth consent screen
   ↓
4. User grants permissions
   ↓
5. Google redirects to /oauth_callback?code=...&state=...
   ↓
6. Server validates state token (CSRF check)
   ↓
7. Server exchanges code for access+refresh tokens
   ↓
8. Server saves token to credentials/user_<id>_token.pickle
   ↓
9. Server creates/updates user in users.json
   ↓
10. User redirected to /user_settings/<user_id>
```

### Digest Generation

When generating a digest for a user:
```python
# web_app.py - generate_user_digest()
gmail_service = user_manager.get_user_gmail_service(user_id)
  ↓
# UserManager.get_user_gmail_service()
token_path = user['token_path']  # e.g., credentials/user_john_at_gmail_dot_com_token.pickle
gmail_service = auth_multiuser.authenticate_gmail_multiuser(token_path)
  ↓
# auth_multiuser.authenticate_gmail_multiuser()
- Loads user's specific token
- Refreshes if expired
- Returns authenticated Gmail service
  ↓
# Back to generate_user_digest()
fetcher = EmailFetcher(gmail_service)
emails = fetcher.get_recent_emails()  # Fetches from user's Gmail
```

---

## What Changed

### Before (Single User)

```python
# auth_test.py
TOKEN_FILE = 'credentials/token.pickle'  # Single token for everyone

def authenticate_gmail():
    creds = load_token(TOKEN_FILE)  # Always same token
    flow.run_local_server(port=0)  # Doesn't work on VPS
```

```python
# web_app.py
def get_user_gmail_service(user_id):
    return authenticate_gmail()  # Everyone uses same token!
```

### After (Multi-User)

```python
# auth_multiuser.py
def authenticate_gmail_multiuser(token_path):  # Per-user token
    creds = load_token(token_path)  # Different for each user
    # No run_local_server(), uses web-based flow

def get_oauth_authorization_url(redirect_uri, state):
    flow.authorization_url()  # Web-based, works on VPS

def handle_oauth_callback(auth_code, redirect_uri, token_path):
    flow.fetch_token(code=auth_code)  # Exchange code
    save_token(token_path)  # Save to user-specific path
```

```python
# web_app.py
def get_user_gmail_service(user_id):
    token_path = user['token_path']  # Get user's token path
    return auth_multiuser.authenticate_gmail_multiuser(token_path)  # Use their token!
```

---

## File Structure

### Before
```
credentials/
  ├── credentials.json      (OAuth client config)
  └── token.pickle          (Single token for everyone)
```

### After
```
credentials/
  ├── credentials.json                                    (OAuth client config - shared)
  ├── user_jesusegunadewunmi_at_gmail_dot_com_token.pickle  (Admin's token)
  ├── user_john_at_example_dot_com_token.pickle             (John's token)
  └── user_sarah_at_example_dot_com_token.pickle            (Sarah's token)
```

---

## Testing Checklist

### ✅ Phase 1: Setup
- [x] Create `auth_multiuser.py` module
- [x] Update `web_app.py` with new OAuth methods
- [x] Add `ADMIN_EMAIL` configuration
- [x] Create token migration function

### ⏳ Phase 2: Google Cloud Console (Manual)
- [ ] Add redirect URI: `http://46.101.177.154:8080/oauth_callback`
- [ ] Add test redirect URI: `http://localhost:8080/oauth_callback`
- [ ] Verify OAuth consent screen scopes
- [ ] Add test users (if in Testing mode)

### ⏳ Phase 3: Deployment
- [ ] Commit and push code to GitHub
- [ ] Pull code on VPS
- [ ] Update `.env` with `ADMIN_EMAIL`
- [ ] Rebuild Docker image
- [ ] Restart container
- [ ] Verify token migration in logs

### ⏳ Phase 4: Testing
- [ ] Test existing admin user still works
- [ ] Test new user signup with different Gmail account
- [ ] Verify new user sees their own emails
- [ ] Verify admin user sees their own emails (not new user's)
- [ ] Test token refresh for expired tokens
- [ ] Test OAuth error handling (user denies access)
- [ ] Test CSRF protection (invalid state token)

---

## Environment Variables

### Required
```bash
BASE_URL=http://46.101.177.154:8080  # Used for OAuth redirect URI
ADMIN_EMAIL=jesusegunadewunmi@gmail.com  # Admin user
```

### Optional (existing)
```bash
ADMIN_USERNAME=ben
ADMIN_PASSWORD=Taiwoben123$
AI_MAX_CONCURRENCY=2
RUN_SCHEDULER=true
```

---

## API Endpoints

### New/Updated Public Endpoints

**GET `/oauth_login`**
- Starts OAuth flow
- Generates state token
- Redirects to Google OAuth consent screen
- **No authentication required**

**GET `/oauth_callback`**
- Handles Google OAuth callback
- Validates state token (CSRF protection)
- Exchanges authorization code for access token
- Creates/updates user account
- **No authentication required** (Google handles auth)

### Existing Protected Endpoints

All admin routes remain protected:
- `GET /` (dashboard) - Requires admin login
- `GET /admin` - Requires admin login
- `POST /send_all_digests` - Requires admin login
- etc.

---

## Security Considerations

### CSRF Protection
- State tokens generated with `secrets.token_hex(16)` (cryptographically secure)
- Tokens stored in Flask session (server-side, not exposed to client)
- Validated on callback before processing authorization code
- Prevents malicious sites from completing OAuth on user's behalf

### Token Isolation
- Each user's token stored in separate file
- File names include user ID: `user_<id>_token.pickle`
- No cross-user token access
- Admin can't access other users' tokens (only their own Gmail service)

### Admin Privileges
- Admin identified by email address (not just login)
- Admin can view all users in dashboard
- Admin can generate digests for any user
- Regular users only access their own settings

---

## Migration Strategy

### Automatic Migration
The system automatically migrates existing tokens on first startup:

1. Checks if `credentials/token.pickle` exists
2. Loads token and extracts email address
3. Copies to `credentials/user_<id>_token.pickle`
4. Updates user record in `users.json`
5. Logs migration status

### Manual Migration (if needed)
If automatic migration fails:

```bash
# On VPS
cd /root/VoxMail/credentials

# Manually copy token
cp token.pickle user_jesusegunadewunmi_at_gmail_dot_com_token.pickle

# Update users.json
nano /root/VoxMail/data/users.json
# Change token_path to: "credentials/user_jesusegunadewunmi_at_gmail_dot_com_token.pickle"

# Restart
docker restart voxmail
```

---

## Troubleshooting

### Common Issues

1. **redirect_uri_mismatch**
   - Cause: Redirect URI not in Google Cloud Console
   - Fix: Add `http://46.101.177.154:8080/oauth_callback`

2. **Invalid state token**
   - Cause: Session expired or cleared
   - Fix: Start fresh from `/oauth_login`

3. **User has no token_path**
   - Cause: User record exists but token missing
   - Fix: User re-authenticates via `/oauth_login`

4. **Token refresh failed**
   - Cause: Refresh token expired or revoked
   - Fix: User re-authenticates via `/oauth_login`

---

## Next Steps

1. **Update Google Cloud Console** (Step 1 in deployment guide)
2. **Deploy to VPS** (Step 3 in deployment guide)
3. **Test with second Gmail account** (Step 4 in deployment guide)
4. **Share signup link** with users: `http://46.101.177.154:8080/oauth_login`
5. **Consider custom domain** and HTTPS (optional but recommended)

---

## Files Modified

- ✅ `auth_multiuser.py` (NEW) - 230 lines
- ✅ `web_app.py` - Modified ~150 lines across multiple sections
- ✅ `MULTIUSER_OAUTH_DEPLOYMENT.md` (NEW) - Complete deployment guide
- ✅ `MULTIUSER_OAUTH_SUMMARY.md` (NEW) - This file

## Lines of Code
- New code: ~450 lines
- Modified code: ~150 lines
- Documentation: ~600 lines
- **Total: ~1200 lines**

---

## Success Criteria

The implementation is successful when:

✅ Multiple users can sign up with different Gmail accounts
✅ Each user sees only their own emails in digests
✅ Existing admin user (jesusegunadewunmi@gmail.com) still works
✅ OAuth works on VPS (not just localhost)
✅ CSRF attacks prevented with state tokens
✅ Tokens refresh automatically when expired
✅ Admin dashboard shows all users
✅ No cross-contamination between users' data

---

*Implementation completed: 2025-10-16*
*Ready for deployment and testing*

