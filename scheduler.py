# =============================================================================
# DIGEST SCHEDULER - scheduler.py
# =============================================================================
# VoxMail - Automated scheduling system for sending daily email digests to all users
# 
# This scheduler:
# 1. Runs continuously in the background
# 2. Checks every hour if any users need their digest sent
# 3. Respects each user's preferred digest time and timezone
# 4. Handles weekend preferences and vacation mode
# 5. Logs all activities and errors
# 6. Can be deployed as a separate process (e.g., on Heroku/Railway)
#
# INTEGRATION:
# - Uses UserManager and DigestDataManager from web_app.py
# - Leverages CompleteEmailAgent for AI processing
# - Integrates with email_templates.py for HTML generation
# - Uses authenticate_gmail for Gmail API access
# =============================================================================

import os
import sys
import json
import time
import base64
import schedule
import traceback
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Any, Optional, Tuple
import pytz

# Import your existing system components
try:
    from complete_advanced_ai_processor import CompleteEmailAgent
    from auth_test import authenticate_gmail
    from email_templates import create_digest_email
    print("✅ Successfully imported system components")
except ImportError as e:
    print(f"❌ Error importing components: {e}")
    print("🔧 Make sure all required files are in the correct location")
    sys.exit(1)

# =============================================================================
# CONFIGURATION
# =============================================================================

BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')
USERS_DATA_FILE = 'data/users.json'
DIGEST_DATA_FILE = 'data/digest_data.json'
SCHEDULER_LOG_FILE = 'data/scheduler.log'

# Ensure data directories exist
os.makedirs('data', exist_ok=True)

# =============================================================================
# LOGGING UTILITY
# =============================================================================

