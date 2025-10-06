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
# INTEGRATION WITH EXISTING AI SYSTEM:
# - Uses CompleteEmailAgent from complete_advanced_ai_processor.py
# - Leverages EmailFetcher from email_fetcher.py  
# - Uses authenticate_gmail from auth_test.py
# - Preserves all advanced AI features and insights
# =============================================================================

import os
import json
import uuid
import base64
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from flask import Flask, render_template, request, redirect, url_for, jsonify, abort
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Lazy import globals - AI components loaded only when needed
CompleteEmailAgent = None
authenticate_gmail = None
EmailFetcher = None

def _lazy_load_ai_components():
    """Load AI components only when actually needed to save memory at startup"""
    global CompleteEmailAgent, authenticate_gmail, EmailFetcher
    if CompleteEmailAgent is None:
        print("📦 Loading AI components...")
        try:
            from complete_advanced_ai_processor import CompleteEmailAgent as _Agent
            from auth_test import authenticate_gmail as _auth
            from email_fetcher import EmailFetcher as _Fetcher
            CompleteEmailAgent = _Agent
            authenticate_gmail = _auth
            EmailFetcher = _Fetcher
            print("✅ AI components loaded successfully")
        except ImportError as e:
            print(f"❌ Error importing AI components: {e}")
            raise

# =============================================================================
# FLASK APP CONFIGURATION
# =============================================================================

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

# Configuration
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')
USERS_DATA_FILE = 'data/users.json'
DIGEST_DATA_FILE = 'data/digest_data.json'

