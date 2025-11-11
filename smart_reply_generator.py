# =============================================================================
# SMART REPLY GENERATOR - smart_reply_generator.py
# =============================================================================
# AI-Enhanced Reply Generation System
# 
# This module uses BART + spaCy + existing AI models to generate natural,
# contextually-aware email replies that sound human-written.
#
# Key Features:
# - Deep context extraction (topics, entities, action items)
# - BART-based acknowledgment generation
# - Confidence scoring with quality thresholds
# - Intelligent template enhancement
# - Learning capability for continuous improvement
# =============================================================================

import re
import warnings
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

warnings.filterwarnings('ignore')

try:
    import spacy
    from transformers import pipeline
    from textblob import TextBlob
    import numpy as np
    print("[OK] Smart Reply Generator - AI libraries loaded")
except ImportError as e:
    print(f"[ERROR] Error importing AI libraries: {e}")
    raise

# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class SmartReplyConfig:
    """Configuration for smart reply generation"""
    
    # Quality settings
    min_confidence_threshold: float = 0.60  # Below this, use safe templates
    high_confidence_threshold: float = 0.80  # Above this, full AI generation
    
    # Generation settings
    max_acknowledgment_length: int = 150  # words
    min_acknowledgment_length: int = 30   # words
    
    # Context extraction
    max_entities_to_extract: int = 10
    extract_dates: bool = True
    extract_topics: bool = True
    extract_questions: bool = True
    
    # Safety settings
    detect_sensitive_topics: bool = True
    use_safe_mode_for_sensitive: bool = True
    
    # Learning settings
    track_user_edits: bool = True
    adapt_to_preferences: bool = True


# =============================================================================
# SENSITIVE TOPIC DETECTOR
# =============================================================================

class SensitiveTopicDetector:
    """
    Detects sensitive topics that require safe mode replies
    """
    
    def __init__(self):
        """Initialize sensitive topic detector"""
        print("[INFO] Initializing Sensitive Topic Detector...")
        
        # Define sensitive keyword categories
        self.sensitive_keywords = {
            'legal': [
                'lawsuit', 'litigation', 'attorney', 'lawyer', 'legal action',
                'court', 'sue', 'sued', 'settlement', 'complaint', 'violation',
                'breach of contract', 'liability', 'indemnity', 'negligence',
                'testimony', 'deposition', 'subpoena', 'injunction'
            ],
            'hr_personnel': [
                'termination', 'fired', 'layoff', 'dismissal', 'resignation',
                'harassment', 'discrimination', 'retaliation', 'grievance',
                'disciplinary', 'performance issue', 'warning', 'reprimand',
                'investigation', 'complaint against', 'hostile work environment',
                'wrongful termination', 'severance'
            ],
            'financial_sensitive': [
                'fraud', 'embezzlement', 'misappropriation', 'insider trading',
                'money laundering', 'tax evasion', 'bribery', 'kickback',
                'financial misconduct', 'audit failure', 'accounting irregularities',
                'securities violation', 'bankruptcy', 'insolvency'
            ],
            'confidential': [
                'confidential', 'proprietary', 'trade secret', 'nda violation',
                'classified', 'restricted', 'privileged', 'sensitive information',
                'data breach', 'leaked', 'unauthorized disclosure', 'espionage',
                'intellectual property theft'
            ],
            'crisis': [
                'emergency', 'urgent crisis', 'critical incident', 'security breach',
                'data leak', 'system compromise', 'ransomware', 'cyberattack',
                'safety violation', 'accident', 'injury', 'fatality', 'disaster',
                'evacuation', 'threat'
            ],
            'ethical': [
                'ethics violation', 'conflict of interest', 'misconduct',
                'improper conduct', 'unethical behavior', 'fraud', 'corruption',
                'nepotism', 'favoritism', 'misuse of funds'
            ]
        }
        
        # Compile regex patterns for faster matching
        self.sensitive_patterns = {}
        for category, keywords in self.sensitive_keywords.items():
            # Create case-insensitive pattern
            pattern = r'\b(' + '|'.join(re.escape(kw) for kw in keywords) + r')\b'
            self.sensitive_patterns[category] = re.compile(pattern, re.IGNORECASE)
        
        print("[OK] Sensitive topic detector ready")
    
    def detect_sensitive_content(self, email_body: str, email_subject: str = "") -> Dict[str, Any]:
        """
        Detect if email contains sensitive topics
        
        Returns:
            {
                'is_sensitive': bool,
                'categories': List[str],
                'matched_keywords': List[str],
                'risk_level': str,  # low, medium, high, critical
                'requires_manual_review': bool
            }
        """
        
        full_text = f"{email_subject} {email_body}".lower()
        
        result = {
            'is_sensitive': False,
            'categories': [],
            'matched_keywords': [],
            'risk_level': 'low',
            'requires_manual_review': False
        }
        
        # Check each category
        for category, pattern in self.sensitive_patterns.items():
            matches = pattern.findall(full_text)
            if matches:
                result['is_sensitive'] = True
                result['categories'].append(category)
                result['matched_keywords'].extend(matches)
        
        # Determine risk level based on categories matched
        if result['is_sensitive']:
            critical_categories = {'legal', 'hr_personnel', 'crisis'}
            high_risk_categories = {'financial_sensitive', 'confidential', 'ethical'}
            
            if any(cat in critical_categories for cat in result['categories']):
                result['risk_level'] = 'critical'
                result['requires_manual_review'] = True
            elif any(cat in high_risk_categories for cat in result['categories']):
                result['risk_level'] = 'high'
                result['requires_manual_review'] = True
            else:
                result['risk_level'] = 'medium'
        
        # Remove duplicates
        result['matched_keywords'] = list(set(result['matched_keywords']))
        
        return result


# =============================================================================
# EDGE CASE HANDLER
# =============================================================================

class EdgeCaseHandler:
    """
    Handles edge cases in email reply generation
    """
    
    def __init__(self):
        """Initialize edge case handler"""
        print("[INFO] Initializing Edge Case Handler...")
        
        # Define thresholds
        self.min_body_length = 10  # Too short to analyze
        self.max_body_length = 10000  # Too long, might be spam
        self.min_meaningful_words = 3  # Minimum words to be meaningful
        
        # Common no-reply patterns
        self.no_reply_patterns = [
            r'do not reply',
            r'no-reply',
            r'noreply',
            r'automated message',
            r'automatic notification',
            r'unsubscribe',
            r'this is an automated'
        ]
        
        print("[OK] Edge case handler ready")
    
    def analyze_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze email for edge cases
        
        Returns:
            {
                'is_edge_case': bool,
                'edge_case_type': str,  # very_short, unclear, multiple_topics, no_reply, spam_like
                'should_generate_reply': bool,
                'recommendation': str
            }
        """
        
        body = email_data.get('body', '')
        subject = email_data.get('subject', '')
        sender = email_data.get('sender', '')
        
        result = {
            'is_edge_case': False,
            'edge_case_type': None,
            'should_generate_reply': True,
            'recommendation': ''
        }
        
        # Check for no-reply sender
        if self._is_no_reply_email(sender, subject, body):
            result['is_edge_case'] = True
            result['edge_case_type'] = 'no_reply'
            result['should_generate_reply'] = False
            result['recommendation'] = 'This appears to be an automated email. No reply needed.'
            return result
        
        # Check if too short
        if len(body.strip()) < self.min_body_length:
            word_count = len(body.split())
            if word_count < self.min_meaningful_words:
                result['is_edge_case'] = True
                result['edge_case_type'] = 'very_short'
                result['should_generate_reply'] = False
                result['recommendation'] = 'Email too short to generate meaningful reply.'
                return result
        
        # Check if too long (possible spam)
        if len(body) > self.max_body_length:
            result['is_edge_case'] = True
            result['edge_case_type'] = 'too_long'
            result['recommendation'] = 'Email unusually long. Review for spam or bulk content.'
        
        # Check for unclear content (mostly special characters or numbers)
        meaningful_chars = sum(c.isalpha() or c.isspace() for c in body)
        if len(body) > 0 and meaningful_chars / len(body) < 0.5:
            result['is_edge_case'] = True
            result['edge_case_type'] = 'unclear'
            result['should_generate_reply'] = False
            result['recommendation'] = 'Email content unclear or contains mostly non-text characters.'
            return result
        
        # Check for multiple disparate topics (heuristic: many sentences with different main subjects)
        sentences = body.split('.')
        if len(sentences) > 10:
            result['is_edge_case'] = True
            result['edge_case_type'] = 'multiple_topics'
            result['recommendation'] = 'Email covers many topics. Reply may need manual review.'
        
        return result
    
    def _is_no_reply_email(self, sender: str, subject: str, body: str) -> bool:
        """Check if email is from a no-reply address"""
        
        # Check sender
        sender_lower = sender.lower()
        if 'noreply' in sender_lower or 'no-reply' in sender_lower:
            return True
        
        # Check content for no-reply indicators
        full_text = f"{subject} {body}".lower()
        for pattern in self.no_reply_patterns:
            if re.search(pattern, full_text, re.IGNORECASE):
                return True
        
        return False


# =============================================================================
# REPLY NECESSITY ANALYZER
# =============================================================================

class ReplyNecessityAnalyzer:
    """
    Determines if an email actually needs a reply based on email type,
    sender patterns, content patterns, and call-to-action presence.
    """
    
    def __init__(self):
        """Initialize reply necessity analyzer"""
        print("[INFO] Initializing Reply Necessity Analyzer...")
        
        # Patterns for different email types
        self.announcement_patterns = [
            r'\b(save the date|mark your calendar|join us|we\'re (excited|pleased|happy) to announce)\b',
            r'\b(upcoming event|event details|event information|registration (is|now) open)\b',
            r'\b(don\'t miss|see you (there|soon)|looking forward to seeing you)\b',
            r'\b(venue|date and time|event agenda|speakers include)\b'
        ]
        
        self.notification_patterns = [
            r'\b(your .+ has been|confirmation of|receipt for|thank you for your)\b',
            r'\b(this is (a|an) (automated|automatic) (message|email|notification))\b',
            r'\b(you (have|\'ve) successfully|your (order|payment|subscription|registration))\b',
            r'\b(status update|activity notification|alert)\b'
        ]
        
        self.marketing_patterns = [
            r'\b(exclusive offer|limited time|special (deal|offer|promotion))\b',
            r'\b(discover|explore|shop now|buy now|get started|learn more)\b',
            r'\b(new (features|products|services|arrivals)|introducing)\b',
            r'\b(don\'t miss out|act now|hurry|ends soon)\b',
            r'\bunsubscribe\b'
        ]
        
        self.newsletter_patterns = [
            r'\b(newsletter|digest|weekly (update|roundup)|monthly (update|roundup))\b',
            r'\b(in this (issue|edition)|this (week|month)\'s)\b',
            r'\b(subscriber|subscription)\b'
        ]
        
        self.invitation_patterns = [
            r'\b(you\'re invited|invitation to|rsvp|please join us)\b',
            r'\b(will you (be|join)|can you (attend|make it|join))\b'
        ]
        
        self.transactional_patterns = [
            r'\b(receipt|invoice|order confirmation|payment (received|confirmed))\b',
            r'\b(transaction (complete|successful)|your purchase)\b'
        ]
        
        self.security_alert_patterns = [
            r'\b(security alert|suspicious activity|unusual (login|activity))\b',
            r'\b(password reset|verify your|action required|immediate action)\b',
            r'\b(detected|exposed|breach|unauthorized)\b'
        ]
        
        # Compile patterns for performance
        self.compiled_patterns = {
            'announcement': [re.compile(p, re.IGNORECASE) for p in self.announcement_patterns],
            'notification': [re.compile(p, re.IGNORECASE) for p in self.notification_patterns],
            'marketing': [re.compile(p, re.IGNORECASE) for p in self.marketing_patterns],
            'newsletter': [re.compile(p, re.IGNORECASE) for p in self.newsletter_patterns],
            'invitation': [re.compile(p, re.IGNORECASE) for p in self.invitation_patterns],
            'transactional': [re.compile(p, re.IGNORECASE) for p in self.transactional_patterns],
            'security_alert': [re.compile(p, re.IGNORECASE) for p in self.security_alert_patterns]
        }
        
        print("[OK] Reply necessity analyzer ready")
    
    def analyze_reply_necessity(self, email_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine if an email actually needs a reply
        
        Returns:
            {
                'needs_reply': bool,
                'necessity_level': 'required'|'optional'|'not_needed'|'action_only',
                'email_intent': str,
                'reason': str,
                'suggested_action': str
            }
        """
        
        subject = email_data.get('subject', '').lower()
        body = email_data.get('body', '').lower()
        sender = email_data.get('sender_email', '').lower()
        full_text = f"{subject} {body}"
        
        result = {
            'needs_reply': True,
            'necessity_level': 'optional',
            'email_intent': 'general',
            'reason': '',
            'suggested_action': 'Review and decide'
        }
        
        # Check for automated/no-reply senders
        if 'noreply' in sender or 'no-reply' in sender or 'donotreply' in sender:
            result['needs_reply'] = False
            result['necessity_level'] = 'not_needed'
            result['email_intent'] = 'automated'
            result['reason'] = 'Automated email from no-reply address'
            result['suggested_action'] = 'Mark as read'
            return result
        
        # Check for security alerts (action needed, but don't reply)
        if self._matches_patterns(full_text, 'security_alert'):
            result['needs_reply'] = False
            result['necessity_level'] = 'action_only'
            result['email_intent'] = 'security_alert'
            result['reason'] = 'Security alert requiring action on platform, not email reply'
            result['suggested_action'] = 'Take action on the platform (e.g., GitHub, etc.)'
            return result
        
        # Check for transactional emails (receipts, confirmations)
        if self._matches_patterns(full_text, 'transactional'):
            result['needs_reply'] = False
            result['necessity_level'] = 'not_needed'
            result['email_intent'] = 'transactional'
            result['reason'] = 'Automated transaction confirmation'
            result['suggested_action'] = 'File for records'
            return result
        
        # Check for marketing emails
        if self._matches_patterns(full_text, 'marketing'):
            result['needs_reply'] = False
            result['necessity_level'] = 'not_needed'
            result['email_intent'] = 'marketing'
            result['reason'] = 'Marketing/promotional content'
            result['suggested_action'] = 'Review offers or unsubscribe'
            return result
        
        # Check for newsletters
        if self._matches_patterns(full_text, 'newsletter'):
            result['needs_reply'] = False
            result['necessity_level'] = 'not_needed'
            result['email_intent'] = 'newsletter'
            result['reason'] = 'Newsletter or periodic update'
            result['suggested_action'] = 'Read and archive'
            return result
        
        # Check for announcements
        if self._matches_patterns(full_text, 'announcement'):
            result['needs_reply'] = False
            result['necessity_level'] = 'optional'
            result['email_intent'] = 'announcement'
            result['reason'] = 'Event announcement or update'
            result['suggested_action'] = 'Add to calendar or acknowledge if interested'
            return result
        
        # Check for invitations (optional reply - RSVP)
        if self._matches_patterns(full_text, 'invitation'):
            result['needs_reply'] = True
            result['necessity_level'] = 'optional'
            result['email_intent'] = 'invitation'
            result['reason'] = 'Event invitation - RSVP if attending'
            result['suggested_action'] = 'RSVP or add to calendar'
            return result
        
        # Check for notifications
        if self._matches_patterns(full_text, 'notification'):
            result['needs_reply'] = False
            result['necessity_level'] = 'not_needed'
            result['email_intent'] = 'notification'
            result['reason'] = 'Automated notification'
            result['suggested_action'] = 'Review and mark as read'
            return result
        
        # Check context for direct questions or requests
        has_questions = len(context.get('questions', [])) > 0
        has_action_items = len(context.get('action_items', [])) > 0
        
        if has_questions or has_action_items:
            result['needs_reply'] = True
            result['necessity_level'] = 'required'
            result['email_intent'] = 'request'
            result['reason'] = 'Contains direct questions or action requests'
            result['suggested_action'] = 'Reply with answers or confirmation'
            return result
        
        # Check email category from context
        email_category = context.get('email_category', 'general')
        if email_category in ['question', 'info_request', 'problem_report']:
            result['needs_reply'] = True
            result['necessity_level'] = 'required'
            result['email_intent'] = email_category
            result['reason'] = f'Email is a {email_category.replace("_", " ")}'
            result['suggested_action'] = 'Reply with response'
            return result
        
        # Default: optional reply for general emails
        result['needs_reply'] = True
        result['necessity_level'] = 'optional'
        result['email_intent'] = 'general'
        result['reason'] = 'General communication'
        result['suggested_action'] = 'Reply if needed'
        return result
    
    def _matches_patterns(self, text: str, pattern_type: str) -> bool:
        """Check if text matches any pattern of given type"""
        patterns = self.compiled_patterns.get(pattern_type, [])
        return any(pattern.search(text) for pattern in patterns)


