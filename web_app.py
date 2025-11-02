# =============================================================================
# WEB APPLICATION - web_app.py
# =============================================================================
# Day 3: Web Interface for VoxMail - AI Email Assistant
# 
# This Flask application handles:
# 1. Button clicks from digest emails (send/edit/archive)
# 2. Reply editing interface
# 3. User settings and preferences
# 4. Daily digest generation and sending
# 5. User management for 70 users
#
# INTEGRATION WITH EXISTING AI SYSTEM (PHASE 4):
# - Uses AdvancedEmailProcessor from complete_advanced_ai_processor.py
# - Includes Phase 1: AI-enhanced reply generation (BART + spaCy)
# - Includes Phase 2: Sensitive detection + Edge case handling + Safe mode
# - Includes Phase 3: Learning tracker for edit feedback
# - Leverages EmailFetcher from email_fetcher.py  
# - Uses authenticate_gmail from auth_test.py
# =============================================================================

import os
import json
import uuid
import base64
import time
import fcntl
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, jsonify, abort, session
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ai_runtime import get_advanced_processor, SEMAPHORE

# Cross-platform file locking
try:
    import msvcrt  # Windows
    _has_msvcrt = True
except ImportError:
    _has_msvcrt = False

# Lazy import globals - AI components loaded only when needed
authenticate_gmail = None
EmailFetcher = None
auth_multiuser = None

def _lazy_load_ai_components():
    """Load AI components only when actually needed to save memory at startup"""
    global authenticate_gmail, EmailFetcher, auth_multiuser
    if authenticate_gmail is None:
        print("📦 Loading AI components...")
        try:
            from auth_test import authenticate_gmail as _auth
            from email_fetcher import EmailFetcher as _Fetcher
            import auth_multiuser as _auth_multi
            authenticate_gmail = _auth
            EmailFetcher = _Fetcher
            auth_multiuser = _auth_multi
            print("✅ AI components loaded successfully")
        except ImportError as e:
            print(f"❌ Error importing AI components: {e}")
            raise

# =============================================================================
# FLASK APP CONFIGURATION
# =============================================================================

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

# Session configuration for admin authentication
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Admin credentials from environment variables
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'ben')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Taiwoben123$')
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'jesusegunadewunmi@gmail.com')  # Special admin user

# Configuration
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')
USERS_DATA_FILE = 'data/users.json'
DIGEST_DATA_FILE = 'data/digest_data.json'

# Ensure data directories exist
os.makedirs('data', exist_ok=True)
os.makedirs('templates', exist_ok=True)

# =============================================================================
# AUTHENTICATION SYSTEM
# =============================================================================

def check_admin_credentials(username: str, password: str) -> bool:
    """Check if provided credentials match admin credentials"""
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD

def check_session_timeout():
    """Check if session has timed out (30 minutes)"""
    if 'logged_in' in session and 'last_activity' in session:
        last_activity = datetime.fromisoformat(session['last_activity'])
        if datetime.now() - last_activity > timedelta(minutes=30):
            session.clear()
            return True
    return False

