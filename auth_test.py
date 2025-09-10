import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Define the permissions we need from Gmail
# READ: Access to read emails, labels, threads
# SEND: Permission to send emails (for our digest and replies)
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',  # Read emails, labels, threads
    'https://www.googleapis.com/auth/gmail.send'       # Send emails (for digest)
]

# File paths for credentials and tokens
CREDENTIALS_FILE = 'credentials/credentials.json'  # OAuth credentials from Google Cloud
TOKEN_FILE = 'credentials/token.pickle'            # Saved authentication tokens

def authenticate_gmail():
    """
    Authenticate with Gmail API using OAuth 2.0 flow
    
    AUTHENTICATION PROCESS:
    1. Check if we have saved authentication tokens
    2. If tokens exist and are valid, use them
    3. If tokens are expired but refreshable, refresh them
    4. If no valid tokens, start OAuth flow for user consent
    5. Save new tokens for future use
    6. Return authenticated Gmail service object
    
    Returns:
        googleapiclient.discovery.Resource: Authenticated Gmail service object
    """
    
    print("🔐 Starting Gmail API authentication...")
    
    # Initialize credentials variable
    creds = None
    
    # =============================================================================
    # STEP 1: CHECK FOR EXISTING AUTHENTICATION TOKENS
    # =============================================================================
    if os.path.exists(TOKEN_FILE):
        print("📂 Found existing authentication tokens")
        try:
            # Load saved credentials from pickle file
            # Pickle is Python's serialization format for storing objects
            with open(TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
            print("✅ Successfully loaded saved credentials")
        except Exception as e:
            print(f"❌ Error loading saved credentials: {e}")
            print("🔄 Will need to re-authenticate")
    else:
        print("📂 No existing authentication tokens found")
    
    # =============================================================================
    # STEP 2: VALIDATE AND REFRESH CREDENTIALS IF NEEDED
    # =============================================================================
    if not creds or not creds.valid:
        print("🔄 Credentials need validation/refresh...")
        
        # Check if credentials are expired but have a refresh token
        if creds and creds.expired and creds.refresh_token:
            print("⏰ Credentials expired, attempting to refresh...")
            try:
                # Attempt to refresh the expired credentials
                creds.refresh(Request())
                print("✅ Successfully refreshed expired credentials")
            except Exception as e:
                print(f"❌ Failed to refresh credentials: {e}")
                print("🔄 Will need to re-authenticate completely")
                creds = None
        
        # If we still don't have valid credentials, start OAuth flow
        if not creds or not creds.valid:
            print("🌐 Starting OAuth 2.0 authentication flow...")
            
            # =============================================================================
            # STEP 3: OAUTH 2.0 AUTHENTICATION FLOW
            # =============================================================================
            
            # Check if credentials file exists
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"❌ Credentials file not found: {CREDENTIALS_FILE}")
                print("📋 Please follow these steps:")
                print("   1. Go to https://console.cloud.google.com")
                print("   2. Create/select project 'Email Digest Assistant'")
                print("   3. Enable Gmail API")
                print("   4. Create OAuth 2.0 credentials")
                print("   5. Download as 'credentials.json'")
                print("   6. Move to credentials/ folder")
                return None
            
            try:
                # Create OAuth flow from credentials file
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE, SCOPES
                )
                
                # Run local server to handle OAuth callback
                # This opens browser for user to grant permissions
                print("🌐 Opening browser for authentication...")
                print("📋 Please:")
                print("   1. Select your Gmail account")
                print("   2. Click 'Allow' to grant permissions")
                print("   3. Return to this terminal")
                
                # Start local server on random port to receive OAuth callback
                creds = flow.run_local_server(port=0)
                
                print("✅ OAuth authentication successful!")
                
            except Exception as e:
                print(f"❌ OAuth authentication failed: {e}")
                print("🔍 Common issues:")
                print("   • credentials.json file missing or invalid")
                print("   • Gmail API not enabled in Google Cloud Console")
                print("   • OAuth consent screen not configured")
                return None
    
    # =============================================================================
    # STEP 4: SAVE CREDENTIALS FOR FUTURE USE
    # =============================================================================
    if creds and creds.valid:
        print("💾 Saving authentication tokens for future use...")
        try:
            # Create credentials directory if it doesn't exist
            os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
            
            # Save credentials to pickle file for future sessions
            with open(TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
            print(f"✅ Credentials saved to {TOKEN_FILE}")
        except Exception as e:
            print(f"⚠️ Warning: Could not save credentials: {e}")
            print("   (Authentication will work but you'll need to re-auth next time)")
    
    # =============================================================================
    # STEP 5: BUILD GMAIL SERVICE OBJECT
    # =============================================================================
    try:
        print("🔨 Building Gmail API service object...")
        
        # Create authenticated Gmail service object
        # This is what we'll use to make Gmail API calls
        service = build('gmail', 'v1', credentials=creds)
        
        print("✅ Gmail API service object created successfully!")
        return service
        
    except Exception as e:
        print(f"❌ Failed to build Gmail service: {e}")
        return None

def test_gmail_connection(service):
    """
    Test the Gmail connection by fetching user profile
    
    Args:
        service: Authenticated Gmail service object
        
    Returns:
        bool: True if connection successful, False otherwise
    """
    
    print("🧪 Testing Gmail API connection...")
    
    try:
        # Get user's Gmail profile to test connection
        profile = service.users().getProfile(userId='me').execute()
        
        # Extract useful information
        email_address = profile.get('emailAddress', 'Unknown')
        messages_total = profile.get('messagesTotal', 0)
        threads_total = profile.get('threadsTotal', 0)
        
        print("✅ Gmail API connection test successful!")
        print(f"📧 Connected to: {email_address}")
        print(f"📊 Total messages: {messages_total:,}")
        print(f"🧵 Total threads: {threads_total:,}")
        
        return True
        
    except Exception as e:
        print(f"❌ Gmail API connection test failed: {e}")
        return False

# =============================================================================
# MAIN EXECUTION - FOR TESTING
# =============================================================================
if __name__ == '__main__':
    """
    Main execution block - runs when file is executed directly
    This tests the authentication and connection
    """
    
    print("=" * 60)
    print("🚀 GMAIL API AUTHENTICATION TEST")
    print("=" * 60)
    
    # Attempt to authenticate
    gmail_service = authenticate_gmail()
    
    if gmail_service:
        print("\n" + "=" * 60)
        print("🎉 AUTHENTICATION SUCCESSFUL!")
        print("=" * 60)
        
        # Test the connection
        connection_success = test_gmail_connection(gmail_service)
        
        if connection_success:
            print("\n✅ Ready to proceed to email fetching!")
            print("📝 Next steps:")
            print("   1. Run: python email_fetcher.py")
            print("   2. This will fetch your recent emails")
        else:
            print("\n❌ Connection test failed")
            print("🔧 Please check your Gmail API settings")
    
    else:
        print("\n" + "=" * 60)
        print("❌ AUTHENTICATION FAILED")
        print("=" * 60)
        print("🔧 Please check:")
        print("   • credentials.json file exists in credentials/ folder")
        print("   • Gmail API is enabled in Google Cloud Console")
        print("   • OAuth consent screen is properly configured")
        print("   • Project has correct permissions")
    
    print("\n" + "=" * 60)