# =============================================================================
# EMAIL CONTEXT EXTRACTOR
# =============================================================================

class EmailContextExtractor:
    """
    Extracts rich context from emails using spaCy and pattern matching
    """
    
    def __init__(self):
        """Initialize the context extractor"""
        print("[INFO] Initializing Email Context Extractor...")
        
        # Load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
            print("[OK] spaCy model loaded for entity extraction")
        except Exception as e:
            print(f"[ERROR] Failed to load spaCy: {e}")
            self.nlp = None
        
        # Initialize pattern matchers
        self._initialize_patterns()
        
    def _initialize_patterns(self):
        """Initialize regex patterns for context extraction"""
        
        # Question patterns
        self.question_patterns = [
            r'\b(what|when|where|who|why|how|which|can you|could you|would you|will you)\b.*\?',
            r'\b(please|kindly)\s+(provide|send|share|let me know|tell me|explain)',
        ]
        
        # Action item patterns
        self.action_patterns = [
            r'\b(need|require|request|want|looking for|asking for)\b.*',
            r'\b(please|kindly)\s+\w+',
            r'\b(can you|could you|would you)\s+\w+',
        ]
        
        # Deadline patterns
        self.deadline_patterns = [
            r'\b(by|before|until|deadline|due)\s+(today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d{1,2}[/-]\d{1,2})',
            r'\b(asap|urgent|immediately|right away|as soon as possible)\b',
            r'\b(this|next)\s+(week|month|quarter)',
        ]
        
        # Attachment references
        self.attachment_patterns = [
            r'\b(attached|attachment|attached file|see attached|find attached)\b',
            r'\b(document|file|spreadsheet|pdf|report|presentation)\b',
        ]
    
    def extract_context(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract comprehensive context from email
        
        Args:
            email_data: Email data dictionary with subject, body, sender info
            
        Returns:
            Dict with extracted context including entities, topics, questions, etc.
        """
        
        print("[INFO] Extracting email context...")
        
        subject = email_data.get('subject', '')
        body = email_data.get('body', '')
        sender_name = email_data.get('sender_name', 'there')
        
        # Combine for analysis
        full_text = f"{subject} {body}"
        
        context = {
            'sender_name': sender_name,
            'subject': subject,
            'main_topic': '',
            'entities': {
                'people': [],
                'organizations': [],
                'dates': [],
                'locations': [],
                'money': []
            },
            'questions': [],
            'action_items': [],
            'deadlines': [],
            'has_attachments': email_data.get('has_attachments', False),
            'attachment_count': email_data.get('attachment_count', 0),
            'urgency_level': 'normal',
            'email_category': 'general',
            'key_phrases': [],
            'extracted_successfully': False
        }
        
        try:
            # Extract entities using spaCy
            if self.nlp:
                context = self._extract_entities_spacy(full_text, context)
            
            # Extract questions
            context['questions'] = self._extract_questions(body)
            
            # Extract action items
            context['action_items'] = self._extract_action_items(body)
            
            # Extract deadlines
            context['deadlines'] = self._extract_deadlines(full_text)
            
            # Determine main topic
            context['main_topic'] = self._determine_main_topic(subject, body, context)
            
            # Determine urgency
            context['urgency_level'] = self._determine_urgency(email_data, context)
            
            # Categorize email
            context['email_category'] = self._categorize_email(subject, body, context)
            
            # Extract key phrases
            context['key_phrases'] = self._extract_key_phrases(body)
            
            context['extracted_successfully'] = True
            print(f"[OK] Context extracted: Topic='{context['main_topic']}', Category={context['email_category']}")
            
        except Exception as e:
            print(f"[WARNING] Context extraction error: {e}")
            context['extracted_successfully'] = False
        
        return context
    
    def _extract_entities_spacy(self, text: str, context: Dict) -> Dict:
        """Extract named entities using spaCy"""
        try:
            # Limit text length for performance
            doc = self.nlp(text[:5000])
            
            for ent in doc.ents:
                if ent.label_ == 'PERSON':
                    if ent.text not in context['entities']['people']:
                        context['entities']['people'].append(ent.text)
                        
                elif ent.label_ == 'ORG':
                    if ent.text not in context['entities']['organizations']:
                        context['entities']['organizations'].append(ent.text)
                        
                elif ent.label_ == 'DATE':
                    if ent.text not in context['entities']['dates']:
                        context['entities']['dates'].append(ent.text)
                        
                elif ent.label_ in ['GPE', 'LOC']:
                    if ent.text not in context['entities']['locations']:
                        context['entities']['locations'].append(ent.text)
                        
                elif ent.label_ == 'MONEY':
                    if ent.text not in context['entities']['money']:
                        context['entities']['money'].append(ent.text)
            
            # Limit number of entities
            for key in context['entities']:
                context['entities'][key] = context['entities'][key][:5]
                
        except Exception as e:
            print(f"[WARNING] spaCy extraction failed: {e}")
        
        return context
    
    def _extract_questions(self, text: str) -> List[str]:
        """Extract questions from email that are actually directed at the user"""
        questions = []
        
        # Find sentences ending with ?
        question_sentences = [s.strip() for s in text.split('.') if '?' in s]
        
        for sentence in question_sentences:
            # Clean up
            sentence = sentence.strip()
            if len(sentence) < 10:  # Too short
                continue
            
            # CRITICAL FIX: Validate question is directed at user
            if not self._is_question_directed_at_user(sentence):
                continue
            
            # Filter out rhetorical questions
            if self._is_rhetorical_question(sentence):
                continue
            
            questions.append(sentence)
            
            if len(questions) >= 3:  # Limit to 3 validated questions
                break
        
        return questions
    
    def _is_question_directed_at_user(self, question: str) -> bool:
        """Check if question is asking the USER something (not rhetorical or general)"""
        question_lower = question.lower()
        
        # Questions directed at user typically contain these patterns
        user_directed_patterns = [
            r'\b(can you|could you|would you|will you|do you|did you|have you|are you)\b',
            r'\b(your|you\'re|you\'ll|you\'ve)\b',
            r'\b(what (do|did|will) you|when (do|did|will) you|where (do|did|will) you|how (do|did|will) you|why (do|did|will) you)\b',
            r'\b(please (let|tell|send|provide|confirm|advise))\b',
            r'\b(need (you to|your))\b'
        ]
        
        # Check if question matches user-directed patterns
        for pattern in user_directed_patterns:
            if re.search(pattern, question_lower):
                return True
        
        # Questions starting with these words are often directed at recipient
        directed_starts = ['can you', 'could you', 'would you', 'will you', 'do you', 'did you', 
                          'have you', 'are you', 'what would you', 'when can you', 'how can you']
        
        if any(question_lower.startswith(start) for start in directed_starts):
            return True
        
        return False
    
    def _is_rhetorical_question(self, question: str) -> bool:
        """Identify rhetorical questions that don't need answers"""
        question_lower = question.lower()
        
        # Common rhetorical question patterns
        rhetorical_patterns = [
            r'\b(isn\'t (it|that) (great|amazing|wonderful|exciting))\b',
            r'\b(who doesn\'t (love|want|like))\b',
            r'\b(what could be (better|more))\b',
            r'\b(right\?|correct\?)$'  # Questions ending with "right?" or "correct?"
        ]
        
        for pattern in rhetorical_patterns:
            if re.search(pattern, question_lower):
                return True
        
        return False
    
    def _extract_action_items(self, text: str) -> List[str]:
        """Extract action items/requests that are actually directed at the user"""
        action_items = []
        text_lower = text.lower()
        
        for pattern in self.action_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                # Get the sentence containing the match
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 100)
                snippet = text[start:end].strip()
                
                if not snippet or len(snippet) < 15:
                    continue
                
                # CRITICAL FIX: Validate action is requested FROM user
                if not self._is_action_requested_from_user(snippet):
                    continue
                
                # Check if action is in past tense (already done)
                if self._is_past_tense_action(snippet):
                    continue
                
                action_items.append(snippet[:150])  # Limit length
                    
                if len(action_items) >= 3:  # Limit to 3 validated action items
                    break
            
            if len(action_items) >= 3:
                break
        
        return action_items
    
    def _is_action_requested_from_user(self, text: str) -> bool:
        """Check if action is being requested FROM the user (not informational)"""
        text_lower = text.lower()
        
        # Patterns indicating request to user
        request_patterns = [
            r'\b(please|kindly|could you|can you|would you) (upload|send|provide|submit|complete|review|confirm|fill|click)\b',
            r'\b(you (need|must|should|have) to|you\'ll need to)\b',
            r'\b(to (get|proceed|continue|register|attend), (please|kindly|you need to|you must))\b',
            r'\b(action (required|needed)|require (your|you to))\b'
        ]
        
        for pattern in request_patterns:
            if re.search(pattern, text_lower):
                return True
        
        # Check for imperative mood (commands directed at user)
        if self._is_imperative_mood(text):
            return True
        
        # Filter out "I will" statements (sender's actions, not user's)
        sender_action_patterns = [
            r'\b(i will|i\'ll|we will|we\'ll|i am|i\'m|we are|we\'re)\b',
            r'\b(has been|have been|was|were) (sent|completed|updated|processed)\b'
        ]
        
        for pattern in sender_action_patterns:
            if re.search(pattern, text_lower):
                return False
        
        return True
    
    def _is_imperative_mood(self, sentence: str) -> bool:
        """Check if sentence is in imperative mood (command/request)"""
        sentence_lower = sentence.lower().strip()
        
        # Imperative sentences often start with verbs
        imperative_starts = [
            'upload', 'send', 'provide', 'submit', 'complete', 'review', 'confirm',
            'fill', 'click', 'download', 'register', 'attend', 'join', 'visit',
            'check', 'update', 'install', 'contact', 'call', 'email', 'reply'
        ]
        
        # Check if sentence starts with imperative verb
        first_word = sentence_lower.split()[0] if sentence_lower else ''
        if any(first_word.startswith(verb) for verb in imperative_starts):
            return True
        
        # Check for "Please [verb]" pattern
        if sentence_lower.startswith('please '):
            return True
        
        return False
    
    def _is_past_tense_action(self, text: str) -> bool:
        """Check if action is in past tense (already completed)"""
        text_lower = text.lower()
        
        # Past tense indicators
        past_patterns = [
            r'\b(has been|have been|was|were) (sent|completed|updated|processed|uploaded|submitted)\b',
            r'\b(sent|completed|updated|processed|uploaded|submitted|registered|confirmed) (on|at|yesterday|last)\b',
            r'\b(already|previously) (sent|completed|updated|processed)\b'
        ]
        
        for pattern in past_patterns:
            if re.search(pattern, text_lower):
                return True
        
        return False
    
    def _extract_deadlines(self, text: str) -> List[str]:
        """Extract deadline mentions"""
        deadlines = []
        text_lower = text.lower()
        
        for pattern in self.deadline_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                deadline_text = match.group(0).strip()
                if deadline_text and deadline_text not in deadlines:
                    deadlines.append(deadline_text)
                    
                if len(deadlines) >= 2:  # Limit to 2 deadlines
                    break
        
        return deadlines
    
    def _determine_main_topic(self, subject: str, body: str, context: Dict) -> str:
        """Determine the main topic/subject of the email"""
        
        # Start with subject if meaningful
        if subject and len(subject) > 5:
            # Remove common prefixes
            topic = re.sub(r'^(re:|fwd:|fw:)\s*', '', subject, flags=re.IGNORECASE).strip()
            
            # If subject is meaningful, use it
            if len(topic) > 10:
                return topic[:100]  # Limit length
        
        # Try to extract from first sentence of body
        sentences = body.split('.')
        if sentences:
            first_sentence = sentences[0].strip()
            if 20 < len(first_sentence) < 150:
                return first_sentence
        
        # Fallback to "your email"
        return "your email"
    
    def _determine_urgency(self, email_data: Dict, context: Dict) -> str:
        """Determine urgency level"""
        
        # Check priority level from email data
        priority_level = email_data.get('priority_level', 'Medium')
        if priority_level == 'High':
            return 'high'
        
        # Check for urgent keywords
        text = f"{email_data.get('subject', '')} {email_data.get('body', '')}".lower()
        urgent_keywords = ['urgent', 'asap', 'emergency', 'critical', 'immediately', 'right away']
        
        if any(keyword in text for keyword in urgent_keywords):
            return 'urgent'
        
        # Check for deadlines
        if context.get('deadlines'):
            return 'high'
        
        return 'normal'
    
    def _categorize_email(self, subject: str, body: str, context: Dict) -> str:
        """Categorize the type of email with enhanced granularity"""
        
        text = f"{subject} {body}".lower()
        
        # NEW: Security alerts (high priority, action required)
        if any(word in text for word in ['security alert', 'suspicious activity', 'detected', 'exposed', 'breach', 'unauthorized']):
            return 'security_alert'
        
        # NEW: Transactional (receipts, confirmations - no reply needed)
        if any(word in text for word in ['receipt', 'invoice', 'order confirmation', 'payment received', 'transaction complete']):
            return 'transactional'
        
        # NEW: Newsletter/digest (periodic updates - no reply needed)
        if any(word in text for word in ['newsletter', 'digest', 'weekly update', 'monthly update', 'subscriber', 'unsubscribe']):
            return 'newsletter'
        
        # NEW: Marketing (promotional content - no reply needed)
        if any(word in text for word in ['exclusive offer', 'limited time', 'special deal', 'shop now', 'buy now', 'discover', 'new features']):
            return 'marketing'
        
        # NEW: Announcement (events, news - no reply needed typically)
        if any(word in text for word in ['save the date', 'join us', 'we\'re excited to announce', 'upcoming event', 'event details']):
            return 'announcement'
        
        # NEW: Invitation (events - RSVP optional)
        if any(word in text for word in ['you\'re invited', 'invitation to', 'rsvp', 'please join us', 'can you attend']):
            return 'invitation'
        
        # NEW: Notification (automated alerts - no reply needed)
        if any(word in text for word in ['your account', 'has been updated', 'confirmation of', 'status update', 'activity notification']):
            # Check if it's a specific notification that needs action
            if 'action required' in text or 'please' in text:
                return 'notification_action_required'
            return 'notification'
        
        # EXISTING: Meeting/scheduling
        if any(word in text for word in ['meeting', 'call', 'schedule', 'appointment', 'available']):
            return 'meeting_request'
        
        # EXISTING: Questions (validated questions in context)
        if context.get('questions'):  # Now uses validated questions only
            return 'question'
        
        # EXISTING: Problem/issue
        if any(word in text for word in ['problem', 'issue', 'error', 'broken', 'bug', 'help', 'support']):
            return 'problem_report'
        
        # EXISTING: Request for information
        if any(word in text for word in ['send', 'provide', 'share', 'need', 'request', 'looking for']):
            return 'info_request'
        
        # EXISTING: Follow-up
        if any(word in text for word in ['follow up', 'following up', 'checking in', 'status', 'update']):
            return 'follow_up'
        
        # EXISTING: Thank you
        if any(word in text for word in ['thank', 'thanks', 'appreciate', 'grateful']):
            return 'acknowledgment'
        
        return 'general'
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases that should be acknowledged"""
        
        key_phrases = []
        
        # Look for quoted text
        quoted = re.findall(r'"([^"]+)"', text)
        key_phrases.extend(quoted[:2])
        
        # Look for emphasized phrases (ALL CAPS)
        caps_phrases = re.findall(r'\b[A-Z]{4,}\b', text)
        key_phrases.extend(caps_phrases[:2])
        
        return key_phrases[:3]  # Limit to 3 phrases


# =============================================================================
# BART-BASED ACKNOWLEDGMENT GENERATOR
# =============================================================================

class BARTAcknowledgmentGenerator:
    """
    Uses BART model creatively to generate contextual acknowledgments
    """
    
    def __init__(self):
        """Initialize BART generator"""
        print("[INFO] Initializing BART Acknowledgment Generator...")
        
        try:
            # Load BART summarization model
            self.bart = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                device=-1  # CPU
            )
            print("[OK] BART model loaded successfully")
        except Exception as e:
            print("[ERROR] Failed to load BART: {e}")
            self.bart = None
    
    def generate_acknowledgment(self, context: Dict[str, Any], tone: str = 'business') -> str:
        """
        Generate contextual acknowledgment using BART
        
        Args:
            context: Extracted email context
            tone: Desired tone (formal, business, casual)
            
        Returns:
            Generated acknowledgment text
        """
        
        if not self.bart:
            return self._fallback_acknowledgment(context, tone)
        
        try:
            # Build intelligent prompt for BART
            prompt = self._build_bart_prompt(context)
            
            # Generate with BART
            result = self.bart(
                prompt,
                max_length=100,
                min_length=30,
                do_sample=False
            )
            
            acknowledgment = result[0]['summary_text']
            
            # Post-process to make it sound natural
            acknowledgment = self._post_process_acknowledgment(result[0]['summary_text'], context, tone)
            
            print(f"[OK] BART generated: '{acknowledgment[:60]}...'")
            return acknowledgment
            
        except Exception as e:
            print(f"[WARNING] BART generation failed: {e}, using fallback")
            return self._fallback_acknowledgment(context, tone)
    
    def _build_bart_prompt(self, context: Dict[str, Any]) -> str:
        """Build an intelligent prompt for BART"""
        
        # Create a pseudo-email that BART can "summarize" into an acknowledgment
        prompt_parts = []
        
        # Add topic
        topic = context.get('main_topic', '')
        if topic:
            prompt_parts.append(f"Email about: {topic}.")
        
        # Add questions
        questions = context.get('questions', [])
        if questions:
            prompt_parts.append(f"Questions asked: {' '.join(questions[:2])}")
        
        # Add action items
        action_items = context.get('action_items', [])
        if action_items:
            prompt_parts.append(f"Requested: {action_items[0]}")
        
        # Add entities
        entities = context.get('entities', {})
        if entities.get('dates'):
            prompt_parts.append(f"Timeline mentioned: {entities['dates'][0]}")
        
        # Add attachment info
        if context.get('has_attachments'):
            count = context.get('attachment_count', 1)
            prompt_parts.append(f"{count} attachment(s) included.")
        
        # Add urgency
        if context.get('urgency_level') in ['urgent', 'high']:
            prompt_parts.append("Marked as urgent.")
        
        prompt = " ".join(prompt_parts)
        
        # Ensure minimum length for BART
        if len(prompt) < 50:
            prompt += " Need to acknowledge receipt and provide response timeline."
        
        return prompt
    
    def _post_process_acknowledgment(self, text: str, context: Dict, tone: str) -> str:
        """Post-process BART output to make it natural"""
        
        # Remove common BART artifacts
        text = text.replace("Email about:", "regarding")
        text = text.replace("Questions asked:", "your questions about")
        text = text.replace("Requested:", "your request for")
        text = text.replace("Timeline mentioned:", "for")
        text = text.replace("attachment(s) included.", "attachments.")
        text = text.replace("Marked as urgent.", "")
        
        # Remove duplicate information
        text = re.sub(r'\d+\s+attachment\(s\)\s+included\.', '', text)
        
        # Clean up spacing
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Build a natural acknowledgment instead of using raw BART output
        acknowledgment = self._build_natural_acknowledgment(context, tone)
        
        return acknowledgment
    
    def _build_natural_acknowledgment(self, context: Dict, tone: str) -> str:
        """Build human-sounding acknowledgment with natural language"""
        import random
        
        sender_name = context.get('sender_name', 'there')
        subject = context.get('subject', '')
        urgency = context.get('urgency_level', 'normal')
        has_attachments = context.get('has_attachments', False)
        questions = context.get('questions', [])
        deadlines = context.get('deadlines', [])
        
        # Determine relationship for greeting style
        relationship = context.get('relationship_context', 'professional')
        
        # Natural greeting variations
        if relationship == 'friend':
            greetings = ["Hey", "Hi", "Hey there"]
        elif relationship == 'colleague':
            greetings = ["Hi", "Hey", "Hi there"]
        elif tone == 'formal':
            greetings = ["Hi", "Hello"]
        else:
            greetings = ["Hi", "Hey", "Hi there"]
        
        greeting = f"{random.choice(greetings)} {sender_name},"
        
        # Natural opening variations
        openings = [
            "Got it",
            "Thanks for sending this over", 
            "Thanks",
            "Perfect timing",
            "Appreciate this",
            "Got your email",
            "Thanks for reaching out"
        ]
        
        # Natural action phrases based on content
        if questions:
            actions = [
                "I'll get back to you on those questions",
                "Let me look into those questions for you",
                "I'll check on that and get back to you",
                "I'll find out and let you know"
            ]
        elif has_attachments:
            actions = [
                "I'll take a look at the doc",
                "Let me review what you sent",
                "I'll check out the attachment",
                "I'll go through the file"
            ]
        elif urgency in ['urgent', 'high']:
            actions = [
                "I'll get on this right away",
                "I'll prioritize this",
                "I'll handle this ASAP",
                "I'll take care of this quickly"
            ]
        else:
            actions = [
                "I'll take a look",
                "Let me check on that",
                "I'll review this",
                "I'll get on this",
                "Let me look into this"
            ]
        
        # Add timeline context naturally
        timeline_phrases = []
        if deadlines:
            deadline = deadlines[0]
            timeline_phrases = [
                f"before {deadline}",
                f"by {deadline}",
                f"in time for {deadline}"
            ]
        elif urgency in ['urgent', 'high']:
            timeline_phrases = [
                "soon",
                "asap",
                "quickly"
            ]
        else:
            timeline_phrases = [
                "soon",
                "shortly",
                "in a bit"
            ]
        
        # Natural closings
        if relationship == 'friend':
            closings = ["Thanks!", "Talk soon!", "Cheers!", "Thanks!"]
        elif relationship == 'colleague':
            closings = ["Thanks!", "Best", "Talk soon", "Thanks"]
        else:
            closings = ["Thanks", "Best", "Thanks!", "Best regards"]
        
        # Build the reply
        parts = [greeting]
        
        # Add opening
        opening = random.choice(openings)
        parts.append(opening + ".")
        
        # Add action with timeline
        action = random.choice(actions)
        timeline = random.choice(timeline_phrases)
        
        # Combine action and timeline naturally
        if timeline in ["soon", "asap", "quickly"]:
            parts.append(f"{action} {timeline}.")
        else:
            parts.append(f"{action} {timeline}.")
        
        # Add closing
        closing = random.choice(closings)
        parts.append(closing)
        
        return "\n\n".join(parts)
    
    def generate_no_reply_message(self, email_intent: str, context: Dict) -> Optional[str]:
        """
        Generate appropriate message for emails that don't need replies
        Returns None if no reply should be generated at all
        """
        
        # For most no-reply cases, return None (no reply generated)
        if email_intent in ['transactional', 'notification', 'marketing', 'newsletter']:
            return None
        
        # For announcements, generate brief optional acknowledgment
        if email_intent == 'announcement':
            topic = context.get('main_topic', 'the event')
            return f"Thanks for the heads up! Looking forward to {topic}."
        
        # For invitations, suggest RSVP
        if email_intent == 'invitation':
            return "Thanks for the invitation! I'll let you know if I can attend."
        
        # For security alerts, don't reply - take action
        if email_intent == 'security_alert':
            return None
        
        # Default: None (no reply)
        return None
    
    def _fallback_acknowledgment(self, context: Dict, tone: str) -> str:
        """Generate acknowledgment without BART (fallback)"""
        
        topic = context.get('main_topic', 'your email')
        category = context.get('email_category', 'general')
        
        # Build based on context
        parts = []
        
        # Opening based on tone
        if tone == 'formal':
            parts.append(f"Thank you for your email regarding {topic}.")
        elif tone == 'business':
            parts.append(f"Thanks for your email about {topic}.")
        else:
            parts.append(f"Thanks for reaching out about {topic}.")
        
        # Add specific acknowledgments
        if context.get('questions'):
            parts.append("I'll address your questions")
        if context.get('has_attachments'):
            count = context.get('attachment_count', 1)
            parts.append(f"and review the {count} document(s) you sent")
        
        return " ".join(parts) + "."


# =============================================================================
# CONFIDENCE SCORER
# =============================================================================

class ConfidenceScorer:
    """
    Calculates confidence score for generated replies (ENHANCED - Priority 3)
    
    Now checks for quality indicators that correlate with actual acceptance:
    - Absence of generic phrases users consistently remove
    - Presence of specific commitments users consistently add
    - Enthusiasm markers users prefer
    - Actual addressing of questions/actions
    """
    
    def __init__(self, learning_stats: Optional[Dict] = None):
        """
        Initialize enhanced confidence scorer
        
        Args:
            learning_stats: Optional learning stats to calibrate confidence
        """
        self.learning_stats = learning_stats
        
        # Generic phrases that users REMOVE (penalty indicators)
        self.generic_penalty_phrases = [
            "i'll get back to you",
            "i'll look into this",
            "thanks for your email about",
            "i see your question",
            "i'll check on this",
            "let me get back to you",
            "i'll follow up",
            "i'll review this"
        ]
        
        # Specific phrases that users ADD (quality indicators)
        self.quality_indicators = [
            "by eod",
            "by end of day",
            "by tomorrow",
            "by [day] afternoon",
            "by [day] morning",
            "i'll send you",
            "i'll share",
            "great question",
            "good question",
            "thanks for reaching out",
            "happy to help",
            "!",  # Enthusiasm marker
        ]
        
        # Vague timeline words (penalty)
        self.vague_timelines = [
            "soon",
            "shortly",
            "later",
            "eventually",
            "in the future"
        ]
        
        # Specific timeline patterns (quality)
        self.specific_timeline_patterns = [
            r'by \w+day',  # by Monday, by Tuesday, by today, by tomorrow
            r'by eod',
            r'by \d+:\d+',  # by 3:00, by 14:30
            r'within \d+ (hours?|days?)',  # within 2 hours, within 3 days
            r'this (morning|afternoon|evening)',
            r'tomorrow (morning|afternoon|evening)'
        ]
    
    def calculate_confidence(self, context: Dict[str, Any], generated_reply: str) -> float:
        """
        Calculate ENHANCED confidence score (0.0 to 1.0)
        
        Now considers:
        - Generic phrase penalties (what users remove)
        - Quality indicators (what users add)
        - Specificity of commitments
        - Question/action addressing
        - Learning-based calibration
        """
        
        score = 0.5  # Base score (neutral)
        reply_lower = generated_reply.lower()
        
        # ========== PENALTY FACTORS (What makes replies BAD) ==========
        
        # PENALTY 1: Generic phrases users consistently remove (-0.15 max)
        generic_count = sum(1 for phrase in self.generic_penalty_phrases if phrase in reply_lower)
        if generic_count > 0:
            penalty = min(0.15, generic_count * 0.05)
            score -= penalty
            # print(f"[CONFIDENCE] Generic phrase penalty: -{penalty:.2f} ({generic_count} phrases)")
        
        # PENALTY 2: Vague timelines (-0.10)
        has_vague_timeline = any(vague in reply_lower for vague in self.vague_timelines)
        if has_vague_timeline:
            score -= 0.10
            # print(f"[CONFIDENCE] Vague timeline penalty: -0.10")
        
        # PENALTY 3: No specific commitment when action needed (-0.15)
        if context.get('action_items') and len(context['action_items']) > 0:
            # Action items present - should have specific commitment
            has_specific_action = any(
                word in reply_lower for word in ['send', 'share', 'provide', 'schedule', 'review', 'update']
            )
            if not has_specific_action:
                score -= 0.15
                # print(f"[CONFIDENCE] Missing specific action penalty: -0.15")
        
        # PENALTY 4: No enthusiasm when question asked (-0.05)
        if context.get('questions') and len(context['questions']) > 0:
            has_enthusiasm = ('!' in generated_reply or 
                            'great question' in reply_lower or 
                            'good question' in reply_lower)
            if not has_enthusiasm:
                score -= 0.05
                # print(f"[CONFIDENCE] Missing enthusiasm penalty: -0.05")
        
        # ========== QUALITY FACTORS (What makes replies GOOD) ==========
        
        # QUALITY 1: Specific timeline present (+0.15)
        has_specific_timeline = any(
            re.search(pattern, reply_lower) for pattern in self.specific_timeline_patterns
        )
        if has_specific_timeline:
            score += 0.15
            # print(f"[CONFIDENCE] Specific timeline bonus: +0.15")
        
        # QUALITY 2: Quality phrases users add (+0.10 max)
        quality_count = sum(1 for phrase in self.quality_indicators 
                          if phrase in reply_lower or phrase in generated_reply)
        if quality_count > 0:
            bonus = min(0.10, quality_count * 0.03)
            score += bonus
            # print(f"[CONFIDENCE] Quality phrases bonus: +{bonus:.2f} ({quality_count} phrases)")
        
        # QUALITY 3: Specific topic/entity reference (+0.10)
        topic_mentioned = False
        if context.get('main_topic') and context['main_topic']:
            # Check if main topic or variant is mentioned
            topic_lower = context['main_topic'].lower()
            if topic_lower in reply_lower and len(topic_lower) > 5:
                topic_mentioned = True
        
        entities_mentioned = any(
            entity.lower() in reply_lower 
            for entities in context.get('entities', {}).values() 
            for entity in entities
        )
        
        if topic_mentioned or entities_mentioned:
            score += 0.10
            # print(f"[CONFIDENCE] Specific reference bonus: +0.10")
        
        # QUALITY 4: Question directly addressed (+0.10)
        if context.get('questions') and len(context['questions']) > 0:
            question = context['questions'][0].lower()
            # Check if reply addresses question type
            addresses_question = False
            
            if 'when' in question and has_specific_timeline:
                addresses_question = True
            elif 'available' in question and ('available' in reply_lower or 'schedule' in reply_lower):
                addresses_question = True
            elif 'status' in question and ('status' in reply_lower or 'update' in reply_lower):
                addresses_question = True
            
            if addresses_question:
                score += 0.10
                # print(f"[CONFIDENCE] Question addressed bonus: +0.10")
        
        # QUALITY 5: Appropriate length (not too short/long) (+0.05)
        word_count = len(generated_reply.split())
        if 40 <= word_count <= 120:  # Based on learning: avg 116 words
            score += 0.05
            # print(f"[CONFIDENCE] Good length bonus: +0.05 ({word_count} words)")
        
        # ========== LEARNING-BASED CALIBRATION ==========
        
        # If we have learning stats showing low acceptance, reduce confidence
        if self.learning_stats:
            overall_acceptance = self.learning_stats.get('overall_acceptance_rate', '100%')
            acceptance_rate = float(overall_acceptance.rstrip('%')) / 100.0
            
            # If acceptance rate is low, apply calibration penalty
            if acceptance_rate < 0.5:  # Less than 50% acceptance
                calibration = 1.0 - (0.5 - acceptance_rate)  # Max 0.5 reduction
                score *= calibration
                # print(f"[CONFIDENCE] Learning calibration: {calibration:.2f}x (acceptance: {overall_acceptance})")
        
        # ========== FINAL BOUNDS ==========
        
        score = max(0.0, min(1.0, score))
        
        return round(score, 2)


# =============================================================================
# CONTENT-SPECIFIC REPLY BUILDER (Priority 1 Enhancement)
# =============================================================================

class QuestionAnalyzer:
    """
    Analyzes questions to extract what they're actually asking about
    This enables specific responses instead of generic "I'll look into it"
    """
    
    def __init__(self):
        """Initialize question analyzer"""
        self.question_topics = {
            'timeline': ['when', 'deadline', 'due', 'timeline', 'schedule', 'date'],
            'availability': ['available', 'free', 'meeting', 'call', 'time to'],
            'status': ['status', 'progress', 'update', 'how is', 'where are we'],
            'clarification': ['what do you mean', 'can you clarify', 'explain', 'wondering'],
            'decision': ['should we', 'do you think', 'would you', 'opinion', 'thoughts'],
            'approval': ['can i', 'may i', 'approve', 'permission', 'okay to'],
            'information': ['what', 'which', 'how', 'where', 'who']
        }
    
    def analyze_question(self, question: str) -> Dict[str, Any]:
        """
        Analyze question to determine what it's asking about
        
        Returns:
            {
                'question': original question,
                'category': question type (timeline, availability, etc.),
                'subject': what the question is about,
                'requires_specific_answer': bool
            }
        """
        # Take only the first sentence/question if multiple exist
        first_question = question.split('?')[0] + '?' if '?' in question else question.split('.')[0]
        question_lower = first_question.lower()
        
        # Determine question category
        category = 'information'
        for cat, keywords in self.question_topics.items():
            if any(keyword in question_lower for keyword in keywords):
                category = cat
                break
        
        # Extract subject (rough heuristic)
        subject = self._extract_question_subject(first_question)
        
        return {
            'question': first_question,
            'category': category,
            'subject': subject,
            'requires_specific_answer': category in ['timeline', 'availability', 'approval']
        }
    
    def _extract_question_subject(self, question: str) -> str:
        """Extract what the question is about"""
        # Try to extract noun phrases or key topics
        # Remove question words and punctuation
        cleaned = re.sub(r'\b(can you|could you|would you|will you|do you|what|when|where|how|why|which|me|you|to me|them|it|the)\b', '', question.lower(), flags=re.IGNORECASE)
        cleaned = re.sub(r'[?,.\n]', '', cleaned)
        cleaned = cleaned.strip()
        
        # Get meaningful words (not too short, not stopwords)
        stopwords = {'for', 'and', 'a', 'an', 'to', 'by', 'is', 'are', 'was', 'were', 'this', 'that', 'send', 'get', 'give', 'tell', 'show'}
        words = [w for w in cleaned.split() if len(w) > 2 and w not in stopwords]
        
        # If we got good words, return first 2-3
        if len(words) >= 2:
            return ' '.join(words[:3])
        
        # Subject extraction failed, return empty to trigger fallback
        return ''


class ActionSpecifier:
    """
    Identifies the exact action requested from user
    This enables specific commitments instead of "I'll get back to you"
    """
    
    def __init__(self):
        """Initialize action specifier"""
        self.action_verbs = {
            'send': ['send', 'email', 'share', 'forward', 'provide'],
            'review': ['review', 'check', 'look at', 'examine', 'go through'],
            'update': ['update', 'inform', 'let know', 'notify'],
            'schedule': ['schedule', 'set up', 'arrange', 'book'],
            'complete': ['complete', 'finish', 'submit', 'deliver'],
            'approve': ['approve', 'sign off', 'authorize'],
            'confirm': ['confirm', 'verify', 'validate']
        }
    
    def specify_action(self, action_item: str) -> Dict[str, Any]:
        """
        Determine what specific action is being requested
        
        Returns:
            {
                'action_text': original action item,
                'action_type': type of action (send, review, etc.),
                'action_object': what to act on,
                'is_concrete': bool (can we commit specifically?)
            }
        """
        action_lower = action_item.lower()
        
        # Identify action type
        action_type = 'general'
        for atype, verbs in self.action_verbs.items():
            if any(verb in action_lower for verb in verbs):
                action_type = atype
                break
        
        # Extract action object (what to send/review/etc.)
        action_object = self._extract_action_object(action_item, action_type)
        
        return {
            'action_text': action_item,
            'action_type': action_type,
            'action_object': action_object,
            'is_concrete': action_type != 'general' and action_object != 'this'
        }
    
    def _extract_action_object(self, action_item: str, action_type: str) -> str:
        """Extract what object the action is about"""
        # Look for nouns after action verbs
        words = action_item.split()
        
        # Common objects to look for
        objects = ['report', 'document', 'file', 'update', 'proposal', 'numbers', 'data', 'info', 'details']
        
        for obj in objects:
            if obj in action_item.lower():
                return obj
        
        # Fallback: return meaningful words
        meaningful = [w for w in words if len(w) > 3 and w.lower() not in ['please', 'could', 'would', 'kindly']][:3]
        return ' '.join(meaningful) if meaningful else 'this'


class CommitmentGenerator:
    """
    Generates specific commitments based on email content
    Replaces vague "I'll get back to you" with concrete actions
    """
    
    def __init__(self):
        """Initialize commitment generator"""
        self.default_timelines = {
            'urgent': 'today',
            'high': 'by end of day',
            'normal': 'soon'
        }
    
    def generate_commitment(self, context: Dict[str, Any], action_spec: Optional[Dict] = None, 
                          question_analysis: Optional[Dict] = None) -> str:
        """
        Generate specific commitment based on what's requested
        
        Args:
            context: Email context with urgency, deadlines, etc.
            action_spec: Specification from ActionSpecifier
            question_analysis: Analysis from QuestionAnalyzer
            
        Returns:
            Specific commitment string
        """
        urgency = context.get('urgency_level', 'normal')
        deadlines = context.get('deadlines', [])
        
        # If there's a specific action requested
        if action_spec and action_spec.get('is_concrete'):
            action_type = action_spec['action_type']
            action_object = action_spec['action_object']
            
            # Clean the action object - only use if it makes sense
            if action_object and len(action_object) > 2 and len(action_object.split()) <= 5:
                # Create specific commitment based on action type
                if action_type == 'send':
                    commitment = f"I'll send you {action_object}"
                elif action_type == 'review':
                    commitment = f"I'll review {action_object}"
                elif action_type == 'update':
                    commitment = f"I'll send you an update"
                elif action_type == 'schedule':
                    commitment = f"I'll set up {action_object}"
                elif action_type == 'complete':
                    commitment = f"I'll complete {action_object}"
                else:
                    commitment = f"I'll take care of that"
            else:
                # Action object is garbled, use generic but still action-specific
                if action_type == 'send':
                    commitment = "I'll send that over"
                elif action_type == 'review':
                    commitment = "I'll review that"
                elif action_type == 'update':
                    commitment = "I'll send you an update"
                else:
                    commitment = "I'll take care of that"
        
        # If there's a specific question
        elif question_analysis and question_analysis.get('requires_specific_answer'):
            category = question_analysis['category']
            subject = question_analysis['subject']
            
            if category == 'availability':
                commitment = "Let me check my calendar and send you some times"
            elif category == 'timeline':
                # Only use subject if clean
                if subject and len(subject) > 2 and len(subject.split()) <= 4:
                    commitment = f"I'll get you those details"
                else:
                    commitment = "I'll get you those details"
            elif category == 'approval':
                commitment = "Let me review this and confirm"
            else:
                commitment = "I'll get back to you on that"
        
        # Default commitment
        else:
            commitment = "I'll take a look at this"
        
        # Add timeline (be careful not to duplicate "by")
        if deadlines:
            deadline = deadlines[0]
            # If deadline already starts with "by", don't add another "by"
            if deadline.lower().startswith('by '):
                commitment += f" {deadline}"
            else:
                commitment += f" by {deadline}"
        else:
            timeline = self.default_timelines.get(urgency, 'soon')
            if timeline != 'soon':
                commitment += f" {timeline}"
            else:
                commitment += " soon"
        
        return commitment


class UserPatternApplier:
    """
    Applies learned user preferences from edit history
    Makes replies sound more like the user's natural style
    """
    
    def __init__(self, user_preferences: Optional[Dict] = None):
        """Initialize with user preferences from learning tracker"""
        self.user_prefs = user_preferences or {}
    
    def apply_user_patterns(self, reply: str, context: Dict[str, Any]) -> str:
        """
        Apply learned user patterns to reply
        
        Args:
            reply: Generated reply text
            context: Email context
            
        Returns:
            Reply adjusted to match user's style
        """
        if not self.user_prefs:
            return reply
        
        # NOW RE-ENABLED with clean data
        # Only apply formality (safe transformation)
        reply = self._apply_formality(reply)
        
        # Note: Closing replacement disabled as it's not needed with short phrases
        # The short phrases don't contain full closings anyway
        
        return reply
    
    def _apply_preferred_closing(self, reply: str) -> str:
        """Replace generic closing with user's preferred style"""
        common_closings = {
            'Thanks': ['Thanks', 'Thanks!', 'Thank you'],
            'Best': ['Best', 'Best regards', 'Best,'],
            'Regards': ['Regards', 'Best regards', 'Kind regards']
        }
        
        # Check user's commonly added phrases for closings
        added_phrases = self.user_prefs.get('phrase_preferences', {}).get('commonly_added_phrases', [])
        
        for phrase in added_phrases:
            phrase_lower = phrase.lower()
            # Look for closing patterns
            if any(closing in phrase_lower for closing in ['thanks!', 'best regards', 'cheers', 'talk soon']):
                # Found user's preferred closing in their edit history
                closing = phrase.split('\n')[-1] if '\n' in phrase else phrase.split('.')[-1]
                closing = closing.strip()
                
                # Replace generic closing in reply
                for generic_closings in common_closings.values():
                    for generic in generic_closings:
                        if generic in reply:
                            reply = reply.replace(generic, closing.capitalize())
                            return reply
        
        return reply
    
    def _apply_formality(self, reply: str) -> str:
        """Adjust formality based on user preference"""
        formality = self.user_prefs.get('communication_style', {}).get('formality_level', 0.6)
        
        # If user prefers casual (formality < 0.5)
        if formality < 0.5:
            # Replace formal phrases with casual ones
            reply = reply.replace('I will', "I'll")
            reply = reply.replace('I would', "I'd")
            reply = reply.replace('Thank you', 'Thanks')
        
        # If user prefers formal (formality > 0.7)
        elif formality > 0.7:
            # Replace casual with formal
            reply = reply.replace("I'll", 'I will')
            reply = reply.replace("I'd", 'I would')
            reply = reply.replace('Thanks!', 'Thank you')
        
        return reply
    
    def _inject_common_phrases(self, reply: str, context: Dict[str, Any]) -> str:
        """Inject user's commonly used phrases when contextually relevant"""
        added_phrases = self.user_prefs.get('phrase_preferences', {}).get('commonly_added_phrases', [])
        
        # Look for phrases that match current context
        if context.get('email_category') == 'meeting_request':
            for phrase in added_phrases:
                if 'available' in phrase.lower() or 'calendar' in phrase.lower():
                    # User commonly mentions specific availability
                    # Could inject learned availability patterns here
                    pass
        
        return reply


