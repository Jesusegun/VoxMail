# =============================================================================
# EMAIL FETCHER - email_fetcher.py
# =============================================================================
# This module handles fetching and processing emails from Gmail API
# It's the "perception" layer of our AI Email Agent - how it sees/reads emails
#
# WHAT THIS MODULE DOES:
# 1. Connects to Gmail API using authentication from auth_test.py
# 2. Fetches recent emails based on time criteria and filters
# 3. Extracts detailed information from each email (sender, subject, body, etc.)
# 4. Handles different email formats (plain text, HTML, multipart)
# 5. Processes attachments and thread information
# 6. Returns structured data for AI processing
# =============================================================================

import datetime
from datetime import UTC
import base64
import re
from email.mime.text import MIMEText
from typing import List, Dict, Optional, Any

# Import BeautifulSoup for better HTML parsing
try:
    from bs4 import BeautifulSoup
    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    BEAUTIFULSOUP_AVAILABLE = False
    print("⚠️ BeautifulSoup not available - using basic HTML stripping")

class EmailFetcher:
    """
    Gmail Email Fetching and Processing System
    
    This class handles all interactions with Gmail API to retrieve and process
    email data. It acts as the "eyes" of our AI Email Agent, gathering the 
    information the agent needs to make intelligent decisions.
    """
    
    def __init__(self, gmail_service):
        """
        Initialize the EmailFetcher with Gmail service
        
        Args:
            gmail_service: Authenticated Gmail API service object from auth_test.py
        """
        self.service = gmail_service
        
        # Email filtering configuration
        # These control which emails we fetch and process
        self.max_emails_per_fetch = 50  # Limit to prevent overwhelming the system
        self.default_hours_lookback = 24  # How far back to look for emails
        
        # Email content limits (to prevent processing huge emails)
        self.max_body_length = 2000  # Characters limit for email body
        self.max_subject_length = 200  # Characters limit for subject line
        
        print("📧 EmailFetcher initialized successfully")
    
    def get_recent_emails(self, hours: int = None, include_read: bool = False, 
                         sender_filter: str = None) -> List[Dict[str, Any]]:
        """
        Fetch recent emails from Gmail based on specified criteria
        
        This is the main entry point for email retrieval. It builds Gmail API
        queries, fetches email lists, and processes each email for detailed info.
        
        Args:
            hours (int): How many hours back to look (default: 24)
            include_read (bool): Whether to include already read emails (default: False)
            sender_filter (str): Optional sender email to filter by
            
        Returns:
            List[Dict]: List of processed email data dictionaries
        """
        
        # Use default if hours not specified
        if hours is None:
            hours = self.default_hours_lookback
        
        print(f"🔍 Fetching emails from last {hours} hours...")
        print(f"📊 Settings: include_read={include_read}, sender_filter={sender_filter}")
        
        try:
            # =============================================================================
            # STEP 1: BUILD GMAIL SEARCH QUERY
            # =============================================================================
            
            # Calculate timestamp for the lookback period
            # Gmail API uses Unix timestamps for date filtering
            now = datetime.datetime.utcnow()
            past = now - datetime.timedelta(hours=hours)
            timestamp = int(past.timestamp())
            
            # Build Gmail search query string
            # Gmail uses a special query syntax similar to Gmail web interface
            query_parts = []
            
            # Time filter - get emails after the calculated timestamp
            query_parts.append(f'after:{timestamp}')
            
            # Read status filter - by default, only get unread emails
            if not include_read:
                query_parts.append('is:unread')
            
            # Sender filter - if specified, only get emails from specific sender
            if sender_filter:
                query_parts.append(f'from:{sender_filter}')
            
            # Exclude spam, trash, and sent emails automatically
            # Only get emails in inbox (received emails, not sent)
            query_parts.extend(['-in:spam', '-in:trash', '-in:sent', 'in:inbox'])
            
            # Join all query parts with spaces
            search_query = ' '.join(query_parts)
            
            print(f"🔎 Gmail search query: {search_query}")
            
            # =============================================================================
            # STEP 2: EXECUTE GMAIL API SEARCH
            # =============================================================================
            
            # Execute the search query against Gmail API
            search_results = self.service.users().messages().list(
                userId='me',  # 'me' refers to the authenticated user
                q=search_query,
                maxResults=self.max_emails_per_fetch
            ).execute()
            
            # Extract message list from API response
            messages = search_results.get('messages', [])
            
            print(f"📮 Found {len(messages)} emails matching criteria")
            
            if not messages:
                print("📭 No emails found matching the criteria")
                return []
            
            # =============================================================================
            # STEP 3: PROCESS EACH EMAIL FOR DETAILED INFORMATION
            # =============================================================================
            
            processed_emails = []
            successful_fetches = 0
            failed_fetches = 0
            
            print("📄 Processing individual emails...")
            
            for index, message in enumerate(messages, 1):
                print(f"⚙️ Processing email {index}/{len(messages)} (ID: {message['id'][:8]}...)")
                
                try:
                    # Get detailed information for this specific email
                    email_details = self.get_email_details(message['id'])
                    
                    if email_details:
                        processed_emails.append(email_details)
                        successful_fetches += 1
                        print(f"✅ Email {index} processed successfully")
                    else:
                        failed_fetches += 1
                        print(f"❌ Email {index} processing failed")
                        
                except Exception as e:
                    failed_fetches += 1
                    print(f"❌ Error processing email {index}: {e}")
                    continue
            
            # =============================================================================
            # STEP 4: REMOVE DUPLICATES
            # =============================================================================
            
            # Remove duplicate emails based on message-id or subject+sender combination
            unique_emails = []
            seen_identifiers = set()
            
            for email in processed_emails:
                # Create unique identifier using subject + sender + approximate time
                identifier = (
                    email.get('subject', '').strip().lower(),
                    email.get('sender_email', '').strip().lower(),
                    email.get('body', '')[:100].strip().lower()  # First 100 chars of body
                )
                
                if identifier not in seen_identifiers:
                    seen_identifiers.add(identifier)
                    unique_emails.append(email)
                else:
                    print(f"🔄 Duplicate email removed: {email.get('subject', 'No Subject')}")
            
            duplicates_removed = len(processed_emails) - len(unique_emails)
            
            # =============================================================================
            # STEP 5: RETURN PROCESSING SUMMARY
            # =============================================================================
            
            print(f"\n📊 Email fetching completed:")
            print(f"   ✅ Successfully processed: {successful_fetches}")
            print(f"   ❌ Failed to process: {failed_fetches}")
            print(f"   🔄 Duplicates removed: {duplicates_removed}")
            print(f"   📧 Total unique emails ready for AI: {len(unique_emails)}")
            
            return unique_emails
            
        except Exception as e:
            print(f"❌ Error in get_recent_emails: {e}")
            print("🔧 This might be due to:")
            print("   • Gmail API authentication issues")
            print("   • Network connectivity problems")
            print("   • Invalid search query parameters")
            return []
    
    def get_email_details(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Extract comprehensive details from a specific email
        
        This method takes an email ID and retrieves all the information our AI
        agent needs: sender, subject, body, attachments, thread info, etc.
        
        Args:
            message_id (str): Gmail message ID
            
        Returns:
            Dict: Comprehensive email information or None if failed
        """
        
        try:
            # =============================================================================
            # STEP 1: FETCH EMAIL DATA FROM GMAIL API
            # =============================================================================
            
            # Get the full email message data
            # format='full' gives us complete email including headers and body
            message_data = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'  # Get complete email data
            ).execute()
            
            # =============================================================================
            # STEP 2: EXTRACT EMAIL HEADERS
            # =============================================================================
            
            # Email headers contain metadata like sender, subject, date
            headers = message_data['payload'].get('headers', [])
            
            # Extract key header information using list comprehension and next()
            # This is a Python pattern for finding specific items in lists
            subject = next(
                (header['value'] for header in headers if header['name'] == 'Subject'),
                'No Subject'  # Default if no subject found
            )
            
            sender = next(
                (header['value'] for header in headers if header['name'] == 'From'),
                'Unknown Sender'  # Default if no sender found
            )
            
            date_header = next(
                (header['value'] for header in headers if header['name'] == 'Date'),
                ''  # Default if no date found
            )
            
            # Additional useful headers
            reply_to = next(
                (header['value'] for header in headers if header['name'] == 'Reply-To'),
                sender  # Use sender if no reply-to specified
            )
            
            message_id_header = next(
                (header['value'] for header in headers if header['name'] == 'Message-ID'),
                message_id  # Use Gmail ID if no Message-ID
            )
            
            # =============================================================================
            # STEP 3: PROCESS SENDER INFORMATION
            # =============================================================================
            
            # Extract clean sender information
            sender_info = self.parse_sender_info(sender)
            
            # =============================================================================
            # STEP 4: EXTRACT EMAIL BODY CONTENT
            # =============================================================================
            
            # Email body extraction is complex due to different formats (plain text, HTML, multipart)
            email_body = self.extract_email_body(message_data['payload'])
            
            # Clean and limit the body content for AI processing
            cleaned_body = self.clean_email_body(email_body)
            
            # =============================================================================
            # STEP 5: CHECK FOR ATTACHMENTS
            # =============================================================================
            
            attachment_info = self.analyze_attachments(message_data['payload'])
            
            # =============================================================================
            # STEP 6: EXTRACT THREAD INFORMATION
            # =============================================================================
            
            thread_id = message_data.get('threadId', message_id)
            thread_info = self.get_thread_context(thread_id, message_id)
            
            # =============================================================================
            # STEP 7: DETERMINE EMAIL PRIORITY INDICATORS
            # =============================================================================
            
            # Look for priority indicators in headers and content
            priority_indicators = self.extract_priority_indicators(headers, subject, email_body)
            
            # =============================================================================
            # STEP 8: BUILD COMPREHENSIVE EMAIL DATA STRUCTURE
            # =============================================================================
            
            email_data = {
                # Basic identification
                'id': message_id,
                'message_id': message_id_header,
                'thread_id': thread_id,
                
                # Core email content
                'subject': subject[:self.max_subject_length],  # Limit subject length
                'sender': sender,
                'sender_name': sender_info['name'],
                'sender_email': sender_info['email'],
                'reply_to': reply_to,
                'date': date_header,
                'body': cleaned_body,
                'raw_body': email_body[:500],  # Keep snippet of original
                
                # Email analysis
                'body_length': len(cleaned_body),
                'has_attachments': attachment_info['has_attachments'],
                'attachment_count': attachment_info['count'],
                'attachment_types': attachment_info['types'],
                'attachment_names': attachment_info['names'],
                
                # Thread context
                'is_thread': thread_info['is_thread'],
                'thread_length': thread_info['length'],
                'thread_position': thread_info['position'],
                
                # Priority and classification hints
                'priority_indicators': priority_indicators,
                'is_automated': self.detect_automated_email(sender, subject, email_body),
                'language': self.detect_language(cleaned_body),
                
                # Processing metadata
                'processed_at': datetime.datetime.utcnow().isoformat(),
                'fetcher_version': '1.0'
            }
            
            print(f"📧 Email details extracted: From {sender_info['name']}, Subject: '{subject[:50]}...'")
            
            return email_data
            
        except Exception as e:
            print(f"❌ Error extracting email details for {message_id}: {e}")
            return None
    
    def extract_email_body(self, payload: Dict) -> str:
        """
        Extract email body content from Gmail payload
        
        Gmail emails can have different structures:
        - Simple text/plain emails
        - HTML emails  
        - Multipart emails with both text and HTML
        - Nested multipart structures
        
        Args:
            payload (Dict): Gmail message payload
            
        Returns:
            str: Extracted email body text
        """
        
        body_text = ""
        
        try:
            # =============================================================================
            # CASE 1: MULTIPART EMAIL (MOST COMMON)
            # =============================================================================
            
            if 'parts' in payload:
                # Email has multiple parts (text, HTML, attachments)
                for part in payload['parts']:
                    mime_type = part.get('mimeType', '')
                    
                    # Prioritize plain text content for AI processing
                    if mime_type == 'text/plain':
                        part_body = part.get('body', {}).get('data', '')
                        if part_body:
                            # Decode base64 encoded content
                            decoded_body = base64.urlsafe_b64decode(part_body).decode('utf-8')
                            body_text = decoded_body
                            break  # Use first plain text part found
                    
                    # If no plain text, use HTML and strip tags
                    elif mime_type == 'text/html' and not body_text:
                        part_body = part.get('body', {}).get('data', '')
                        if part_body:
                            html_body = base64.urlsafe_b64decode(part_body).decode('utf-8')
                            body_text = self.strip_html_tags(html_body)
                    
                    # Handle nested multipart structures
                    elif mime_type.startswith('multipart/'):
                        nested_body = self.extract_email_body(part)
                        if nested_body and not body_text:
                            body_text = nested_body
            
            # =============================================================================
            # CASE 2: SIMPLE EMAIL (SINGLE PART)
            # =============================================================================
            
            else:
                # Email has single body content
                body_data = payload.get('body', {}).get('data', '')
                if body_data:
                    mime_type = payload.get('mimeType', '')
                    
                    # Decode the body content
                    decoded_body = base64.urlsafe_b64decode(body_data).decode('utf-8')
                    
                    if mime_type == 'text/plain':
                        body_text = decoded_body
                    elif mime_type == 'text/html':
                        body_text = self.strip_html_tags(decoded_body)
                    else:
                        body_text = decoded_body  # Try to use as-is
            
            # =============================================================================
            # FALLBACK: RETURN SOMETHING USEFUL
            # =============================================================================
            
            if not body_text:
                # If we couldn't extract body, provide a helpful placeholder
                body_text = "[Email body could not be extracted - may be encrypted or have unsupported format]"
            
            return body_text
            
        except Exception as e:
            print(f"⚠️ Error extracting email body: {e}")
            return "[Error extracting email body content]"
    
    def clean_email_body(self, raw_body: str) -> str:
        """
        Clean email body for AI processing
        
        Email bodies often contain noise like signatures, previous email chains,
        formatting artifacts, etc. This method cleans the content to extract
        the actual message for AI analysis.
        
        Args:
            raw_body (str): Raw email body text
            
        Returns:
            str: Cleaned email body suitable for AI processing
        """
        
        if not raw_body:
            return ""
        
        # Start with the original body
        cleaned = raw_body
        
        # =============================================================================
        # DECODE HTML ENTITIES AND REMOVE HTML TAGS
        # =============================================================================
        
        # Use BeautifulSoup to properly parse HTML emails
        if BEAUTIFULSOUP_AVAILABLE and ('<html' in cleaned.lower() or '&' in cleaned):
            try:
                soup = BeautifulSoup(cleaned, 'html.parser')
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                # Get text and decode HTML entities
                cleaned = soup.get_text()
            except:
                # Fallback to basic HTML stripping
                import html
                cleaned = html.unescape(cleaned)
                cleaned = re.sub(r'<[^>]+>', '', cleaned)
        else:
            # Basic HTML entity decoding
            import html
            cleaned = html.unescape(cleaned)
            # Remove HTML tags
            cleaned = re.sub(r'<[^>]+>', '', cleaned)
        
        # Remove zero-width spaces and other invisible characters
        cleaned = re.sub(r'[\u200B-\u200D\uFEFF]', '', cleaned)  # Zero-width spaces
        cleaned = re.sub(r'[\u00A0]', ' ', cleaned)  # Non-breaking spaces to regular spaces
        
        # =============================================================================
        # REMOVE QUOTED PREVIOUS EMAILS
        # =============================================================================
        
        # Remove "On [date] [person] wrote:" blocks
        cleaned = re.sub(r'On .* wrote:.*', '', cleaned, flags=re.MULTILINE | re.DOTALL)
        
        # Remove email headers in forwarded messages
        cleaned = re.sub(r'From:.*?Subject:.*?\n', '', cleaned, flags=re.MULTILINE | re.DOTALL)
        
        # Remove lines starting with > (quoted text)
        lines = cleaned.split('\n')
        cleaned_lines = [line for line in lines if not line.strip().startswith('>')]
        cleaned = '\n'.join(cleaned_lines)
        
        # =============================================================================
        # REMOVE EMAIL SIGNATURES
        # =============================================================================
        
        # Remove common signature separators
        signature_separators = ['--', '___', '***', 'Best regards', 'Sincerely', 'Thanks,']
        
        for separator in signature_separators:
            if separator in cleaned:
                # Split at separator and keep only the part before it
                parts = cleaned.split(separator, 1)
                cleaned = parts[0].strip()
                break
        
        # =============================================================================
        # REMOVE FORMATTING ARTIFACTS
        # =============================================================================
        
        # Remove excessive whitespace
        cleaned = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned)  # Multiple empty lines to double
        cleaned = re.sub(r'[ \t]+', ' ', cleaned)  # Multiple spaces/tabs to single space
        
        # Remove common email artifacts
        cleaned = re.sub(r'Sent from my \w+', '', cleaned)  # "Sent from my iPhone" etc.
        cleaned = re.sub(r'Get Outlook for \w+', '', cleaned)  # Outlook mobile signatures
        
        # Remove common marketing email artifacts
        cleaned = re.sub(r'View in browser', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'Unsubscribe.*$', '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
        cleaned = re.sub(r'Click here.*$', '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
        
        # Remove URLs that are just tracking links
        cleaned = re.sub(r'https?://[^\s]+\?utm_[^\s]+', '[link]', cleaned)
        
        # =============================================================================
        # FINAL CLEANUP AND VALIDATION
        # =============================================================================
        
        # Trim whitespace
        cleaned = cleaned.strip()
        
        # Ensure reasonable length for AI processing
        if len(cleaned) > self.max_body_length:
            # Truncate but try to end at sentence boundary
            truncated = cleaned[:self.max_body_length]
            last_sentence = truncated.rfind('.')
            if last_sentence > self.max_body_length * 0.8:  # If sentence ending is reasonable
                cleaned = truncated[:last_sentence + 1]
            else:
                cleaned = truncated + "..."
        
        # If cleaning removed everything, return a snippet of the original
        if not cleaned or len(cleaned) < 10:
            cleaned = raw_body[:200] + "..." if len(raw_body) > 200 else raw_body
        
        return cleaned
    
    def parse_sender_info(self, sender_raw: str) -> Dict[str, str]:
        """
        Parse sender information to extract name and email
        
        Gmail sender field can be in various formats:
        - "John Doe <john@example.com>"
        - "john@example.com"
        - "John Doe" <john@example.com>
        
        Args:
            sender_raw (str): Raw sender field from email
            
        Returns:
            Dict: Parsed sender information with 'name' and 'email' keys
        """
        
        # Regex pattern to match "Name <email@domain.com>" format
        match = re.search(r'^(.*?)\s*<([^>]+)>$', sender_raw.strip())
        
        if match:
            # Format: "Name <email>"
            name = match.group(1).strip().strip('"')  # Remove quotes if present
            email = match.group(2).strip()
        elif '@' in sender_raw:
            # Format: just "email@domain.com"
            name = sender_raw.split('@')[0]  # Use part before @ as name
            email = sender_raw.strip()
        else:
            # Fallback: use as name, no email extracted
            name = sender_raw.strip()
            email = "unknown@email.com"
        
        return {
            'name': name if name else email.split('@')[0],
            'email': email.lower()  # Normalize email to lowercase
        }
    
    def analyze_attachments(self, payload: Dict) -> Dict[str, Any]:
        """
        Analyze email attachments
        
        Args:
            payload (Dict): Gmail message payload
            
        Returns:
            Dict: Attachment analysis results
        """
        
        attachments = {
            'has_attachments': False,
            'count': 0,
            'types': [],
            'names': []
        }
        
        try:
            if 'parts' in payload:
                for part in payload['parts']:
                    filename = part.get('filename', '')
                    if filename:  # Part has a filename, so it's an attachment
                        attachments['has_attachments'] = True
                        attachments['count'] += 1
                        attachments['names'].append(filename)
                        
                        # Extract file extension for type classification
                        if '.' in filename:
                            file_extension = filename.split('.')[-1].lower()
                            if file_extension not in attachments['types']:
                                attachments['types'].append(file_extension)
        
        except Exception as e:
            print(f"⚠️ Error analyzing attachments: {e}")
        
        return attachments
    
    def get_thread_context(self, thread_id: str, current_message_id: str) -> Dict[str, Any]:
        """
        Get context about email thread
        
        Args:
            thread_id (str): Gmail thread ID
            current_message_id (str): Current message ID
            
        Returns:
            Dict: Thread context information
        """
        
        thread_info = {
            'is_thread': False,
            'length': 1,
            'position': 1
        }
        
        try:
            # Get thread information from Gmail API
            thread_data = self.service.users().threads().get(
                userId='me',
                id=thread_id
            ).execute()
            
            messages_in_thread = thread_data.get('messages', [])
            thread_length = len(messages_in_thread)
            
            if thread_length > 1:
                thread_info['is_thread'] = True
                thread_info['length'] = thread_length
                
                # Find position of current message in thread
                for index, msg in enumerate(messages_in_thread):
                    if msg['id'] == current_message_id:
                        thread_info['position'] = index + 1
                        break
        
        except Exception as e:
            print(f"⚠️ Error getting thread context: {e}")
        
        return thread_info
    
    def extract_priority_indicators(self, headers: List[Dict], subject: str, body: str) -> List[str]:
        """
        Extract indicators that suggest email priority
        
        Args:
            headers (List[Dict]): Email headers
            subject (str): Email subject
            body (str): Email body
            
        Returns:
            List[str]: List of priority indicators found
        """
        
        indicators = []
        
        # Check subject for priority keywords
        priority_keywords = ['urgent', 'asap', 'important', 'critical', 'deadline', 'emergency']
        subject_lower = subject.lower()
        
        for keyword in priority_keywords:
            if keyword in subject_lower:
                indicators.append(f'urgent_keyword_subject: {keyword}')
        
        # Check for high importance headers
        for header in headers:
            if header['name'].lower() == 'x-priority' and header['value'] == '1':
                indicators.append('high_priority_header')
            elif header['name'].lower() == 'importance' and header['value'].lower() == 'high':
                indicators.append('high_importance_header')
        
        # Check body for urgency indicators
        body_lower = body.lower()
        for keyword in priority_keywords:
            if keyword in body_lower:
                indicators.append(f'urgent_keyword_body: {keyword}')
                break  # Only add one body indicator to avoid spam
        
        return indicators
    
    def detect_automated_email(self, sender: str, subject: str, body: str) -> bool:
        """
        Detect if email is automated/marketing
        
        Args:
            sender (str): Email sender
            subject (str): Email subject  
            body (str): Email body
            
        Returns:
            bool: True if email appears to be automated
        """
        
        # Automated email indicators
        automated_indicators = [
            'noreply', 'no-reply', 'donotreply', 'notification',
            'newsletter', 'marketing', 'support@', 'info@'
        ]
        
        sender_lower = sender.lower()
        
        # Check sender for automated indicators
        for indicator in automated_indicators:
            if indicator in sender_lower:
                return True
        
        # Check for unsubscribe links (common in marketing emails)
        if 'unsubscribe' in body.lower():
            return True
        
        return False
    
    def detect_language(self, text: str) -> str:
        """
        Simple language detection
        
        Args:
            text (str): Text to analyze
            
        Returns:
            str: Detected language code
        """
        
        # Simple heuristic-based language detection
        # In production, you might use langdetect library
        
        if not text:
            return 'unknown'
        
        # Count English common words
        english_words = ['the', 'and', 'is', 'in', 'to', 'of', 'a', 'that', 'it', 'with']
        text_lower = text.lower()
        
        english_count = sum(1 for word in english_words if word in text_lower)
        
        if english_count >= 3:
            return 'en'
        else:
            return 'unknown'
    
    def strip_html_tags(self, html_content: str) -> str:
        """
        Strip HTML tags from content using BeautifulSoup for robust parsing
        
        Args:
            html_content (str): HTML content
            
        Returns:
            str: Plain text content
        """
        
        if BEAUTIFULSOUP_AVAILABLE:
            try:
                # Use BeautifulSoup for robust HTML parsing
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Remove script and style elements completely
                for script in soup(['script', 'style', 'head', 'meta']):
                    script.decompose()
                
                # Get text and clean up whitespace
                text = soup.get_text(separator=' ', strip=True)
                
                # Clean up multiple spaces and newlines
                text = re.sub(r'\s+', ' ', text)
                text = re.sub(r'\n\s*\n', '\n\n', text)
                
                return text.strip()
                
            except Exception as e:
                print(f"⚠️ BeautifulSoup parsing failed: {e}, falling back to regex")
        
        # Fallback: Simple HTML tag removal using regex
        # Remove style and script blocks first
        clean_text = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        clean_text = re.sub(r'<script[^>]*>.*?</script>', '', clean_text, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', '', clean_text)
        
        # Convert HTML entities
        html_entities = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'",
            '&nbsp;': ' '
        }
        
        for entity, replacement in html_entities.items():
            clean_text = clean_text.replace(entity, replacement)
        
        # Clean up whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text)
        
        return clean_text.strip()

# =============================================================================
# TESTING AND DEMONSTRATION CODE
# =============================================================================

def test_email_fetcher():
    """
    Test function to demonstrate EmailFetcher capabilities
    """
    
    print("=" * 70)
    print("🧪 EMAIL FETCHER TEST")
    print("=" * 70)
    
    # Note: This will only work once you have Gmail API credentials set up
    print("⚠️ This test requires Gmail API authentication")
    print("📋 To run this test:")
    print("   1. Complete Google Cloud Console setup")
    print("   2. Add credentials.json to credentials/ folder")
    print("   3. Run: python auth_test.py first")
    print("   4. Then run: python email_fetcher.py")
    
    try:
        # Import authentication function
        from auth_test import authenticate_gmail
        
        # Authenticate with Gmail
        print("\n🔐 Authenticating with Gmail...")
        gmail_service = authenticate_gmail()
        
        if gmail_service:
            print("✅ Gmail authentication successful!")
            
            # Create EmailFetcher instance
            print("\n📧 Creating EmailFetcher...")
            fetcher = EmailFetcher(gmail_service)
            
            # Test email fetching
            print("\n🔍 Fetching recent emails...")
            recent_emails = fetcher.get_recent_emails(
                hours=48,           # Look back 48 hours
                include_read=True   # Include read emails for testing
            )
            
            # Display results
            print(f"\n📊 RESULTS:")
            print(f"   📧 Emails fetched: {len(recent_emails)}")
            
            if recent_emails:
                print(f"\n📝 SAMPLE EMAIL DATA:")
                sample_email = recent_emails[0]
                
                print(f"   From: {sample_email['sender_name']} ({sample_email['sender_email']})")
                print(f"   Subject: {sample_email['subject']}")
                print(f"   Body length: {sample_email['body_length']} characters")
                print(f"   Attachments: {sample_email['attachment_count']}")
                print(f"   Thread: {'Yes' if sample_email['is_thread'] else 'No'}")
                print(f"   Priority indicators: {sample_email['priority_indicators']}")
                print(f"   Body preview: {sample_email['body'][:100]}...")
            
            print("\n✅ EmailFetcher test completed successfully!")
            
        else:
            print("❌ Gmail authentication failed")
            print("   Please run python auth_test.py first")
    
    except ImportError:
        print("❌ Cannot import auth_test module")
        print("   Please ensure auth_test.py exists and is working")
    except Exception as e:
        print(f"❌ Test failed: {e}")

# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == '__main__':
    """
    Main execution - run tests when file is executed directly
    """
    test_email_fetcher()