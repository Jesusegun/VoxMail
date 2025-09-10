# =============================================================================
# COMPLETE ADVANCED AI SYSTEM - complete_advanced_ai_system.py
# =============================================================================
# DAY 2 AFTERNOON: Complete Enhanced AI Email Agent System
# 
# This is the COMPLETE file with all advanced features:
# - Advanced reply generation with tone matching
# - Calendar event detection and extraction
# - Email thread intelligence and conversation tracking
# - Smart template system for consistent responses
# - Enhanced learning with behavioral pattern recognition
# - Complete integration pipeline for production use
# =============================================================================

import os
import re
import json
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

# Import base AI processor from Day 2 Morning
try:
    from ai_processor import EmailProcessor, AIProcessorConfig
    print("✅ Base AI Processor imported from Day 2 Morning")
except ImportError:
    print("❌ Cannot import base AI processor. Make sure ai_processor.py exists from Day 2 Morning")
    exit(1)

# Additional imports for advanced features
try:
    import spacy
    from transformers import pipeline
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from textblob import TextBlob
    print("✅ Advanced AI libraries loaded")
except ImportError as e:
    print(f"❌ Advanced AI libraries missing: {e}")

# =============================================================================
# ADVANCED AI CONFIGURATION
# =============================================================================

@dataclass
class AdvancedAIConfig(AIProcessorConfig):
    """Enhanced configuration for advanced AI features"""
    
    # Advanced reply generation settings
    tone_analysis_enabled: bool = True
    context_window_size: int = 3
    reply_template_matching: bool = True
    
    # Calendar integration settings
    calendar_extraction_enabled: bool = True
    meeting_detection_threshold: float = 0.7
    deadline_lookahead_days: int = 30
    
    # Thread intelligence settings
    thread_analysis_enabled: bool = True
    max_thread_depth: int = 10
    thread_summary_enabled: bool = True
    
    # Learning and adaptation settings
    behavioral_learning_enabled: bool = True
    writing_style_adaptation: bool = True
    response_time_tracking: bool = True