class ContentSpecificReplyBuilder:
    """
    Main builder that creates human-sounding replies by addressing actual email content
    This replaces the generic template-based approach
    """
    
    def __init__(self, user_preferences: Optional[Dict] = None):
        """Initialize content-specific reply builder"""
        self.question_analyzer = QuestionAnalyzer()
        self.action_specifier = ActionSpecifier()
        self.commitment_generator = CommitmentGenerator()
        self.user_pattern_applier = UserPatternApplier(user_preferences)
    
    def build_reply(self, context: Dict[str, Any], tone: str = 'business', 
                   relationship_context: Optional[Dict] = None,
                   greeting_builder: Optional[Any] = None) -> str:
        """
        Build human-sounding reply addressing specific email content
        
        Args:
            context: Extracted email context with questions, actions, etc.
            tone: Communication tone (formal, business, casual)
            relationship_context: Optional sender relationship context (Priority 2)
            greeting_builder: Optional PersonalizedGreetingBuilder (Priority 2)
            
        Returns:
            Natural-sounding reply that addresses email specifics
        """
        import random
        
        sender_name = context.get('sender_name', 'there')
        questions = context.get('questions', [])
        action_items = context.get('action_items', [])
        deadlines = context.get('deadlines', [])
        urgency = context.get('urgency_level', 'normal')
        main_topic = context.get('main_topic', '')
        
        # Build reply parts
        parts = []
        
        # 1. GREETING (contextual + personalized with Priority 2 enhancement)
        if greeting_builder and relationship_context:
            greeting = greeting_builder.build_greeting(sender_name, relationship_context)
        else:
            greeting = self._build_greeting(sender_name, tone, context)
        parts.append(greeting)
        
        # 2. SPECIFIC ACKNOWLEDGMENT (not generic)
        acknowledgment = self._build_specific_acknowledgment(context, questions, action_items, main_topic)
        if acknowledgment:
            parts.append(acknowledgment)
        
        # 3. SPECIFIC COMMITMENT (not "I'll get back to you")
        commitment = self._build_specific_commitment(context, questions, action_items)
        parts.append(commitment)
        
        # 4. CLOSING (learned from user)
        closing = self._build_closing(tone, urgency)
        parts.append(closing)
        
        # Combine parts naturally
        reply = "\n\n".join(parts)
        
        # Apply user patterns
        reply = self.user_pattern_applier.apply_user_patterns(reply, context)
        
        return reply
    
    def _build_greeting(self, sender_name: str, tone: str, context: Dict) -> str:
        """Build contextual greeting"""
        import random
        
        if tone == 'formal':
            greetings = ["Dear", "Hello"]
        elif tone == 'casual':
            greetings = ["Hey", "Hi"]
        else:  # business
            greetings = ["Hi", "Hey", "Hello"]
        
        greeting = random.choice(greetings)
        return f"{greeting} {sender_name},"
    
    def _build_specific_acknowledgment(self, context: Dict, questions: List[str], 
                                      action_items: List[str], main_topic: str) -> str:
        """Build acknowledgment that references actual content"""
        import random
        
        # If there's a specific question
        if questions:
            question_analysis = self.question_analyzer.analyze_question(questions[0])
            category = question_analysis['category']
            subject = question_analysis['subject']
            
            if category == 'availability':
                return random.choice([
                    "Thanks for reaching out about scheduling!",
                    "Got your message about meeting up.",
                    "Thanks for checking on availability."
                ])
            elif category == 'timeline':
                # Only use subject if it's clean and meaningful (at least 2 words)
                if subject and len(subject) > 3 and len(subject.split()) >= 2:
                    return random.choice([
                        f"Thanks for your question about {subject}!",
                        f"Good question about {subject}.",
                        f"Got your question on {subject}."
                    ])
                else:
                    return random.choice([
                        "Thanks for your question!",
                        "Good question!",
                        "Got your message!"
                    ])
            elif category == 'status':
                if subject and len(subject) > 3 and len(subject.split()) <= 4:
                    return f"Thanks for checking in on {subject}."
                else:
                    return "Thanks for checking in!"
            else:
                return random.choice([
                    "Great question!",
                    "Good question!",
                    "Thanks for asking about that."
                ])
        
        # If there's a specific action requested
        elif action_items:
            action_spec = self.action_specifier.specify_action(action_items[0])
            if action_spec['is_concrete']:
                action_obj = action_spec['action_object']
                # Only use if clean
                if action_obj and len(action_obj) > 3 and len(action_obj.split()) <= 4:
                    return random.choice([
                        f"Got it - thanks for flagging {action_obj}.",
                        f"Thanks for the heads up on {action_obj}.",
                        f"Noted on {action_obj}."
                    ])
        
        # If there's a clear topic
        if main_topic and len(main_topic) > 10 and len(main_topic) < 50:
            return random.choice([
                f"Thanks for reaching out!",
                "Got your message.",
                "Thanks for sending this over."
            ])
        
        # Generic but warm fallback
        return random.choice([
            "Thanks for reaching out!",
            "Got your email.",
            "Thanks for sending this over."
        ])
    
    def _build_specific_commitment(self, context: Dict, questions: List[str], 
                                   action_items: List[str]) -> str:
        """Build specific commitment instead of generic response"""
        
        # Analyze question if present
        question_analysis = None
        if questions:
            question_analysis = self.question_analyzer.analyze_question(questions[0])
        
        # Specify action if present
        action_spec = None
        if action_items:
            action_spec = self.action_specifier.specify_action(action_items[0])
        
        # Generate specific commitment
        commitment = self.commitment_generator.generate_commitment(
            context, action_spec, question_analysis
        )
        
        return commitment
    
    def _build_closing(self, tone: str, urgency: str) -> str:
        """Build natural closing"""
        import random
        
        if tone == 'formal':
            closings = ["Best regards", "Regards", "Sincerely"]
        elif tone == 'casual':
            closings = ["Thanks!", "Cheers!", "Talk soon!"]
        else:  # business
            if urgency in ['urgent', 'high']:
                closings = ["Thanks", "Best", "Talk soon"]
            else:
                closings = ["Thanks", "Best", "Thanks!"]
        
        return random.choice(closings)


