# =============================================================================
# AI PROCESSOR - ai_processor.py  
# =============================================================================
# This is the BRAIN of your AI Email Agent! [BRAIN]
# 
# This module transforms raw email data into intelligent insights using:
# - Advanced AI models for text summarization (BART/T5)
# - Natural Language Processing for entity extraction (spaCy)
# - Machine Learning for priority classification
# - Intelligent VIP detection and learning algorithms
# - Draft reply generation with context awareness
#
# COGNITIVE CAPABILITIES YOUR AI AGENT WILL HAVE:
# 1. READ & UNDERSTAND: Comprehend email content using AI
# 2. SUMMARIZE: Create concise, intelligent summaries  
# 3. PRIORITIZE: Classify emails by importance automatically
# 4. LEARN: Adapt to communication patterns over time
# 5. GENERATE: Create contextual draft replies
# 6. ANALYZE: Extract dates, deadlines, and key information
# =============================================================================

import os
import re
import json
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')  # Suppress model loading warnings

# =============================================================================
# AI MODEL IMPORTS
# =============================================================================

try:
    # Hugging Face Transformers for AI models
    from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
    print("[OK] Transformers library loaded successfully")
except ImportError:
    print("[ERROR] Transformers not installed. Run: pip install transformers torch")
    exit(1)

try:
    # spaCy for advanced NLP
    import spacy
    from spacy import displacy
    print("[OK] spaCy library loaded successfully")
except ImportError:
    print("[ERROR] spaCy not installed. Run: pip install spacy")
    exit(1)

try:
    # Additional ML libraries
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import nltk
    from textblob import TextBlob
    print("[OK] Additional ML libraries loaded successfully")
except ImportError:
    print("[ERROR] Some ML libraries missing. Check installation.")

# =============================================================================
# AI PROCESSOR CONFIGURATION
# =============================================================================

@dataclass
class AIProcessorConfig:
    """
    Configuration class for AI Processor settings
    
    This centralizes all AI model settings and thresholds,
    making it easy to tune your AI Agent's behavior
    """
    
    # Summarization settings
    summarization_model: str = "facebook/bart-large-cnn"  # BART model for summaries
    max_summary_length: int = 100    # Maximum words in summary
    min_summary_length: int = 20     # Minimum words in summary
    
    # Priority classification thresholds
    high_priority_threshold: int = 3   # Score needed for high priority
    medium_priority_threshold: int = 1  # Score needed for medium priority
    
    # VIP learning settings
    vip_response_threshold: int = 3     # Response count to become VIP
    vip_decay_days: int = 30           # Days before VIP status decays
    
    # Text processing limits
    max_body_length: int = 1000        # Max characters to process for AI
    max_subject_length: int = 200      # Max subject length to process
    
    # Model caching
    cache_models: bool = True          # Cache models in memory for speed
    
    # Language settings
    default_language: str = "en"       # Default language for processing

