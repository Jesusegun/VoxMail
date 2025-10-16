# Google Cloud Console OAuth Setup Guide

## Step-by-Step Instructions

### 1. Access Google Cloud Console

1. Open your browser and go to: https://console.cloud.google.com
2. Sign in with your Google account (jesusegunadewunmi@gmail.com)
3. You should see the Google Cloud Console dashboard

### 2. Select Your Project

Look at the top left of the page, next to "Google Cloud":
- Click on the project dropdown
- Select your project: **"VoxMail"** or **"Email Digest Assistant"** or **"email-digest-assistant-471211"**
- The project name should appear in the top bar

### 3. Navigate to Credentials

From the left sidebar menu:
1. Click on **"APIs & Services"** (you might need to expand the hamburger menu ☰)
2. Click on **"Credentials"**

OR use direct link:
https://console.cloud.google.com/apis/credentials

### 4. Find Your OAuth 2.0 Client ID

On the Credentials page, you'll see a section called **"OAuth 2.0 Client IDs"**

Look for your client:
- **Name**: Something like "VoxMail Client" or "Desktop client 1" or similar
- **Type**: "Web application" or might say "Desktop"
- **Client ID**: Starts with a number (like 920089117591-...)

Click on the **name** or the **pencil icon (✏️)** to edit it.

### 5. Update OAuth Client Settings

You're now on the "Edit OAuth client" page.

#### 5.1 Client Type
If it says **"Application type: Desktop"**, change it to:
- **Application type: Web application**

#### 5.2 Authorized Redirect URIs

Scroll down to the **"Authorized redirect URIs"** section.

Click **"+ ADD URI"** and add these URIs (one at a time):

**URI 1 (Production - VPS):**
```
http://46.101.177.154:8080/oauth_callback
```

**URI 2 (Local Testing):**
```
http://localhost:8080/oauth_callback
```

Your redirect URIs list should now show:
- ✅ `http://46.101.177.154:8080/oauth_callback`
- ✅ `http://localhost:8080/oauth_callback`

#### 5.3 Save Changes

Scroll to the bottom and click **"SAVE"**

You should see a success message: "OAuth client updated"

### 6. Verify OAuth Consent Screen

Click **"OAuth consent screen"** in the left sidebar.

Verify these settings:

#### Publishing Status
- If it says **"Testing"**: You can add up to 100 test users
- If you need more users, click **"PUBLISH APP"**

#### App Information
- **App name**: Should be set (e.g., "VoxMail" or "Email Digest Assistant")
- **User support email**: Your email
- **App logo**: Optional

#### Scopes
Click "Edit App" and scroll to "Scopes" section. Verify these scopes are added:
- ✅ `https://www.googleapis.com/auth/gmail.readonly`
- ✅ `https://www.googleapis.com/auth/gmail.send`

If missing, click **"ADD OR REMOVE SCOPES"** and add them.

#### Test Users (if app is in Testing mode)
If your app is in "Testing" status:
- Click **"ADD USERS"**
- Add any Gmail accounts you want to test with
- These users can sign up via OAuth

**Note**: If app is **Published**, anyone with a Gmail account can sign up.

### 7. Wait for Propagation (Optional)

After saving changes, Google's servers need to sync:
- **Wait time**: 5-10 minutes
- **What to do**: Make some coffee ☕ or proceed to VPS deployment

### 8. Verification Checklist

Before leaving Google Cloud Console, verify:

- ✅ Project selected: "VoxMail" or "Email Digest Assistant"
- ✅ OAuth client type: **Web application**
- ✅ Redirect URI added: `http://46.101.177.154:8080/oauth_callback`
- ✅ Redirect URI added: `http://localhost:8080/oauth_callback`
- ✅ Changes saved successfully
- ✅ OAuth consent screen configured
- ✅ Scopes include gmail.readonly and gmail.send

---

## Common Issues

### Issue: "Can't find OAuth Client"

**Solution**: Your OAuth client might be for "Desktop" application. You need to either:
- Change the application type to "Web application" (preferred)
- Or create a new OAuth client for "Web application"

### Issue: "Redirect URI Mismatch" Error Later

**Cause**: URI in Google Cloud Console doesn't exactly match what the app is using

**Fix**: Make sure URIs are EXACTLY:
- `http://46.101.177.154:8080/oauth_callback` (no trailing slash, no https)
- `http://localhost:8080/oauth_callback`

### Issue: "This app isn't verified"

**For testing**: Click "Advanced" → "Go to VoxMail (unsafe)" → Continue
**For production**: Submit app for Google verification (takes 1-2 weeks)

---

## What's Next?

Once Google Cloud Console is updated:

✅ **Google Cloud Console configured**
⏳ **Next**: Deploy to VPS
⏳ **Then**: Test with multiple Gmail accounts

Continue to the VPS deployment in the next section!

