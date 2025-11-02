# =============================================================================
# MULTI-USER OAUTH AUTHENTICATION - auth_multiuser.py
# =============================================================================
# Web-based OAuth 2.0 flow for multi-user Gmail authentication
# Each user gets their own OAuth token stored separately
# =============================================================================

import os
import pickle
import secrets
from typing import Optional, Tuple
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]

# Default credentials file (shared across all users)
DEFAULT_CREDENTIALS_FILE = 'credentials/credentials.json'

def authenticate_gmail_multiuser(
    token_path: str,
    credentials_path: str = DEFAULT_CREDENTIALS_FILE
) -> Optional[object]:
    """
    Authenticate with Gmail API using per-user token file.
    
    This function handles token refresh if expired, but does NOT start
    a new OAuth flow. For new users, use get_oauth_authorization_url()
    and handle_oauth_callback() instead.
    
    Args:
        token_path: Path to user-specific token pickle file
        credentials_path: Path to OAuth credentials JSON (shared)
    
    Returns:
        Authenticated Gmail service object, or None if authentication fails
    """
    
    print(f"🔐 Authenticating with token: {token_path}")
    
    creds = None
    
    # Load existing token if available
    if os.path.exists(token_path):
        print(f"📂 Loading existing token from {token_path}")
        try:
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
            print("✅ Token loaded successfully")
        except Exception as e:
            print(f"❌ Error loading token: {e}")
            return None
    else:
        print(f"📂 No existing token found at {token_path}")
        print("💡 User needs to complete OAuth flow via /oauth_login")
        return None
    
    # Check if credentials are valid
    if not creds or not creds.valid:
        print("🔄 Credentials need validation/refresh...")
        
        # Try to refresh if expired
        if creds and creds.expired and creds.refresh_token:
            print("⏰ Token expired, attempting to refresh...")
            try:
                creds.refresh(Request())
                print("✅ Token refreshed successfully")
                
                # Save refreshed token
                with open(token_path, 'wb') as token:
                    pickle.dump(creds, token)
                print(f"💾 Refreshed token saved to {token_path}")
                
            except Exception as e:
                print(f"❌ Failed to refresh token: {e}")
                print("💡 User needs to re-authenticate via /oauth_login")
                return None
        else:
            print("❌ Token invalid and cannot be refreshed")
            print("💡 User needs to complete OAuth flow via /oauth_login")
            return None
    
    # Build Gmail service
    try:
        print("🔨 Building Gmail API service...")
        service = build('gmail', 'v1', credentials=creds)
        print("✅ Gmail service created successfully")
        return service
    except Exception as e:
        print(f"❌ Failed to build Gmail service: {e}")
        return None


def get_oauth_authorization_url(
    redirect_uri: str,
    state: str,
    credentials_path: str = DEFAULT_CREDENTIALS_FILE
) -> str:
    """
    Generate OAuth authorization URL for user to grant permissions.
    
    Args:
        redirect_uri: URL where Google will redirect after authorization
        state: Random state token for CSRF protection
        credentials_path: Path to OAuth credentials JSON
    
    Returns:
        Authorization URL to redirect user to
    
    Raises:
        FileNotFoundError: If credentials file doesn't exist
        Exception: If OAuth flow creation fails
    """
    
    print("🌐 Generating OAuth authorization URL...")
    
    if not os.path.exists(credentials_path):
        raise FileNotFoundError(
            f"Credentials file not found: {credentials_path}\n"
            "Please download credentials.json from Google Cloud Console"
        )
    
    try:
        # Create OAuth flow
        flow = Flow.from_client_secrets_file(
            credentials_path,
            scopes=SCOPES,
            redirect_uri=redirect_uri
        )
        
        # Generate authorization URL with state parameter
        authorization_url, _ = flow.authorization_url(
            access_type='offline',  # Get refresh token
            include_granted_scopes='true',  # Incremental authorization
            state=state,  # CSRF protection
            prompt='consent'  # Force consent screen to ensure refresh token
        )
        
        print(f"✅ Authorization URL generated")
        print(f"🔗 Redirect URI: {redirect_uri}")
        return authorization_url
        
    except Exception as e:
        print(f"❌ Failed to generate authorization URL: {e}")
        raise


def handle_oauth_callback(
    auth_code: str,
    redirect_uri: str,
    token_path: str,
    credentials_path: str = DEFAULT_CREDENTIALS_FILE
) -> Tuple[object, str]:
    """
    Handle OAuth callback by exchanging authorization code for access token.
    
    Args:
        auth_code: Authorization code from Google OAuth callback
        redirect_uri: Same redirect URI used in authorization request
        token_path: Path where to save the user's token
        credentials_path: Path to OAuth credentials JSON
    
    Returns:
        Tuple of (gmail_service, email_address)
    
    Raises:
        Exception: If token exchange or profile fetch fails
    """
    
    print("🔄 Handling OAuth callback...")
    print(f"📝 Authorization code: {auth_code[:20]}...")
    
    try:
        # Create OAuth flow with same parameters as authorization
        flow = Flow.from_client_secrets_file(
            credentials_path,
            scopes=SCOPES,
            redirect_uri=redirect_uri
        )
        
        # Exchange authorization code for access token
        print("🔑 Exchanging authorization code for access token...")
        flow.fetch_token(code=auth_code)
        creds = flow.credentials
        print("✅ Access token obtained successfully")
        
        # Validate that we have both required scopes
        granted_scopes = creds.scopes if hasattr(creds, 'scopes') and creds.scopes else []
        print(f"📋 Granted scopes: {granted_scopes}")
        
        required_scopes = set(SCOPES)
        granted_scopes_set = set(granted_scopes)
        
        if not required_scopes.issubset(granted_scopes_set):
            missing_scopes = required_scopes - granted_scopes_set
            print(f"❌ Missing required scopes: {missing_scopes}")
            raise PermissionError("Missing required Gmail permissions. Both read and send permissions are needed.")
        
        # Save credentials to user-specific token file
        print(f"💾 Saving token to {token_path}...")
        os.makedirs(os.path.dirname(token_path), exist_ok=True)
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
        print(f"✅ Token saved to {token_path}")
        
        # Build Gmail service
        print("🔨 Building Gmail service...")
        service = build('gmail', 'v1', credentials=creds)
        
        # Get user's email address from Gmail profile
        print("📧 Fetching user profile...")
        profile = service.users().getProfile(userId='me').execute()
        email_address = profile.get('emailAddress')
        
        if not email_address:
            raise Exception("Could not extract email address from Gmail profile")
        
        print(f"✅ Authentication successful for: {email_address}")
        return service, email_address
        
    except Exception as e:
        print(f"❌ OAuth callback handling failed: {e}")
        raise


def generate_state_token() -> str:
    """
    Generate a cryptographically secure random state token for CSRF protection.
    
    Returns:
        32-character hex string
    """
    return secrets.token_hex(16)


# =============================================================================
# MODULE END
# =============================================================================