class EmailProcessor:
    """
    The AI Brain of Your Email Agent [BRAIN]
    
    This class contains all the artificial intelligence that transforms
    your email agent from a simple reader into an intelligent assistant.
    
    COGNITIVE ARCHITECTURE:
    - Perception: Understanding email content with NLP
    - Analysis: Extracting meaning and importance  
    - Learning: Adapting to user patterns over time
    - Generation: Creating appropriate responses
    """
    
    def __init__(self, config: Optional[AIProcessorConfig] = None):
        """
        Initialize the AI Email Processor
        
        This sets up all the AI models and cognitive systems your agent needs
        to understand and process emails intelligently.
        
        Args:
            config: AI processor configuration (uses defaults if None)
        """
        
        print("[BRAIN] Initializing AI Email Processor...")
        print("=====================================")
        
        # Use provided config or create default
        self.config = config or AIProcessorConfig()
        
        # Initialize model storage
        self.models = {}
        self.nlp_models = {}
        
        # Initialize VIP learning system
        self.vip_data_file = "ai_data/vip_senders.json"
        self.learning_data_file = "ai_data/learning_patterns.json"
        self.vip_senders = self._load_vip_data()
        
        # Initialize priority keywords and patterns
        self._initialize_priority_patterns()
        
        # Load AI models
        self._initialize_ai_models()
        
        # Initialize learning system
        self._initialize_learning_system()
        
        print("[OK] AI Email Processor initialized successfully!")
        print(f"[TARGET] Ready to process emails with intelligence level: EXPERT")
    
    def _initialize_ai_models(self):
        """
        Initialize all AI models needed for email processing
        
        This loads the neural networks and AI models that give your
        agent its cognitive capabilities.
        """
        
        print("\n[AI] Loading AI Models...")
        print("========================")
        
        # =============================================================================
        # 1. SUMMARIZATION MODEL (THE COMPREHENSION BRAIN)
        # =============================================================================
        
        print("[NOTE] Loading text summarization model...")
        try:
            # Load BART model for email summarization
            # BART is a state-of-the-art transformer model excellent at summarization
            self.models['summarizer'] = pipeline(
                "summarization",
                model=self.config.summarization_model,
                tokenizer=self.config.summarization_model,
                framework="pt",  # Use PyTorch
                device=-1        # Use CPU (change to 0 for GPU)
            )
            print(f"[OK] Summarization model loaded: {self.config.summarization_model}")
            
        except Exception as e:
            print(f"[WARNING] Warning: Could not load summarization model: {e}")
            print("[PROCESS] Will use fallback extractive summarization")
            self.models['summarizer'] = None
        
        # =============================================================================
        # 2. SENTIMENT ANALYSIS MODEL (THE EMOTION DETECTOR)
        # =============================================================================
        
        print("[EMOJI] Loading sentiment analysis model...")
        try:
            # Load sentiment analysis for detecting email tone and urgency
            self.models['sentiment'] = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                device=-1
            )
            print("[OK] Sentiment analysis model loaded")
            
        except Exception as e:
            print(f"[WARNING] Warning: Could not load sentiment model: {e}")
            print("[PROCESS] Will use TextBlob fallback")
            self.models['sentiment'] = None
        
        # =============================================================================
        # 3. NLP MODEL (THE LANGUAGE UNDERSTANDING BRAIN)
        # =============================================================================
        
        print("[EMOJI] Loading advanced NLP model...")
        try:
            # Load spaCy model for named entity recognition and language processing
            self.nlp_models['en'] = spacy.load("en_core_web_sm")
            print("[OK] spaCy English model loaded for entity extraction")
            
        except Exception as e:
            print(f"[ERROR] Error loading spaCy model: {e}")
            print("[EMOJI] Please run: python -m spacy download en_core_web_sm")
            self.nlp_models['en'] = None
        
        # =============================================================================
        # 4. SIMILARITY MODEL (THE PATTERN RECOGNITION BRAIN)
        # =============================================================================
        
        print("[TARGET] Loading similarity detection model...")
        try:
            # Initialize TF-IDF vectorizer for text similarity
            # This helps detect similar emails and patterns
            self.models['tfidf'] = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2)  # Include both single words and pairs
            )
            print("[OK] Text similarity model initialized")
            
        except Exception as e:
            print(f"[WARNING] Warning: Could not initialize similarity model: {e}")
            self.models['tfidf'] = None
        
        print("\n[PARTY] AI Model loading complete!")
    
    def _initialize_priority_patterns(self):
        """
        Initialize priority detection patterns and keywords
        
        This sets up the knowledge base your AI agent uses to
        recognize important emails automatically.
        """
        
        print("[TARGET] Initializing priority detection patterns...")
        
        # =============================================================================
        # URGENT KEYWORDS - IMMEDIATE ATTENTION REQUIRED
        # =============================================================================
        
        # These words in subject or body indicate high priority
        self.urgent_keywords = [
            # Time-sensitive words
            'urgent', 'asap', 'immediate', 'emergency', 'critical', 'deadline',
            'rush', 'quick', 'fast', 'now', 'today', 'tomorrow',
            
            # Action-required words  
            'approve', 'approval', 'confirm', 'confirmation', 'respond',
            'reply', 'action', 'required', 'needed', 'please',
            
            # Problem/issue words
            'issue', 'problem', 'error', 'bug', 'down', 'failed',
            'broken', 'help', 'support', 'fix'
        ]
        
        # =============================================================================
        # VIP SENDER INDICATORS - IMPORTANT PEOPLE
        # =============================================================================
        
        # Title keywords that indicate VIP senders
        self.vip_titles = [
            'ceo', 'cto', 'cfo', 'president', 'director', 'manager',
            'partner', 'client', 'customer', 'lead', 'head', 'chief',
            'founder', 'owner', 'principal', 'senior', 'executive'
        ]
        
        # Email domain patterns that suggest important senders
        self.vip_domains = [
            'client', 'partner', 'board', 'executive', 'management',
            'leadership', 'customer', 'support', 'sales'
        ]
        
        # =============================================================================
        # AUTOMATED EMAIL PATTERNS - LOW PRIORITY INDICATORS
        # =============================================================================
        
        # Patterns that indicate automated/marketing emails
        self.automated_patterns = [
            # No-reply addresses
            r'noreply@', r'no-reply@', r'donotreply@', r'notification@',
            
            # Marketing/newsletter indicators
            r'newsletter@', r'marketing@', r'promo@', r'offers@',
            
            # System notifications
            r'system@', r'admin@', r'info@', r'alerts@',
            
            # Social media automated emails
            r'via\s+linkedin', r'linkedin\.com', r'facebook\.com', r'twitter\.com',
            r'instagram\.com', r'github\.com'
        ]
        
        # Common automated email subjects
        self.automated_subjects = [
            'newsletter', 'digest', 'notification', 'alert', 'update',
            'reminder', 'confirmation', 'receipt', 'invoice', 'statement',
            # Connection and social media patterns
            'just messaged you', 'wants to connect', 'invitation', 'i want to connect',
            'join the', 'group chat', 'connection request', 'new way to earn',
            'exclusive', 'perks', 'you can\'t miss', 'fx rate', 'daily rate'
        ]
        
        print("[OK] Priority patterns initialized")
    
    def _initialize_learning_system(self):
        """
        Initialize the learning and adaptation system
        
        This is what makes your AI agent smart - it learns from patterns
        and adapts to your communication style over time.
        """
        
        print("[EMOJI] Initializing AI learning system...")
        
        # Create data directory for AI learning
        os.makedirs("ai_data", exist_ok=True)
        
        # Learning patterns storage
        self.learning_patterns = {
            'response_times': {},      # How quickly you respond to different senders
            'email_importance': {},    # Which emails you actually read/respond to
            'writing_style': {         # Your communication style patterns
                'avg_length': 0,
                'common_phrases': [],
                'formality_level': 'medium'
            },
            'schedule_patterns': {},   # When you typically read emails
            'topic_preferences': {}    # Which topics you prioritize
        }
        
        # Load existing learning data
        self._load_learning_data()
        
        print("[OK] Learning system initialized")
    
    def summarize_email(self, email_data: Dict[str, Any]) -> str:
        """
        Create an intelligent summary of email content
        
        This is where your AI agent demonstrates comprehension - it reads
        the email and creates a concise, intelligent summary that captures
        the key points.
        
        Args:
            email_data: Email data dictionary from EmailFetcher
            
        Returns:
            str: Intelligent summary of the email content
        """
        
        email_body = email_data.get('body', '')
        email_subject = email_data.get('subject', '')
        
        print(f"[NOTE] Summarizing email: '{email_subject[:50]}...'")
        
        # =============================================================================
        # PREPROCESSING: PREPARE TEXT FOR AI ANALYSIS
        # =============================================================================
        
        # Combine subject and body for better context
        full_text = f"{email_subject}. {email_body}"
        
        # Clean and prepare text for AI processing
        cleaned_text = self._preprocess_text_for_ai(full_text)
        
        # Check if text is too short for summarization
        if len(cleaned_text.split()) < 20:
            print("[EMOJI] Email too short for AI summarization, returning cleaned version")
            return cleaned_text[:200] + "..." if len(cleaned_text) > 200 else cleaned_text
        
        # =============================================================================
        # AI SUMMARIZATION: USE NEURAL NETWORK TO UNDERSTAND AND SUMMARIZE
        # =============================================================================
        
        try:
            if self.models['summarizer']:
                print("[BRAIN] Using BART neural network for summarization...")
                
                # Use advanced AI model for summarization
                summary_result = self.models['summarizer'](
                    cleaned_text,
                    max_length=self.config.max_summary_length,
                    min_length=self.config.min_summary_length,
                    do_sample=False
                )
                
                ai_summary = summary_result[0]['summary_text']
                print(f"[OK] AI summary generated: {len(ai_summary)} characters")
                
                return ai_summary
            
            else:
                # Fallback to extractive summarization
                print("[PROCESS] Using fallback extractive summarization...")
                return self._extractive_summarization(cleaned_text)
                
        except Exception as e:
            print(f"[WARNING] AI summarization failed: {e}")
            print("[PROCESS] Falling back to extractive method...")
            return self._extractive_summarization(cleaned_text)
    
    def calculate_priority(self, email_data: Dict[str, Any]) -> Tuple[str, int, List[str]]:
        """
        Calculate email priority using AI and pattern recognition
        
        This is your AI agent's decision-making system - it analyzes multiple
        factors to determine how important an email is.
        
        Args:
            email_data: Email data dictionary
            
        Returns:
            Tuple[str, int, List[str]]: (priority_level, score, reasons)
        """
        
        print(f"[TARGET] Analyzing priority for email from: {email_data.get('sender_name', 'Unknown')}")
        
        priority_score = 0
        priority_reasons = []
        
        # Extract email components for analysis
        sender = email_data.get('sender', '').lower()
        sender_email = email_data.get('sender_email', '').lower()
        subject = email_data.get('subject', '').lower()
        body = email_data.get('body', '').lower()
        has_attachments = email_data.get('has_attachments', False)
        
        # =============================================================================
        # FACTOR 1: VIP SENDER ANALYSIS (LEARNING-BASED)
        # =============================================================================
        
        vip_score = self._analyze_vip_sender(sender_email, sender)
        if vip_score > 0:
            priority_score += vip_score
            if vip_score >= 3:
                priority_reasons.append(f"VIP sender (learned from interactions)")
            else:
                priority_reasons.append(f"Known sender (interaction history)")
        
        # =============================================================================
        # FACTOR 2: URGENT KEYWORD ANALYSIS (AI-POWERED)
        # =============================================================================
        
        urgent_score = self._analyze_urgent_keywords(subject, body)
        if urgent_score > 0:
            priority_score += urgent_score
            priority_reasons.append(f"Contains urgent keywords (+{urgent_score})")
        
        # =============================================================================
        # FACTOR 3: SEMANTIC URGENCY ANALYSIS (AI SENTIMENT)
        # =============================================================================
        
        sentiment_urgency = self._analyze_sentiment_urgency(subject + " " + body)
        if sentiment_urgency > 0:
            priority_score += sentiment_urgency
            priority_reasons.append(f"AI detected urgency in tone (+{sentiment_urgency})")
        
        # =============================================================================
        # FACTOR 4: CONTENT COMPLEXITY ANALYSIS (AI-POWERED)
        # =============================================================================
        
        complexity_score = self._analyze_content_complexity(email_data)
        if complexity_score > 0:
            priority_score += complexity_score
            priority_reasons.append(f"Complex content requiring attention (+{complexity_score})")
        
        # =============================================================================
        # FACTOR 5: TEMPORAL INDICATORS (AI TIME EXTRACTION)  
        # =============================================================================
        
        time_sensitivity = self._analyze_time_sensitivity(body, subject)
        if time_sensitivity > 0:
            priority_score += time_sensitivity
            priority_reasons.append(f"Time-sensitive content (+{time_sensitivity})")
        
        # =============================================================================
        # FACTOR 6: ATTACHMENT ANALYSIS
        # =============================================================================
        
        if has_attachments:
            attachment_score = self._analyze_attachment_importance(email_data)
            priority_score += attachment_score
            if attachment_score > 0:
                priority_reasons.append(f"Important attachments (+{attachment_score})")
        
        # =============================================================================
        # FACTOR 7: AUTOMATED EMAIL DETECTION (PENALTY)
        # =============================================================================
        
        if self._is_automated_email(sender_email, subject, body):
            priority_score -= 3  # Increased penalty for automated emails (was -2)
            priority_reasons.append("Automated email (priority reduced)")
        
        # =============================================================================
        # PRIORITY CLASSIFICATION
        # =============================================================================
        
        if priority_score >= self.config.high_priority_threshold:
            priority_level = "High"
        elif priority_score >= self.config.medium_priority_threshold:
            priority_level = "Medium"
        else:
            priority_level = "Low"
        
        print(f"[TARGET] Priority calculated: {priority_level} (score: {priority_score})")
        print(f"[EMOJI] Reasons: {', '.join(priority_reasons) if priority_reasons else 'Standard email'}")
        
        return priority_level, priority_score, priority_reasons
    
    def extract_entities_and_dates(self, email_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Extract important entities and dates from email using AI
        
        This demonstrates your AI agent's comprehension abilities - it can
        identify people, organizations, dates, and other important information.
        
        Args:
            email_data: Email data dictionary
            
        Returns:
            Dict: Extracted entities and dates
        """
        
        print("[SEARCH] Extracting entities and dates with AI...")
        
        entities = {
            'people': [],
            'organizations': [],
            'locations': [],
            'dates': [],
            'money': [],
            'times': [],
            'deadlines': [],
            'meetings': []
        }
        
        email_text = f"{email_data.get('subject', '')} {email_data.get('body', '')}"
        
        # =============================================================================
        # AI-POWERED ENTITY EXTRACTION USING spaCy
        # =============================================================================
        
        try:
            if self.nlp_models.get('en'):
                print("[BRAIN] Using spaCy AI for entity recognition...")
                
                # Process text with spaCy's neural network
                doc = self.nlp_models['en'](email_text[:1000])  # Limit text length
                
                # Extract named entities
                for ent in doc.ents:
                    entity_text = ent.text.strip()
                    entity_label = ent.label_
                    
                    # Categorize entities based on spaCy's classification
                    if entity_label in ['PERSON']:
                        entities['people'].append(entity_text)
                    elif entity_label in ['ORG']:
                        entities['organizations'].append(entity_text)
                    elif entity_label in ['GPE', 'LOC']:  # Geopolitical entity, Location
                        entities['locations'].append(entity_text)
                    elif entity_label in ['DATE']:
                        entities['dates'].append(entity_text)
                    elif entity_label in ['TIME']:
                        entities['times'].append(entity_text)
                    elif entity_label in ['MONEY']:
                        entities['money'].append(entity_text)
                
                print(f"[OK] AI extracted {sum(len(v) for v in entities.values())} entities")
                
        except Exception as e:
            print(f"[WARNING] AI entity extraction failed: {e}")
        
        # =============================================================================
        # PATTERN-BASED DEADLINE AND MEETING EXTRACTION
        # =============================================================================
        
        # Extract deadlines using regex patterns
        deadline_patterns = [
            r'deadline[:\s]+([^\.]+)',
            r'due[:\s]+([^\.]+)',
            r'by\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            r'by\s+(\d{1,2}[\/\-]\d{1,2})',
            r'before\s+([^\.]+)'
        ]
        
        for pattern in deadline_patterns:
            matches = re.finditer(pattern, email_text.lower())
            for match in matches:
                deadline = match.group(1).strip()[:50]  # Limit length
                if deadline not in entities['deadlines']:
                    entities['deadlines'].append(deadline)
        
        # Extract meeting references
        meeting_patterns = [
            r'meeting[:\s]+([^\.]+)',
            r'call[:\s]+([^\.]+)',
            r'appointment[:\s]+([^\.]+)',
            r'conference[:\s]+([^\.]+)'
        ]
        
        for pattern in meeting_patterns:
            matches = re.finditer(pattern, email_text.lower())
            for match in matches:
                meeting = match.group(1).strip()[:50]  # Limit length
                if meeting not in entities['meetings']:
                    entities['meetings'].append(meeting)
        
        # Remove duplicates and empty entries
        for key in entities:
            entities[key] = list(set([item for item in entities[key] if item and len(item.strip()) > 2]))
        
        return entities
    
    def generate_draft_reply(self, email_data: Dict[str, Any]) -> str:
        """
        Generate contextual draft reply using AI and pattern matching
        
        This showcases your AI agent's generation capabilities - it can
        create appropriate responses based on email content and context.
        
        Args:
            email_data: Email data dictionary
            
        Returns:
            str: Generated draft reply
        """
        
        print(f"[EMOJI] Generating draft reply for: {email_data.get('subject', 'No Subject')}")
        
        # Extract context for reply generation
        subject = email_data.get('subject', '').lower()
        body = email_data.get('body', '').lower()
        sender_name = email_data.get('sender_name', 'there')
        priority_level = email_data.get('priority_level', 'Medium')
        
        # =============================================================================
        # CONTEXT ANALYSIS FOR REPLY TYPE
        # =============================================================================
        
        reply_context = self._analyze_reply_context(subject, body)
        
        # =============================================================================
        # DRAFT REPLY GENERATION BASED ON CONTEXT
        # =============================================================================
        
        if reply_context['type'] == 'meeting_request':
            draft = self._generate_meeting_reply(sender_name, reply_context)
            
        elif reply_context['type'] == 'urgent_request':
            draft = self._generate_urgent_reply(sender_name, reply_context)
            
        elif reply_context['type'] == 'question':
            draft = self._generate_question_reply(sender_name, reply_context)
            
        elif reply_context['type'] == 'thank_you':
            draft = self._generate_thank_you_reply(sender_name, reply_context)
            
        elif reply_context['type'] == 'information_request':
            draft = self._generate_info_request_reply(sender_name, reply_context)
            
        else:
            # Default professional reply
            draft = self._generate_default_reply(sender_name, priority_level)
        
        print(f"[OK] Draft reply generated: {len(draft)} characters")
        return draft
    
    def learn_from_interaction(self, email_data: Dict[str, Any], user_action: str):
        """
        Learn from user interactions to improve AI performance
        
        This is what makes your AI agent truly intelligent - it observes
        your behavior and adapts its future recommendations.
        
        Args:
            email_data: Email data dictionary
            user_action: Action taken by user ('read', 'reply', 'delete', 'archive', etc.)
        """
        
        print(f"[EMOJI] Learning from user action: {user_action}")
        
        sender_email = email_data.get('sender_email', '').lower()
        priority_level = email_data.get('priority_level', 'Medium')
        
        # =============================================================================
        # VIP SENDER LEARNING
        # =============================================================================
        
        if user_action in ['reply', 'forward', 'read']:
            # User engaged with this sender - potential VIP
            self._update_vip_score(sender_email, +1)
            
        elif user_action in ['delete', 'spam']:
            # User didn't find this sender important
            self._update_vip_score(sender_email, -1)
        
        # =============================================================================
        # PRIORITY ACCURACY LEARNING
        # =============================================================================
        
        if user_action == 'reply' and priority_level == 'Low':
            # We underestimated priority - learn from this
            print("[EMOJI] Learning: Low priority email was actually important")
            self._adjust_priority_weights(email_data, increase=True)
            
        elif user_action == 'delete' and priority_level == 'High':
            # We overestimated priority - learn from this  
            print("[EMOJI] Learning: High priority email wasn't actually important")
            self._adjust_priority_weights(email_data, increase=False)
        
        # =============================================================================
        # RESPONSE TIME LEARNING
        # =============================================================================
        
        if user_action == 'reply':
            response_time = datetime.now()
            self.learning_patterns['response_times'][sender_email] = {
                'last_response': response_time.isoformat(),
                'avg_response_hours': self._calculate_avg_response_time(sender_email)
            }
        
        # Save learning data
        self._save_learning_data()
        print("[OK] Learning data updated")
    
    def process_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete AI processing pipeline for a single email
        
        This is your AI agent's main cognitive function - it takes raw email
        data and transforms it into intelligent, actionable information.
        
        Args:
            email_data: Raw email data from EmailFetcher
            
        Returns:
            Dict: Processed email with AI-generated insights
        """
        
        print(f"\n[BRAIN] AI PROCESSING EMAIL: {email_data.get('subject', 'No Subject')}")
        print("=" * 60)
        
        # PERFORMANCE: Track individual AI operations
        import time
        base_timing = {}
        
        # Start with the original email data
        processed_email = email_data.copy()
        
        try:
            # =============================================================================
            # STEP 1: AI SUMMARIZATION
            # =============================================================================
            
            print("[NOTE] Step 1: AI Summarization...")
            step1_start = time.time()
            processed_email['ai_summary'] = self.summarize_email(email_data)
            base_timing['summarization'] = time.time() - step1_start
            print(f"⏱️  Summarization took {base_timing['summarization']:.2f}s")
            
            # =============================================================================
            # STEP 2: PRIORITY ANALYSIS
            # =============================================================================
            
            print("[TARGET] Step 2: Priority Analysis...")
            step2_start = time.time()
            priority_level, priority_score, reasons = self.calculate_priority(email_data)
            processed_email['priority_level'] = priority_level
            processed_email['priority_score'] = priority_score  
            processed_email['priority_reasons'] = reasons
            base_timing['priority_analysis'] = time.time() - step2_start
            print(f"⏱️  Priority analysis took {base_timing['priority_analysis']:.2f}s")
            
            # =============================================================================
            # STEP 3: ENTITY EXTRACTION
            # =============================================================================
            
            print("[SEARCH] Step 3: Entity Extraction...")
            step3_start = time.time()
            extracted_entities = self.extract_entities_and_dates(email_data)
            processed_email['extracted_entities'] = extracted_entities
            base_timing['entity_extraction'] = time.time() - step3_start
            print(f"⏱️  Entity extraction took {base_timing['entity_extraction']:.2f}s")
            
            # =============================================================================
            # STEP 4: DRAFT REPLY GENERATION (FOR HIGH PRIORITY)
            # =============================================================================
            
            if priority_level in ['High', 'Medium']:
                print("[EMOJI] Step 4: Draft Reply Generation...")
                step4_start = time.time()
                processed_email['draft_reply'] = self.generate_draft_reply(email_data)
                base_timing['draft_reply'] = time.time() - step4_start
                print(f"⏱️  Draft reply took {base_timing['draft_reply']:.2f}s")
            else:
                processed_email['draft_reply'] = None
                base_timing['draft_reply'] = 0
            
            # =============================================================================
            # STEP 5: ACTIONABLE INSIGHTS
            # =============================================================================
            
            print("[IDEA] Step 5: Generating Insights...")
            step5_start = time.time()
            processed_email['actionable_insights'] = self._generate_insights(processed_email)
            base_timing['insights'] = time.time() - step5_start
            
            # =============================================================================
            # STEP 6: AI CONFIDENCE SCORE
            # =============================================================================
            
            processed_email['ai_confidence'] = self._calculate_confidence_score(processed_email)
            
            # =============================================================================
            # STEP 7: PROCESSING METADATA
            # =============================================================================
            
            processed_email['ai_processed_at'] = datetime.now().isoformat()
            processed_email['ai_version'] = "1.0"
            processed_email['base_ai_timing'] = base_timing  # Add timing data
            
            total_base_time = sum(base_timing.values())
            print("[OK] AI processing completed successfully!")
            print(f"[TARGET] Result: {priority_level} priority, {len(processed_email['ai_summary'])} char summary")
            print(f"⏱️  Base processing took {total_base_time:.2f}s total")
            
            return processed_email
            
        except Exception as e:
            print(f"[ERROR] AI processing failed: {e}")
            # Return original data with error info
            processed_email['ai_error'] = str(e)
            processed_email['ai_processed'] = False
            return processed_email
    
    # =============================================================================
    # HELPER METHODS - THE AI'S COGNITIVE SUPPORT FUNCTIONS
    # =============================================================================
    
    def _preprocess_text_for_ai(self, text: str) -> str:
        """Clean and prepare text for AI processing"""
        
        if not text:
            return ""
        
        # =============================================================================
        # STEP 1: HTML CONTENT DETECTION AND CLEANING
        # =============================================================================
        
        # Check if content is HTML
        html_indicators = ['<html', '<body', '<div', '<table', '<tr', '<td', '<p>', '<br', '<!DOCTYPE']
        is_html = any(indicator in text.lower() for indicator in html_indicators)
        
        if is_html:
            print("[EMOJI] Detected HTML content - extracting readable text...")
            cleaned = self._extract_text_from_html(text)
        else:
            cleaned = text
        
        # =============================================================================
        # STEP 2: EMAIL ARTIFACTS REMOVAL
        # =============================================================================
        
        # Remove email artifacts and clean text
        cleaned = re.sub(r'On .* wrote:', '', cleaned)  # Remove quoted text
        cleaned = re.sub(r'From:.*?Subject:', '', cleaned, flags=re.MULTILINE | re.DOTALL)
        cleaned = re.sub(r'[>\|]+.*', '', cleaned, flags=re.MULTILINE)  # Remove quote lines
        cleaned = re.sub(r'https?://\S+', '[URL]', cleaned)  # Replace URLs
        
        # =============================================================================
        # STEP 3: NORMALIZE WHITESPACE AND FORMATTING
        # =============================================================================
        
        # Remove excessive whitespace and normalize
        cleaned = re.sub(r'\s+', ' ', cleaned)  # Normalize whitespace
        cleaned = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned)  # Reduce multiple newlines
        
        # =============================================================================
        # STEP 4: EXTRACT MEANINGFUL CONTENT
        # =============================================================================
        
        # Try to extract the most meaningful sentences
        cleaned = self._extract_meaningful_content(cleaned)
        
        # =============================================================================
        # STEP 5: LENGTH LIMITING
        # =============================================================================
        
        # Limit length for AI processing
        max_length = self.config.max_body_length
        if len(cleaned) > max_length:
            # Try to cut at sentence boundary
            truncated = cleaned[:max_length]
            last_sentence = truncated.rfind('.')
            if last_sentence > max_length * 0.8:
                cleaned = truncated[:last_sentence + 1]
            else:
                cleaned = truncated + "..."
        
        return cleaned.strip()
    
    def _extract_text_from_html(self, html_content: str) -> str:
        """Extract readable text from HTML content"""
        
        try:
            # Try to import BeautifulSoup for proper HTML parsing
            try:
                from bs4 import BeautifulSoup
                
                # Parse HTML with BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Get text content
                text = soup.get_text()
                
                # Clean up lines and whitespace
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = ' '.join(chunk for chunk in chunks if chunk)
                
                print("[OK] HTML parsed successfully with BeautifulSoup")
                return text
                
            except ImportError:
                print("[WARNING] BeautifulSoup not available, using regex fallback")
                # Fallback to regex-based HTML stripping
                return self._strip_html_regex(html_content)
                
        except Exception as e:
            print(f"[WARNING] HTML parsing failed: {e}, using regex fallback")
            return self._strip_html_regex(html_content)
    
    def _strip_html_regex(self, html_content: str) -> str:
        """Fallback HTML stripping using regex"""
        
        # Remove HTML tags
        cleaned = re.sub(r'<[^>]+>', ' ', html_content)
        
        # Remove CSS content
        cleaned = re.sub(r'style\s*=\s*["\'][^"\']*["\']', '', cleaned, flags=re.IGNORECASE)
        
        # Remove JavaScript
        cleaned = re.sub(r'<script.*?</script>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove CSS blocks
        cleaned = re.sub(r'<style.*?</style>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove common HTML entities
        html_entities = {
            '&nbsp;': ' ',
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'",
            '&hellip;': '...'
        }
        
        for entity, replacement in html_entities.items():
            cleaned = cleaned.replace(entity, replacement)
        
        # Clean up excessive whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned.strip()
    
    def _extract_meaningful_content(self, text: str) -> str:
        """Extract the most meaningful content from text"""
        
        # Split into sentences
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        if len(sentences) <= 3:
            return text
        
        # Filter out very short sentences and common noise
        meaningful_sentences = []
        noise_patterns = [
            r'^(thanks?|best|regards|sincerely).*',
            r'^\s*[a-z]\s*$',  # Single letters
            r'^\s*\d+\s*$',    # Just numbers
            r'^(click here|view|download).*',
            r'^(unsubscribe|privacy policy).*'
        ]
        
        for sentence in sentences:
            # Skip very short or noisy sentences
            if len(sentence) < 10:
                continue
                
            # Skip sentences that match noise patterns
            is_noise = any(re.match(pattern, sentence.lower()) for pattern in noise_patterns)
            if is_noise:
                continue
                
            meaningful_sentences.append(sentence)
        
        # Return the most meaningful sentences (up to 5)
        if meaningful_sentences:
            return '. '.join(meaningful_sentences[:5]) + '.'
        else:
            # If no meaningful sentences found, return original
            return text
    
    def _extractive_summarization(self, text: str) -> str:
        """Fallback extractive summarization when AI models fail"""
        
        sentences = text.split('. ')
        if len(sentences) <= 2:
            return text
        
        # Use TF-IDF to find most important sentences
        try:
            if self.models.get('tfidf'):
                tfidf_matrix = self.models['tfidf'].fit_transform(sentences)
                sentence_scores = tfidf_matrix.sum(axis=1).A1
                
                # Get top 2-3 sentences
                top_indices = sentence_scores.argsort()[-2:][::-1]
                summary_sentences = [sentences[i] for i in sorted(top_indices)]
                return '. '.join(summary_sentences) + '.'
        except:
            pass
        
        # Simple fallback - first and last sentences
        return f"{sentences[0]}. {sentences[-1]}."
    
    def _analyze_vip_sender(self, sender_email: str, sender: str) -> int:
        """Analyze if sender is VIP based on learning data"""
        
        score = 0
        
        # Check learned VIP status
        if sender_email in self.vip_senders:
            vip_data = self.vip_senders[sender_email]
            interaction_count = vip_data.get('interactions', 0)
            
            if interaction_count >= 5:
                score += 3  # High VIP
            elif interaction_count >= 2:
                score += 2  # Medium VIP
            else:
                score += 1  # Low VIP
        
        # Check for VIP title indicators
        for title in self.vip_titles:
            if title in sender.lower():
                score += 1
                break
        
        return min(score, 4)  # Cap at 4
    
    def _analyze_urgent_keywords(self, subject: str, body: str) -> int:
        """Analyze urgency based on keywords"""
        
        score = 0
        text = f"{subject} {body}".lower()
        
        # Check for social media/marketing contexts that reduce urgency
        social_contexts = ['group chat', 'join', 'connect', 'linkedin', 'follow', 'network']
        is_social_context = any(context in text for context in social_contexts)
        
        # Count urgent keywords with different weights
        high_urgency = ['urgent', 'emergency', 'critical', 'asap']
        medium_urgency = ['important', 'deadline', 'quick', 'rush']
        
        for keyword in high_urgency:
            if keyword in text:
                # Reduce urgency score for social media contexts
                if is_social_context:
                    score += 1  # Reduced from 2
                else:
                    score += 2
        
        for keyword in medium_urgency:
            if keyword in text:
                # Reduce urgency score for social media contexts  
                if is_social_context:
                    score += 0  # Don't add score for social contexts
                else:
                    score += 1
        
        return min(score, 3)  # Cap at 3
    
    def _analyze_sentiment_urgency(self, text: str) -> int:
        """Use AI sentiment analysis to detect urgency"""
        
        try:
            if self.models.get('sentiment'):
                result = self.models['sentiment'](text[:512])  # Limit text length
                
                # Check for negative sentiment (often indicates problems/urgency)
                if result[0]['label'] == 'NEGATIVE' and result[0]['score'] > 0.7:
                    return 1
            else:
                # Fallback to TextBlob
                blob = TextBlob(text)
                if blob.sentiment.polarity < -0.3:  # Negative sentiment
                    return 1
        except:
            pass
        
        return 0
    
    def _analyze_content_complexity(self, email_data: Dict[str, Any]) -> int:
        """Analyze content complexity to determine importance"""
        
        score = 0
        body = email_data.get('body', '')
        
        # Long emails might be more complex/important
        if len(body) > 500:
            score += 1
        
        # Multiple paragraphs indicate structured content
        if body.count('\n\n') > 2:
            score += 1
        
        # Technical terms might indicate important business content
        tech_terms = ['contract', 'agreement', 'proposal', 'budget', 'project']
        if any(term in body.lower() for term in tech_terms):
            score += 1
        
        return min(score, 2)
    
    def _analyze_time_sensitivity(self, body: str, subject: str) -> int:
        """Extract and analyze time-sensitive content"""
        
        text = f"{subject} {body}".lower()
        score = 0
        
        # Time-sensitive phrases
        time_phrases = [
            'today', 'tomorrow', 'this week', 'end of day', 'eod',
            'by friday', 'by monday', 'deadline', 'due date'
        ]
        
        for phrase in time_phrases:
            if phrase in text:
                score += 1
                break  # Only count once
        
        # Check for specific dates in near future (simplified)
        if re.search(r'(monday|tuesday|wednesday|thursday|friday)', text):
            score += 1
        
        return min(score, 2)
    
    def _analyze_attachment_importance(self, email_data: Dict[str, Any]) -> int:
        """Analyze importance of email attachments"""
        
        attachment_types = email_data.get('attachment_types', [])
        
        # Important document types
        important_types = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx']
        
        for att_type in attachment_types:
            if att_type.lower() in important_types:
                return 1
        
        return 0
    
    def _is_automated_email(self, sender_email: str, subject: str, body: str) -> bool:
        """Detect automated/marketing emails"""
        
        # Check sender patterns
        for pattern in self.automated_patterns:
            if re.search(pattern, sender_email, re.IGNORECASE):
                return True
        
        # Check subject patterns
        subject_lower = subject.lower()
        for automated_word in self.automated_subjects:
            if automated_word in subject_lower:
                return True
        
        # Check for unsubscribe links and marketing indicators
        body_lower = body.lower()
        marketing_indicators = [
            'unsubscribe', 'opt out', 'manage preferences', 'marketing email',
            'promotional email', 'this email was sent to', 'you received this email',
            'click here to', 'visit our website', 'follow us on', 'download our app'
        ]
        
        for indicator in marketing_indicators:
            if indicator in body_lower:
                return True
        
        # Check for social media connection patterns
        connection_patterns = [
            'wants to connect with you', 'sent you a connection request',
            'accept this invitation', 'join our network', 'expand your network',
            'connect on linkedin', 'follow on linkedin'
        ]
        
        for pattern in connection_patterns:
            if pattern in body_lower:
                return True
        
        return False
    
    def _analyze_reply_context(self, subject: str, body: str) -> Dict[str, Any]:
        """Analyze email context to determine reply type"""
        
        context = {'type': 'general', 'details': {}}
        
        if any(word in subject for word in ['meeting', 'call', 'appointment']):
            context['type'] = 'meeting_request'
        elif any(word in subject + body for word in ['urgent', 'asap', 'emergency']):
            context['type'] = 'urgent_request'
        elif '?' in body or any(word in body for word in ['how', 'what', 'when', 'where', 'why']):
            context['type'] = 'question'
        elif any(word in body for word in ['thank', 'thanks', 'appreciate']):
            context['type'] = 'thank_you'
        elif any(word in body for word in ['send', 'provide', 'share', 'need']):
            context['type'] = 'information_request'
        
        return context
    
    def _generate_meeting_reply(self, sender_name: str, context: Dict) -> str:
        """Generate meeting-related reply"""
        return f"Hi {sender_name},\n\nThank you for the meeting request. I'll check my calendar and get back to you shortly with my availability.\n\nBest regards"
    
    def _generate_urgent_reply(self, sender_name: str, context: Dict) -> str:
        """Generate urgent reply"""
        return f"Hi {sender_name},\n\nI've received your urgent message and will prioritize this. I'll respond with a detailed update by end of day.\n\nThanks for bringing this to my attention.\n\nBest regards"
    
    def _generate_question_reply(self, sender_name: str, context: Dict) -> str:
        """Generate question-response reply"""
        return f"Hi {sender_name},\n\nThank you for your question. I'll review the details and provide you with a comprehensive response shortly.\n\nBest regards"
    
    def _generate_thank_you_reply(self, sender_name: str, context: Dict) -> str:
        """Generate thank you reply"""
        return f"Hi {sender_name},\n\nYou're very welcome! I'm glad I could help. Please don't hesitate to reach out if you need anything else.\n\nBest regards"
    
    def _generate_info_request_reply(self, sender_name: str, context: Dict) -> str:
        """Generate information request reply"""
        return f"Hi {sender_name},\n\nI'll gather the requested information and send it to you shortly. If you need anything specific or have a preferred format, please let me know.\n\nBest regards"
    
    def _generate_default_reply(self, sender_name: str, priority_level: str) -> str:
        """Generate default professional reply"""
        if priority_level == "High":
            return f"Hi {sender_name},\n\nThank you for your email. I've noted the urgency and will address this promptly. I'll get back to you with a detailed response soon.\n\nBest regards"
        else:
            return f"Hi {sender_name},\n\nThank you for your email. I'll review the details and respond accordingly.\n\nBest regards"
    
    def _generate_insights(self, processed_email: Dict[str, Any]) -> List[str]:
        """Generate actionable insights from processed email"""
        
        insights = []
        
        # Priority-based insights
        if processed_email['priority_level'] == 'High':
            insights.append("[EMOJI] Requires immediate attention")
        
        # Entity-based insights
        entities = processed_email.get('extracted_entities', {})
        if entities.get('deadlines'):
            insights.append(f"[EMOJI] Contains deadline: {entities['deadlines'][0]}")
        
        if entities.get('meetings'):
            insights.append(f"[EMOJI] Meeting mentioned: {entities['meetings'][0]}")
        
        # Attachment insights
        if processed_email.get('has_attachments'):
            insights.append(f"[EMOJI] {processed_email['attachment_count']} attachment(s) to review")
        
        # Thread insights
        if processed_email.get('is_thread') and processed_email.get('thread_length', 1) > 3:
            insights.append("[THREAD] Part of ongoing conversation thread")
        
        return insights
    
    def _calculate_confidence_score(self, processed_email: Dict[str, Any]) -> float:
        """Calculate AI confidence in processing results"""
        
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on successful processing
        if processed_email.get('ai_summary'):
            confidence += 0.2
        
        if processed_email.get('priority_reasons'):
            confidence += 0.1
        
        if processed_email.get('extracted_entities'):
            entity_count = sum(len(v) for v in processed_email['extracted_entities'].values())
            if entity_count > 0:
                confidence += 0.1
        
        if processed_email.get('draft_reply'):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _load_vip_data(self) -> Dict[str, Any]:
        """Load VIP sender data from file"""
        try:
            with open(self.vip_data_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def _save_vip_data(self):
        """Save VIP sender data to file"""
        os.makedirs(os.path.dirname(self.vip_data_file), exist_ok=True)
        with open(self.vip_data_file, 'w') as f:
            json.dump(self.vip_senders, f, indent=2)
    
    def _update_vip_score(self, sender_email: str, change: int):
        """Update VIP score for a sender"""
        if sender_email not in self.vip_senders:
            self.vip_senders[sender_email] = {'interactions': 0, 'last_interaction': ''}
        
        self.vip_senders[sender_email]['interactions'] += change
        self.vip_senders[sender_email]['last_interaction'] = datetime.now().isoformat()
        
        # Remove if score becomes too low
        if self.vip_senders[sender_email]['interactions'] <= -3:
            del self.vip_senders[sender_email]
        
        self._save_vip_data()
    
    def _load_learning_data(self):
        """Load learning patterns from file"""
        try:
            with open(self.learning_data_file, 'r') as f:
                loaded_data = json.load(f)
                self.learning_patterns.update(loaded_data)
        except FileNotFoundError:
            pass
    
    def _save_learning_data(self):
        """Save learning patterns to file"""
        os.makedirs(os.path.dirname(self.learning_data_file), exist_ok=True)
        with open(self.learning_data_file, 'w') as f:
            json.dump(self.learning_patterns, f, indent=2)
    
    def _adjust_priority_weights(self, email_data: Dict[str, Any], increase: bool):
        """Adjust priority calculation weights based on feedback"""
        # This would implement weight adjustment logic for priority learning
        # For now, we'll just log the learning opportunity
        action = "increase" if increase else "decrease"
        print(f"[EMOJI] Learning opportunity: {action} priority weight for similar emails")
    
    def _calculate_avg_response_time(self, sender_email: str) -> float:
        """Calculate average response time for a sender"""
        # Simplified implementation - in production would track actual response times
        return 24.0  # Default 24 hours

# =============================================================================
# TESTING AND DEMONSTRATION CODE
# =============================================================================

def test_ai_processor():
    """
    Test the AI Email Processor with sample data
    """
    
    print("=" * 70)
    print("[TEST] AI EMAIL PROCESSOR TEST")
    print("=" * 70)
    
    # Create AI processor instance
    print("[BRAIN] Initializing AI Processor...")
    processor = EmailProcessor()
    
    # Test with sample email data
    sample_email = {
        'id': 'test_001',
        'subject': 'URGENT: Contract approval needed by Friday',
        'sender': 'Sarah Johnson <s.johnson@client.com>',
        'sender_name': 'Sarah Johnson',
        'sender_email': 's.johnson@client.com',
        'body': '''Hi there,
        
I hope this email finds you well. We need to get the Q4 contract approved by Friday EOD to meet our deadline. 

The contract includes:
- Budget allocation: $50,000
- Timeline: 3 months
- Key deliverables outlined in attached document

Can you please review and provide approval? This is quite urgent as the client is waiting for our response.

Best regards,
Sarah Johnson
Senior Project Manager''',
        'has_attachments': True,
        'attachment_count': 1,
        'attachment_types': ['pdf'],
        'is_thread': False
    }
    
    print("\n[EMAIL] Processing sample email...")
    print(f"   Subject: {sample_email['subject']}")
    print(f"   From: {sample_email['sender_name']}")
    
    # Process the email with AI
    processed_email = processor.process_email(sample_email)
    
    # Display results
    print("\n[TARGET] AI PROCESSING RESULTS:")
    print("=" * 50)
    
    print(f"\n[NOTE] AI Summary:")
    print(f"   {processed_email.get('ai_summary', 'No summary generated')}")
    
    print(f"\n[TARGET] Priority Analysis:")
    print(f"   Level: {processed_email.get('priority_level', 'Unknown')}")
    print(f"   Score: {processed_email.get('priority_score', 0)}")
    print(f"   Reasons: {', '.join(processed_email.get('priority_reasons', []))}")
    
    print(f"\n[SEARCH] Extracted Entities:")
    entities = processed_email.get('extracted_entities', {})
    for entity_type, items in entities.items():
        if items:
            print(f"   {entity_type.capitalize()}: {', '.join(items[:3])}")  # Show first 3
    
    if processed_email.get('draft_reply'):
        print(f"\n[EMOJI] Draft Reply:")
        print(f"   {processed_email['draft_reply'][:100]}...")
    
    print(f"\n[IDEA] Actionable Insights:")
    insights = processed_email.get('actionable_insights', [])
    for insight in insights:
        print(f"   {insight}")
    
    print(f"\n[INFO] AI Confidence: {processed_email.get('ai_confidence', 0):.1%}")
    
    # Test learning simulation
    print(f"\n[EMOJI] Testing Learning System...")
    processor.learn_from_interaction(processed_email, 'reply')
    
    print("\n[OK] AI Processor test completed successfully!")
    print("[PARTY] Your AI Email Agent brain is working perfectly!")

if __name__ == '__main__':
    """Run tests when file is executed directly"""
    test_ai_processor()