def log_message(message: str, level: str = "INFO"):
    """
    Log messages to both console and log file
    
    Args:
        message: Log message
        level: Log level (INFO, WARNING, ERROR, SUCCESS)
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Console output with colors
    emoji_map = {
        "INFO": "ℹ️",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "SUCCESS": "✅"
    }
    emoji = emoji_map.get(level, "📝")
    
    log_line = f"[{timestamp}] [{level}] {message}"
    print(f"{emoji} {log_line}")
    
    # File output
    try:
        with open(SCHEDULER_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_line + "\n")
    except Exception as e:
        print(f"⚠️ Could not write to log file: {e}")

# =============================================================================
# USER MANAGEMENT (Simplified from web_app.py)
# =============================================================================

class SimplifiedUserManager:
    """
    Simplified user manager for scheduler (read-only operations)
    This mirrors the UserManager from web_app.py but focused on scheduling needs
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
            log_message("No users file found - creating empty user list", "WARNING")
            return {}
        except Exception as e:
            log_message(f"Error loading users: {e}", "ERROR")
            return {}
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user data by ID"""
        return self.users.get(user_id)
    
    def get_all_active_users(self) -> List[Tuple[str, Dict[str, Any]]]:
        """Get all users who are not in vacation mode"""
        active_users = []
        for user_id, user_data in self.users.items():
            if not user_data.get('vacation_mode', False):
                active_users.append((user_id, user_data))
        return active_users
    
    def should_send_digest(self, user_data: Dict[str, Any], current_datetime: datetime) -> bool:
        """
        Determine if digest should be sent for this user right now
        
        Checks:
        1. User's preferred digest time (hour)
        2. User's timezone
        3. Weekend preferences
        4. Vacation mode
        """
        
        # Check vacation mode
        if user_data.get('vacation_mode', False):
            return False
        
        # Get user's timezone
        user_timezone = user_data.get('timezone', 'UTC')
        try:
            tz = pytz.timezone(user_timezone)
            user_time = current_datetime.astimezone(tz)
        except Exception as e:
            log_message(f"Invalid timezone {user_timezone}, using UTC: {e}", "WARNING")
            user_time = current_datetime
        
        # Check if it's the user's preferred hour
        preferred_hour = user_data.get('digest_time', 8)
        if user_time.hour != preferred_hour:
            return False
        
        # Check weekend preferences
        is_weekend = user_time.weekday() >= 5  # Saturday=5, Sunday=6
        if is_weekend:
            weekend_pref = user_data.get('weekend_digests', 'urgent_only')
            if weekend_pref == 'off':
                return False
            # If 'urgent_only', we'll still generate digest but filter will be applied later
        
        return True

# =============================================================================
# DIGEST DATA MANAGEMENT (Simplified from web_app.py)
# =============================================================================

class SimplifiedDigestManager:
    """
    Simplified digest data manager for scheduler
    This mirrors the DigestDataManager from web_app.py
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
            log_message(f"Error loading digest data: {e}", "ERROR")
            return {}
    
    def _save_data(self):
        """Save digest data to file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.digest_data, f, indent=2, default=str)
        except Exception as e:
            log_message(f"Error saving digest data: {e}", "ERROR")
    
    def store_email_data(self, user_id: str, email_id: str, email_data: Dict[str, Any]):
        """Store processed email data for button actions"""
        if user_id not in self.digest_data:
            self.digest_data[user_id] = {}
        
        self.digest_data[user_id][email_id] = {
            'email_data': email_data,
            'stored_at': datetime.now().isoformat(),
            'actions_taken': []
        }
        
        self._save_data()
    
    def record_digest_sent(self, user_id: str, email_count: int, success: bool = True):
        """Record when a digest is sent"""
        if user_id not in self.digest_data:
            self.digest_data[user_id] = {}
        
        if 'digest_history' not in self.digest_data[user_id]:
            self.digest_data[user_id]['digest_history'] = []
        
        self.digest_data[user_id]['digest_history'].append({
            'sent_at': datetime.now().isoformat(),
            'email_count': email_count,
            'success': success,
            'sent_by': 'scheduler'
        })
        
        self._save_data()

# =============================================================================
# DIGEST GENERATION CORE
# =============================================================================

class DigestScheduler:
    """
    Main scheduler class that handles automated digest generation and sending
    """
    
    def __init__(self):
        """Initialize the digest scheduler"""
        log_message("=" * 60)
        log_message("🚀 Initializing VoxMail Digest Scheduler")
        log_message("=" * 60)
        
        self.user_manager = SimplifiedUserManager()
        self.digest_manager = SimplifiedDigestManager()
        
        # Track statistics
        self.stats = {
            'total_digests_sent': 0,
            'total_emails_processed': 0,
            'failed_digests': 0,
            'started_at': datetime.now().isoformat()
        }
        
        log_message(f"📊 Loaded {len(self.user_manager.users)} users")
        log_message(f"⏰ Scheduler ready to run")
        log_message("=" * 60)
    
    def generate_user_digest(self, user_id: str, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate daily digest for a specific user using AI system
        
        Args:
            user_id: User identifier
            user_data: User configuration and preferences
        
        Returns:
            Dict with digest data or None if failed
        """
        
        log_message(f"🤖 Generating digest for {user_data.get('email', user_id)}")
        
        try:
            # Initialize AI system
            agent = CompleteEmailAgent(use_gmail_api=True)
            
            # Check weekend preference
            is_weekend = datetime.now().weekday() >= 5
            weekend_pref = user_data.get('weekend_digests', 'urgent_only')
            
            # Process emails
            if is_weekend and weekend_pref == 'urgent_only':
                log_message("📅 Weekend mode: Processing urgent emails only")
                # You could add filtering here, but for now process all and let AI prioritize
            
            results = agent.process_daily_emails(
                hours_back=24,
                max_emails=None  # No limits
            )
            
            # Store email data for button actions
            for priority_group in ['high_priority', 'medium_priority', 'low_priority']:
                for email in results.get(priority_group, []):
                    email_id = email.get('id', str(time.time()))
                    self.digest_manager.store_email_data(user_id, email_id, email)
            
            # Add user-specific metadata
            results['user_id'] = user_id
            results['user_preferences'] = user_data
            results['generated_at'] = datetime.now().isoformat()
            
            summary = results.get('processing_summary', {})
            total = summary.get('total_processed', 0)
            high = summary.get('high_priority_count', 0)
            medium = summary.get('medium_priority_count', 0)
            low = summary.get('low_priority_count', 0)
            
            log_message(f"✅ Digest generated: {total} emails ({high} high, {medium} medium, {low} low)", "SUCCESS")
            
            return results
            
        except Exception as e:
            log_message(f"Error generating digest: {e}", "ERROR")
            log_message(traceback.format_exc(), "ERROR")
            return None
    
    def send_digest_email(self, user_id: str, user_data: Dict[str, Any], digest_data: Dict[str, Any]) -> bool:
        """
        Send digest email to user
        
        Args:
            user_id: User identifier
            user_data: User configuration
            digest_data: Processed digest data from AI
        
        Returns:
            bool: True if successful, False otherwise
        """
        
        user_email = user_data.get('email', 'unknown')
        
        try:
            log_message(f"📧 Sending digest email to {user_email}")
            
            # Generate HTML email
            digest_html = create_digest_email(digest_data, BASE_URL)
            
            # Get Gmail service
            gmail_service = authenticate_gmail()
            if not gmail_service:
                raise Exception("Failed to authenticate with Gmail")
            
            # Create email message
            message = MIMEMultipart('alternative')
            message['to'] = user_email
            message['subject'] = f"📧 VoxMail Daily Digest - {datetime.now().strftime('%A, %B %d')}"
            
            html_part = MIMEText(digest_html, 'html')
            message.attach(html_part)
            
            # Send via Gmail API
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            send_result = gmail_service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            # Record success
            total_emails = digest_data.get('processing_summary', {}).get('total_processed', 0)
            self.digest_manager.record_digest_sent(user_id, total_emails, success=True)
            
            # Update stats
            self.stats['total_digests_sent'] += 1
            self.stats['total_emails_processed'] += total_emails
            
            log_message(f"✅ Digest sent successfully to {user_email} ({total_emails} emails)", "SUCCESS")
            return True
            
        except Exception as e:
            log_message(f"Error sending digest to {user_email}: {e}", "ERROR")
            log_message(traceback.format_exc(), "ERROR")
            
            # Record failure
            self.digest_manager.record_digest_sent(user_id, 0, success=False)
            self.stats['failed_digests'] += 1
            
            # Send error notification to admin
            self._send_error_notification(user_email, str(e))
            
            return False
    
    def _send_error_notification(self, user_email: str, error_message: str):
        """
        Send error notification to admin email
        
        Args:
            user_email: User who failed to receive digest
            error_message: Error details
        """
        try:
            gmail_service = authenticate_gmail()
            if not gmail_service:
                return
            
            # Get admin email from environment or use default
            admin_email = os.environ.get('ADMIN_EMAIL', 'jesusegunadewunmi@gmail.com')
            
            message = MIMEText(
                f"Failed to send digest to {user_email}\n\n"
                f"Error: {error_message}\n\n"
                f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"Please check the scheduler logs for more details."
            )
            message['to'] = admin_email
            message['subject'] = f"🚨 VoxMail Error - {user_email}"
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            gmail_service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            log_message("📧 Error notification sent to admin", "INFO")
            
        except Exception as e:
            log_message(f"Could not send error notification: {e}", "WARNING")
    
    def check_and_send_digests(self):
        """
        Main scheduling function - checks all users and sends digests as needed
        
        This function is called every hour by the scheduler
        """
        current_time = datetime.now()
        log_message("=" * 60)
        log_message(f"⏰ Hourly Check - {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        log_message("=" * 60)
        
        # Get all active users
        active_users = self.user_manager.get_all_active_users()
        log_message(f"👥 Checking {len(active_users)} active users")
        
        if not active_users:
            log_message("No active users found", "WARNING")
            return
        
        # Check each user
        digests_to_send = []
        for user_id, user_data in active_users:
            if self.user_manager.should_send_digest(user_data, current_time):
                user_email = user_data.get('email', user_id)
                log_message(f"📋 User {user_email} scheduled for digest")
                digests_to_send.append((user_id, user_data))
        
        if not digests_to_send:
            log_message(f"No digests scheduled for this hour")
            return
        
        log_message(f"📤 Sending {len(digests_to_send)} digest(s)")
        
        # Process each user
        for user_id, user_data in digests_to_send:
            user_email = user_data.get('email', user_id)
            
            try:
                log_message(f"🔄 Processing digest for {user_email}")
                
                # Generate digest
                digest_data = self.generate_user_digest(user_id, user_data)
                
                if not digest_data:
                    log_message(f"Failed to generate digest for {user_email}", "ERROR")
                    continue
                
                # Check if there are any emails to report
                total_emails = digest_data.get('processing_summary', {}).get('total_processed', 0)
                if total_emails == 0:
                    log_message(f"No new emails for {user_email}, skipping digest")
                    continue
                
                # Send digest
                success = self.send_digest_email(user_id, user_data, digest_data)
                
                if success:
                    log_message(f"✅ Successfully processed {user_email}", "SUCCESS")
                else:
                    log_message(f"Failed to send digest to {user_email}", "ERROR")
                
                # Small delay between users to avoid rate limiting
                time.sleep(2)
                
            except Exception as e:
                log_message(f"Error processing {user_email}: {e}", "ERROR")
                log_message(traceback.format_exc(), "ERROR")
                continue
        
        # Print statistics
        log_message("=" * 60)
        log_message("📊 Scheduler Statistics:")
        log_message(f"   Total digests sent: {self.stats['total_digests_sent']}")
        log_message(f"   Total emails processed: {self.stats['total_emails_processed']}")
        log_message(f"   Failed digests: {self.stats['failed_digests']}")
        log_message(f"   Running since: {self.stats['started_at']}")
        log_message("=" * 60)
    
    def run_scheduler(self):
        """
        Main scheduler loop - runs continuously
        
        This function schedules the hourly check and runs forever
        """
        log_message("=" * 60)
        log_message("🤖 VoxMail Scheduler Starting")
        log_message("=" * 60)
        log_message(f"⏰ Will check every hour for scheduled digests")
        log_message(f"👥 Managing {len(self.user_manager.users)} users")
        log_message(f"📧 Base URL: {BASE_URL}")
        log_message("=" * 60)
        
        # Schedule the hourly check
        schedule.every().hour.at(":00").do(self.check_and_send_digests)
        
        # Also run an immediate check on startup (optional)
        log_message("🚀 Running immediate check on startup...")
        self.check_and_send_digests()
        
        # Main loop
        log_message("♾️ Entering main scheduler loop...")
        log_message("💡 Press Ctrl+C to stop the scheduler")
        log_message("=" * 60)
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute if any scheduled tasks need to run
                
        except KeyboardInterrupt:
            log_message("=" * 60)
            log_message("🛑 Scheduler stopped by user")
            log_message("=" * 60)
            log_message("📊 Final Statistics:")
            log_message(f"   Total digests sent: {self.stats['total_digests_sent']}")
            log_message(f"   Total emails processed: {self.stats['total_emails_processed']}")
            log_message(f"   Failed digests: {self.stats['failed_digests']}")
            log_message("=" * 60)
        
        except Exception as e:
            log_message(f"Fatal error in scheduler loop: {e}", "ERROR")
            log_message(traceback.format_exc(), "ERROR")

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """
    Main entry point for the scheduler
    
    Usage:
        python scheduler.py
    
    For production (Heroku/Railway):
        Add to Procfile:
        scheduler: python scheduler.py
    """
    
    # Initialize and run scheduler
    scheduler = DigestScheduler()
    scheduler.run_scheduler()

if __name__ == '__main__':
    main()