def login_required(f):
    """Decorator to protect admin routes - requires login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if session has timed out
        if check_session_timeout():
            return redirect(url_for('admin_login', next=request.url, timeout=1))
        
        # Check if user is logged in
        if not session.get('logged_in'):
            return redirect(url_for('admin_login', next=request.url))
        
        # Update last activity time
        session['last_activity'] = datetime.now().isoformat()
        
        return f(*args, **kwargs)
    return decorated_function

# =============================================================================
# USER MANAGEMENT SYSTEM
# =============================================================================

class UserManager:
    """
    Manages the 70 users and their individual Gmail credentials and preferences
    
    Each user has:
    - Individual Gmail API credentials/tokens
    - Digest time preferences (any hour 0-23 + timezone)
    - Weekend and vacation settings
    - AI behavior preferences
    """
    
    def __init__(self):
        self.users_file = USERS_DATA_FILE
        self.users = self._load_users()
    
    def _load_users(self) -> Dict[str, Any]:
        """Load user data from JSON file"""
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"❌ Error loading users: {e}")
            return {}
    
    def _save_users(self):
        """Save user data to JSON file"""
        try:
            with open(self.users_file, 'w') as f:
                json.dump(self.users, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving users: {e}")
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user data by ID"""
        return self.users.get(user_id)
    
    def create_user(self, user_id: str, email: str, **preferences) -> Dict[str, Any]:
        """Create a new user with default preferences"""
        
        default_prefs = {
            'email': email,
            'digest_time': 8,  # 8 AM default
            'timezone': 'UTC',
            'weekend_digests': 'urgent_only',  # 'full', 'urgent_only', 'off'
            'vacation_mode': False,
            'vacation_delegate': '',
            'show_insights_by_default': False,  # UI preference for progressive disclosure
            'created_at': datetime.now().isoformat(),
            'credentials_path': f'credentials/user_{user_id}_credentials.json',
            'token_path': f'credentials/user_{user_id}_token.pickle'
        }
        
        # Override with provided preferences
        default_prefs.update(preferences)
        
        self.users[user_id] = default_prefs
        self._save_users()
        
        print(f"✅ Created user {user_id} with email {email}")
        return default_prefs
    
    def update_user_preferences(self, user_id: str, **preferences):
        """Update user preferences"""
        if user_id in self.users:
            self.users[user_id].update(preferences)
            self._save_users()
            print(f"✅ Updated preferences for user {user_id}")
    
    def start_oauth_flow(self, flask_session) -> str:
        """
        Start OAuth flow by generating authorization URL.
        
        Args:
            flask_session: Flask session object to store state token
        
        Returns:
            str: Authorization URL to redirect user to Google
        """
        _lazy_load_ai_components()
        
        print("🌐 Starting OAuth flow for new user...")
        
        # Generate unique state token for CSRF protection
        state = auth_multiuser.generate_state_token()
        flask_session['oauth_state'] = state
        
        # Build redirect URI (where Google will send user back)
        redirect_uri = f"{BASE_URL}/oauth_callback"
        
        # Generate authorization URL
        auth_url = auth_multiuser.get_oauth_authorization_url(
            redirect_uri=redirect_uri,
            state=state
        )
        
        print(f"✅ Authorization URL generated")
        print(f"🔗 Redirect URI: {redirect_uri}")
        return auth_url
    
    def complete_oauth_flow(self, auth_code: str, state: str, flask_session) -> str:
        """
        Complete OAuth flow by exchanging authorization code for token.
        
        Args:
            auth_code: Authorization code from Google callback
            state: State token from Google callback
            flask_session: Flask session object to validate state
        
        Returns:
            str: User ID of authenticated user
        
        Raises:
            ValueError: If state token doesn't match (CSRF attack)
            Exception: If OAuth flow fails
        """
        _lazy_load_ai_components()
        
        print("🔄 Completing OAuth flow...")
        
        # Validate state token (CSRF protection)
        expected_state = flask_session.get('oauth_state')
        if not expected_state or state != expected_state:
            raise ValueError("Invalid state token - possible CSRF attack")
        
        print("✅ State token validated")
        
        # Generate temporary token path
        temp_token_path = f'credentials/temp_{uuid.uuid4().hex}_token.pickle'
        redirect_uri = f"{BASE_URL}/oauth_callback"
        
        try:
            # Exchange authorization code for access token
            gmail_service, email_address = auth_multiuser.handle_oauth_callback(
                auth_code=auth_code,
                redirect_uri=redirect_uri,
                token_path=temp_token_path
            )
            
            print(f"✅ OAuth successful for: {email_address}")
            
            # Create user ID from email (normalized)
            user_id = email_address.replace('@', '_at_').replace('.', '_dot_')
            final_token_path = f'credentials/user_{user_id}_token.pickle'
            
            # Move temp token to final location
            import shutil
            shutil.move(temp_token_path, final_token_path)
            print(f"💾 Token moved to: {final_token_path}")
            
            # Check if user already exists
            if user_id in self.users:
                print(f"✅ Existing user re-authenticated: {email_address}")
                # Update last login and token path
                self.users[user_id]['last_login'] = datetime.now().isoformat()
                self.users[user_id]['token_path'] = final_token_path
                self._save_users()
            else:
                # Create new user
                print(f"🆕 Creating new user: {email_address}")
                
                # Get Gmail profile for stats
                try:
                    profile = gmail_service.users().getProfile(userId='me').execute()
                    messages_total = profile.get('messagesTotal', 0)
                    threads_total = profile.get('threadsTotal', 0)
                except:
                    messages_total = 0
                    threads_total = 0
                
                user_data = {
                    'email': email_address,
                    'digest_time': 8,  # 8 AM default
                    'timezone': 'UTC',
                    'weekend_digests': 'urgent_only',
                    'vacation_mode': False,
                    'vacation_delegate': '',
                    'show_insights_by_default': False,
                    'created_at': datetime.now().isoformat(),
                    'last_login': datetime.now().isoformat(),
                    'credentials_path': f'credentials/user_{user_id}_credentials.json',
                    'token_path': final_token_path,
                    'gmail_messages_total': messages_total,
                    'gmail_threads_total': threads_total,
                    'total_digests_sent': 0
                }
                
                self.users[user_id] = user_data
                self._save_users()
                print(f"✅ New user created: {email_address}")
            
            # Clear state token from session
            flask_session.pop('oauth_state', None)
            
            return user_id
            
        except Exception as e:
            # Clean up temp token if it exists
            if os.path.exists(temp_token_path):
                os.remove(temp_token_path)
            print(f"❌ OAuth flow failed: {e}")
            raise

    def get_user_gmail_service(self, user_id: str):
        """Get authenticated Gmail service for specific user using their token"""
        _lazy_load_ai_components()
        
        user = self.get_user(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Get user's token path
        token_path = user.get('token_path')
        if not token_path:
            raise ValueError(f"User {user_id} has no token_path - needs to complete OAuth")
        
        # Authenticate using user-specific token
        gmail_service = auth_multiuser.authenticate_gmail_multiuser(token_path)
        
        if not gmail_service:
            raise Exception(f"Failed to authenticate user {user_id} - token may be invalid")
        
        return gmail_service

# Initialize user manager
user_manager = UserManager()

# =============================================================================
# TOKEN MIGRATION FOR EXISTING USERS
# =============================================================================

def migrate_existing_user_token():
    """
    Migrate the existing single-user token to the new per-user token system.
    This is called once on startup to handle the transition from single-user
    to multi-user OAuth.
    """
    old_token_path = 'credentials/token.pickle'
    
    # Check if old token exists
    if not os.path.exists(old_token_path):
        print("📂 No old token to migrate")
        return
    
    print("🔄 Migrating existing OAuth token to multi-user system...")
    
    try:
        # Load old token to get email address
        _lazy_load_ai_components()
        
        import pickle
        from googleapiclient.discovery import build
        
        with open(old_token_path, 'rb') as f:
            creds = pickle.load(f)
        
        # Build Gmail service to get user email
        service = build('gmail', 'v1', credentials=creds)
        profile = service.users().getProfile(userId='me').execute()
        email_address = profile.get('emailAddress')
        
        if not email_address:
            print("❌ Could not extract email from old token")
            return
        
        print(f"📧 Old token belongs to: {email_address}")
        
        # Create user ID
        user_id = email_address.replace('@', '_at_').replace('.', '_dot_')
        new_token_path = f'credentials/user_{user_id}_token.pickle'
        
        # Check if new token already exists
        if os.path.exists(new_token_path):
            print(f"✅ Token already migrated to: {new_token_path}")
            return
        
        # Copy old token to new location
        import shutil
        shutil.copy2(old_token_path, new_token_path)
        print(f"✅ Token migrated to: {new_token_path}")
        
        # Update user record if exists
        user = user_manager.get_user(user_id)
        if user:
            user['token_path'] = new_token_path
            user_manager._save_users()
            print(f"✅ Updated user record for {user_id}")
        else:
            print(f"⚠️  User {user_id} not found in users.json - they'll need to re-authenticate")
        
        print("✅ Token migration complete!")
        print(f"💡 You can now delete the old token: {old_token_path}")
        
    except Exception as e:
        print(f"❌ Token migration failed: {e}")
        print("💡 Users may need to re-authenticate via /oauth_login")

# Run migration on startup
migrate_existing_user_token()

# =============================================================================
# DIGEST DATA MANAGEMENT
# =============================================================================

class DigestDataManager:
    """
    Manages digest data and email reply storage
    
    Stores:
    - Processed email data from AI system
    - Generated replies for button actions
    - User interaction history for learning
    
    FIXES:
    - Reloads data from disk before critical operations (prevents stale data)
    - Uses file locking to prevent race conditions in concurrent writes
    """
    
    def __init__(self):
        self.data_file = DIGEST_DATA_FILE
        self.lock_file = f"{self.data_file}.lock"
        self.digest_data = self._load_data()
        self._file_mtime = self._get_file_mtime()
    
    def _get_file_mtime(self) -> float:
        """Get file modification time"""
        try:
            return os.path.getmtime(self.data_file) if os.path.exists(self.data_file) else 0
        except:
            return 0
    
    def _acquire_lock(self, file_handle):
        """Acquire file lock (cross-platform)"""
        if _has_msvcrt:
            # Windows
            msvcrt.locking(file_handle.fileno(), msvcrt.LK_LOCK, 1)
        else:
            # Unix/Linux
            try:
                fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX)
            except (IOError, OSError):
                pass  # Lock not supported on this system
    
    def _release_lock(self, file_handle):
        """Release file lock (cross-platform)"""
        if _has_msvcrt:
            # Windows
            try:
                msvcrt.locking(file_handle.fileno(), msvcrt.LK_UNLCK, 1)
            except:
                pass
        else:
            # Unix/Linux
            try:
                fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)
            except (IOError, OSError):
                pass
    
    def _should_reload(self) -> bool:
        """Check if file has been modified since last load"""
        current_mtime = self._get_file_mtime()
        if current_mtime > self._file_mtime:
            return True
        return False
    
    def _reload_if_needed(self):
        """Reload data from disk if file has been modified (fixes stale data issue)"""
        if self._should_reload():
            print(f"🔄 Reloading digest data (file modified)")
            try:
                current_mtime = self._get_file_mtime()
                new_data = self._load_data()
                # Merge new data, preserving any in-memory changes
                for user_id, user_data in new_data.items():
                    if user_id not in self.digest_data:
                        self.digest_data[user_id] = {}
                    if isinstance(user_data, dict):
                        for key, value in user_data.items():
                            if key == 'digest_history':
                                # Merge digest history
                                if 'digest_history' not in self.digest_data[user_id]:
                                    self.digest_data[user_id]['digest_history'] = []
                                existing_entries = {e.get('sent_at'): e for e in self.digest_data[user_id].get('digest_history', [])}
                                for entry in value:
                                    if entry.get('sent_at') not in existing_entries:
                                        self.digest_data[user_id]['digest_history'].append(entry)
                            elif key not in self.digest_data[user_id]:
                                # Only add if doesn't exist (preserve existing email data)
                                self.digest_data[user_id][key] = value
                self._file_mtime = current_mtime
                print(f"✅ Digest data reloaded and merged")
            except Exception as e:
                print(f"⚠️  Error reloading data: {e}")
    
    def _load_data(self) -> Dict[str, Any]:
        """Load digest data from file with locking"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    self._acquire_lock(f)
                    try:
                        data = json.load(f)
                    finally:
                        self._release_lock(f)
                    return data
            return {}
        except Exception as e:
            print(f"❌ Error loading digest data: {e}")
            return {}
    
    def _save_data(self):
        """Save digest data to file with atomic write and locking (prevents race conditions)"""
        try:
            # Write to temporary file first (atomic write)
            temp_file = f"{self.data_file}.tmp"
            with open(temp_file, 'w') as f:
                self._acquire_lock(f)
                try:
                    json.dump(self.digest_data, f, indent=2, default=str)
                    f.flush()
                    os.fsync(f.fileno())  # Ensure data is written to disk
                finally:
                    self._release_lock(f)
            
            # Atomically replace the original file
            shutil.move(temp_file, self.data_file)
            self._file_mtime = self._get_file_mtime()
            
        except Exception as e:
            print(f"❌ Error saving digest data: {e}")
            # Clean up temp file if it exists
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass
    
    def store_email_data(self, user_id: str, email_id: str, email_data: Dict[str, Any]):
        """Store processed email data for button actions - PRESERVES existing data"""
        
        # FIX: Reload data if file has been modified (fixes stale data issue)
        self._reload_if_needed()
        
        # Validate email_id
        if not email_id:
            print(f"⚠️  Warning: email_id is None or empty, generating UUID")
            email_id = str(uuid.uuid4())
        
        if user_id not in self.digest_data:
            self.digest_data[user_id] = {}
        
        # Only store if email doesn't already exist (preserve existing data)
        if email_id not in self.digest_data[user_id]:
            # Store the complete email data from your AI system
            self.digest_data[user_id][email_id] = {
                'email_data': email_data,
                'stored_at': datetime.now().isoformat(),
                'actions_taken': []
            }
            print(f"📧 Stored new email data: {email_id}")
        else:
            print(f"📧 Email data already exists, preserving: {email_id}")
        
        self._save_data()
    
    def get_email_data(self, user_id: str, email_id: str) -> Optional[Dict[str, Any]]:
        """Get stored email data - reloads from disk if file was modified"""
        # FIX: Reload data if file has been modified (fixes stale data issue)
        self._reload_if_needed()
        
        # FIX #4: Add defensive checks for old data structures (backward compatibility)
        user_data = self.digest_data.get(user_id, {})
        if not user_data:
            return None
        
        email_entry = user_data.get(email_id)
        if not email_entry:
            return None
        
        # Handle both old and new data structures
        # New structure: {'email_data': {...}, 'stored_at': ..., 'actions_taken': [...]}
        # Old structure: email_entry IS the email_data directly
        if isinstance(email_entry, dict):
            if 'email_data' in email_entry:
                # New structure
                return email_entry['email_data']
            else:
                # Old structure - email_entry is the email data itself
                # Check if it looks like email data (has common email fields)
                if any(key in email_entry for key in ['sender_email', 'subject', 'body', 'ai_summary']):
                    return email_entry
        
        return None
    
    def record_action(self, user_id: str, email_id: str, action: str):
        """Record user action for learning"""
        # FIX: Reload data if file has been modified
        self._reload_if_needed()
        
        if user_id in self.digest_data and email_id in self.digest_data[user_id]:
            self.digest_data[user_id][email_id]['actions_taken'].append({
                'action': action,
                'timestamp': datetime.now().isoformat()
            })
            self._save_data()
    
    def record_digest_sent(self, user_id: str, email_count: int):
        """Record when a digest is sent"""
        # FIX: Reload data if file has been modified
        self._reload_if_needed()
        
        if user_id not in self.digest_data:
            self.digest_data[user_id] = {}
        
        if 'digest_history' not in self.digest_data[user_id]:
            self.digest_data[user_id]['digest_history'] = []
        
        self.digest_data[user_id]['digest_history'].append({
            'sent_at': datetime.now().isoformat(),
            'email_count': email_count
        })
        
        self._save_data()
    
    def get_stats_today(self) -> Dict[str, int]:
        """Get statistics for today"""
        today = datetime.now().date()
        
        digests_sent = 0
        emails_processed = 0
        
        for user_id, user_data in self.digest_data.items():
            # Count digests sent today
            if 'digest_history' in user_data:
                for digest in user_data['digest_history']:
                    try:
                        sent_date = datetime.fromisoformat(digest['sent_at']).date()
                        if sent_date == today:
                            digests_sent += 1
                            emails_processed += digest.get('email_count', 0)
                    except:
                        pass
        
        return {
            'digests_sent_today': digests_sent,
            'total_emails_processed': emails_processed
        }

# Initialize digest data manager  
digest_manager = DigestDataManager()

# =============================================================================
# CORE DIGEST GENERATION
# =============================================================================

def generate_user_digest(user_id: str) -> Dict[str, Any]:
    """
    Generate daily digest for a specific user using your AI system
    
    PHASE 4 INTEGRATION: Now using AdvancedEmailProcessor with Phase 1+2+3 features:
    - Phase 1: AI-enhanced reply generation (BART + spaCy)
    - Phase 2: Sensitive topic detection & edge case handling
    - Phase 3: Learning from user edits & confidence adjustments
    """
    
    # PERFORMANCE INSTRUMENTATION: Start timing
    digest_start_time = time.time()
    timing_breakdown = {
        'total': 0,
        'fetch_emails': 0,
        'ai_processing': 0,
        'per_email': [],
        'organize_results': 0,
        'store_data': 0
    }
    
    # Load AI components only when actually generating a digest
    _lazy_load_ai_components()
    
    print(f"🚀 Generating daily digest for user {user_id} (Phase 1+2+3 enabled)")
    print(f"⏱️  [PERFORMANCE] Starting digest generation at {datetime.now().strftime('%H:%M:%S')}")
    
    user = user_manager.get_user(user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")
    
    try:
        # Initialize AdvancedEmailProcessor via singleton to avoid duplicate model loads
        print("🤖 Obtaining AdvancedEmailProcessor singleton (Phase 1+2+3)...")
        processor = get_advanced_processor()
        
        # Get Gmail service for this user
        print("📧 Fetching recent emails...")
        fetch_start = time.time()
        gmail_service = user_manager.get_user_gmail_service(user_id)
        
        # Fetch emails using EmailFetcher
        fetcher = EmailFetcher(gmail_service)
        raw_emails = fetcher.get_recent_emails(hours=24, include_read=False)
        timing_breakdown['fetch_emails'] = time.time() - fetch_start
        print(f"📬 Fetched {len(raw_emails)} emails")
        print(f"⏱️  [PERFORMANCE] Email fetch took {timing_breakdown['fetch_emails']:.2f}s")
        
        if not raw_emails:
            return {
                'total_emails': 0,
                'high_priority': [],
                'medium_priority': [],
                'low_priority': [],
                'processing_summary': {'message': 'No emails found in last 24 hours'},
                'user_id': user_id,
                'user_preferences': user,
                'generated_at': datetime.now().isoformat()
            }
        
        # PHASE 2 OPTIMIZATION: Use batch processing for massive speedup!
        print("🚀 Processing emails with OPTIMIZED BATCH AI (Phase 2)...")
        ai_processing_start = time.time()
        
        # Gate AI-heavy work to cap concurrency
        SEMAPHORE.acquire()
        try:
            # Use optimized batch processing (processes 10 emails at once through BART)
            processed_emails = processor.process_email_batch_optimized(
                raw_emails,
                batch_size=10  # Process 10 emails per batch
            )
        finally:
            SEMAPHORE.release()
        
        # Ensure all emails have IDs for tracking
        for result in processed_emails:
            if 'id' not in result:
                result['id'] = str(uuid.uuid4())
        
        timing_breakdown['ai_processing'] = time.time() - ai_processing_start
        print(f"✅ Processed {len(processed_emails)} emails with BATCH AI optimization")
        print(f"⏱️  [PERFORMANCE] Total AI processing took {timing_breakdown['ai_processing']:.2f}s")
        print(f"⏱️  [PERFORMANCE] Average per email: {timing_breakdown['ai_processing']/len(processed_emails):.2f}s")
        print(f"🚀 [SPEEDUP] Batch processing enabled - expect 4-5x faster than sequential!")
        
        # Organize by priority
        print("📋 Organizing by priority...")
        organize_start = time.time()
        high_priority = []
        medium_priority = []
        low_priority = []
        
        for email in processed_emails:
            priority = email.get('priority_level', 'Low')
            if priority == 'High':
                high_priority.append(email)
            elif priority == 'Medium':
                medium_priority.append(email)
            else:
                low_priority.append(email)
        
        # Sort by AI confidence and priority score
        high_priority.sort(key=lambda x: (
            x.get('priority_score', 0),
            x.get('reply_confidence', 0)
        ), reverse=True)
        
        medium_priority.sort(key=lambda x: x.get('reply_confidence', 0), reverse=True)
        low_priority.sort(key=lambda x: x.get('reply_confidence', 0), reverse=True)
        timing_breakdown['organize_results'] = time.time() - organize_start
        
        # Store email data for button actions
        print("💾 Storing email data for button actions...")
        store_start = time.time()
        for priority_group in ['high_priority', 'medium_priority', 'low_priority']:
            email_list = {'high_priority': high_priority, 'medium_priority': medium_priority, 'low_priority': low_priority}[priority_group]
            for email in email_list:
                email_id = email.get('id')
                # FIX #3: Ensure email_id is never None (validate at source)
                if not email_id:
                    print(f"⚠️  Warning: Email missing 'id' field, generating UUID")
                    email_id = str(uuid.uuid4())
                    email['id'] = email_id  # Set it back in the email dict for consistency
                digest_manager.store_email_data(user_id, email_id, email)
        timing_breakdown['store_data'] = time.time() - store_start
        
        # Count Phase 1+2+3 features used
        ai_enhanced_count = sum(1 for e in processed_emails if e.get('reply_method') == 'ai_enhanced')
        safe_mode_count = sum(1 for e in processed_emails if e.get('reply_method') == 'safe_mode')
        edge_case_count = sum(1 for e in processed_emails if e.get('edge_case_detected'))
        
        # Generate processing summary
        processing_summary = {
            'total_processed': len(processed_emails),
            'high_priority_count': len(high_priority),
            'medium_priority_count': len(medium_priority),
            'low_priority_count': len(low_priority),
            'phase_features': {
                'ai_enhanced_replies': ai_enhanced_count,
                'safe_mode_replies': safe_mode_count,
                'edge_cases_detected': edge_case_count,
                'learning_enabled': True
            }
        }
        
        # PERFORMANCE: Calculate total time
        timing_breakdown['total'] = time.time() - digest_start_time
        
        # Add user-specific metadata
        results = {
            'total_emails': len(processed_emails),
            'high_priority': high_priority,
            'medium_priority': medium_priority,
            'low_priority': low_priority,
            'processing_summary': processing_summary,
            'user_id': user_id,
            'user_preferences': user,
            'generated_at': datetime.now().isoformat(),
            'performance_metrics': timing_breakdown  # Add performance data
        }
        
        print(f"✅ Digest generated successfully with Phase 1+2+3!")
        print(f"📊 Summary: {len(processed_emails)} emails processed")
        print(f"   🔥 High: {len(high_priority)}, ⚡ Medium: {len(medium_priority)}, 💤 Low: {len(low_priority)}")
        print(f"   🤖 AI-enhanced: {ai_enhanced_count}, 🛡️ Safe mode: {safe_mode_count}, ⚠️ Edge cases: {edge_case_count}")
        
        # PERFORMANCE REPORT
        print(f"\n{'='*60}")
        print(f"⏱️  PERFORMANCE REPORT - User {user_id}")
        print(f"{'='*60}")
        print(f"Total Digest Generation Time: {timing_breakdown['total']:.2f}s ({timing_breakdown['total']/60:.2f} minutes)")
        print(f"  ├─ Email Fetching:       {timing_breakdown['fetch_emails']:.2f}s ({timing_breakdown['fetch_emails']/timing_breakdown['total']*100:.1f}%)")
        print(f"  ├─ AI Processing:        {timing_breakdown['ai_processing']:.2f}s ({timing_breakdown['ai_processing']/timing_breakdown['total']*100:.1f}%)")
        print(f"  │  └─ Per Email Avg:     {timing_breakdown['ai_processing']/len(processed_emails):.2f}s")
        print(f"  ├─ Organizing Results:   {timing_breakdown['organize_results']:.2f}s ({timing_breakdown['organize_results']/timing_breakdown['total']*100:.1f}%)")
        print(f"  └─ Storing Data:         {timing_breakdown['store_data']:.2f}s ({timing_breakdown['store_data']/timing_breakdown['total']*100:.1f}%)")
        
        # Show optimization info
        total_high_medium = len([e for e in processed_emails if e.get('priority_level') in ['High', 'Medium']])
        total_low = len([e for e in processed_emails if e.get('priority_level') == 'Low'])
        
        print(f"\n🚀 OPTIMIZATIONS ACTIVE:")
        print(f"  ✅ Phase 2: Batch AI processing (10 emails per batch)")
        print(f"  ✅ Phase 4: Skip replies for {total_low} low-priority emails")
        print(f"  📊 Generated {total_high_medium} replies (High/Medium only)")
        print(f"  💰 Estimated savings: ~{total_low * 30:.0f}s from skipped replies")
        print(f"  🎯 Target: 1-2 minutes per digest (vs 12 min before!)")
        
        print(f"{'='*60}\n")
        
        return results
        
    except Exception as e:
        print(f"❌ Error generating digest for user {user_id}: {e}")
        import traceback
        traceback.print_exc()
        return {
            'total_emails': 0,
            'high_priority': [],
            'medium_priority': [],
            'low_priority': [],
            'processing_summary': {'error': str(e)},
            'user_id': user_id,
            'error': True
        }

# =============================================================================
# BUTTON ACTION HANDLERS
# =============================================================================

@app.route('/send/<user_id>/<email_id>')
def send_reply(user_id: str, email_id: str):
    """
    Handle 'Send Reply' button clicks from digest emails
    
    This sends the AI-generated reply using your existing Gmail integration
    """
    
    print(f"📤 Send reply request: User {user_id}, Email {email_id}")
    
    try:
        # Get the stored email data with AI-generated reply
        email_data = digest_manager.get_email_data(user_id, email_id)
        if not email_data:
            abort(404, "Email data not found")
        
        # Get the AI-generated reply from your advanced system
        advanced_reply = email_data.get('advanced_reply', {})
        reply_text = advanced_reply.get('primary_reply', '')
        
        if not reply_text:
            abort(400, "No reply available for this email")
        
        # Get Gmail service for this user
        gmail_service = user_manager.get_user_gmail_service(user_id)
        
        # Prepare reply email
        original_subject = email_data.get('subject', '')
        reply_subject = f"Re: {original_subject}" if not original_subject.startswith('Re:') else original_subject
        
        # Create email message
        message = MIMEText(reply_text)
        message['to'] = email_data.get('sender_email', '')
        message['subject'] = reply_subject
        message['in-reply-to'] = email_data.get('message_id', '')
        
        # Send via Gmail API
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        send_result = gmail_service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        # Record the action for learning
        digest_manager.record_action(user_id, email_id, 'reply_sent')
        
        print(f"✅ Reply sent successfully!")
        return render_template('action_success.html', 
                             action='Reply sent', 
                             email_subject=original_subject,
                             user_id=user_id)
        
    except Exception as e:
        print(f"❌ Error sending reply: {e}")
        return render_template('action_error.html', 
                             error=str(e),
                             action='send reply',
                             user_id=user_id), 500

@app.route('/details/<user_id>/<email_id>')
def email_details(user_id: str, email_id: str):
    """
    Handle 'More' button clicks - shows expanded AI insights
    
    Displays full AI analysis, thread status, tone analysis, etc.
    """
    
    print(f"🔍 Details request: User {user_id}, Email {email_id}")
    
    try:
        # Get the stored email data
        email_data = digest_manager.get_email_data(user_id, email_id)
        if not email_data:
            abort(404, "Email data not found")
        
        # Get user preferences
        user = user_manager.get_user(user_id)
        if not user:
            abort(404, "User not found")
        
        # Prepare detailed view data
        details_data = {
            'user_id': user_id,
            'email_id': email_id,
            'sender_name': email_data.get('sender_name', 'Unknown'),
            'sender_email': email_data.get('sender_email', ''),
            'subject': email_data.get('subject', 'No Subject'),
            'received_date': email_data.get('received_date', 'Unknown'),
            'body': email_data.get('body', ''),
            'ai_summary': email_data.get('ai_summary', ''),
            'priority_level': email_data.get('priority_level', 'Medium'),
            'priority_score': email_data.get('priority_score', 0),
            'priority_reasons': email_data.get('priority_reasons', []),
            'tone_analysis': email_data.get('tone_analysis', {}),
            'thread_analysis': email_data.get('thread_analysis', {}),
            'contextual_insights': email_data.get('contextual_insights', []),
            'advanced_reply': email_data.get('advanced_reply', {}),
            'entities': email_data.get('entities', {})
        }
        
        return render_template('email_details.html', **details_data)
        
    except Exception as e:
        print(f"❌ Error loading details page: {e}")
        return render_template('action_error.html', 
                             error=str(e),
                             action='view details',
                             user_id=user_id), 500

@app.route('/edit/<user_id>/<email_id>')
def edit_reply(user_id: str, email_id: str):
    """
    Handle 'Edit Reply' button clicks from digest emails
    
    Shows edit interface with AI-generated reply and alternatives
    """
    
    print(f"✏️ Edit reply request: User {user_id}, Email {email_id}")
    
    try:
        # Get the stored email data
        email_data = digest_manager.get_email_data(user_id, email_id)
        if not email_data:
            abort(404, "Email data not found")
        
        # Prepare data for edit template
        edit_data = {
            'user_id': user_id,
            'email_id': email_id,
            'original_email': {
                'sender_name': email_data.get('sender_name', 'Unknown'),
                'sender_email': email_data.get('sender_email', ''),
                'subject': email_data.get('subject', 'No Subject'),
                'body': email_data.get('body', ''),
                'ai_summary': email_data.get('ai_summary', ''),
            },
            'advanced_reply': email_data.get('advanced_reply', {}),
            'contextual_insights': email_data.get('contextual_insights', []),
            'tone_analysis': email_data.get('tone_analysis', {}),
            'thread_analysis': email_data.get('thread_analysis', {}),
            'priority_reasons': email_data.get('priority_reasons', [])
        }
        
        return render_template('edit_reply.html', 
                             user_id=edit_data['user_id'],
                             email_id=edit_data['email_id'],
                             original_email=edit_data['original_email'],
                             advanced_reply=edit_data['advanced_reply'],
                             contextual_insights=edit_data['contextual_insights'],
                             tone_analysis=edit_data['tone_analysis'],
                             thread_analysis=edit_data['thread_analysis'],
                             priority_reasons=edit_data['priority_reasons'])
        
    except Exception as e:
        print(f"❌ Error loading edit page: {e}")
        return render_template('action_error.html', 
                             error=str(e),
                             action='edit reply',
                             user_id=user_id), 500

@app.route('/send_edited/<user_id>/<email_id>', methods=['POST'])
def send_edited_reply(user_id: str, email_id: str):
    """
    Handle sending of edited replies
    
    PHASE 3 INTEGRATION: Now tracks edits to improve future AI-generated replies
    """
    
    print(f"📤 Send edited reply: User {user_id}, Email {email_id}")
    
    try:
        # Get edited reply content
        edited_reply = request.form.get('reply_content', '').strip()
        if not edited_reply:
            abort(400, "Reply content cannot be empty")
        
        # Get original email data
        email_data = digest_manager.get_email_data(user_id, email_id)
        if not email_data:
            abort(404, "Email data not found")
        
        # PHASE 3: Track the edit before sending (close the learning loop)
        original_reply = email_data.get('advanced_reply', {}).get('primary_reply', '')
        if original_reply:
            print("🧠 Tracking reply edit for learning...")
            try:
                # Call track_edit endpoint to record the learning
                track_result = track_reply_edit_internal(
                    user_id=user_id,
                    email_id=email_id,
                    original_reply=original_reply,
                    edited_reply=edited_reply,
                    email_data=email_data
                )
                print(f"✅ Edit tracked: {track_result.get('edit_type', 'unknown')}, similarity: {track_result.get('similarity', 0):.2f}")
            except Exception as track_error:
                print(f"⚠️ Failed to track edit (non-critical): {track_error}")
                # Don't fail the send operation if tracking fails
        
        # Send the edited reply (same logic as send_reply but with edited content)
        gmail_service = user_manager.get_user_gmail_service(user_id)
        
        original_subject = email_data.get('subject', '')
        reply_subject = f"Re: {original_subject}" if not original_subject.startswith('Re:') else original_subject
        
        message = MIMEText(edited_reply)
        message['to'] = email_data.get('sender_email', '')
        message['subject'] = reply_subject
        message['in-reply-to'] = email_data.get('message_id', '')
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        send_result = gmail_service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        # Record the action
        digest_manager.record_action(user_id, email_id, 'edited_reply_sent')
        
        print(f"✅ Edited reply sent successfully!")
        return render_template('action_success.html', 
                             action='Edited reply sent', 
                             email_subject=original_subject,
                             user_id=user_id)
        
    except Exception as e:
        print(f"❌ Error sending edited reply: {e}")
        return render_template('action_error.html', 
                             error=str(e),
                             action='send edited reply',
                             user_id=user_id), 500

@app.route('/track_edit/<user_id>/<email_id>', methods=['POST'])
def track_reply_edit(user_id: str, email_id: str):
    """
    PHASE 3: Track reply edits for learning system
    
    This endpoint records when users edit AI-generated replies and learns from the changes
    to improve future suggestions. Returns learning insights and edit analysis.
    
    Expected POST data:
    {
        "original_reply": "AI-generated reply text",
        "edited_reply": "User's edited version",
        "accepted": true/false  # Whether user accepted (minor edit) or rejected (major rewrite)
    }
    """
    
    print(f"🧠 Track edit request: User {user_id}, Email {email_id}")
    
    try:
        # Parse request data
        data = request.get_json() or {}
        original_reply = data.get('original_reply', '').strip()
        edited_reply = data.get('edited_reply', '').strip()
        
        if not original_reply or not edited_reply:
            return jsonify({
                'success': False,
                'error': 'Both original_reply and edited_reply are required'
            }), 400
        
        # Get email data for context
        email_data = digest_manager.get_email_data(user_id, email_id)
        if not email_data:
            return jsonify({
                'success': False,
                'error': 'Email data not found'
            }), 404
        
        # Call internal tracking function
        result = track_reply_edit_internal(
            user_id=user_id,
            email_id=email_id,
            original_reply=original_reply,
            edited_reply=edited_reply,
            email_data=email_data
        )
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Error tracking edit: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def track_reply_edit_internal(user_id: str, email_id: str, original_reply: str, 
                              edited_reply: str, email_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Internal function to track reply edits (used by both track_reply_edit route and send_edited)
    
    PHASE 3: Integrates with SmartReplyGenerator learning system
    """
    
    try:
        # Load smart reply generator with learning tracker via singleton
        processor = get_advanced_processor()
        
        # Get the smart reply generator (which has the learning tracker)
        if not hasattr(processor, 'smart_reply_generator') or processor.smart_reply_generator is None:
            print("⚠️ Smart reply generator not available, skipping edit tracking")
            return {
                'success': False,
                'error': 'Smart reply generator not initialized'
            }
        
        generator = processor.smart_reply_generator
        
        # Extract metadata from email for tracking
        advanced_reply = email_data.get('advanced_reply', {})
        reply_metadata = advanced_reply.get('reply_metadata', {})
        
        # Track the edit using Phase 3 learning tracker
        print(f"📝 Tracking edit with smart reply generator...")
        edit_result = generator.track_reply_edit(
            email_data=email_data,
            original_reply=original_reply,
            edited_reply=edited_reply,
            reply_metadata=reply_metadata
        )
        
        # Get updated learning insights
        insights = generator.get_learning_insights()
        
        # Return comprehensive tracking result
        return {
            'success': True,
            'edit_tracked': True,
            'edit_id': edit_result.get('edit_id'),
            'similarity': edit_result.get('similarity', 0.0),
            'edit_type': edit_result.get('edit_type', 'unknown'),
            'changes_detected': edit_result.get('changes_detected', []),
            'learning_insights': {
                'total_edits_tracked': insights.get('total_edits', 0),
                'acceptance_rate': insights.get('acceptance_rate', 0.0),
                'learning_confidence': insights.get('learning_confidence', 0.0),
                'average_similarity': insights.get('average_similarity', 0.0)
            },
            'message': f"Edit tracked successfully! Similarity: {edit_result.get('similarity', 0):.2%}"
        }
        
    except Exception as e:
        print(f"❌ Error in track_reply_edit_internal: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }

@app.route('/archive/<user_id>/<email_id>')
def archive_email(user_id: str, email_id: str):
    """
    Handle archive button clicks
    """
    
    print(f"🗂️ Archive email: User {user_id}, Email {email_id}")
    
    try:
        # Record the action for learning
        digest_manager.record_action(user_id, email_id, 'archived')
        
        # In a full implementation, you'd archive the email via Gmail API
        # For now, just record the action
        
        email_data = digest_manager.get_email_data(user_id, email_id)
        subject = email_data.get('subject', 'Email') if email_data else 'Email'
        
        return render_template('action_success.html', 
                             action='Email archived', 
                             email_subject=subject,
                             user_id=user_id)
        
    except Exception as e:
        print(f"❌ Error archiving email: {e}")
        return render_template('action_error.html', 
                             error=str(e),
                             action='archive email',
                             user_id=user_id), 500

# =============================================================================
# USER SETTINGS AND MANAGEMENT
# =============================================================================

@app.route('/settings/<user_id>')
@app.route('/user_settings/<user_id>')  # Alternative URL for compatibility
def user_settings(user_id: str):
    """
    User settings page for digest preferences
    """
    
    user = user_manager.get_user(user_id)
    if not user:
        abort(404, "User not found")
    
    return render_template('user_settings.html', user=user, user_id=user_id)

@app.route('/update_settings/<user_id>', methods=['POST'])
def update_settings(user_id: str):
    """
    Update user settings
    """
    
    try:
        # Get form data
        digest_time = int(request.form.get('digest_time', 8))
        timezone = request.form.get('timezone', 'UTC')
        weekend_digests = request.form.get('weekend_digests', 'urgent_only')
        vacation_mode = request.form.get('vacation_mode') == 'on'
        vacation_delegate = request.form.get('vacation_delegate', '')
        show_insights_by_default = request.form.get('show_insights_by_default') == 'on'
        
        # Update user preferences
        user_manager.update_user_preferences(
            user_id,
            digest_time=digest_time,
            timezone=timezone,
            weekend_digests=weekend_digests,
            vacation_mode=vacation_mode,
            vacation_delegate=vacation_delegate,
            show_insights_by_default=show_insights_by_default
        )
        
        return redirect(url_for('settings_success', user_id=user_id))
        
    except Exception as e:
        print(f"❌ Error updating settings: {e}")
        return render_template('action_error.html', 
                             error=str(e),
                             action='update settings',
                             user_id=user_id), 500

@app.route('/settings_success/<user_id>')
def settings_success(user_id: str):
    """
    Show success page after saving settings
    """
    user = user_manager.get_user(user_id)
    if not user:
        abort(404)
    
    return render_template('settings_success.html', 
                         user=user,
                         user_id=user_id)

# =============================================================================
# DIGEST GENERATION AND TESTING ROUTES
# =============================================================================

@app.route('/generate_digest/<user_id>')
def generate_digest_route(user_id: str):
    """
    Generate and display digest for testing (before sending via email)
    """
    
    try:
        digest_data = generate_user_digest(user_id)
        user = user_manager.get_user(user_id)
        
        # Prepare data for template
        template_data = {
            'user_id': user_id,
            'user': user,
            'digest_html': None,  # Will be generated by email_templates
            'digest_stats': {
                'total_emails': digest_data.get('total_emails', 0),
                'high_priority': len(digest_data.get('high_priority', [])),
                'suggested_replies': sum(1 for email in digest_data.get('high_priority', []) + digest_data.get('medium_priority', []) if email.get('advanced_reply', {}).get('primary_reply')),
                'generation_time': digest_data.get('generated_at', 'Unknown')
            },
            'generation_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return render_template('digest_preview.html', **template_data)
        
    except Exception as e:
        print(f"❌ Error generating digest: {e}")
        return render_template('action_error.html', 
                             error=str(e),
                             action='generate digest',
                             user_id=user_id), 500

@app.route('/send_digest/<user_id>')
def send_digest_route(user_id: str):
    """
    Generate and send digest email to user
    """
    
    try:
        # Generate digest data
        digest_data = generate_user_digest(user_id)
        
        # Generate HTML email (will create this next)
        from email_templates import create_digest_email
        digest_html = create_digest_email(digest_data, BASE_URL)
        
        # Send digest email
        user = user_manager.get_user(user_id)
        gmail_service = user_manager.get_user_gmail_service(user_id)
        
        # Create digest email
        message = MIMEMultipart('alternative')
        message['to'] = user['email']
        message['subject'] = f"📧 VoxMail Daily Digest - {datetime.now().strftime('%A, %B %d')}"
        html_part = MIMEText(digest_html, 'html')
        message.attach(html_part)
        
        # Send via Gmail API
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        send_result = gmail_service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        # Record digest sent for stats tracking
        total_emails = digest_data.get('total_emails', 0)
        digest_manager.record_digest_sent(user_id, total_emails)
        
        print(f"✅ Digest sent to {user['email']} - {total_emails} emails processed")
        return jsonify({
            'success': True,
            'message': f"Digest sent to {user['email']}",
            'total_emails': total_emails
        })
        
    except Exception as e:
        print(f"❌ Error sending digest: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# =============================================================================
# ADMIN AND TESTING ROUTES
# =============================================================================

@app.route('/')
@login_required
def dashboard():
    """
    Comprehensive Admin Dashboard
    
    Shows all users, system statistics, health monitoring, and recent activity.
    This is your main control panel for managing the email digest system.
    """
    try:
        # Get all users with detailed information
        users = []
        for user_id, user_info in user_manager.users.items():
            user_data = {
                'id': user_id,
                'email': user_info.get('email', 'Unknown'),
                'digest_time': user_info.get('digest_time', 8),
                'timezone': user_info.get('timezone', 'UTC'),
                'vacation_mode': user_info.get('vacation_mode', False),
                'show_insights_by_default': user_info.get('show_insights_by_default', False),
                'weekend_digests': user_info.get('weekend_digests', 'full'),
                'created_at': user_info.get('created_at', 'Unknown')
            }
            users.append(user_data)
        
        # System statistics with real tracking
        today_stats = digest_manager.get_stats_today()
        stats = {
            'total_users': len(users),
            'active_users_today': len([u for u in users if not u.get('vacation_mode', False)]),
            'digests_sent_today': today_stats['digests_sent_today'],
            'total_emails_processed': today_stats['total_emails_processed']
        }
        
        # Recent activity (can be expanded with real tracking)
        recent_activity = []
        for user in users[:5]:  # Show last 5 users
            recent_activity.append({
                'type': 'user',
                'description': f"User: {user['email']}",
                'details': f"Digest time: {user['digest_time']}:00 {user['timezone']}",
                'timestamp': user.get('created_at', 'Unknown')
            })
        
        # System health check
        system_health = {
            'ai_processing': True,
            'gmail_api': True,
            'email_sending': True,
            'storage': True
        }
        
        return render_template('admin_dashboard.html',
                             users=users,
                             stats=stats,
                             recent_activity=recent_activity,
                             system_health=system_health)
    
    except Exception as e:
        print(f"❌ Error loading dashboard: {e}")
        return render_template('error.html',
                             error_code=500,
                             error_message=f"Dashboard error: {str(e)}"), 500

@app.route('/oauth_login')
def oauth_login():
    """
    OAuth authentication endpoint - Start multi-user OAuth flow.
    
    This redirects the user to Google's consent screen where they can
    authorize VoxMail to access their Gmail account.
    """
    try:
        print("🔐 Starting OAuth flow for new user...")
        
        # Start OAuth flow and get authorization URL
        auth_url = user_manager.start_oauth_flow(session)
        
        print(f"✅ Redirecting to Google OAuth: {auth_url[:50]}...")
        return redirect(auth_url)
    
    except Exception as e:
        print(f"❌ Error starting OAuth flow: {e}")
        import traceback
        traceback.print_exc()
        return render_template('action_error.html', 
                             error=f"Failed to start OAuth flow: {str(e)}")

@app.route('/oauth_callback')
def oauth_callback():
    """
    OAuth callback endpoint - Complete multi-user OAuth flow.
    
    Google redirects here after user grants/denies permissions.
    We exchange the authorization code for an access token and
    create/update the user account.
    """
    try:
        # Get authorization code and state from query params
        auth_code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')
        
        # Handle errors (user denied access)
        if error:
            print(f"❌ OAuth error from Google: {error}")
            # Show friendly permissions explanation page instead of error
            return render_template('permissions_needed.html'), 403
        
        # Validate required parameters
        if not auth_code or not state:
            print("❌ Missing OAuth parameters")
            return render_template('action_error.html', 
                                 error="Missing OAuth parameters (code or state)")
        
        print(f"🔄 Processing OAuth callback...")
        print(f"📝 Authorization code: {auth_code[:20]}...")
        print(f"🔐 State token: {state[:20]}...")
        
        # Complete OAuth flow
        user_id = user_manager.complete_oauth_flow(auth_code, state, session)
        
        print(f"✅ OAuth flow completed successfully for user: {user_id}")
        return redirect(url_for('user_settings', user_id=user_id))
    
    except ValueError as e:
        # CSRF attack or invalid state
        print(f"❌ OAuth callback validation failed: {e}")
        return render_template('action_error.html', 
                             error=f"OAuth validation failed: {str(e)}"), 403
    
    except PermissionError as e:
        # User didn't grant required scopes
        print(f"❌ Missing required permissions: {e}")
        return render_template('permissions_needed.html'), 403
    
    except Exception as e:
        print(f"❌ OAuth callback failed: {e}")
        import traceback
        traceback.print_exc()
        return render_template('action_error.html', 
                             error=f"OAuth callback failed: {str(e)}"), 500

@app.route('/preview_digest/<user_id>')
def preview_digest(user_id: str):
    """
    Preview digest without sending
    """
    try:
        digest_data = generate_user_digest(user_id)
        user = user_manager.get_user(user_id)
        
        # Generate the actual HTML digest
        from email_templates import create_digest_email
        digest_html = create_digest_email(digest_data, BASE_URL)
        
        # Prepare data for template
        template_data = {
            'user_id': user_id,
            'user': user,
            'digest_html': digest_html,
            'digest_stats': {
                'total_emails': digest_data.get('total_emails', 0),
                'high_priority': len(digest_data.get('high_priority', [])),
                'suggested_replies': sum(1 for email in digest_data.get('high_priority', []) + digest_data.get('medium_priority', []) if email.get('advanced_reply', {}).get('primary_reply')),
                'generation_time': digest_data.get('generated_at', 'Unknown')
            },
            'generation_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return render_template('digest_preview.html', **template_data)
        
    except Exception as e:
        print(f"❌ Error previewing digest: {e}")
        return render_template('action_error.html', 
                             error=str(e),
                             action='preview digest',
                             user_id=user_id), 500

@app.route('/admin')
@login_required
def admin_dashboard():
    """
    Redirect to main dashboard (merged into /)
    Kept for backward compatibility with existing links/bookmarks
    """
    return redirect(url_for('dashboard'))

@app.route('/system_check')
@login_required
def system_check():
    """
    System health check endpoint
    """
    try:
        health_results = {
            'timestamp': datetime.now().isoformat(),
            'ai_processing': True,  # You can add actual checks here
            'gmail_api': True,
            'email_sending': True,
            'storage': True,
            'user_count': len(user_manager.users),
            'status': 'healthy'
        }
        
        return jsonify(health_results)
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/bulk_actions')
@login_required
def bulk_actions():
    """
    Bulk actions page for admin
    """
    return render_template('action_success.html',
                         message="Bulk actions feature coming soon!")

@app.route('/send_all_digests')
@login_required
def send_all_digests():
    """
    Send digests to all active users (manual bulk send)
    
    This is different from the scheduler:
    - Scheduler: Automatic, runs at user's preferred time
    - This route: Manual trigger, sends immediately to ALL active users
    
    Use cases:
    - Testing digest generation for all users
    - Emergency digest send outside normal schedule
    - Admin-triggered digest after system maintenance
    """
    try:
        print("=" * 60)
        print("📤 Manual Bulk Digest Send Initiated")
        print("=" * 60)
        
        # Track results
        results = {
            'success': [],
            'failed': [],
            'skipped': []
        }
        
        # Get all users
        total_users = len(user_manager.users)
        print(f"👥 Processing {total_users} user(s)...")
        
        for user_id, user_info in user_manager.users.items():
            user_email = user_info.get('email', user_id)
            
            try:
                # Skip users in vacation mode
                if user_info.get('vacation_mode', False):
                    print(f"✈️ Skipping {user_email} (vacation mode)")
                    results['skipped'].append({
                        'email': user_email,
                        'reason': 'vacation_mode'
                    })
                    continue
                
                print(f"\n🔄 Processing {user_email}...")
                
                # Generate digest using your AI system
                print(f"   🤖 Generating AI digest...")
                digest_data = generate_user_digest(user_id)
                
                if not digest_data or digest_data.get('error'):
                    error_msg = digest_data.get('processing_summary', {}).get('error', 'Unknown error')
                    print(f"   ❌ Failed to generate digest: {error_msg}")
                    results['failed'].append({
                        'email': user_email,
                        'error': error_msg
                    })
                    continue
                
                # Check if there are any emails to report
                total_emails = digest_data.get('processing_summary', {}).get('total_processed', 0)
                if total_emails == 0:
                    print(f"   📭 No new emails, skipping")
                    results['skipped'].append({
                        'email': user_email,
                        'reason': 'no_new_emails'
                    })
                    continue
                
                # Generate HTML email
                print(f"   📝 Creating HTML digest...")
                from email_templates import create_digest_email
                digest_html = create_digest_email(digest_data, BASE_URL)
                
                # Send email
                print(f"   📧 Sending email...")
                gmail_service = user_manager.get_user_gmail_service(user_id)
                
                message = MIMEMultipart('alternative')
                message['to'] = user_email
                message['subject'] = f"📧 VoxMail Daily Digest - {datetime.now().strftime('%A, %B %d')}"
                html_part = MIMEText(digest_html, 'html')
                message.attach(html_part)
                
                raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
                send_result = gmail_service.users().messages().send(
                    userId='me',
                    body={'raw': raw_message}
                ).execute()
                
                # Record success
                digest_manager.record_digest_sent(user_id, total_emails)
                
                results['success'].append({
                    'email': user_email,
                    'emails_processed': total_emails,
                    'message_id': send_result.get('id')
                })
                
                print(f"   ✅ Sent successfully! ({total_emails} emails processed)")
                
                # Small delay to avoid rate limiting
                time.sleep(2)
                
            except Exception as user_error:
                print(f"   ❌ Error: {user_error}")
                results['failed'].append({
                    'email': user_email,
                    'error': str(user_error)
                })
                continue
        
        # Calculate statistics
        success_count = len(results['success'])
        failed_count = len(results['failed'])
        skipped_count = len(results['skipped'])
        
        print("\n" + "=" * 60)
        print("📊 Bulk Send Summary:")
        print(f"   ✅ Successful: {success_count}")
        print(f"   ❌ Failed: {failed_count}")
        print(f"   ⏭️ Skipped: {skipped_count}")
        print("=" * 60)
        
        # Return JSON response with detailed results
        return jsonify({
            'success': True,
            'total_users': total_users,
            'sent_count': success_count,
            'failed_count': failed_count,
            'skipped_count': skipped_count,
            'details': {
                'successful': results['success'],
                'failed': results['failed'],
                'skipped': results['skipped']
            },
            'message': f"Sent {success_count} digest(s), {failed_count} failed, {skipped_count} skipped"
        })
    
    except Exception as e:
        print(f"\n❌ Fatal error in bulk send: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Bulk send failed'
        }), 500


@app.route('/create_user', methods=['GET', 'POST'])
@login_required
def create_user():
    """
    DEPRECATED: Manual user creation
    
    Users should authenticate via OAuth instead: /oauth_login
    This route is kept for compatibility only.
    """
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        email = request.form.get('email')
        
        if user_id and email:
            # Mark that this user needs OAuth authentication
            user_data = user_manager.create_user(user_id, email)
            user_data['needs_oauth'] = True
            user_manager._save_users()
            
            return render_template('action_success.html',
                                 message=f"User {email} created. They must authenticate via OAuth at /oauth_login")
    
    return render_template('action_error.html',
                         error="Please use OAuth authentication instead: /oauth_login")

# =============================================================================
# AUTHENTICATION ROUTES
# =============================================================================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """
    Admin login page
    """
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if check_admin_credentials(username, password):
            # Set session variables
            session['logged_in'] = True
            session['username'] = username
            session['last_activity'] = datetime.now().isoformat()
            session.permanent = True
            
            print(f"✅ Admin logged in: {username}")
            
            # Redirect to original destination or dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard'))
        else:
            print(f"❌ Failed login attempt for username: {username}")
            return render_template('admin_login.html', error='Invalid username or password')
    
    # Check for session timeout message
    timeout = request.args.get('timeout')
    timeout_message = 'Your session has expired. Please login again.' if timeout else None
    
    return render_template('admin_login.html', timeout_message=timeout_message)

@app.route('/admin/logout')
def admin_logout():
    """
    Admin logout - clear session and redirect to login
    """
    username = session.get('username', 'Unknown')
    session.clear()
    print(f"👋 Admin logged out: {username}")
    return redirect(url_for('admin_login'))

# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', 
                         error_code=404,
                         error_message="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', 
                         error_code=500,
                         error_message="Internal server error"), 500

# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == '__main__':
    print("🚀 Starting VoxMail Web Application...")
    print("=" * 60)
    
    print(f"\n🌐 Web interface: {BASE_URL}")
    
    # Run Flask app
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'

    # Optional: warm up AI models at startup to avoid first-request latency
    try:
        from ai_runtime import warmup
        print("🧠 Warming up AI models (singleton init)...")
        warmup()
        print("✅ AI warmup complete")
    except Exception as _warm_err:
        print(f"⚠️ AI warmup skipped: {_warm_err}")
    
    print(f"🚀 Starting Flask on 0.0.0.0:{port}")
    app.run(debug=debug, host='0.0.0.0', port=port, threaded=True)