# Ensure data directories exist
os.makedirs('data', exist_ok=True)
os.makedirs('templates', exist_ok=True)

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
    
    def authenticate_and_register_user(self) -> Optional[str]:
        """
        Authenticate user via Google OAuth and register them if new.
        This is how users are actually added - through OAuth authentication.
        
        Returns:
            str: User ID if successful, None if failed
        """
        try:
            # Use your existing OAuth authentication
            gmail_service = authenticate_gmail()
            if not gmail_service:
                return None
                
            # Get user's Gmail profile to extract email
            profile = gmail_service.users().getProfile(userId='me').execute()
            email_address = profile.get('emailAddress')
            
            if not email_address:
                print("❌ Could not get email address from Gmail profile")
                return None
                
            # Create user ID from email (normalized)
            user_id = email_address.replace('@', '_at_').replace('.', '_dot_')
            
            # Check if user already exists
            if user_id in self.users:
                print(f"✅ Existing user authenticated: {email_address}")
                # Update last login time
                self.users[user_id]['last_login'] = datetime.now().isoformat()
                self._save_users()
                return user_id
                
            # Create new user from OAuth authentication
            print(f"🆕 Creating new user from OAuth: {email_address}")
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
                'token_path': f'credentials/user_{user_id}_token.pickle',
                'gmail_messages_total': profile.get('messagesTotal', 0),
                'gmail_threads_total': profile.get('threadsTotal', 0),
                'total_digests_sent': 0
            }
            
            self.users[user_id] = user_data
            self._save_users()
            
            print(f"✅ New user registered successfully: {email_address}")
            return user_id
            
        except Exception as e:
            print(f"❌ Error in OAuth authentication/registration: {e}")
            return None

    def get_user_gmail_service(self, user_id: str):
        """Get authenticated Gmail service for specific user"""
        user = self.get_user(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Each user has their own credentials in Google Cloud Console
        # For now, we'll use the main auth_test.py authentication
        # In production, you'd have per-user credential management with
        # individual OAuth tokens stored per user
        return authenticate_gmail()

# Initialize user manager
user_manager = UserManager()

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
    """
    
    def __init__(self):
        self.data_file = DIGEST_DATA_FILE
        self.digest_data = self._load_data()
    
    def _load_data(self) -> Dict[str, Any]:
        """Load digest data from file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"❌ Error loading digest data: {e}")
            return {}
    
    def _save_data(self):
        """Save digest data to file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.digest_data, f, indent=2, default=str)
        except Exception as e:
            print(f"❌ Error saving digest data: {e}")
    
    def store_email_data(self, user_id: str, email_id: str, email_data: Dict[str, Any]):
        """Store processed email data for button actions"""
        
        if user_id not in self.digest_data:
            self.digest_data[user_id] = {}
        
        # Store the complete email data from your AI system
        self.digest_data[user_id][email_id] = {
            'email_data': email_data,
            'stored_at': datetime.now().isoformat(),
            'actions_taken': []
        }
        
        self._save_data()
    
    def get_email_data(self, user_id: str, email_id: str) -> Optional[Dict[str, Any]]:
        """Get stored email data"""
        return self.digest_data.get(user_id, {}).get(email_id, {}).get('email_data')
    
    def record_action(self, user_id: str, email_id: str, action: str):
        """Record user action for learning"""
        if user_id in self.digest_data and email_id in self.digest_data[user_id]:
            self.digest_data[user_id][email_id]['actions_taken'].append({
                'action': action,
                'timestamp': datetime.now().isoformat()
            })
            self._save_data()
    
    def record_digest_sent(self, user_id: str, email_count: int):
        """Record when a digest is sent"""
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
    
    This integrates with your existing CompleteEmailAgent and preserves
    all the sophisticated AI features you've built.
    """
    
    # Load AI components only when actually generating a digest
    _lazy_load_ai_components()
    
    print(f"🚀 Generating daily digest for user {user_id}")
    
    user = user_manager.get_user(user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")
    
    try:
        # Initialize your AI system - exactly as you designed it
        print("🤖 Initializing CompleteEmailAgent...")
        agent = CompleteEmailAgent(use_gmail_api=True)
        
        # Process daily emails using your advanced AI
        print("📧 Processing emails with advanced AI...")
        
        # Let your sophisticated AI do what it does best - no dumbing down with thresholds!
        results = agent.process_daily_emails(
            hours_back=24,
            max_emails=None  # No limits as you specified
        )
        
        # Store email data for button actions
        print("💾 Storing email data for button actions...")
        for priority_group in ['high_priority', 'medium_priority', 'low_priority']:
            for email in results.get(priority_group, []):
                email_id = email.get('id', str(uuid.uuid4()))
                digest_manager.store_email_data(user_id, email_id, email)
        
        # Add user-specific metadata
        results['user_id'] = user_id
        results['user_preferences'] = user
        results['generated_at'] = datetime.now().isoformat()
        
        print(f"✅ Digest generated successfully!")
        print(f"📊 Summary: {results['processing_summary']['total_processed']} emails processed")
        print(f"   🔥 High: {results['processing_summary']['high_priority_count']}")
        print(f"   ⚡ Medium: {results['processing_summary']['medium_priority_count']}")
        print(f"   💤 Low: {results['processing_summary']['low_priority_count']}")
        
        return results
        
    except Exception as e:
        print(f"❌ Error generating digest for user {user_id}: {e}")
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
    
    Displays full AI analysis, calendar events, thread status, tone analysis, etc.
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
            'calendar_events': email_data.get('calendar_events', {}),
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
            'calendar_events': email_data.get('calendar_events', {}),
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
                             calendar_events=edit_data['calendar_events'],
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
        
        return redirect(url_for('user_settings', user_id=user_id))
        
    except Exception as e:
        print(f"❌ Error updating settings: {e}")
        return render_template('action_error.html', 
                             error=str(e),
                             action='update settings',
                             user_id=user_id), 500

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
    OAuth authentication endpoint - this is how users are actually added!
    
    When someone visits this URL:
    1. They go through Google OAuth flow
    2. If successful, they're automatically registered as a user
    3. They're redirected to their user settings
    """
    try:
        print("🔐 Starting OAuth authentication for new user...")
        
        # Authenticate and register user through OAuth
        user_id = user_manager.authenticate_and_register_user()
        
        if user_id:
            print(f"✅ OAuth authentication successful for user: {user_id}")
            return redirect(url_for('user_settings', user_id=user_id))
        else:
            print("❌ OAuth authentication failed")
            return render_template('action_error.html', 
                                 error="OAuth authentication failed. Please try again.")
    
    except Exception as e:
        print(f"❌ Error during OAuth login: {e}")
        return render_template('action_error.html', 
                             error=f"Authentication error: {str(e)}")

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
def admin_dashboard():
    """
    Redirect to main dashboard (merged into /)
    Kept for backward compatibility with existing links/bookmarks
    """
    return redirect(url_for('dashboard'))

@app.route('/system_check')
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
def bulk_actions():
    """
    Bulk actions page for admin
    """
    return render_template('action_success.html',
                         message="Bulk actions feature coming soon!")

@app.route('/send_all_digests')
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

@app.route('/create_test_user')
def create_test_user():
    """
    Create a test user for development/testing
    """
    try:
        test_user_id = 'test_user'
        test_email = 'jesusegunadewunmi@gmail.com'  # Updated to your real email
        
        # Check if user already exists
        existing_user = user_manager.get_user(test_user_id)
        if existing_user:
            return render_template('action_success.html',
                                 message=f"Test user already exists: {test_email}")
        
        # Create test user
        user_manager.create_user(test_user_id, test_email)
        
        return render_template('action_success.html',
                             message=f"Test user created successfully: {test_email}")
    
    except Exception as e:
        return render_template('action_error.html',
                             error=str(e),
                             action='create test user')

@app.route('/create_user', methods=['GET', 'POST'])
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
    
    # Create a test user if none exist
    if not user_manager.users:
        print("👤 Creating test user...")
        user_manager.create_user(
            'test_user', 
            'jesusegunadewunmi@gmail.com',
            digest_time=8,
            timezone='UTC'
        )
        print("✅ Test user created: test_user")
    
    print(f"\n🌐 Web interface: {BASE_URL}")
    
    # Run Flask app
    port = int(os.environ.get('PORT', 5000))
    debug = False if os.environ.get('PORT') else True
    
    print(f"🚀 Starting Flask on 0.0.0.0:{port}")
    app.run(debug=debug, host='0.0.0.0', port=port, threaded=True)