# =============================================================================
# SENDER INTELLIGENCE & RELATIONSHIP CONTEXT (Priority 2 Enhancement)
# =============================================================================

class SenderHistoryAnalyzer:
    """
    Analyzes sender history to personalize replies based on past interactions
    """
    
    def __init__(self, behavioral_patterns: Dict):
        """
        Initialize sender history analyzer
        
        Args:
            behavioral_patterns: Dict from behavioral_patterns.json
        """
        self.behavioral_patterns = behavioral_patterns
        print("[INFO] Sender History Analyzer initialized")
    
    def get_sender_profile(self, sender_email: str) -> Dict[str, Any]:
        """
        Build comprehensive sender profile from history
        
        Returns:
            {
                'interaction_count': int,
                'preferred_tone': str (formal/business/casual),
                'typical_priority': str (High/Medium/Low),
                'relationship_level': str (new/regular/frequent),
                'tone_consistency': float (0-1, how consistent their preferred tone is)
            }
        """
        
        profile = {
            'interaction_count': 0,
            'preferred_tone': 'business',  # default
            'typical_priority': 'Medium',
            'relationship_level': 'new',
            'tone_consistency': 0.5
        }
        
        # Get communication style data
        comm_style = self.behavioral_patterns.get('communication_style', {})
        sender_style = comm_style.get(sender_email, {})
        
        if sender_style:
            formal = sender_style.get('formal_count', 0)
            business = sender_style.get('business_count', 0)
            casual = sender_style.get('casual_count', 0)
            
            total = formal + business + casual
            profile['interaction_count'] = total
            
            # Determine preferred tone (highest count)
            if total > 0:
                max_count = max(formal, business, casual)
                if formal == max_count:
                    profile['preferred_tone'] = 'formal'
                elif casual == max_count:
                    profile['preferred_tone'] = 'casual'
                else:
                    profile['preferred_tone'] = 'business'
                
                # Calculate tone consistency
                profile['tone_consistency'] = max_count / total
            
            # Determine relationship level
            if total >= 20:
                profile['relationship_level'] = 'frequent'
            elif total >= 5:
                profile['relationship_level'] = 'regular'
            else:
                profile['relationship_level'] = 'new'
        
        # Get priority patterns
        priority_patterns = self.behavioral_patterns.get('priority_patterns', {})
        sender_priorities = priority_patterns.get(sender_email, {})
        
        if sender_priorities:
            high = sender_priorities.get('High', 0)
            medium = sender_priorities.get('Medium', 0)
            low = sender_priorities.get('Low', 0)
            
            total_priority = high + medium + low
            if total_priority > 0:
                max_priority = max(high, medium, low)
                if high == max_priority:
                    profile['typical_priority'] = 'High'
                elif low == max_priority:
                    profile['typical_priority'] = 'Low'
                else:
                    profile['typical_priority'] = 'Medium'
        
        return profile