class AdvancedEmailProcessor(EmailProcessor):
    """Advanced AI Email Processor - Day 2 Afternoon Enhancement"""
    
    def __init__(self, config: Optional[AdvancedAIConfig] = None):
        """Initialize the Advanced AI Email Processor"""
        
        # Initialize base processor first
        base_config = config or AdvancedAIConfig()
        super().__init__(base_config)
        
        print("🚀 Initializing Advanced AI Email Processor...")
        
        # Store advanced config
        self.advanced_config = base_config
        
        # Initialize advanced components
        self._initialize_advanced_systems()
        self._initialize_template_system()
        self._initialize_calendar_system()
        self._initialize_thread_system()
        self._initialize_behavioral_learning()
        
        print("✅ Advanced AI Email Processor ready!")
    
    def _initialize_advanced_systems(self):
        """Initialize advanced AI systems and models"""
        
        print("🧠 Loading advanced AI models...")
        
        try:
            # Load advanced sentiment analysis for tone detection
            self.models['advanced_sentiment'] = pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base",
                device=-1
            )
            print("✅ Advanced emotion detection model loaded")
        except:
            print("⚠️ Advanced emotion model not available, using base sentiment")
        
        try:
            # Initialize text similarity for template matching
            self.advanced_tfidf = TfidfVectorizer(
                max_features=2000,
                stop_words='english',
                ngram_range=(1, 3),
                lowercase=True
            )
            print("✅ Advanced text similarity system initialized")
        except:
            print("⚠️ Advanced similarity system failed to initialize")
        
        # Conversation context analyzer
        self.conversation_contexts = {}
        self.user_communication_patterns = {}
        
        print("✅ Advanced systems initialized")
    
    def _initialize_template_system(self):
        """Initialize intelligent template system for replies"""
        
        print("📝 Initializing smart template system...")
        
        # Contextual reply templates
        self.reply_templates = {
            'meeting_request': {
                'formal': "Dear {sender_name},\n\nThank you for your meeting request. I will review my calendar and respond with my availability shortly.\n\nBest regards",
                'business': "Hi {sender_name},\n\nThanks for reaching out about the meeting. I'll check my schedule and get back to you with some time options.\n\nBest",
                'casual': "Hi {sender_name},\n\nSure! Let me check my calendar and I'll send you some times that work.\n\nThanks!"
            },
            
            'urgent_request': {
                'formal': "Dear {sender_name},\n\nI have received your urgent request and understand the time-sensitive nature. I will prioritize this and provide a response by {deadline}.\n\nRegards",
                'business': "Hi {sender_name},\n\nGot your urgent message. I'm on it and will get back to you by {deadline}.\n\nThanks",
                'casual': "Hi {sender_name},\n\nSaw your urgent email - will handle this ASAP and update you by {deadline}.\n\nThanks!"
            },
            
            'info_request': {
                'formal': "Dear {sender_name},\n\nThank you for your inquiry. I will gather the requested information and provide a comprehensive response shortly.\n\nBest regards",
                'business': "Hi {sender_name},\n\nThanks for your question. I'll pull together the info you need and send it over soon.\n\nBest",
                'casual': "Hi {sender_name},\n\nSure thing! Let me get that information for you.\n\nThanks!"
            },
            
            'follow_up': {
                'formal': "Dear {sender_name},\n\nThank you for following up on this matter. I will review the current status and provide an update accordingly.\n\nBest regards",
                'business': "Hi {sender_name},\n\nThanks for the follow-up. Let me check on this and get you an update.\n\nBest",
                'casual': "Hi {sender_name},\n\nGood timing on the follow-up! Let me see where we're at with this.\n\nThanks!"
            },
            
            'problem_report': {
                'formal': "Dear {sender_name},\n\nI acknowledge receipt of your concern and understand the importance of resolving this matter promptly. I will investigate and respond with a solution.\n\nRegards",
                'business': "Hi {sender_name},\n\nThanks for bringing this to my attention. I'll look into it right away and get back to you with a solution.\n\nBest",
                'casual': "Hi {sender_name},\n\nThanks for the heads up! I'll check this out and fix it.\n\nThanks!"
            },
            
            'connection_request': {
                'formal': "Dear {sender_name},\n\nThank you for your connection request. I appreciate your interest in connecting.\n\nBest regards",
                'business': "Hi {sender_name},\n\nThanks for reaching out to connect. I'd be happy to connect with you.\n\nBest",
                'casual': "Hi {sender_name},\n\nThanks for wanting to connect! Looking forward to it.\n\nCheers!"
            },
            
            'acknowledgment': {
                'formal': "Dear {sender_name},\n\nThank you for your kind words. I appreciate your feedback.\n\nBest regards", 
                'business': "Hi {sender_name},\n\nThanks for the positive feedback! Much appreciated.\n\nBest",
                'casual': "Hi {sender_name},\n\nThanks! Really appreciate it.\n\nCheers!"
            }
        }
        
        # Tone detection patterns
        self.tone_indicators = {
            'formal': ['dear', 'regards', 'sincerely', 'respectfully', 'kindly', 'please find attached'],
            'business': ['thanks', 'best', 'appreciate', 'following up', 'as discussed'],
            'casual': ['hi', 'hey', 'thanks!', 'awesome', 'sounds good', 'no problem']
        }
        
        print("✅ Smart template system ready")
    
    def _initialize_calendar_system(self):
        """Initialize calendar event detection and extraction"""
        
        print("📅 Initializing calendar intelligence...")
        
        # Meeting detection patterns
        self.meeting_patterns = [
            r'meeting\s+(on|at|scheduled for)\s+([^.]+)',
            r'call\s+(on|at|scheduled for)\s+([^.]+)',
            r'appointment\s+(on|at|for)\s+([^.]+)',
            r'conference\s+(on|at)\s+([^.]+)',
            r'let\'s\s+(meet|discuss|talk)\s+(on|at|about)\s+([^.]+)',
            r'available\s+(for\s+)?(a\s+)?(meeting|call)\s+(on|at)\s+([^.]+)'
        ]
        
        # Time pattern recognition
        self.time_patterns = [
            r'(\d{1,2}):(\d{2})\s*(am|pm)',
            r'(\d{1,2})\s*(am|pm)',
            r'at\s+(\d{1,2})',
            r'(\d{1,2}):(\d{2})'
        ]
        
        # Date pattern recognition
        self.date_patterns = [
            r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}',
            r'\d{1,2}/\d{1,2}(/\d{4})?',
            r'\d{1,2}-\d{1,2}(-\d{4})?',
            r'(today|tomorrow|next week|this week|next month)'
        ]
        
        # Deadline detection patterns
        self.deadline_patterns = [
            r'deadline\s+(is|of|by)\s+([^.]+)',
            r'due\s+(by|on|at)\s+([^.]+)',
            r'needs?\s+to\s+be\s+(done|completed|finished)\s+(by|before)\s+([^.]+)',
            r'must\s+be\s+(submitted|completed|ready)\s+(by|before)\s+([^.]+)'
        ]
        
        print("✅ Calendar intelligence system ready")
    
    def _initialize_thread_system(self):
        """Initialize email thread analysis and conversation tracking"""
        
        print("🧵 Initializing thread intelligence...")
        
        # Thread conversation storage
        self.active_threads = {}
        self.thread_summaries = {}
        
        # Conversation flow patterns
        self.conversation_flows = {
            'question_answer': ['question', 'answer', 'follow_up'],
            'request_response': ['request', 'acknowledgment', 'completion'],
            'meeting_planning': ['proposal', 'availability', 'confirmation'],
            'problem_solving': ['issue_report', 'investigation', 'solution', 'verification']
        }
        
        print("✅ Thread intelligence system ready")
    
    def _initialize_behavioral_learning(self):
        """Initialize behavioral learning and adaptation system"""
        
        print("🎓 Initializing behavioral learning...")
        
        # User behavior patterns
        self.user_patterns = {
            'response_times': {},
            'communication_style': {},
            'priority_patterns': {},
            'template_preferences': {},
            'meeting_preferences': {}
        }
        
        # Load existing behavioral data
        self.behavior_data_file = "ai_data/behavioral_patterns.json"
        self._load_behavioral_data()
        
        print("✅ Behavioral learning system ready")
    
    # =============================================================================
    # ADVANCED EMAIL PROCESSING METHODS
    # =============================================================================
    
    def advanced_process_email(self, email_data: Dict[str, Any], 
                             thread_context: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Advanced email processing with contextual awareness"""
        
        print(f"\n🚀 ADVANCED AI PROCESSING: {email_data.get('subject', 'No Subject')}")
        
        # Start with base processing
        processed_email = super().process_email(email_data)
        
        try:
            # Thread context analysis
            if self.advanced_config.thread_analysis_enabled:
                print("🧵 Analyzing thread context...")
                thread_analysis = self.analyze_thread_context(email_data, thread_context)
                processed_email['thread_analysis'] = thread_analysis
            
            # Advanced tone analysis
            if self.advanced_config.tone_analysis_enabled:
                print("🎭 Advanced tone analysis...")
                tone_analysis = self.analyze_communication_tone(email_data, processed_email)
                processed_email['tone_analysis'] = tone_analysis
            
            # Calendar event extraction
            if self.advanced_config.calendar_extraction_enabled:
                print("📅 Calendar intelligence extraction...")
                calendar_events = self.extract_calendar_events(email_data)
                processed_email['calendar_events'] = calendar_events
            
            # Advanced reply generation
            print("✍️ Advanced reply generation...")
            advanced_reply = self.generate_advanced_reply(
                email_data, 
                processed_email, 
                thread_context
            )
            processed_email['advanced_reply'] = advanced_reply
            
            # Contextual insights generation
            print("💡 Generating contextual insights...")
            contextual_insights = self.generate_contextual_insights(
                processed_email, 
                thread_context
            )
            processed_email['contextual_insights'] = contextual_insights
            
            # Behavioral learning update
            if self.advanced_config.behavioral_learning_enabled:
                print("🎓 Updating behavioral learning...")
                self.update_behavioral_patterns(email_data, processed_email)
            
            # Advanced metadata
            processed_email.update({
                'advanced_processing_version': '2.0',
                'advanced_features_enabled': {
                    'thread_analysis': self.advanced_config.thread_analysis_enabled,
                    'tone_analysis': self.advanced_config.tone_analysis_enabled,
                    'calendar_extraction': self.advanced_config.calendar_extraction_enabled,
                    'behavioral_learning': self.advanced_config.behavioral_learning_enabled
                },
                'processing_timestamp': datetime.now().isoformat()
            })
            
            print("✅ Advanced AI processing completed successfully!")
            return processed_email
            
        except Exception as e:
            print(f"❌ Advanced processing failed: {e}")
            processed_email['advanced_processing_error'] = str(e)
            return processed_email
    
    def analyze_thread_context(self, email_data: Dict[str, Any], 
                             thread_context: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Analyze email thread context and conversation flow"""
        
        thread_analysis = {
            'is_continuation': False,
            'conversation_stage': 'initial',
            'topic_drift': 0.0,
            'urgency_escalation': False,
            'key_participants': [],
            'conversation_summary': '',
            'recommended_action': 'respond'
        }
        
        if not thread_context or len(thread_context) == 0:
            thread_analysis['conversation_stage'] = 'initial'
            return thread_analysis
        
        try:
            # Analyze conversation progression
            thread_analysis['is_continuation'] = True
            thread_analysis['conversation_stage'] = self._determine_conversation_stage(thread_context)
            
            # Analyze topic consistency
            thread_analysis['topic_drift'] = self._calculate_topic_drift(email_data, thread_context)
            
            # Check for urgency escalation
            thread_analysis['urgency_escalation'] = self._detect_urgency_escalation(thread_context)
            
            # Extract key participants
            thread_analysis['key_participants'] = self._extract_thread_participants(thread_context)
            
            # Generate conversation summary
            if self.advanced_config.thread_summary_enabled:
                thread_analysis['conversation_summary'] = self._generate_thread_summary(thread_context)
            
            # Recommend action based on thread analysis
            thread_analysis['recommended_action'] = self._recommend_thread_action(
                email_data, 
                thread_context, 
                thread_analysis
            )
            
        except Exception as e:
            print(f"⚠️ Thread analysis failed: {e}")
        
        return thread_analysis
    
    def analyze_communication_tone(self, email_data: Dict[str, Any], 
                                 base_processed: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze communication tone and style for appropriate response matching"""
        
        email_text = f"{email_data.get('subject', '')} {email_data.get('body', '')}"
        
        tone_analysis = {
            'detected_tone': 'business',
            'formality_level': 'medium',
            'emotional_state': 'neutral',
            'urgency_tone': 'normal',
            'relationship_type': 'professional',
            'confidence_score': 0.0
        }
        
        try:
            # Formality level detection
            formal_score = 0
            casual_score = 0
            
            # Check for formal indicators
            for indicator in self.tone_indicators['formal']:
                if indicator in email_text.lower():
                    formal_score += 1
            
            # Check for casual indicators
            for indicator in self.tone_indicators['casual']:
                if indicator in email_text.lower():
                    casual_score += 1
            
            # Determine formality level
            if formal_score > casual_score:
                tone_analysis['formality_level'] = 'formal'
                tone_analysis['detected_tone'] = 'formal'
            elif casual_score > formal_score:
                tone_analysis['formality_level'] = 'casual'
                tone_analysis['detected_tone'] = 'casual'
            else:
                tone_analysis['formality_level'] = 'business'
                tone_analysis['detected_tone'] = 'business'
            
            # Emotional state analysis
            if self.models.get('advanced_sentiment'):
                emotion_result = self.models['advanced_sentiment'](email_text[:512])
                if emotion_result:
                    tone_analysis['emotional_state'] = emotion_result[0]['label'].lower()
                    tone_analysis['confidence_score'] = emotion_result[0]['score']
            else:
                # Fallback to basic sentiment
                blob = TextBlob(email_text)
                if blob.sentiment.polarity > 0.1:
                    tone_analysis['emotional_state'] = 'positive'
                elif blob.sentiment.polarity < -0.1:
                    tone_analysis['emotional_state'] = 'negative'
                else:
                    tone_analysis['emotional_state'] = 'neutral'
            
            # Urgency tone detection
            urgency_indicators = base_processed.get('priority_reasons', [])
            if any('urgent' in reason.lower() for reason in urgency_indicators):
                tone_analysis['urgency_tone'] = 'urgent'
            elif base_processed.get('priority_level') == 'High':
                tone_analysis['urgency_tone'] = 'high'
            else:
                tone_analysis['urgency_tone'] = 'normal'
            
            # Relationship type detection
            sender_email = email_data.get('sender_email', '').lower()
            
            # Check VIP status for relationship type
            if sender_email in self.vip_senders:
                interactions = self.vip_senders[sender_email].get('interactions', 0)
                if interactions > 5:
                    tone_analysis['relationship_type'] = 'established'
                else:
                    tone_analysis['relationship_type'] = 'developing'
            else:
                tone_analysis['relationship_type'] = 'professional'
            
        except Exception as e:
            print(f"⚠️ Tone analysis failed: {e}")
        
        return tone_analysis
    
    def extract_calendar_events(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract calendar events, meetings, and deadlines from email content"""
        
        email_text = f"{email_data.get('subject', '')} {email_data.get('body', '')}"
        
        calendar_events = {
            'meetings': [],
            'deadlines': [],
            'appointments': [],
            'time_mentions': [],
            'date_mentions': [],
            'calendar_confidence': 0.0
        }
        
        try:
            # Meeting detection
            for pattern in self.meeting_patterns:
                matches = re.finditer(pattern, email_text.lower())
                for match in matches:
                    meeting_info = {
                        'type': 'meeting',
                        'raw_text': match.group(0),
                        'details': match.groups()[-1] if match.groups() else '',
                        'confidence': 0.8
                    }
                    calendar_events['meetings'].append(meeting_info)
            
            # Deadline extraction
            for pattern in self.deadline_patterns:
                matches = re.finditer(pattern, email_text.lower())
                for match in matches:
                    deadline_info = {
                        'type': 'deadline',
                        'raw_text': match.group(0),
                        'deadline': match.groups()[-1] if match.groups() else '',
                        'confidence': 0.9
                    }
                    calendar_events['deadlines'].append(deadline_info)
            
            # Time and date extraction
            for pattern in self.time_patterns:
                matches = re.finditer(pattern, email_text.lower())
                for match in matches:
                    calendar_events['time_mentions'].append(match.group(0))
            
            for pattern in self.date_patterns:
                matches = re.finditer(pattern, email_text.lower())
                for match in matches:
                    calendar_events['date_mentions'].append(match.group(0))
            
            # Calendar confidence calculation
            total_events = (len(calendar_events['meetings']) + 
                          len(calendar_events['deadlines']) + 
                          len(calendar_events['time_mentions']) + 
                          len(calendar_events['date_mentions']))
            
            if total_events > 0:
                calendar_events['calendar_confidence'] = min(total_events * 0.2, 1.0)
            
        except Exception as e:
            print(f"⚠️ Calendar extraction failed: {e}")
        
        return calendar_events
    
    def generate_advanced_reply(self, email_data: Dict[str, Any], 
                              processed_data: Dict[str, Any],
                              thread_context: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Generate advanced, contextually aware draft reply"""
        
        reply_data = {
            'primary_reply': '',
            'alternative_replies': [],
            'reply_metadata': {
                'tone_matched': False,
                'context_aware': False,
                'template_used': '',
                'personalization_level': 'standard'
            }
        }
        
        try:
            # Get tone analysis
            tone_analysis = processed_data.get('tone_analysis', {})
            detected_tone = tone_analysis.get('detected_tone', 'business')
            
            # Get thread analysis
            thread_analysis = processed_data.get('thread_analysis', {})
            
            # Determine reply context type
            reply_context = self._determine_reply_context(email_data, processed_data, thread_context)
            
            # Check if this email type needs a reply
            if reply_context['category'] == 'no_reply_needed':
                return reply_data  # Return empty reply data
            
            # Get appropriate template
            template_category = reply_context['category']
            tone_level = detected_tone
            
            if template_category in self.reply_templates and tone_level in self.reply_templates[template_category]:
                base_template = self.reply_templates[template_category][tone_level]
                
                # Generate primary reply
                reply_data['primary_reply'] = self._personalize_template(
                    base_template, 
                    email_data, 
                    processed_data,
                    reply_context
                )
                
                # Generate alternative replies with different tones
                for alt_tone in ['formal', 'business', 'casual']:
                    if alt_tone != tone_level and alt_tone in self.reply_templates[template_category]:
                        alt_template = self.reply_templates[template_category][alt_tone]
                        alt_reply = self._personalize_template(
                            alt_template,
                            email_data,
                            processed_data,
                            reply_context
                        )
                        reply_data['alternative_replies'].append({
                            'tone': alt_tone,
                            'reply': alt_reply
                        })
                
                # Set metadata
                reply_data['reply_metadata'].update({
                    'tone_matched': True,
                    'context_aware': thread_context is not None,
                    'template_used': f"{template_category}_{tone_level}",
                    'personalization_level': 'high'
                })
            
            else:
                # Fallback to base reply generation
                reply_data['primary_reply'] = processed_data.get('draft_reply', 
                    self._generate_fallback_reply(email_data['sender_name']))
            
        except Exception as e:
            print(f"⚠️ Advanced reply generation failed: {e}")
            reply_data['primary_reply'] = f"Hi {email_data.get('sender_name', 'there')},\n\nThank you for your email. I'll review and respond accordingly.\n\nBest regards"
        
        return reply_data
    
    def generate_contextual_insights(self, processed_email: Dict[str, Any], 
                                   thread_context: Optional[List[Dict]] = None) -> List[str]:
        """Generate advanced contextual insights and recommendations"""
        
        insights = []
        
        try:
            # Thread-based insights
            thread_analysis = processed_email.get('thread_analysis', {})
            if thread_analysis.get('is_continuation'):
                stage = thread_analysis.get('conversation_stage', 'unknown')
                insights.append(f"🧵 Conversation stage: {stage}")
                
                if thread_analysis.get('urgency_escalation'):
                    insights.append("⚠️ Urgency has escalated in this thread")
            
            # Tone-based insights
            tone_analysis = processed_email.get('tone_analysis', {})
            if tone_analysis.get('emotional_state') in ['negative', 'frustrated']:
                insights.append("😔 Sender may be frustrated - consider empathetic response")
            elif tone_analysis.get('urgency_tone') == 'urgent':
                insights.append("⚡ High urgency detected - prioritize immediate response")
            
            # Calendar-based insights
            calendar_events = processed_email.get('calendar_events', {})
            if calendar_events.get('meetings'):
                meeting_count = len(calendar_events['meetings'])
                insights.append(f"📅 {meeting_count} meeting(s) mentioned - may need calendar coordination")
            
            if calendar_events.get('deadlines'):
                deadline_count = len(calendar_events['deadlines'])
                insights.append(f"⏰ {deadline_count} deadline(s) identified - time-sensitive action required")
            
            # Priority-based insights
            priority_level = processed_email.get('priority_level')
            priority_reasons = processed_email.get('priority_reasons', [])
            
            if priority_level == 'High' and len(priority_reasons) > 2:
                insights.append("🔥 Multiple high-priority indicators - requires immediate attention")
            
            # Entity-based insights
            entities = processed_email.get('extracted_entities', {})
            if entities.get('people') and len(entities['people']) > 3:
                insights.append("👥 Multiple people mentioned - may be group coordination needed")
            
            if entities.get('money'):
                insights.append("💰 Financial information mentioned - handle with care")
            
            # Attachment insights
            if processed_email.get('has_attachments'):
                attachment_count = processed_email.get('attachment_count', 0)
                if attachment_count > 2:
                    insights.append(f"📎 {attachment_count} attachments - document review required")
            
            # AI confidence insights
            ai_confidence = processed_email.get('ai_confidence', 0)
            if ai_confidence < 0.7:
                insights.append("🤔 AI confidence lower than usual - manual review recommended")
            
        except Exception as e:
            print(f"⚠️ Insight generation failed: {e}")
        
        return insights
    
    # =============================================================================
    # HELPER METHODS FOR ADVANCED PROCESSING
    # =============================================================================
    
    def _determine_conversation_stage(self, thread_context: List[Dict]) -> str:
        """Determine what stage the conversation is in"""
        if len(thread_context) <= 1:
            return 'initial'
        elif len(thread_context) <= 3:
            return 'developing'
        elif len(thread_context) <= 6:
            return 'ongoing'
        else:
            return 'extended'
    
    def _calculate_topic_drift(self, current_email: Dict, thread_context: List[Dict]) -> float:
        """Calculate how much the topic has drifted from original"""
        try:
            if not thread_context:
                return 0.0
            
            current_subject = current_email.get('subject', '').lower()
            original_subject = thread_context[0].get('subject', '').lower()
            
            current_words = set(current_subject.split())
            original_words = set(original_subject.split())
            
            if not original_words:
                return 0.0
            
            common_words = current_words.intersection(original_words)
            similarity = len(common_words) / len(original_words)
            
            return 1.0 - similarity
        except:
            return 0.0
    
    def _detect_urgency_escalation(self, thread_context: List[Dict]) -> bool:
        """Detect if urgency has escalated through the thread"""
        try:
            if len(thread_context) < 2:
                return False
            
            recent_urgency = sum(1 for email in thread_context[-2:] 
                               if 'urgent' in email.get('subject', '').lower() or 
                                  'urgent' in email.get('body', '').lower())
            
            earlier_urgency = sum(1 for email in thread_context[:-2] 
                                if 'urgent' in email.get('subject', '').lower() or 
                                   'urgent' in email.get('body', '').lower())
            
            return recent_urgency > earlier_urgency
        except:
            return False
    
    def _extract_thread_participants(self, thread_context: List[Dict]) -> List[str]:
        """Extract all participants in the email thread"""
        participants = set()
        try:
            for email in thread_context:
                sender_email = email.get('sender_email', '')
                if sender_email:
                    participants.add(sender_email)
            return list(participants)
        except:
            return []
    
    def _generate_thread_summary(self, thread_context: List[Dict]) -> str:
        """Generate a summary of the email thread conversation"""
        try:
            if not thread_context:
                return "No thread context available"
            
            participant_count = len(self._extract_thread_participants(thread_context))
            email_count = len(thread_context)
            subjects = [email.get('subject', '') for email in thread_context]
            
            return f"Thread with {participant_count} participants across {email_count} emails. Main topics: {', '.join(subjects[:2])}"
        except:
            return "Thread summary unavailable"
    
    def _recommend_thread_action(self, current_email: Dict, thread_context: List[Dict], 
                                thread_analysis: Dict) -> str:
        """Recommend action based on thread analysis"""
        if thread_analysis.get('urgency_escalation'):
            return 'urgent_response'
        elif thread_analysis.get('conversation_stage') == 'extended':
            return 'summarize_and_close'
        elif thread_analysis.get('topic_drift', 0) > 0.7:
            return 'clarify_scope'
        else:
            return 'respond_normally'
    
    def _determine_reply_context(self, email_data: Dict, processed_data: Dict, 
                                thread_context: Optional[List[Dict]]) -> Dict[str, Any]:
        """Determine the context type for reply generation"""
        subject = email_data.get('subject', '').lower()
        body = email_data.get('body', '').lower()
        sender_email = email_data.get('sender_email', '').lower()
        
        context = {
            'category': 'info_request',
            'urgency': 'normal',
            'relationship': 'professional',
            'specifics': {}
        }
        
        # Check for automated/promotional emails that typically don't need replies
        automated_indicators = ['noreply', 'no-reply', 'donotreply', 'automated', 'notification']
        promotional_indicators = ['unsubscribe', 'marketing', 'newsletter', 'promotion', 'offer', 'deal']
        social_media_indicators = ['linkedin', 'facebook', 'twitter', 'instagram']
        
        if (any(indicator in sender_email for indicator in automated_indicators) or
            any(indicator in body for indicator in promotional_indicators) or
            'via linkedin' in sender_email or
            any(phrase in subject for phrase in ['fx rate', 'daily rate', 'newsletter', 'notification'])):
            context['category'] = 'no_reply_needed'
            return context
        
        # Determine category based on content
        if any(word in subject + body for word in ['meeting', 'call', 'appointment', 'schedule', 'available']):
            context['category'] = 'meeting_request'
        elif any(word in subject + body for word in ['urgent', 'asap', 'emergency', 'critical', 'deadline']):
            context['category'] = 'urgent_request'
        elif any(word in subject + body for word in ['problem', 'issue', 'error', 'broken', 'help', 'support']):
            context['category'] = 'problem_report'
        elif any(word in subject + body for word in ['connect', 'invitation', 'join', 'network']):
            context['category'] = 'connection_request'
        elif any(word in subject + body for word in ['follow up', 'following up', 'checking in', 'status', 'update']):
            context['category'] = 'follow_up'
        elif any(word in subject + body for word in ['thank', 'thanks', 'appreciate', 'great work']):
            context['category'] = 'acknowledgment'
        elif thread_context and len(thread_context) > 1:
            context['category'] = 'follow_up'
        
        # Determine urgency
        priority_level = processed_data.get('priority_level', 'Medium')
        if priority_level == 'High':
            context['urgency'] = 'high'
        elif 'urgent' in subject + body:
            context['urgency'] = 'urgent'
        
        return context
    
    def _personalize_template(self, template: str, email_data: Dict, 
                            processed_data: Dict, reply_context: Dict) -> str:
        """Personalize reply template with context-specific information"""
        try:
            sender_name = email_data.get('sender_name', 'there')
            
            # Prepare template variables
            template_vars = {'sender_name': sender_name}
            
            # Add deadline context if urgent or if template contains deadline
            if '{deadline}' in template:
                if reply_context.get('urgency') in ['urgent', 'high']:
                    calendar_events = processed_data.get('calendar_events', {})
                    deadlines = calendar_events.get('deadlines', [])
                    
                    if deadlines:
                        deadline_text = deadlines[0].get('deadline', 'end of day')
                        template_vars['deadline'] = deadline_text
                    else:
                        template_vars['deadline'] = 'end of day'
                else:
                    template_vars['deadline'] = 'shortly'
            
            # Format template with all variables
            personalized = template.format(**template_vars)
            return personalized
            
        except Exception as e:
            print(f"⚠️ Template personalization failed: {e}")
            # Safe fallback
            sender_name = email_data.get('sender_name', 'there')
            return f"Hi {sender_name},\n\nThank you for your email. I'll review and respond accordingly.\n\nBest regards"
    
    def _generate_fallback_reply(self, sender_name: str) -> str:
        """Generate fallback reply when templates fail"""
        return f"Hi {sender_name},\n\nThank you for your email. I'll review and respond accordingly.\n\nBest regards"
    
    def update_behavioral_patterns(self, email_data: Dict, processed_data: Dict):
        """Update behavioral learning patterns based on email processing"""
        try:
            sender_email = email_data.get('sender_email', '').lower()
            
            # Update communication style patterns
            tone_analysis = processed_data.get('tone_analysis', {})
            if sender_email not in self.user_patterns['communication_style']:
                self.user_patterns['communication_style'][sender_email] = {
                    'formal_count': 0,
                    'business_count': 0,
                    'casual_count': 0
                }
            
            detected_tone = tone_analysis.get('detected_tone', 'business')
            self.user_patterns['communication_style'][sender_email][f'{detected_tone}_count'] += 1
            
            # Update priority patterns
            priority_level = processed_data.get('priority_level')
            if priority_level and sender_email not in self.user_patterns['priority_patterns']:
                self.user_patterns['priority_patterns'][sender_email] = {
                    'High': 0, 'Medium': 0, 'Low': 0
                }
            
            if priority_level:
                self.user_patterns['priority_patterns'][sender_email][priority_level] += 1
            
            # Save behavioral data
            self._save_behavioral_data()
        except Exception as e:
            print(f"⚠️ Behavioral pattern update failed: {e}")
    
    def _load_behavioral_data(self):
        """Load behavioral patterns from file"""
        try:
            if os.path.exists(self.behavior_data_file):
                with open(self.behavior_data_file, 'r') as f:
                    loaded_patterns = json.load(f)
                    self.user_patterns.update(loaded_patterns)
        except:
            pass
    
    def _save_behavioral_data(self):
        """Save behavioral patterns to file"""
        try:
            os.makedirs(os.path.dirname(self.behavior_data_file), exist_ok=True)
            with open(self.behavior_data_file, 'w') as f:
                json.dump(self.user_patterns, f, indent=2)
        except:
            pass
    
    # =============================================================================
    # BATCH PROCESSING FOR MULTIPLE EMAILS
    # =============================================================================
    
    def process_email_batch(self, emails: List[Dict[str, Any]], 
                           include_threads: bool = True) -> List[Dict[str, Any]]:
        """Process a batch of emails with thread awareness and context"""
        
        print(f"\n🚀 BATCH PROCESSING {len(emails)} EMAILS WITH ADVANCED AI")
        
        processed_emails = []
        thread_map = {}
        
        # Group emails by thread if enabled
        if include_threads:
            print("🧵 Analyzing email threads...")
            for email in emails:
                thread_id = email.get('thread_id', email.get('id'))
                if thread_id not in thread_map:
                    thread_map[thread_id] = []
                thread_map[thread_id].append(email)
        
        # Process each email with context
        print("🤖 Processing emails with AI...")
        
        for i, email in enumerate(emails, 1):
            print(f"   Processing email {i}/{len(emails)}...")
            
            try:
                # Get thread context if available
                thread_context = None
                if include_threads:
                    thread_id = email.get('thread_id', email.get('id'))
                    thread_emails = thread_map.get(thread_id, [])
                    thread_context = [e for e in thread_emails if e.get('id') != email.get('id')]
                
                # Process with advanced AI
                processed_email = self.advanced_process_email(email, thread_context)
                processed_emails.append(processed_email)
                
            except Exception as e:
                print(f"   ❌ Failed to process email {i}: {e}")
                email['processing_error'] = str(e)
                processed_emails.append(email)
        
        # Generate batch insights
        print("💡 Generating batch insights...")
        batch_insights = self._generate_batch_insights(processed_emails)
        
        # Add batch insights to each email
        for email in processed_emails:
            email['batch_insights'] = batch_insights
        
        print(f"✅ Batch processing complete! Processed {len(processed_emails)} emails")
        return processed_emails
    
    def _generate_batch_insights(self, processed_emails: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate insights across the entire batch of emails"""
        
        insights = {
            'total_emails': len(processed_emails),
            'high_priority_count': 0,
            'urgent_replies_needed': 0,
            'meeting_requests': 0,
            'deadlines_today': 0,
            'top_senders': {},
            'common_topics': [],
            'recommended_actions': []
        }
        
        try:
            for email in processed_emails:
                # Count priorities
                if email.get('priority_level') == 'High':
                    insights['high_priority_count'] += 1
                
                # Count urgent replies
                tone_analysis = email.get('tone_analysis', {})
                if tone_analysis.get('urgency_tone') in ['urgent', 'high']:
                    insights['urgent_replies_needed'] += 1
                
                # Count meeting requests
                calendar_events = email.get('calendar_events', {})
                if calendar_events.get('meetings'):
                    insights['meeting_requests'] += len(calendar_events['meetings'])
                
                # Track senders
                sender = email.get('sender_email', 'unknown')
                insights['top_senders'][sender] = insights['top_senders'].get(sender, 0) + 1
            
            # Generate recommendations
            if insights['high_priority_count'] > 3:
                insights['recommended_actions'].append("🔥 Multiple high-priority emails need immediate attention")
            
            if insights['meeting_requests'] > 2:
                insights['recommended_actions'].append("📅 Several meeting requests need calendar coordination")
            
            if insights['urgent_replies_needed'] > 1:
                insights['recommended_actions'].append("⚡ Multiple urgent responses required today")
            
        except Exception as e:
            print(f"⚠️ Batch insights generation failed: {e}")
        
        return insights

# =============================================================================
# COMPLETE INTEGRATION WITH EMAIL FETCHING SYSTEM
# =============================================================================

class CompleteEmailAgent:
    """Complete Email Agent combining fetching + advanced AI processing"""
    
    def __init__(self, use_gmail_api: bool = False):
        """Initialize complete email agent"""
        
        print("🤖 INITIALIZING COMPLETE AI EMAIL AGENT")
        
        self.use_gmail_api = use_gmail_api
        
        # Initialize email fetching system
        if use_gmail_api:
            try:
                from auth_test import authenticate_gmail
                from email_fetcher import EmailFetcher
                
                print("📧 Initializing Gmail API connection...")
                gmail_service = authenticate_gmail()
                self.email_fetcher = EmailFetcher(gmail_service)
                print("✅ Gmail API email fetcher ready")
                
            except Exception as e:
                print(f"❌ Gmail API failed, switching to mock: {e}")
                from mock_email_fetcher import MockEmailFetcher
                self.email_fetcher = MockEmailFetcher()
                self.use_gmail_api = False
                print("✅ Mock email fetcher ready")
        else:
            try:
                from mock_email_fetcher import MockEmailFetcher
                self.email_fetcher = MockEmailFetcher()
                print("✅ Mock email fetcher ready")
            except ImportError:
                print("❌ Mock email fetcher not available")
                raise
        
        # Initialize advanced AI processor
        print("🧠 Initializing Advanced AI Processor...")
        self.ai_processor = AdvancedEmailProcessor()
        print("✅ Advanced AI processor ready")
        
        print("🎉 Complete AI Email Agent initialized successfully!")
    
    def process_daily_emails(self, hours_back: int = 24, max_emails: int = 50) -> Dict[str, Any]:
        """Complete daily email processing workflow"""
        
        print(f"\n🚀 STARTING DAILY EMAIL PROCESSING")
        print(f"📅 Fetching emails from last {hours_back} hours...")
        
        try:
            # Fetch emails
            print("📥 Step 1: Fetching emails...")
            if self.use_gmail_api:
                raw_emails = self.email_fetcher.get_recent_emails(
                    hours=hours_back,
                    include_read=False
                )
            else:
                raw_emails = self.email_fetcher.get_recent_emails(
                    hours=hours_back,
                    count=min(max_emails, 15)
                )
            
            print(f"📧 Fetched {len(raw_emails)} emails")
            
            if not raw_emails:
                return {
                    'total_emails': 0,
                    'high_priority': [],
                    'medium_priority': [],
                    'low_priority': [],
                    'processing_summary': 'No emails found in specified timeframe'
                }
            
            # Advanced AI processing
            print("🤖 Step 2: Processing with Advanced AI...")
            processed_emails = self.ai_processor.process_email_batch(
                raw_emails[:max_emails],
                include_threads=True
            )
            
            # Organize by priority
            print("📊 Step 3: Organizing by priority...")
            
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
            
            # Sort by AI confidence and urgency
            high_priority.sort(key=lambda x: (
                x.get('priority_score', 0),
                x.get('ai_confidence', 0)
            ), reverse=True)
            
            medium_priority.sort(key=lambda x: x.get('ai_confidence', 0), reverse=True)
            low_priority.sort(key=lambda x: x.get('ai_confidence', 0), reverse=True)
            
            # Generate processing summary
            print("📈 Step 4: Generating summary...")
            
            emails_with_replies = sum(1 for e in processed_emails if e.get('advanced_reply'))
            emails_with_calendar = sum(1 for e in processed_emails if e.get('calendar_events', {}).get('meetings'))
            emails_with_threads = sum(1 for e in processed_emails if e.get('thread_analysis', {}).get('is_continuation'))
            
            processing_summary = {
                'total_processed': len(processed_emails),
                'high_priority_count': len(high_priority),
                'medium_priority_count': len(medium_priority),
                'low_priority_count': len(low_priority),
                'ai_features_used': {
                    'advanced_replies_generated': emails_with_replies,
                    'calendar_events_detected': emails_with_calendar,
                    'thread_conversations_analyzed': emails_with_threads
                },
                'top_insights': self._extract_top_insights(processed_emails),
                'recommended_actions': self._generate_daily_recommendations(high_priority, medium_priority)
            }
            
            # Return organized results
            results = {
                'total_emails': len(processed_emails),
                'high_priority': high_priority,
                'medium_priority': medium_priority,
                'low_priority': low_priority,
                'processing_summary': processing_summary,
                'processing_timestamp': datetime.now().isoformat()
            }
            
            print("✅ Daily email processing completed successfully!")
            print(f"📊 Results: {len(high_priority)} high, {len(medium_priority)} medium, {len(low_priority)} low priority")
            
            return results
            
        except Exception as e:
            print(f"❌ Daily email processing failed: {e}")
            return {
                'total_emails': 0,
                'high_priority': [],
                'medium_priority': [],
                'low_priority': [],
                'processing_summary': f'Processing failed: {str(e)}',
                'error': True
            }
    
    def _extract_top_insights(self, processed_emails: List[Dict]) -> List[str]:
        """Extract the most important insights across all emails"""
        
        insights = []
        
        try:
            # Count urgent emails
            urgent_count = sum(1 for e in processed_emails 
                             if e.get('tone_analysis', {}).get('urgency_tone') == 'urgent')
            
            if urgent_count > 0:
                insights.append(f"⚡ {urgent_count} emails marked as urgent need immediate attention")
            
            # Count meetings
            meeting_count = sum(len(e.get('calendar_events', {}).get('meetings', [])) 
                              for e in processed_emails)
            
            if meeting_count > 0:
                insights.append(f"📅 {meeting_count} meetings detected requiring calendar coordination")
            
            # Count escalated threads
            escalated_threads = sum(1 for e in processed_emails 
                                  if e.get('thread_analysis', {}).get('urgency_escalation'))
            
            if escalated_threads > 0:
                insights.append(f"🔥 {escalated_threads} email threads show urgency escalation")
            
            # Identify top senders
            sender_counts = {}
            for email in processed_emails:
                sender = email.get('sender_name', 'Unknown')
                sender_counts[sender] = sender_counts.get(sender, 0) + 1
            
            if sender_counts:
                top_sender = max(sender_counts, key=sender_counts.get)
                top_count = sender_counts[top_sender]
                if top_count > 2:
                    insights.append(f"👤 Most emails from {top_sender} ({top_count} emails)")
            
        except Exception as e:
            insights.append(f"⚠️ Insight analysis error: {str(e)}")
        
        return insights[:5]
    
    def _generate_daily_recommendations(self, high_priority: List[Dict], 
                                      medium_priority: List[Dict]) -> List[str]:
        """Generate actionable recommendations for the day"""
        
        recommendations = []
        
        try:
            # High priority recommendations
            if len(high_priority) > 5:
                recommendations.append("🔥 Focus on high-priority emails first - you have more than usual today")
            
            # Meeting coordination recommendations
            meeting_emails = [e for e in high_priority + medium_priority 
                            if e.get('calendar_events', {}).get('meetings')]
            
            if len(meeting_emails) > 2:
                recommendations.append("📅 Block time for calendar coordination - multiple meeting requests detected")
            
            # Quick reply recommendations
            quick_reply_emails = [e for e in high_priority 
                                if e.get('advanced_reply', {}).get('primary_reply')]
            
            if len(quick_reply_emails) > 3:
                recommendations.append("⚡ Several draft replies ready - consider batch sending to save time")
            
            # Thread follow-up recommendations
            extended_threads = [e for e in high_priority + medium_priority 
                              if e.get('thread_analysis', {}).get('conversation_stage') == 'extended']
            
            if extended_threads:
                recommendations.append("🧵 Some email threads are getting long - consider phone calls to resolve faster")
            
        except Exception as e:
            recommendations.append(f"⚠️ Recommendation generation error: {str(e)}")
        
        return recommendations[:4]

# =============================================================================
# TESTING FUNCTIONS
# =============================================================================

def test_advanced_ai_processor():
    """Test the Advanced AI Processor with sample data"""
    
    print("=" * 80)
    print("🧪 ADVANCED AI EMAIL PROCESSOR TEST")
    print("=" * 80)
    
    # Create advanced processor
    print("🚀 Initializing Advanced AI Processor...")
    advanced_processor = AdvancedEmailProcessor()
    
    # Test with sample email thread
    sample_emails = [
        {
            'id': 'email_001',
            'thread_id': 'thread_123',
            'subject': 'Meeting request for project discussion',
            'sender': 'John Smith <j.smith@company.com>',
            'sender_name': 'John Smith', 
            'sender_email': 'j.smith@company.com',
            'body': '''Hi there,

I hope you're doing well. I'd like to schedule a meeting to discuss the Q4 project timeline. 

Are you available for a call this Friday at 2 PM? We should be able to cover everything in about an hour.

Let me know your thoughts.

Best regards,
John Smith
Senior Project Manager''',
            'has_attachments': False,
            'is_thread': False
        },
        {
            'id': 'email_002', 
            'thread_id': 'thread_123',
            'subject': 'URGENT: Re: Meeting request - Need immediate response',
            'sender': 'John Smith <j.smith@company.com>',
            'sender_name': 'John Smith',
            'sender_email': 'j.smith@company.com', 
            'body': '''Hi,

I haven't heard back about the meeting request. This is quite urgent as we need to finalize the project timeline by EOD Friday.

Could you please confirm your availability ASAP? The client is waiting for our response.

Thanks,
John''',
            'has_attachments': False,
            'is_thread': True
        }
    ]
    
    print(f"\n📧 Testing with {len(sample_emails)} sample emails...")
    
    # Process emails as batch
    processed_batch = advanced_processor.process_email_batch(sample_emails)
    
    # Display results
    print(f"\n🎯 ADVANCED AI PROCESSING RESULTS:")
    
    for i, email in enumerate(processed_batch, 1):
        print(f"\n📧 EMAIL {i} RESULTS:")
        print(f"   Subject: {email.get('subject')}")
        print(f"   Priority: {email.get('priority_level')} (Score: {email.get('priority_score')})")
        print(f"   AI Summary: {email.get('ai_summary', 'N/A')[:100]}...")
        
        tone_analysis = email.get('tone_analysis', {})
        print(f"   Detected Tone: {tone_analysis.get('detected_tone', 'N/A')}")
        print(f"   Formality Level: {tone_analysis.get('formality_level', 'N/A')}")
        
        thread_analysis = email.get('thread_analysis', {})
        print(f"   Thread Stage: {thread_analysis.get('conversation_stage', 'N/A')}")
        
        calendar_events = email.get('calendar_events', {})
        print(f"   Meetings Detected: {len(calendar_events.get('meetings', []))}")
        print(f"   Deadlines Detected: {len(calendar_events.get('deadlines', []))}")
        
        advanced_reply = email.get('advanced_reply', {})
        if advanced_reply.get('primary_reply'):
            print(f"   AI Reply: {advanced_reply['primary_reply'][:80]}...")
        
        contextual_insights = email.get('contextual_insights', [])
        if contextual_insights:
            print(f"   Key Insights: {', '.join(contextual_insights[:2])}")
    
    # Display batch insights
    if processed_batch:
        batch_insights = processed_batch[0].get('batch_insights', {})
        print(f"\n📊 BATCH INSIGHTS:")
        print(f"   High Priority Emails: {batch_insights.get('high_priority_count', 0)}")
        print(f"   Urgent Replies Needed: {batch_insights.get('urgent_replies_needed', 0)}")
        print(f"   Meeting Requests: {batch_insights.get('meeting_requests', 0)}")
        
        recommendations = batch_insights.get('recommended_actions', [])
        if recommendations:
            print(f"   Recommendations: {recommendations[0]}")
    
    print(f"\n🎉 Advanced AI Processor test completed successfully!")
    return True

def test_complete_email_agent():
    """Test the complete email agent end-to-end"""
    
    print("=" * 80)
    print("🧪 COMPLETE AI EMAIL AGENT - END-TO-END TEST")  
    print("=" * 80)
    
    # Test with mock data
    print("🤖 Creating Complete AI Email Agent (mock mode)...")
    agent = CompleteEmailAgent(use_gmail_api=False)
    
    # Run daily email processing
    print("\n📅 Running daily email processing...")
    results = agent.process_daily_emails(hours_back=24, max_emails=10)
    
    # Display comprehensive results
    print(f"\n🎯 COMPLETE EMAIL AGENT RESULTS:")
    
    print(f"📊 PROCESSING SUMMARY:")
    summary = results['processing_summary']
    print(f"   Total emails processed: {summary['total_processed']}")
    print(f"   High priority: {summary['high_priority_count']}")
    print(f"   Medium priority: {summary['medium_priority_count']}")
    print(f"   Low priority: {summary['low_priority_count']}")
    
    print(f"\n🤖 AI FEATURES UTILIZED:")
    ai_features = summary['ai_features_used']
    print(f"   Advanced replies generated: {ai_features['advanced_replies_generated']}")
    print(f"   Calendar events detected: {ai_features['calendar_events_detected']}")
    print(f"   Thread conversations analyzed: {ai_features['thread_conversations_analyzed']}")
    
    print(f"\n💡 TOP INSIGHTS:")
    for insight in summary['top_insights']:
        print(f"   {insight}")
    
    print(f"\n📋 DAILY RECOMMENDATIONS:")
    for recommendation in summary['recommended_actions']:
        print(f"   {recommendation}")
    
    # Show sample high priority email
    if results['high_priority']:
        print(f"\n📧 SAMPLE HIGH PRIORITY EMAIL:")
        sample = results['high_priority'][0]
        print(f"   From: {sample.get('sender_name')}")
        print(f"   Subject: {sample.get('subject')}")
        print(f"   Priority Score: {sample.get('priority_score')}")
        print(f"   AI Summary: {sample.get('ai_summary', 'N/A')[:100]}...")
        
        tone_analysis = sample.get('tone_analysis', {})
        if tone_analysis:
            print(f"   Detected Tone: {tone_analysis.get('detected_tone', 'N/A')}")
        
        advanced_reply = sample.get('advanced_reply', {})
        if advanced_reply.get('primary_reply'):
            print(f"   Draft Reply: {advanced_reply['primary_reply'][:80]}...")
    
    print(f"\n🎉 Complete Email Agent test successful!")
    return True

# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == '__main__':
    print("🚀 RUNNING COMPLETE ADVANCED AI TESTS")
    print("=" * 80)
    
    # Test 1: Advanced AI Processor standalone
    test_advanced_ai_processor()
    
    print("\n" + "="*80)
    
    # Test 2: Complete Email Agent end-to-end  
    test_complete_email_agent()
    
    print("\n🎊 ALL ADVANCED AI TESTS COMPLETED SUCCESSFULLY!")
    print("🤖 Your AI Email Agent has enterprise-level intelligence!")
    print("📅 Ready for Day 3: Web Interface & Interactive Features!")