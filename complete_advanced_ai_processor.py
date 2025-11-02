# =============================================================================
# COMPLETE ADVANCED AI SYSTEM - complete_advanced_ai_system.py
# =============================================================================
# DAY 2 AFTERNOON: Complete Enhanced AI Email Agent System
# 
# This is the COMPLETE file with all advanced features:
# - Advanced reply generation with tone matching
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
    print("[OK] Base AI Processor imported from Day 2 Morning")
except ImportError:
    print("[ERROR] Cannot import base AI processor. Make sure ai_processor.py exists from Day 2 Morning")
    exit(1)

# Import Smart Reply Generator (Phase 1 + 2)
try:
    from smart_reply_generator import SmartReplyGenerator, SmartReplyConfig
    print("[OK] Smart Reply Generator (Phase 1+2) imported")
except ImportError:
    print("[ERROR] Cannot import smart_reply_generator. Make sure smart_reply_generator.py exists")
    SmartReplyGenerator = None

# Additional imports for advanced features
try:
    import spacy
    from transformers import pipeline
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from textblob import TextBlob
    print("[OK] Advanced AI libraries loaded")
except ImportError as e:
    print(f"[ERROR] Advanced AI libraries missing: {e}")

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
        
        print("[INIT] Initializing Advanced AI Email Processor...")
        
        # Store advanced config
        self.advanced_config = base_config
        
        # Initialize advanced components
        self._initialize_advanced_systems()
        self._initialize_template_system()
        self._initialize_thread_system()
        self._initialize_behavioral_learning()
        
        # Initialize Smart Reply Generator (Phase 1 + 2)
        self._initialize_smart_reply_generator()
        
        print("[OK] Advanced AI Email Processor ready!")
    
    def _initialize_advanced_systems(self):
        """Initialize advanced AI systems and models"""
        
        print("[BRAIN] Loading advanced AI models...")
        
        try:
            # Load advanced sentiment analysis for tone detection
            self.models['advanced_sentiment'] = pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base",
                device=-1
            )
            print("[OK] Advanced emotion detection model loaded")
        except:
            print("[WARNING] Advanced emotion model not available, using base sentiment")
        
        try:
            # Initialize text similarity for template matching
            self.advanced_tfidf = TfidfVectorizer(
                max_features=2000,
                stop_words='english',
                ngram_range=(1, 3),
                lowercase=True
            )
            print("[OK] Advanced text similarity system initialized")
        except:
            print("[WARNING] Advanced similarity system failed to initialize")
        
        # Conversation context analyzer
        self.conversation_contexts = {}
        self.user_communication_patterns = {}
        
        print("[OK] Advanced systems initialized")
    
    def _initialize_smart_reply_generator(self):
        """Initialize Smart Reply Generator (Phase 1 + 2)"""
        
        print("[AI] Initializing Smart Reply Generator (Phase 1+2)...")
        
        if SmartReplyGenerator is None:
            print("[WARNING] Smart Reply Generator not available, using legacy templates")
            self.smart_reply_generator = None
            return
        
        try:
            # Create configuration for smart reply generator
            smart_config = SmartReplyConfig(
                min_confidence_threshold=0.60,
                high_confidence_threshold=0.80,
                detect_sensitive_topics=True,
                use_safe_mode_for_sensitive=True,
                track_user_edits=True,
                adapt_to_preferences=True
            )
            
            # Initialize the generator
            self.smart_reply_generator = SmartReplyGenerator(smart_config)
            print("[OK] Smart Reply Generator ready (BART + spaCy + Safety)")
            
        except Exception as e:
            print(f"[WARNING] Smart Reply Generator initialization failed: {e}")
            self.smart_reply_generator = None
    
    def _initialize_template_system(self):
        """Initialize intelligent template system for replies"""
        
        print("[NOTE] Initializing smart template system...")
        
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
        
        print("[OK] Smart template system ready")
    
    def _initialize_thread_system(self):
        """Initialize email thread analysis and conversation tracking"""
        
        print("[THREAD] Initializing thread intelligence...")
        
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
        
        print("[OK] Thread intelligence system ready")
    
    def _initialize_behavioral_learning(self):
        """Initialize behavioral learning and adaptation system"""
        
        print("[EMOJI] Initializing behavioral learning...")
        
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
        
        print("[OK] Behavioral learning system ready")
    
    # =============================================================================
    # ADVANCED EMAIL PROCESSING METHODS
    # =============================================================================
    
    def advanced_process_email(self, email_data: Dict[str, Any], 
                             thread_context: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Advanced email processing with contextual awareness"""
        
        print(f"\n[INIT] ADVANCED AI PROCESSING: {email_data.get('subject', 'No Subject')}")
        
        # PERFORMANCE: Track AI operation times
        import time
        ai_timing = {}
        
        # Start with base processing
        base_start = time.time()
        processed_email = super().process_email(email_data)
        ai_timing['base_processing'] = time.time() - base_start
        
        try:
            # Thread context analysis
            if self.advanced_config.thread_analysis_enabled:
                print("[THREAD] Analyzing thread context...")
                thread_start = time.time()
                thread_analysis = self.analyze_thread_context(email_data, thread_context)
                processed_email['thread_analysis'] = thread_analysis
                ai_timing['thread_analysis'] = time.time() - thread_start
            
            # Advanced tone analysis
            if self.advanced_config.tone_analysis_enabled:
                print("[EMOJI] Advanced tone analysis...")
                tone_start = time.time()
                tone_analysis = self.analyze_communication_tone(email_data, processed_email)
                processed_email['tone_analysis'] = tone_analysis
                ai_timing['tone_analysis'] = time.time() - tone_start
            
            # Advanced reply generation
            print("[EMOJI] Advanced reply generation...")
            reply_start = time.time()
            advanced_reply = self.generate_advanced_reply(
                email_data, 
                processed_email, 
                thread_context
            )
            processed_email['advanced_reply'] = advanced_reply
            ai_timing['reply_generation'] = time.time() - reply_start
            
            # Contextual insights generation
            print("[IDEA] Generating contextual insights...")
            contextual_insights = self.generate_contextual_insights(
                processed_email, 
                thread_context
            )
            processed_email['contextual_insights'] = contextual_insights
            
            # Behavioral learning update
            if self.advanced_config.behavioral_learning_enabled:
                print("[EMOJI] Updating behavioral learning...")
                self.update_behavioral_patterns(email_data, processed_email)
            
            # Advanced metadata
            processed_email.update({
                'advanced_processing_version': '2.0',
                'advanced_features_enabled': {
                    'thread_analysis': self.advanced_config.thread_analysis_enabled,
                    'tone_analysis': self.advanced_config.tone_analysis_enabled,
                    'behavioral_learning': self.advanced_config.behavioral_learning_enabled
                },
                'processing_timestamp': datetime.now().isoformat(),
                'ai_timing': ai_timing  # Add timing breakdown
            })
            
            # PERFORMANCE: Log timing breakdown
            total_time = sum(ai_timing.values())
            print(f"[OK] Advanced AI processing completed in {total_time:.2f}s")
            for operation, duration in ai_timing.items():
                print(f"  ├─ {operation}: {duration:.2f}s ({duration/total_time*100:.1f}%)")
            
            return processed_email
            
        except Exception as e:
            print(f"[ERROR] Advanced processing failed: {e}")
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
            print(f"[WARNING] Thread analysis failed: {e}")
        
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
            print(f"[WARNING] Tone analysis failed: {e}")
        
        return tone_analysis
    
    def generate_advanced_reply(self, email_data: Dict[str, Any], 
                              processed_data: Dict[str, Any],
                              thread_context: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Generate advanced, contextually aware draft reply using Smart Reply Generator
        (Phase 1 + 2 Integration)
        """
        
        reply_data = {
            'primary_reply': '',
            'alternative_replies': [],
            'reply_metadata': {
                'tone_matched': False,
                'context_aware': False,
                'template_used': '',
                'personalization_level': 'standard',
                'generation_method': 'legacy',  # legacy, ai_enhanced, safe_mode, no_reply
                'confidence_score': 0.0,
                'confidence_level': 'low',
                'sensitive_detected': False,
                'requires_manual_review': False
            }
        }
        
        try:
            # Get tone analysis
            tone_analysis = processed_data.get('tone_analysis', {})
            detected_tone = tone_analysis.get('detected_tone', 'business')
            
            # === PHASE 1+2: USE SMART REPLY GENERATOR ===
            if self.smart_reply_generator is not None:
                try:
                    # Prepare email data for smart generator
                    smart_email_data = {
                        'subject': email_data.get('subject', ''),
                        'body': email_data.get('body', ''),
                        'sender': email_data.get('sender', ''),
                        'sender_name': email_data.get('sender_name', 'there')
                    }
                    
                    # Generate smart reply
                    smart_result = self.smart_reply_generator.generate_smart_reply(
                        email_data=smart_email_data,
                        detected_tone=detected_tone
                    )
                    
                    # Extract results (NEW: Handle None for no-reply emails)
                    reply_data['primary_reply'] = smart_result['reply_text']  # Can be None
                    reply_data['reply_metadata'].update({
                        'tone_matched': True,
                        'context_aware': True,
                        'generation_method': smart_result['generation_method'],
                        'confidence_score': smart_result['confidence_score'],
                        'confidence_level': smart_result['confidence_level'],
                        'personalization_level': 'high' if smart_result['confidence_score'] >= 0.80 else 'medium'
                    })
                    
                    # NEW: Add reply necessity metadata
                    if 'reply_necessity' in smart_result['metadata']:
                        rn = smart_result['metadata']['reply_necessity']
                        reply_data['reply_metadata'].update({
                            'reply_needed': rn.get('needs_reply', True),
                            'necessity_level': rn.get('necessity_level', 'optional'),
                            'email_intent': rn.get('email_intent', 'general'),
                            'suggested_action': rn.get('suggested_action', '')
                        })
                    
                    # NEW: Add reply recommendation for no-reply emails
                    if 'reply_recommendation' in smart_result['metadata']:
                        reply_data['reply_metadata']['reply_recommendation'] = smart_result['metadata']['reply_recommendation']
                    
                    # Add safety metadata
                    if 'sensitive_analysis' in smart_result['metadata']:
                        sa = smart_result['metadata']['sensitive_analysis']
                        reply_data['reply_metadata'].update({
                            'sensitive_detected': sa['is_sensitive'],
                            'sensitive_categories': sa.get('categories', []),
                            'risk_level': sa.get('risk_level', 'low'),
                            'requires_manual_review': sa.get('requires_manual_review', False)
                        })
                    
                    # Add edge case metadata
                    if 'edge_case_analysis' in smart_result['metadata']:
                        eca = smart_result['metadata']['edge_case_analysis']
                        reply_data['reply_metadata']['edge_case_detected'] = eca['is_edge_case']
                        if eca['is_edge_case']:
                            reply_data['reply_metadata']['edge_case_type'] = eca['edge_case_type']
                    
                    print(f"[OK] Smart reply generated (Confidence: {smart_result['confidence_score']:.2f}, Method: {smart_result['generation_method']})")
                    return reply_data
                    
                except Exception as e:
                    print(f"[WARNING] Smart reply generation failed: {e}, falling back to legacy templates")
            
            # === LEGACY TEMPLATE SYSTEM (Fallback) ===
            # Get thread analysis
            thread_analysis = processed_data.get('thread_analysis', {})
            
            # Determine reply context type
            reply_context = self._determine_reply_context(email_data, processed_data, thread_context)
            
            # Check if this email type needs a reply
            if reply_context['category'] == 'no_reply_needed':
                reply_data['reply_metadata']['generation_method'] = 'no_reply'
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
                    'personalization_level': 'medium',
                    'generation_method': 'legacy_template'
                })
            
            else:
                # Fallback to base reply generation
                reply_data['primary_reply'] = processed_data.get('draft_reply', 
                    self._generate_fallback_reply(email_data['sender_name']))
                reply_data['reply_metadata']['generation_method'] = 'legacy_fallback'
            
        except Exception as e:
            print(f"[ERROR] Advanced reply generation failed: {e}")
            reply_data['primary_reply'] = f"Hi {email_data.get('sender_name', 'there')},\n\nThank you for your email. I'll review and respond accordingly.\n\nBest regards"
            reply_data['reply_metadata']['generation_method'] = 'error_fallback'
        
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
                insights.append(f"[THREAD] Conversation stage: {stage}")
                
                if thread_analysis.get('urgency_escalation'):
                    insights.append("[WARNING] Urgency has escalated in this thread")
            
            # Tone-based insights
            tone_analysis = processed_email.get('tone_analysis', {})
            if tone_analysis.get('emotional_state') in ['negative', 'frustrated']:
                insights.append("[EMOTION] Sender may be frustrated - consider empathetic response")
            elif tone_analysis.get('urgency_tone') == 'urgent':
                insights.append("[EMOJI] High urgency detected - prioritize immediate response")
            
            # Priority-based insights
            priority_level = processed_email.get('priority_level')
            priority_reasons = processed_email.get('priority_reasons', [])
            
            if priority_level == 'High' and len(priority_reasons) > 2:
                insights.append("[FIRE] Multiple high-priority indicators - requires immediate attention")
            
            # Entity-based insights
            entities = processed_email.get('extracted_entities', {})
            if entities.get('people') and len(entities['people']) > 3:
                insights.append("[EMOJI] Multiple people mentioned - may be group coordination needed")
            
            if entities.get('money'):
                insights.append("[EMOJI] Financial information mentioned - handle with care")
            
            # Attachment insights
            if processed_email.get('has_attachments'):
                attachment_count = processed_email.get('attachment_count', 0)
                if attachment_count > 2:
                    insights.append(f"[EMOJI] {attachment_count} attachments - document review required")
            
            # AI confidence insights
            ai_confidence = processed_email.get('ai_confidence', 0)
            if ai_confidence < 0.7:
                insights.append("[EMOJI] AI confidence lower than usual - manual review recommended")
            
        except Exception as e:
            print(f"[WARNING] Insight generation failed: {e}")
        
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
                    template_vars['deadline'] = 'end of day'
                else:
                    template_vars['deadline'] = 'shortly'
            
            # Format template with all variables
            personalized = template.format(**template_vars)
            return personalized
            
        except Exception as e:
            print(f"[WARNING] Template personalization failed: {e}")
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
            print(f"[WARNING] Behavioral pattern update failed: {e}")
    
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
    # BATCH PROCESSING FOR MULTIPLE EMAILS (OPTIMIZED)
    # =============================================================================
    
    def process_email_batch_optimized(self, emails: List[Dict[str, Any]], 
                                      batch_size: int = 10) -> List[Dict[str, Any]]:
        """
        OPTIMIZED batch processing with batched AI inference for BART and RoBERTa
        
        This method groups emails into batches and processes them through AI models
        simultaneously, dramatically reducing processing time.
        
        Args:
            emails: List of raw email dictionaries
            batch_size: Number of emails to process in each batch (default: 10)
            
        Returns:
            List of processed email dictionaries with AI insights
        """
        
        print(f"\n[ROCKET] OPTIMIZED BATCH PROCESSING {len(emails)} EMAILS")
        print(f"[INFO] Using batch size: {batch_size}")
        
        import time
        batch_start = time.time()
        
        processed_emails = []
        
        # Split emails into batches
        for batch_idx in range(0, len(emails), batch_size):
            batch = emails[batch_idx:batch_idx + batch_size]
            batch_num = (batch_idx // batch_size) + 1
            total_batches = (len(emails) + batch_size - 1) // batch_size
            
            print(f"\n[BATCH {batch_num}/{total_batches}] Processing {len(batch)} emails...")
            batch_process_start = time.time()
            
            # ========================================================
            # STEP 1: BATCH SUMMARIZATION (BART)
            # ========================================================
            print("[BRAIN] Batch summarizing emails with BART...")
            summaries_start = time.time()
            
            summaries = self._batch_summarize(batch)
            
            summaries_time = time.time() - summaries_start
            print(f"⏱️  Batch summarization: {summaries_time:.2f}s ({summaries_time/len(batch):.2f}s per email)")
            
            # ========================================================
            # STEP 2: INDIVIDUAL PROCESSING (Priority, Entities, etc.)
            # ========================================================
            print("[TARGET] Processing priority, entities, and metadata...")
            individual_start = time.time()
            
            batch_results = []
            for idx, email in enumerate(batch):
                # Start with base email data
                processed = email.copy()
                
                # Add AI summary from batch
                processed['ai_summary'] = summaries[idx]
                
                # Priority analysis (includes RoBERTa sentiment)
                priority_level, priority_score, reasons = self.calculate_priority(email)
                processed['priority_level'] = priority_level
                processed['priority_score'] = priority_score
                processed['priority_reasons'] = reasons
                
                # Entity extraction (spaCy)
                processed['extracted_entities'] = self.extract_entities_and_dates(email)
                
                # Confidence and metadata
                processed['ai_confidence'] = self._calculate_confidence_score(processed)
                processed['actionable_insights'] = self._generate_insights(processed)
                processed['ai_processed_at'] = datetime.now().isoformat()
                
                batch_results.append(processed)
            
            individual_time = time.time() - individual_start
            print(f"⏱️  Individual processing: {individual_time:.2f}s ({individual_time/len(batch):.2f}s per email)")
            
            # ========================================================
            # STEP 3: SELECTIVE REPLY GENERATION (PHASE 4 OPTIMIZATION)
            # ========================================================
            print("[EMOJI] Generating replies for High/Medium priority emails (Phase 4)...")
            replies_start = time.time()
            
            # Count how many emails get replies
            reply_count = sum(1 for p in batch_results if p['priority_level'] in ['High', 'Medium'])
            skipped_count = len(batch_results) - reply_count
            print(f"[INFO] Generating replies for {reply_count} emails, skipping {skipped_count} low-priority")
            
            # Generate replies ONLY for High/Medium priority emails
            for idx, email in enumerate(batch):
                processed = batch_results[idx]
                
                # Get tone for reply matching
                tone_analysis = self.analyze_communication_tone(email, processed)
                processed['tone_analysis'] = tone_analysis
                
                # Add thread analysis
                thread_analysis = self.analyze_thread_context(email, None)
                processed['thread_analysis'] = thread_analysis
                
                # PHASE 4: Only generate replies for important emails
                if processed['priority_level'] in ['High', 'Medium']:
                    # Generate reply for high/medium priority
                    advanced_reply = self.generate_advanced_reply(email, processed, None)
                    processed['advanced_reply'] = advanced_reply
                    
                    # Extract metadata
                    reply_metadata = advanced_reply.get('reply_metadata', {})
                    processed['reply_confidence'] = reply_metadata.get('confidence_score', 0.0)
                    processed['reply_method'] = reply_metadata.get('generation_method', 'unknown')
                    processed['is_sensitive'] = reply_metadata.get('sensitive_detected', False)
                else:
                    # Skip reply generation for low-priority emails
                    processed['advanced_reply'] = {
                        'primary_reply': None,
                        'alternative_replies': [],
                        'reply_metadata': {
                            'generation_method': 'skipped_low_priority',
                            'confidence_score': 0.0,
                            'tone_matched': False,
                            'context_aware': False,
                            'skip_reason': 'Low priority email - reply not needed'
                        }
                    }
                    processed['reply_confidence'] = 0.0
                    processed['reply_method'] = 'skipped_low_priority'
                    processed['is_sensitive'] = False
                
                # Add contextual insights
                processed['contextual_insights'] = self.generate_contextual_insights(processed, None)
                
                # Update behavioral learning
                if self.advanced_config.behavioral_learning_enabled:
                    self.update_behavioral_patterns(email, processed)
            
            replies_time = time.time() - replies_start
            print(f"⏱️  Reply generation: {replies_time:.2f}s ({replies_time/len(batch):.2f}s per email)")
            
            # Add to final results
            processed_emails.extend(batch_results)
            
            batch_time = time.time() - batch_process_start
            print(f"✅ Batch {batch_num} complete: {batch_time:.2f}s total ({batch_time/len(batch):.2f}s per email)")
        
        total_time = time.time() - batch_start
        
        # Calculate Phase 4 savings
        total_replies_generated = sum(1 for e in processed_emails if e.get('reply_method') != 'skipped_low_priority')
        total_replies_skipped = sum(1 for e in processed_emails if e.get('reply_method') == 'skipped_low_priority')
        
        print(f"\n[PARTY] OPTIMIZED BATCH COMPLETE!")
        print(f"⏱️  Total time: {total_time:.2f}s ({total_time/len(emails):.2f}s per email)")
        print(f"🚀 Processed {len(processed_emails)} emails")
        print(f"\n📊 PHASE 4 OPTIMIZATION:")
        print(f"  ✅ Replies generated: {total_replies_generated} (High/Medium priority)")
        print(f"  ⚡ Replies skipped: {total_replies_skipped} (Low priority)")
        print(f"  💰 Time saved: ~{total_replies_skipped * 30:.0f}s by skipping low-priority replies!")
        
        return processed_emails
    
    def _batch_summarize(self, emails: List[Dict[str, Any]]) -> List[str]:
        """
        Batch summarize multiple emails using BART
        
        Args:
            emails: List of email dictionaries
            
        Returns:
            List of summary strings (one per email)
        """
        summaries = []
        
        try:
            if self.models.get('summarizer'):
                # Prepare batch of email texts
                email_texts = []
                for email in emails:
                    subject = email.get('subject', '')
                    body = email.get('body', '')
                    text = f"{subject}\n\n{body}"
                    
                    # Clean and limit text
                    cleaned = re.sub(r'\s+', ' ', text).strip()
                    if len(cleaned) > 1000:
                        cleaned = cleaned[:1000]
                    
                    email_texts.append(cleaned)
                
                # Check if emails are long enough for summarization
                needs_summarization = []
                for idx, text in enumerate(email_texts):
                    word_count = len(text.split())
                    if word_count >= 50:  # Minimum words for summarization
                        needs_summarization.append((idx, text))
                
                if needs_summarization:
                    # Batch process emails that need summarization
                    indices, texts = zip(*needs_summarization)
                    
                    print(f"[BART] Summarizing {len(texts)} emails in batch...")
                    
                    # BART batch inference
                    batch_summaries = self.models['summarizer'](
                        list(texts),
                        max_length=100,
                        min_length=30,
                        do_sample=False,
                        batch_size=len(texts)  # Process all at once
                    )
                    
                    # Create results dictionary
                    summary_map = {}
                    for idx, summary_result in zip(indices, batch_summaries):
                        summary_map[idx] = summary_result['summary_text']
                    
                    # Build final summaries list with fallbacks for short emails
                    for idx, text in enumerate(email_texts):
                        if idx in summary_map:
                            summaries.append(summary_map[idx])
                        else:
                            # Email too short, use cleaned text
                            summaries.append(text[:200])
                else:
                    # All emails too short for summarization
                    print("[INFO] All emails too short for BART, using cleaned text")
                    summaries = [text[:200] for text in email_texts]
            
            else:
                # Fallback: extractive summarization
                print("[FALLBACK] Using extractive summarization")
                for email in emails:
                    text = f"{email.get('subject', '')} {email.get('body', '')}"
                    summaries.append(self._extractive_summarization(text))
        
        except Exception as e:
            print(f"[ERROR] Batch summarization failed: {e}")
            # Fallback to individual summaries
            for email in emails:
                summaries.append(self.summarize_email(email))
        
        return summaries
    
    def process_email_batch(self, emails: List[Dict[str, Any]], 
                           include_threads: bool = True) -> List[Dict[str, Any]]:
        """Process a batch of emails with thread awareness and context"""
        
        print(f"\n[INIT] BATCH PROCESSING {len(emails)} EMAILS WITH ADVANCED AI")
        
        processed_emails = []
        thread_map = {}
        
        # Group emails by thread if enabled
        if include_threads:
            print("[THREAD] Analyzing email threads...")
            for email in emails:
                thread_id = email.get('thread_id', email.get('id'))
                if thread_id not in thread_map:
                    thread_map[thread_id] = []
                thread_map[thread_id].append(email)
        
        # Process each email with context
        print("[AI] Processing emails with AI...")
        
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
                print(f"   [ERROR] Failed to process email {i}: {e}")
                email['processing_error'] = str(e)
                processed_emails.append(email)
        
        # Generate batch insights
        print("[IDEA] Generating batch insights...")
        batch_insights = self._generate_batch_insights(processed_emails)
        
        # Add batch insights to each email
        for email in processed_emails:
            email['batch_insights'] = batch_insights
        
        print(f"[OK] Batch processing complete! Processed {len(processed_emails)} emails")
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
                
                # Track senders
                sender = email.get('sender_email', 'unknown')
                insights['top_senders'][sender] = insights['top_senders'].get(sender, 0) + 1
            
            # Generate recommendations
            if insights['high_priority_count'] > 3:
                insights['recommended_actions'].append("[FIRE] Multiple high-priority emails need immediate attention")
            
            if insights['urgent_replies_needed'] > 1:
                insights['recommended_actions'].append("[EMOJI] Multiple urgent responses required today")
            
        except Exception as e:
            print(f"[WARNING] Batch insights generation failed: {e}")
        
        return insights

# =============================================================================
# COMPLETE INTEGRATION WITH EMAIL FETCHING SYSTEM
# =============================================================================

class CompleteEmailAgent:
    """Complete Email Agent combining fetching + advanced AI processing"""
    
    def __init__(self, use_gmail_api: bool = False):
        """Initialize complete email agent"""
        
        print("[AI] INITIALIZING COMPLETE AI EMAIL AGENT")
        
        self.use_gmail_api = use_gmail_api
        
        # Initialize email fetching system
        if use_gmail_api:
            try:
                # Use multi-user auth (auth_test.py is deprecated)
                try:
                    import auth_multiuser
                    from email_fetcher import EmailFetcher
                    # Note: Multi-user auth requires user-specific token paths
                    # For CompleteEmailAgent, use mock mode unless user provides token
                    print("[EMAIL] Gmail API requires user-specific authentication")
                    print("[EMAIL] Switching to mock mode (use UserManager for real Gmail access)")
                    raise ImportError("Use UserManager.get_user_gmail_service() for Gmail access")
                except ImportError:
                    pass
                
                from mock_email_fetcher import MockEmailFetcher
                self.email_fetcher = MockEmailFetcher()
                self.use_gmail_api = False
                print("[OK] Mock email fetcher ready")
        else:
            try:
                from mock_email_fetcher import MockEmailFetcher
                self.email_fetcher = MockEmailFetcher()
                print("[OK] Mock email fetcher ready")
            except ImportError:
                print("[ERROR] Mock email fetcher not available")
                raise
        
        # Initialize advanced AI processor
        print("[BRAIN] Initializing Advanced AI Processor...")
        self.ai_processor = AdvancedEmailProcessor()
        print("[OK] Advanced AI processor ready")
        
        print("[PARTY] Complete AI Email Agent initialized successfully!")
    
    def process_daily_emails(self, hours_back: int = 24, max_emails: int = 50) -> Dict[str, Any]:
        """Complete daily email processing workflow"""
        
        print(f"\n[INIT] STARTING DAILY EMAIL PROCESSING")
        print(f"[EMOJI] Fetching emails from last {hours_back} hours...")
        
        try:
            # Fetch emails
            print("[EMOJI] Step 1: Fetching emails...")
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
            
            print(f"[EMAIL] Fetched {len(raw_emails)} emails")
            
            if not raw_emails:
                return {
                    'total_emails': 0,
                    'high_priority': [],
                    'medium_priority': [],
                    'low_priority': [],
                    'processing_summary': 'No emails found in specified timeframe'
                }
            
            # Advanced AI processing
            print("[AI] Step 2: Processing with Advanced AI...")
            processed_emails = self.ai_processor.process_email_batch(
                raw_emails[:max_emails],
                include_threads=True
            )
            
            # Organize by priority
            print("[INFO] Step 3: Organizing by priority...")
            
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
            print("[CHART] Step 4: Generating summary...")
            
            emails_with_replies = sum(1 for e in processed_emails if e.get('advanced_reply'))
            emails_with_threads = sum(1 for e in processed_emails if e.get('thread_analysis', {}).get('is_continuation'))
            
            processing_summary = {
                'total_processed': len(processed_emails),
                'high_priority_count': len(high_priority),
                'medium_priority_count': len(medium_priority),
                'low_priority_count': len(low_priority),
                'ai_features_used': {
                    'advanced_replies_generated': emails_with_replies,
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
            
            print("[OK] Daily email processing completed successfully!")
            print(f"[INFO] Results: {len(high_priority)} high, {len(medium_priority)} medium, {len(low_priority)} low priority")
            
            return results
            
        except Exception as e:
            print(f"[ERROR] Daily email processing failed: {e}")
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
                insights.append(f"[EMOJI] {urgent_count} emails marked as urgent need immediate attention")
            
            # Count escalated threads
            escalated_threads = sum(1 for e in processed_emails 
                                  if e.get('thread_analysis', {}).get('urgency_escalation'))
            
            if escalated_threads > 0:
                insights.append(f"[FIRE] {escalated_threads} email threads show urgency escalation")
            
            # Identify top senders
            sender_counts = {}
            for email in processed_emails:
                sender = email.get('sender_name', 'Unknown')
                sender_counts[sender] = sender_counts.get(sender, 0) + 1
            
            if sender_counts:
                top_sender = max(sender_counts, key=sender_counts.get)
                top_count = sender_counts[top_sender]
                if top_count > 2:
                    insights.append(f"[EMOJI] Most emails from {top_sender} ({top_count} emails)")
            
        except Exception as e:
            insights.append(f"[WARNING] Insight analysis error: {str(e)}")
        
        return insights[:5]
    
    def _generate_daily_recommendations(self, high_priority: List[Dict], 
                                      medium_priority: List[Dict]) -> List[str]:
        """Generate actionable recommendations for the day"""
        
        recommendations = []
        
        try:
            # High priority recommendations
            if len(high_priority) > 5:
                recommendations.append("[FIRE] Focus on high-priority emails first - you have more than usual today")
            
            # Quick reply recommendations
            quick_reply_emails = [e for e in high_priority 
                                if e.get('advanced_reply', {}).get('primary_reply')]
            
            if len(quick_reply_emails) > 3:
                recommendations.append("[EMOJI] Several draft replies ready - consider batch sending to save time")
            
            # Thread follow-up recommendations
            extended_threads = [e for e in high_priority + medium_priority 
                              if e.get('thread_analysis', {}).get('conversation_stage') == 'extended']
            
            if extended_threads:
                recommendations.append("[THREAD] Some email threads are getting long - consider phone calls to resolve faster")
            
        except Exception as e:
            recommendations.append(f"[WARNING] Recommendation generation error: {str(e)}")
        
        return recommendations[:4]

# =============================================================================
# MODULE END
# =============================================================================