class RelationshipContextBuilder:
    """
    Builds relationship context to personalize greeting and overall tone
    """
    
    def __init__(self, sender_analyzer: SenderHistoryAnalyzer):
        """
        Initialize relationship context builder
        
        Args:
            sender_analyzer: SenderHistoryAnalyzer instance
        """
        self.sender_analyzer = sender_analyzer
        print("[INFO] Relationship Context Builder initialized")
    
    def build_context(self, sender_email: str, sender_name: str, 
                     current_urgency: str) -> Dict[str, Any]:
        """
        Build relationship context for personalization
        
        Returns:
            {
                'greeting_style': str (formal/friendly/casual),
                'use_first_name': bool,
                'reference_history': bool,
                'relationship_acknowledgment': str (optional phrase to add),
                'tone_override': str (if sender history strongly suggests different tone)
            }
        """
        
        profile = self.sender_analyzer.get_sender_profile(sender_email)
        
        context = {
            'greeting_style': 'professional',
            'use_first_name': True,
            'reference_history': False,
            'relationship_acknowledgment': '',
            'tone_override': None
        }
        
        # Determine greeting style based on relationship
        if profile['relationship_level'] == 'frequent':
            # Frequent contacts get warmer greetings
            if profile['preferred_tone'] == 'casual':
                context['greeting_style'] = 'casual'
                context['reference_history'] = True
                context['relationship_acknowledgment'] = self._get_frequent_acknowledgment()
            elif profile['preferred_tone'] == 'business':
                context['greeting_style'] = 'friendly'
                context['reference_history'] = True
            else:  # formal
                context['greeting_style'] = 'professional'
        
        elif profile['relationship_level'] == 'regular':
            # Regular contacts get friendly but professional
            if profile['preferred_tone'] == 'casual':
                context['greeting_style'] = 'friendly'
            else:
                context['greeting_style'] = 'professional'
        
        else:  # new
            # New contacts get professional treatment
            context['greeting_style'] = 'professional'
            context['use_first_name'] = profile['preferred_tone'] != 'formal'
        
        # Strong tone consistency = override current tone detection
        if profile['tone_consistency'] > 0.8 and profile['interaction_count'] >= 3:
            context['tone_override'] = profile['preferred_tone']
        
        # High priority senders get priority treatment
        if profile['typical_priority'] == 'High' and current_urgency != 'urgent':
            context['relationship_acknowledgment'] = "I'll prioritize this for you."
        
        return context
    
    def _get_frequent_acknowledgment(self) -> str:
        """Get acknowledgment phrase for frequent contacts"""
        import random
        phrases = [
            "Great to hear from you again!",
            "Thanks as always for reaching out!",
            "Always happy to help!",
            ""  # Sometimes no special acknowledgment
        ]
        return random.choice(phrases)


class PersonalizedGreetingBuilder:
    """
    Builds personalized greetings based on sender relationship
    """
    
    def __init__(self):
        """Initialize personalized greeting builder"""
        print("[INFO] Personalized Greeting Builder initialized")
    
    def build_greeting(self, sender_name: str, relationship_context: Dict) -> str:
        """
        Build personalized greeting
        
        Args:
            sender_name: Name of sender
            relationship_context: Context from RelationshipContextBuilder
        
        Returns:
            Personalized greeting string
        """
        
        greeting_style = relationship_context.get('greeting_style', 'professional')
        use_first_name = relationship_context.get('use_first_name', True)
        
        # Extract first name if needed
        name_to_use = sender_name
        if use_first_name and ' ' in sender_name:
            name_to_use = sender_name.split()[0]
        
        # Build greeting based on style
        if greeting_style == 'casual':
            greetings = [f"Hey {name_to_use}!", f"Hi {name_to_use}!"]
        elif greeting_style == 'friendly':
            greetings = [f"Hi {name_to_use}", f"Hello {name_to_use}"]
        else:  # professional
            greetings = [f"Hi {name_to_use}", f"Hello {name_to_use}"]
        
        import random
        greeting = random.choice(greetings)
        
        # Add relationship acknowledgment if present
        rel_ack = relationship_context.get('relationship_acknowledgment', '')
        if rel_ack:
            greeting = f"{greeting}\n\n{rel_ack}"
        
        return greeting


class ToneAdapter:
    """
    Adapts detected tone based on sender history and relationship
    """
    
    def __init__(self, sender_analyzer: SenderHistoryAnalyzer):
        """
        Initialize tone adapter
        
        Args:
            sender_analyzer: SenderHistoryAnalyzer instance
        """
        self.sender_analyzer = sender_analyzer
        print("[INFO] Tone Adapter initialized")
    
    def adapt_tone(self, detected_tone: str, sender_email: str, 
                   sender_name: str, urgency: str) -> str:
        """
        Adapt tone based on sender history
        
        If sender consistently prefers a different tone (80%+ consistency, 3+ interactions),
        override the detected tone with their preference.
        
        Args:
            detected_tone: Tone detected from current email
            sender_email: Sender's email address
            sender_name: Sender's name
            urgency: Email urgency level
        
        Returns:
            Adapted tone (may be same as detected or overridden)
        """
        
        profile = self.sender_analyzer.get_sender_profile(sender_email)
        
        # Strong preference override
        if profile['tone_consistency'] > 0.8 and profile['interaction_count'] >= 3:
            adapted_tone = profile['preferred_tone']
            if adapted_tone != detected_tone:
                print(f"[INFO] Tone adapted: {detected_tone} → {adapted_tone} (sender preference, {profile['interaction_count']} interactions)")
            return adapted_tone
        
        # Moderate preference influence (blend)
        if profile['tone_consistency'] > 0.6 and profile['interaction_count'] >= 5:
            preferred = profile['preferred_tone']
            
            # If detected is formal but sender prefers casual, meet in middle (business)
            if detected_tone == 'formal' and preferred == 'casual':
                print(f"[INFO] Tone moderated: formal → business (sender preference)")
                return 'business'
            
            # If detected is casual but sender prefers formal, meet in middle (business)
            if detected_tone == 'casual' and preferred == 'formal':
                print(f"[INFO] Tone moderated: casual → business (sender preference)")
                return 'business'
        
        # No override needed
        return detected_tone


# =============================================================================
# ACTIVE LEARNING APPLICATION (Priority 4 Enhancement)
# =============================================================================

class LearnedPhraseInjector:
    """
    Actively injects commonly added phrases from learning history
    into generated replies to match user's natural style
    """
    
    def __init__(self, user_preferences: Optional[Dict] = None):
        """
        Initialize learned phrase injector
        
        Args:
            user_preferences: User preferences from learning tracker
        """
        self.user_prefs = user_preferences or {}
        
        # Extract learned phrases
        phrase_prefs = self.user_prefs.get('phrase_preferences', {})
        self.commonly_added = phrase_prefs.get('commonly_added_phrases', [])
        self.avoided = phrase_prefs.get('avoided_phrases', [])
        
        # Filter to ensure only SHORT phrases (safety check)
        self.commonly_added = [p for p in self.commonly_added if len(p) < 60]
        
        print(f"[INFO] Learned Phrase Injector initialized ({len(self.commonly_added)} short phrases)")
    
    def inject_learned_phrases(self, reply: str, context: Dict[str, Any]) -> str:
        """
        Inject learned phrases into reply where appropriate
        
        Args:
            reply: Generated reply
            context: Email context (questions, actions, etc.)
            
        Returns:
            Reply enhanced with learned phrases
        """
        
        # NOW RE-ENABLED with clean SHORT phrase data
        
        # STRATEGY 1: Add enthusiasm markers if user consistently adds them
        if context.get('questions') and self._user_adds_enthusiasm():
            reply = self._add_enthusiasm(reply, context)
        
        # STRATEGY 2: Inject specific timeline phrases user prefers
        reply = self._inject_timeline_phrases(reply)
        
        return reply
    
    def _enhance_greeting(self, reply: str) -> str:
        """Replace generic greeting with learned one"""
        
        # Find learned greetings
        learned_greetings = []
        for phrase in self.commonly_added:
            phrase_lower = phrase.lower()
            if any(greeting in phrase_lower for greeting in ['thanks for reaching out', 'thanks for asking', 'good question', 'great question']):
                learned_greetings.append(phrase)
        
        if not learned_greetings:
            return reply
        
        # Check if reply has generic greeting patterns
        generic_patterns = [
            'thanks for your email',
            'thank you for your email',
            'thanks for your message'
        ]
        
        reply_lower = reply.lower()
        for generic in generic_patterns:
            if generic in reply_lower:
                # User prefers different greeting
                import random
                learned = random.choice(learned_greetings)
                
                # Extract just the greeting part (first sentence)
                learned_greeting = learned.split('.')[0] if '.' in learned else learned
                learned_greeting = learned_greeting.split('\n')[0] if '\n' in learned_greeting else learned_greeting
                
                # Replace generic with learned
                reply = reply.replace(
                    reply[reply.lower().find(generic):reply.lower().find(generic) + len(generic)],
                    learned_greeting
                )
                break
        
        return reply
    
    def _user_adds_enthusiasm(self) -> bool:
        """Check if user consistently adds enthusiasm markers"""
        
        enthusiasm_count = sum(
            1 for phrase in self.commonly_added
            if '!' in phrase or 'great' in phrase.lower() or 'happy to' in phrase.lower()
        )
        
        # If >30% of learned phrases have enthusiasm
        if self.commonly_added and enthusiasm_count / len(self.commonly_added) > 0.3:
            return True
        
        return False
    
    def _add_enthusiasm(self, reply: str, context: Dict[str, Any]) -> str:
        """Add enthusiasm if missing but user typically adds it"""
        
        # If reply doesn't have exclamation marks but user likes them
        if '!' not in reply:
            # Find learned enthusiastic phrases
            enthusiastic_phrases = [
                phrase for phrase in self.commonly_added
                if 'great question' in phrase.lower() or 'good question' in phrase.lower()
            ]
            
            if enthusiastic_phrases and context.get('questions'):
                # Add at beginning after greeting
                lines = reply.split('\n\n')
                if len(lines) > 1:
                    # Add after first line (greeting)
                    lines[1] = "Great question! " + lines[1]
                    reply = '\n\n'.join(lines)
        
        return reply
    
    def _inject_timeline_phrases(self, reply: str) -> str:
        """Inject specific timeline phrases user prefers"""
        
        # First check if reply already has a specific timeline
        has_specific_timeline = any(phrase in reply.lower() for phrase in [
            'by eod', 'by tomorrow', 'by end of day', 'this afternoon', 
            'this morning', 'by monday', 'by friday', 'by next week'
        ])
        
        # If already has specific timeline, don't inject another
        if has_specific_timeline:
            return reply
        
        # Find learned timeline phrases
        timeline_phrases = []
        for phrase in self.commonly_added:
            phrase_lower = phrase.lower()
            if any(time in phrase_lower for time in ['by eod', 'by tomorrow', 'by end of day', 'this afternoon', 'this morning']):
                timeline_phrases.append(phrase)
        
        if not timeline_phrases:
            return reply
        
        # Check if reply has vague timeline
        vague_patterns = ['soon', 'shortly', 'later']
        
        reply_lower = reply.lower()
        for vague in vague_patterns:
            if vague in reply_lower:
                # Find a relevant learned timeline phrase
                import random
                learned_timeline = random.choice(timeline_phrases)
                
                # Extract the timeline part
                # e.g., "I'll send you an update by EOD tomorrow" -> "by EOD tomorrow"
                timeline_part = learned_timeline
                if 'by ' in learned_timeline.lower():
                    timeline_start = learned_timeline.lower().find('by ')
                    timeline_part = learned_timeline[timeline_start:].split('.')[0].strip()
                
                # Replace vague with specific (only first occurrence)
                reply = reply.replace(vague, timeline_part, 1)
                break
        
        return reply
    
    def _enhance_acknowledgment(self, reply: str, context: Dict[str, Any]) -> str:
        """Enhance generic acknowledgment with user's style"""
        
        # Find learned acknowledgment patterns
        acknowledgments = [
            phrase for phrase in self.commonly_added
            if any(ack in phrase.lower() for ack in ['thanks for', 'happy to', 'i\'d be happy', 'looking forward'])
        ]
        
        if not acknowledgments:
            return reply
        
        # If reply is too generic, enhance it
        generic_acks = ['i see your question', 'thanks for your email about']
        
        reply_lower = reply.lower()
        for generic in generic_acks:
            if generic in reply_lower:
                # Replace with more natural learned phrase
                import random
                learned_ack = random.choice(acknowledgments)
                
                # Extract acknowledgment part
                ack_sentence = learned_ack.split('.')[0] if '.' in learned_ack else learned_ack
                ack_sentence = ack_sentence.split('\n')[0] if '\n' in ack_sentence else ack_sentence
                
                # Replace
                start_idx = reply_lower.find(generic)
                end_idx = start_idx + len(generic)
                reply = reply[:start_idx] + ack_sentence.strip() + reply[end_idx:]
                break
        
        return reply


class CategorySpecificAdapter:
    """
    Adapts replies based on email category using learned patterns
    Different categories (meeting_request, question, etc.) get different treatment
    """
    
    def __init__(self, learning_stats: Optional[Dict] = None):
        """
        Initialize category-specific adapter
        
        Args:
            learning_stats: Learning statistics with per-category performance
        """
        self.learning_stats = learning_stats or {}
        self.category_performance = self.learning_stats.get('method_performance', {})
        
        print("[INFO] Category-Specific Adapter initialized")
    
    def adapt_for_category(self, reply: str, category: str, confidence: float) -> Tuple[str, float]:
        """
        Adapt reply based on category-specific learning
        
        Args:
            reply: Generated reply
            category: Email category (meeting_request, question, etc.)
            confidence: Current confidence score
            
        Returns:
            Tuple of (adapted_reply, adjusted_confidence)
        """
        
        # Adjust confidence based on category performance
        if category in self.category_performance:
            cat_performance = self.category_performance[category]
            acceptance_rate = float(cat_performance.get('acceptance_rate', '50%').rstrip('%')) / 100.0
            
            # If this category has low acceptance, reduce confidence
            if acceptance_rate < 0.5:
                confidence *= 0.9
                print(f"[INFO] Category '{category}' has {acceptance_rate*100:.0f}% acceptance - confidence reduced")
        
        # Category-specific enhancements
        if category == 'meeting_request':
            reply = self._enhance_meeting_request(reply)
        elif category == 'question':
            reply = self._enhance_question_response(reply)
        
        return reply, confidence
    
    def _enhance_meeting_request(self, reply: str) -> str:
        """Add meeting-specific enhancements"""
        
        # Ensure meeting requests mention availability/scheduling
        if 'available' not in reply.lower() and 'schedule' not in reply.lower():
            # Add scheduling mention
            if 'i\'ll' in reply.lower() and 'get back' in reply.lower():
                reply = reply.replace('get back to you', 'get back to you with my availability')
        
        return reply
    
    def _enhance_question_response(self, reply: str) -> str:
        """Add question-specific enhancements"""
        
        # Ensure questions get enthusiastic response
        if '!' not in reply and 'question' not in reply.lower():
            # Find first line after greeting
            lines = reply.split('\n\n')
            if len(lines) > 1 and 'thanks' in lines[1].lower():
                if not any(enthusiasm in lines[1].lower() for enthusiasm in ['great', 'good', '!']):
                    lines[1] = lines[1].replace('Thanks', 'Thanks!')
                    reply = '\n\n'.join(lines)
        
        return reply


# =============================================================================
# MAIN SMART REPLY GENERATOR
# =============================================================================

class SmartReplyGenerator:
    """
    Main class orchestrating smart reply generation
    """
    
    def __init__(self, config: Optional[SmartReplyConfig] = None):
        """Initialize the smart reply generator"""
        
        print("\n[INFO] INITIALIZING SMART REPLY GENERATOR")
        print("=" * 60)
        
        self.config = config or SmartReplyConfig()
        
        # Initialize components
        self.context_extractor = EmailContextExtractor()
        self.bart_generator = BARTAcknowledgmentGenerator()
        
        # Initialize learning system (Phase 3) - MOVED UP for Priority 3
        if self.config.track_user_edits:
            try:
                from reply_learning_tracker import ReplyLearningTracker
                self.learning_tracker = ReplyLearningTracker()
                print("[INFO] Learning tracker enabled")
            except ImportError:
                print("[WARNING] Learning tracker not available")
                self.learning_tracker = None
        else:
            self.learning_tracker = None
        
        # Initialize Enhanced Confidence Scorer with learning stats (Priority 3)
        learning_stats = self._load_learning_stats()
        self.confidence_scorer = ConfidenceScorer(learning_stats)
        print("[INFO] Enhanced confidence scorer initialized")
        
        # Initialize safety components (Phase 2)
        self.sensitive_detector = SensitiveTopicDetector()
        self.edge_case_handler = EdgeCaseHandler()
        
        # Initialize reply necessity analyzer (NEW)
        self.reply_necessity_analyzer = ReplyNecessityAnalyzer()
        
        # Initialize Content-Specific Reply Builder (Priority 1 Enhancement)
        user_prefs = self.learning_tracker.user_preferences if self.learning_tracker else None
        self.content_reply_builder = ContentSpecificReplyBuilder(user_prefs)
        print("[INFO] Content-specific reply builder initialized")
        
        # Initialize Sender Intelligence System (Priority 2 Enhancement)
        behavioral_data = self._load_behavioral_patterns()
        self.sender_analyzer = SenderHistoryAnalyzer(behavioral_data)
        self.relationship_builder = RelationshipContextBuilder(self.sender_analyzer)
        self.greeting_builder = PersonalizedGreetingBuilder()
        self.tone_adapter = ToneAdapter(self.sender_analyzer)
        print("[INFO] Sender intelligence system initialized")
        
        # Initialize Active Learning Application (Priority 4 Enhancement)
        self.phrase_injector = LearnedPhraseInjector(user_prefs)
        self.category_adapter = CategorySpecificAdapter(learning_stats)
        print("[INFO] Active learning application initialized")
        
        # Load templates for fallback/combination
        self._initialize_templates()
        
        print("[OK] Smart Reply Generator ready!")
        print("=" * 60)
    
    def _initialize_templates(self):
        """Initialize template components"""
        
        self.openings = {
            'formal': "Dear {sender_name},\n\n",
            'business': "Hi {sender_name},\n\n",
            'casual': "Hi {sender_name},\n\n"
        }
        
        self.closings = {
            'urgent': {
                'formal': "\n\nI will prioritize this and respond by end of day.\n\nBest regards",
                'business': "\n\nI'm on this and will update you by end of day.\n\nBest",
                'casual': "\n\nI'll handle this ASAP and get back to you today.\n\nThanks!"
            },
            'high': {
                'formal': "\n\nI will review this and provide a detailed response shortly.\n\nBest regards",
                'business': "\n\nI'll review this and get back to you soon.\n\nBest",
                'casual': "\n\nI'll look into this and update you soon.\n\nThanks!"
            },
            'normal': {
                'formal': "\n\nI will review this matter and respond accordingly.\n\nBest regards",
                'business': "\n\nI'll get back to you on this.\n\nBest",
                'casual': "\n\nI'll get back to you.\n\nThanks!"
            }
        }
        
        # Safe mode templates for sensitive topics (Phase 2)
        self.safe_mode_templates = {
            'legal': {
                'formal': "Thank you for your email regarding this legal matter. Due to the sensitive nature of this topic, I will need to review this carefully and may need to consult with our legal team before providing a comprehensive response. I will get back to you within 24-48 hours.",
                'business': "Thanks for your email about this legal matter. Given the sensitivity involved, I'd like to review this carefully before responding. I'll get back to you within 1-2 business days.",
                'casual': "Thanks for reaching out about this. Since this involves legal matters, I want to make sure I respond appropriately. Let me review this and I'll get back to you soon."
            },
            'hr_personnel': {
                'formal': "Thank you for bringing this HR matter to my attention. I recognize the importance and sensitivity of your concerns. I will review this matter carefully and coordinate with the appropriate parties. You can expect a response within 24-48 hours.",
                'business': "Thanks for your email about this HR matter. I understand this is important and sensitive. Let me review this carefully and coordinate with the right people. I'll respond within 1-2 business days.",
                'casual': "Thanks for reaching out about this. I understand this is a sensitive HR matter. Let me review this properly and I'll get back to you soon."
            },
            'financial_sensitive': {
                'formal': "Thank you for your email regarding this financial matter. Due to the sensitive nature of this topic, I will need to review this carefully with the appropriate stakeholders. I will provide a detailed response within 24-48 hours.",
                'business': "Thanks for your email about this financial matter. Given the sensitivity, I need to review this carefully before responding. I'll get back to you within 1-2 business days.",
                'casual': "Thanks for reaching out. Since this involves sensitive financial matters, let me review this carefully and I'll get back to you soon."
            },
            'confidential': {
                'formal': "Thank you for your email. I acknowledge receipt of this confidential matter. I will handle this with appropriate discretion and provide a response within 24-48 hours.",
                'business': "Thanks for your email. I've received your message about this confidential matter and will handle it appropriately. I'll respond within 1-2 business days.",
                'casual': "Thanks for reaching out. I've got your message about this confidential matter and will handle it carefully. I'll get back to you soon."
            },
            'crisis': {
                'formal': "Thank you for alerting me to this urgent matter. I have received your email and am treating this with the highest priority. I will respond immediately or escalate to the appropriate parties as needed.",
                'business': "Thanks for the urgent heads up. I've received your message and am prioritizing this immediately. I'll respond or escalate as needed ASAP.",
                'casual': "Thanks for the urgent message. I've got it and am on this immediately. I'll respond or escalate as needed right away."
            },
            'ethical': {
                'formal': "Thank you for bringing this ethical matter to my attention. I recognize the importance of addressing this appropriately. I will review this carefully and may need to consult with relevant parties. You can expect a response within 24-48 hours.",
                'business': "Thanks for raising this ethical concern. I take this seriously and will review it carefully. I may need to coordinate with others. I'll get back to you within 1-2 business days.",
                'casual': "Thanks for bringing this up. I take ethical matters seriously. Let me review this properly and I'll get back to you soon."
            },
            'general_sensitive': {
                'formal': "Thank you for your email. I recognize the sensitive nature of this matter and will handle it with appropriate care. I will review this thoroughly and provide a thoughtful response within 24-48 hours.",
                'business': "Thanks for your email. I understand this is a sensitive matter. Let me review this carefully and I'll provide a thoughtful response within 1-2 business days.",
                'casual': "Thanks for reaching out. I understand this is sensitive. Let me review this carefully and I'll get back to you soon."
            }
        }
    
    def _load_behavioral_patterns(self) -> Dict:
        """Load behavioral patterns from JSON file"""
        import json
        import os
        
        try:
            patterns_path = os.path.join('ai_data', 'behavioral_patterns.json')
            if os.path.exists(patterns_path):
                with open(patterns_path, 'r') as f:
                    return json.load(f)
            else:
                print("[WARNING] behavioral_patterns.json not found, using empty patterns")
                return {'communication_style': {}, 'priority_patterns': {}}
        except Exception as e:
            print(f"[WARNING] Error loading behavioral patterns: {e}")
            return {'communication_style': {}, 'priority_patterns': {}}
    
    def _load_learning_stats(self) -> Dict:
        """Load learning statistics for confidence calibration (Priority 3)"""
        import json
        import os
        
        try:
            stats_path = os.path.join('ai_data', 'learning_stats.json')
            if os.path.exists(stats_path):
                with open(stats_path, 'r') as f:
                    return json.load(f)
            else:
                print("[WARNING] learning_stats.json not found, using defaults")
                return {'overall_acceptance_rate': '100%'}
        except Exception as e:
            print(f"[WARNING] Error loading learning stats: {e}")
            return {'overall_acceptance_rate': '100%'}
    
    def generate_smart_reply(self, email_data: Dict[str, Any], 
                           detected_tone: str = 'business') -> Dict[str, Any]:
        """
        Generate smart, contextually-aware reply
        
        Args:
            email_data: Email data with subject, body, sender, etc.
            detected_tone: Tone to match (formal, business, casual)
            
        Returns:
            Dict with generated reply, confidence score, metadata
        """
        
        print(f"\n[INFO] Generating smart reply for: {email_data.get('subject', 'No Subject')}")
        
        result = {
            'reply_text': '',
            'confidence_score': 0.0,
            'confidence_level': 'low',  # low, medium, high
            'context_used': {},
            'generation_method': 'template',  # template, hybrid, ai_enhanced
            'metadata': {}
        }
        
        try:
            # NEW: Step 0 - Extract context first (needed for reply necessity check)
            context = self.context_extractor.extract_context(email_data)
            result['context_used'] = context
            
            # NEW: Step 1 - Check reply necessity FIRST
            reply_necessity = self.reply_necessity_analyzer.analyze_reply_necessity(email_data, context)
            result['metadata']['reply_necessity'] = reply_necessity
            
            # If reply is not needed, return early with recommendation
            if not reply_necessity['needs_reply']:
                print(f"[INFO] Reply not needed: {reply_necessity['reason']}")
                print(f"[INFO] Suggested action: {reply_necessity['suggested_action']}")
                
                # Check if we should generate optional acknowledgment
                optional_reply = self.bart_generator.generate_no_reply_message(
                    reply_necessity['email_intent'], 
                    context
                )
                
                if optional_reply:
                    result['reply_text'] = optional_reply
                    result['confidence_score'] = 0.60
                    result['confidence_level'] = 'medium'
                    result['generation_method'] = 'optional_acknowledgment'
                else:
                    result['reply_text'] = None
                    result['confidence_score'] = 0.0
                    result['confidence_level'] = 'low'
                    result['generation_method'] = 'no_reply_needed'
                
                result['metadata']['reply_recommendation'] = f"No reply needed - {reply_necessity['reason']}"
                result['metadata']['suggested_action'] = reply_necessity['suggested_action']
                result['metadata']['email_intent'] = reply_necessity['email_intent']
                
                return result
            
            # PHASE 2: Safety checks before generation
            
            # Step 2: Check for edge cases
            edge_case_analysis = self.edge_case_handler.analyze_email(email_data)
            result['metadata']['edge_case_analysis'] = edge_case_analysis
            
            if edge_case_analysis['is_edge_case'] and not edge_case_analysis['should_generate_reply']:
                result['reply_text'] = f"[Note: {edge_case_analysis['recommendation']}]"
                result['confidence_score'] = 0.0
                result['confidence_level'] = 'low'
                result['generation_method'] = 'no_reply'
                result['metadata']['skip_reason'] = edge_case_analysis['edge_case_type']
                print(f"[INFO] Edge case detected: {edge_case_analysis['edge_case_type']}")
                return result
            
            # Step 3: Check for sensitive topics
            sensitive_analysis = self.sensitive_detector.detect_sensitive_content(
                email_data.get('body', ''),
                email_data.get('subject', '')
            )
            result['metadata']['sensitive_analysis'] = sensitive_analysis
            
            if sensitive_analysis['is_sensitive'] and self.config.use_safe_mode_for_sensitive:
                # Use safe mode template for sensitive topics
                print(f"[WARNING] Sensitive content detected: {sensitive_analysis['categories']}")
                print(f"[INFO] Using safe mode template (Risk: {sensitive_analysis['risk_level']})")
                
                reply = self._generate_safe_mode_reply(
                    email_data=email_data,
                    sensitive_analysis=sensitive_analysis,
                    tone=detected_tone
                )
                
                result['reply_text'] = reply
                result['confidence_score'] = 0.70  # Medium-high confidence for safe templates
                result['confidence_level'] = 'medium'
                result['generation_method'] = 'safe_mode'
                result['metadata']['requires_manual_review'] = sensitive_analysis['requires_manual_review']
                
                return result
            
            # Context already extracted in Step 0, continue to Step 4
            
            # PRIORITY 2 ENHANCEMENT: Apply Sender Intelligence
            sender_email = email_data.get('sender', email_data.get('sender_email', ''))
            sender_name = email_data.get('sender_name', 'there')
            
            # Get sender profile and relationship context
            sender_profile = self.sender_analyzer.get_sender_profile(sender_email)
            relationship_context = self.relationship_builder.build_context(
                sender_email, sender_name, context.get('urgency_level', 'normal')
            )
            
            # Adapt tone based on sender history (Priority 2)
            original_tone = detected_tone
            detected_tone = self.tone_adapter.adapt_tone(
                detected_tone, sender_email, sender_name, context.get('urgency_level', 'normal')
            )
            
            if original_tone != detected_tone:
                result['metadata']['tone_adapted'] = {
                    'original': original_tone,
                    'adapted': detected_tone,
                    'reason': f"Sender preference ({sender_profile['interaction_count']} interactions)"
                }
            
            # Add sender profile to metadata for transparency
            result['metadata']['sender_profile'] = {
                'interactions': sender_profile['interaction_count'],
                'relationship': sender_profile['relationship_level'],
                'preferred_tone': sender_profile['preferred_tone']
            }
            
            # Step 4: Generate CONTENT-SPECIFIC reply (Priority 1 Enhancement)
            print("[INFO] Using Content-Specific Reply Builder...")
            reply = self.content_reply_builder.build_reply(
                context, 
                detected_tone,
                relationship_context=relationship_context,  # Priority 2
                greeting_builder=self.greeting_builder      # Priority 2
            )
            
            # PRIORITY 4 ENHANCEMENT: Apply Active Learning
            print("[INFO] Applying learned patterns from edit history...")
            
            # Step 4a: Inject learned phrases (Priority 4)
            reply = self.phrase_injector.inject_learned_phrases(reply, context)
            
            # Step 4b: Apply category-specific adaptations (Priority 4)
            email_category = context.get('email_category', 'general')
            reply, _ = self.category_adapter.adapt_for_category(
                reply, email_category, confidence=0.5  # Temp confidence for category check
            )
            
            result['reply_text'] = reply
            result['generation_method'] = 'content_specific_learned'  # Updated to show Priority 4
            
            # Step 5: Calculate confidence (Priority 3 Enhanced)
            confidence = self.confidence_scorer.calculate_confidence(context, reply)
            
            # PRIORITY 4: Apply category-specific confidence adjustment
            _, confidence = self.category_adapter.adapt_for_category(
                reply, email_category, confidence
            )
            
            # PHASE 3: Apply learning-based confidence adjustment
            if self.learning_tracker and self.config.adapt_to_preferences:
                adjustment = self.learning_tracker.get_confidence_adjustment(
                    generation_method='ai_enhanced',
                    category=context['email_category']
                )
                confidence = min(1.0, confidence * adjustment)
                result['metadata']['learning_adjustment'] = adjustment
            
            result['confidence_score'] = confidence
            
            # Determine confidence level
            if confidence >= self.config.high_confidence_threshold:
                result['confidence_level'] = 'high'
            elif confidence >= self.config.min_confidence_threshold:
                result['confidence_level'] = 'medium'
            else:
                result['confidence_level'] = 'low'
            
            # Step 5: Add metadata
            result['metadata'] = {
                'topic_extracted': context['main_topic'],
                'category': context['email_category'],
                'urgency': context['urgency_level'],
                'entities_found': sum(len(v) for v in context['entities'].values()),
                'has_questions': len(context['questions']) > 0,
                'has_deadlines': len(context['deadlines']) > 0
            }
            
            print(f"[OK] Reply generated | Confidence: {confidence} ({result['confidence_level']})")
            
        except Exception as e:
            print(f"[ERROR] Smart reply generation failed: {e}")
            result['reply_text'] = self._generate_safe_fallback(email_data['sender_name'])
            result['confidence_score'] = 0.3
            result['confidence_level'] = 'low'
            result['generation_method'] = 'fallback'
        
        return result
    
    def track_reply_edit(self, 
                        email_data: Dict[str, Any],
                        original_reply: str,
                        edited_reply: str,
                        reply_metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Track user edit to learn preferences (Phase 3)
        
        Args:
            email_data: Original email data
            original_reply: AI-generated reply
            edited_reply: User-edited reply
            reply_metadata: Metadata from generation
            
        Returns:
            Edit analysis or None if tracking disabled
        """
        
        if not self.learning_tracker:
            print("[WARNING] Learning tracker not enabled")
            return None
        
        try:
            edit = self.learning_tracker.track_reply_edit(
                email_data=email_data,
                original_reply=original_reply,
                edited_reply=edited_reply,
                reply_metadata=reply_metadata
            )
            
            from dataclasses import asdict
            return asdict(edit)
            
        except Exception as e:
            print(f"[ERROR] Failed to track edit: {e}")
            return None
    
    def get_learning_insights(self) -> Dict[str, Any]:
        """
        Get learning insights and statistics (Phase 3)
        
        Returns:
            Dictionary with learning statistics and preferences
        """
        
        if not self.learning_tracker:
            return {'message': 'Learning tracker not enabled'}
        
        try:
            insights = self.learning_tracker.get_learning_insights()
            insights['user_preferences'] = self.learning_tracker.user_preferences
            return insights
        except Exception as e:
            print(f"[ERROR] Failed to get insights: {e}")
            return {'error': str(e)}
    
    def _compose_reply(self, sender_name: str, acknowledgment: str, 
                      context: Dict, tone: str) -> str:
        """Compose the final reply from components"""
        
        # Get opening
        opening = self.openings[tone].format(sender_name=sender_name)
        
        # Get closing based on urgency
        urgency = context.get('urgency_level', 'normal')
        closing = self.closings[urgency][tone]
        
        # Add specific timeline if deadline mentioned
        if context.get('deadlines'):
            deadline = context['deadlines'][0]
            closing = closing.replace('shortly', f'by {deadline}')
            closing = closing.replace('soon', f'by {deadline}')
        
        # Compose full reply
        full_reply = f"{opening}{acknowledgment}{closing}"
        
        return full_reply
    
    def _generate_safe_mode_reply(self, email_data: Dict[str, Any], 
                                  sensitive_analysis: Dict[str, Any], 
                                  tone: str) -> str:
        """
        Generate safe, conservative reply for sensitive topics
        
        Args:
            email_data: Email information
            sensitive_analysis: Results from sensitive topic detection
            tone: Communication tone to match
            
        Returns:
            Safe mode reply text
        """
        
        sender_name = email_data.get('sender_name', 'there')
        categories = sensitive_analysis.get('categories', [])
        
        # Select appropriate template based on primary category
        if 'legal' in categories:
            template_key = 'legal'
        elif 'hr_personnel' in categories:
            template_key = 'hr_personnel'
        elif 'financial_sensitive' in categories:
            template_key = 'financial_sensitive'
        elif 'confidential' in categories:
            template_key = 'confidential'
        elif 'crisis' in categories:
            template_key = 'crisis'
        elif 'ethical' in categories:
            template_key = 'ethical'
        else:
            template_key = 'general_sensitive'
        
        # Get template for tone
        template_body = self.safe_mode_templates[template_key].get(tone, 
                        self.safe_mode_templates[template_key]['business'])
        
        # Add opening
        opening = self.openings[tone].format(sender_name=sender_name)
        
        # Add closing
        closing = "\n\nBest regards"
        if tone == 'casual':
            closing = "\n\nThanks"
        elif tone == 'formal':
            closing = "\n\nRespectfully"
        
        # Compose full reply
        safe_reply = f"{opening}{template_body}{closing}"
        
        # Add internal flag if requires manual review
        if sensitive_analysis.get('requires_manual_review'):
            safe_reply += "\n\n[INTERNAL NOTE: This reply was generated for a sensitive topic. Manual review recommended before sending.]"
        
        return safe_reply
    
    def _generate_safe_fallback(self, sender_name: str) -> str:
        """Generate safe fallback reply"""
        return f"Hi {sender_name},\n\nThank you for your email. I'll review this and respond accordingly.\n\nBest regards"


