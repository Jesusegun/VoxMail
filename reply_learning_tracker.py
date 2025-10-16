# =============================================================================
# REPLY LEARNING TRACKER - Phase 3
# =============================================================================
# Tracks user edits to AI-generated replies and learns from patterns
# 
# Features:
# - Track original vs edited replies
# - Analyze edit patterns (tone changes, length adjustments, phrase preferences)
# - Learn user communication style
# - Adapt confidence scoring based on historical accuracy
# - Build user-specific preference profiles
# =============================================================================

import json
import os
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import warnings
warnings.filterwarnings('ignore')

try:
    from textblob import TextBlob
    from difflib import SequenceMatcher
    import numpy as np
    print("[OK] Learning system libraries loaded")
except ImportError as e:
    print(f"[ERROR] Learning libraries missing: {e}")


# =============================================================================
# LEARNING DATA STRUCTURES
# =============================================================================

@dataclass
class ReplyEdit:
    """Records a single edit instance"""
    edit_id: str
    timestamp: str
    email_subject: str
    email_category: str
    sender_name: str
    original_reply: str
    edited_reply: str
    generation_method: str  # ai_enhanced, safe_mode, legacy_template
    original_confidence: float
    tone_detected: str
    edit_similarity: float  # 0.0 to 1.0
    edit_type: str  # minor_tweak, moderate_change, major_rewrite, complete_rejection
    changes_detected: Dict[str, Any]  # tone_shift, length_change, phrase_additions, etc.


# =============================================================================
# REPLY LEARNING TRACKER
# =============================================================================

class ReplyLearningTracker:
    """
    Tracks and analyzes user edits to learn communication preferences
    """
    
    def __init__(self, data_dir: str = "ai_data"):
        """Initialize the learning tracker"""
        
        print("[INFO] Initializing Reply Learning Tracker (Phase 3)...")
        
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        # Data files
        self.edits_file = os.path.join(data_dir, "reply_edits.json")
        self.preferences_file = os.path.join(data_dir, "user_preferences.json")
        self.learning_stats_file = os.path.join(data_dir, "learning_stats.json")
        
        # Load existing data
        self.edits_history: List[ReplyEdit] = []
        self.user_preferences: Dict[str, Any] = {}
        self.learning_stats: Dict[str, Any] = {}
        
        self._load_data()
        self._initialize_preferences()
        
        print("[OK] Reply Learning Tracker ready")
    
    def _load_data(self):
        """Load existing learning data"""
        
        # Load edits history
        if os.path.exists(self.edits_file):
            try:
                with open(self.edits_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.edits_history = [ReplyEdit(**edit) for edit in data]
                print(f"[OK] Loaded {len(self.edits_history)} historical edits")
            except Exception as e:
                print(f"[WARNING] Failed to load edits: {e}")
        
        # Load preferences
        if os.path.exists(self.preferences_file):
            try:
                with open(self.preferences_file, 'r', encoding='utf-8') as f:
                    self.user_preferences = json.load(f)
                print(f"[OK] Loaded user preferences")
            except Exception as e:
                print(f"[WARNING] Failed to load preferences: {e}")
        
        # Load stats
        if os.path.exists(self.learning_stats_file):
            try:
                with open(self.learning_stats_file, 'r', encoding='utf-8') as f:
                    self.learning_stats = json.load(f)
                print(f"[OK] Loaded learning statistics")
            except Exception as e:
                print(f"[WARNING] Failed to load stats: {e}")
    
    def _initialize_preferences(self):
        """Initialize default preference structure"""
        
        if not self.user_preferences:
            self.user_preferences = {
                'communication_style': {
                    'preferred_tone': 'business',  # formal, business, casual
                    'formality_level': 0.6,  # 0.0 (casual) to 1.0 (formal)
                    'verbosity': 0.5,  # 0.0 (concise) to 1.0 (detailed)
                    'friendliness': 0.5  # 0.0 (professional) to 1.0 (friendly)
                },
                'phrase_preferences': {
                    'preferred_openings': [],
                    'preferred_closings': [],
                    'avoided_phrases': [],
                    'commonly_added_phrases': []
                },
                'structural_preferences': {
                    'avg_reply_length': 0,
                    'uses_bullet_points': False,
                    'includes_action_items': True,
                    'mentions_deadlines_explicitly': True
                },
                'confidence_adjustments': {
                    'ai_enhanced_accuracy': 1.0,  # multiplier based on acceptance rate
                    'safe_mode_accuracy': 1.0,
                    'by_category': {}  # category-specific adjustments
                },
                'learning_metadata': {
                    'total_edits_tracked': 0,
                    'last_updated': datetime.now().isoformat(),
                    'learning_confidence': 0.0  # 0.0 to 1.0, how confident we are in patterns
                }
            }
    
    def track_reply_edit(self, 
                        email_data: Dict[str, Any],
                        original_reply: str,
                        edited_reply: str,
                        reply_metadata: Dict[str, Any]) -> ReplyEdit:
        """
        Track a user edit to a generated reply
        
        Args:
            email_data: Original email information
            original_reply: AI-generated reply
            edited_reply: User-edited reply
            reply_metadata: Metadata from reply generation
            
        Returns:
            ReplyEdit object with analysis
        """
        
        print(f"[INFO] Tracking reply edit for: {email_data.get('subject', 'No Subject')}")
        
        # Calculate similarity
        similarity = self._calculate_similarity(original_reply, edited_reply)
        
        # Determine edit type
        edit_type = self._classify_edit_type(similarity, original_reply, edited_reply)
        
        # Analyze changes
        changes = self._analyze_changes(original_reply, edited_reply)
        
        # Create edit record
        edit = ReplyEdit(
            edit_id=f"edit_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.edits_history)}",
            timestamp=datetime.now().isoformat(),
            email_subject=email_data.get('subject', ''),
            email_category=reply_metadata.get('email_category', 'unknown'),
            sender_name=email_data.get('sender_name', ''),
            original_reply=original_reply,
            edited_reply=edited_reply,
            generation_method=reply_metadata.get('generation_method', 'unknown'),
            original_confidence=reply_metadata.get('confidence_score', 0.0),
            tone_detected=reply_metadata.get('tone', 'business'),
            edit_similarity=similarity,
            edit_type=edit_type,
            changes_detected=changes
        )
        
        # Add to history
        self.edits_history.append(edit)
        
        # Update preferences based on this edit
        self._update_preferences(edit)
        
        # Save data
        self._save_data()
        
        print(f"[OK] Edit tracked: {edit_type} (similarity: {similarity:.2f})")
        
        return edit
    
    def _calculate_similarity(self, original: str, edited: str) -> float:
        """Calculate similarity between original and edited replies"""
        
        if not original or not edited:
            return 0.0
        
        # Use SequenceMatcher for similarity
        return SequenceMatcher(None, original.lower(), edited.lower()).ratio()
    
    def _classify_edit_type(self, similarity: float, original: str, edited: str) -> str:
        """Classify the type of edit made"""
        
        if similarity >= 0.95:
            return 'minor_tweak'  # Small punctuation/word changes
        elif similarity >= 0.70:
            return 'moderate_change'  # Rephrasing but keeping structure
        elif similarity >= 0.40:
            return 'major_rewrite'  # Significant changes
        else:
            return 'complete_rejection'  # Completely different reply
    
    def _analyze_changes(self, original: str, edited: str) -> Dict[str, Any]:
        """Analyze what changed between original and edited"""
        
        changes = {
            'length_change': len(edited) - len(original),
            'length_change_percent': ((len(edited) - len(original)) / max(len(original), 1)) * 100,
            'tone_shift': None,
            'added_phrases': [],
            'removed_phrases': [],
            'structure_changes': []
        }
        
        # Detect tone shift
        try:
            orig_sentiment = TextBlob(original).sentiment.polarity
            edit_sentiment = TextBlob(edited).sentiment.polarity
            
            if edit_sentiment - orig_sentiment > 0.2:
                changes['tone_shift'] = 'more_positive'
            elif edit_sentiment - orig_sentiment < -0.2:
                changes['tone_shift'] = 'more_negative'
            else:
                changes['tone_shift'] = 'similar'
        except:
            changes['tone_shift'] = 'unknown'
        
        # Find added phrases (simple approach)
        orig_sentences = set(original.lower().split('.'))
        edit_sentences = set(edited.lower().split('.'))
        
        added = edit_sentences - orig_sentences
        removed = orig_sentences - edit_sentences
        
        changes['added_phrases'] = [s.strip() for s in added if len(s.strip()) > 10][:5]
        changes['removed_phrases'] = [s.strip() for s in removed if len(s.strip()) > 10][:5]
        
        # Detect structure changes
        if '\n\n' in edited and '\n\n' not in original:
            changes['structure_changes'].append('added_paragraphs')
        if '•' in edited or '-' in edited[:len(edited)//2]:  # bullets in first half
            if not ('•' in original or '-' in original[:len(original)//2]):
                changes['structure_changes'].append('added_bullet_points')
        
        return changes
    
    def _update_preferences(self, edit: ReplyEdit):
        """Update user preferences based on edit"""
        
        prefs = self.user_preferences
        
        # Update communication style
        if edit.edit_type in ['minor_tweak', 'moderate_change']:
            # User accepted most of the reply, this is good
            if edit.generation_method == 'ai_enhanced':
                prefs['confidence_adjustments']['ai_enhanced_accuracy'] = min(1.2,
                    prefs['confidence_adjustments']['ai_enhanced_accuracy'] * 1.02)
        elif edit.edit_type == 'complete_rejection':
            # User rejected the reply, reduce confidence
            if edit.generation_method == 'ai_enhanced':
                prefs['confidence_adjustments']['ai_enhanced_accuracy'] = max(0.5,
                    prefs['confidence_adjustments']['ai_enhanced_accuracy'] * 0.95)
        
        # Track length preferences
        changes = edit.changes_detected
        current_avg = prefs['structural_preferences']['avg_reply_length']
        new_length = len(edit.edited_reply)
        
        if current_avg == 0:
            prefs['structural_preferences']['avg_reply_length'] = new_length
        else:
            # Moving average
            prefs['structural_preferences']['avg_reply_length'] = int(current_avg * 0.9 + new_length * 0.1)
        
        # Track phrase preferences
        if changes['added_phrases']:
            prefs['phrase_preferences']['commonly_added_phrases'].extend(changes['added_phrases'])
            # Keep only recent 20
            prefs['phrase_preferences']['commonly_added_phrases'] = \
                prefs['phrase_preferences']['commonly_added_phrases'][-20:]
        
        # Update metadata
        prefs['learning_metadata']['total_edits_tracked'] += 1
        prefs['learning_metadata']['last_updated'] = datetime.now().isoformat()
        
        # Calculate learning confidence (based on number of edits)
        edit_count = prefs['learning_metadata']['total_edits_tracked']
        prefs['learning_metadata']['learning_confidence'] = min(1.0, edit_count / 50)
    
    def get_confidence_adjustment(self, 
                                 generation_method: str, 
                                 category: str = None) -> float:
        """
        Get confidence adjustment multiplier based on learning
        
        Returns:
            Multiplier to apply to base confidence (0.5 to 1.2)
        """
        
        adjustments = self.user_preferences['confidence_adjustments']
        
        # Get base adjustment for method
        if generation_method == 'ai_enhanced':
            base = adjustments.get('ai_enhanced_accuracy', 1.0)
        elif generation_method == 'safe_mode':
            base = adjustments.get('safe_mode_accuracy', 1.0)
        else:
            base = 1.0
        
        # Apply category-specific adjustment if available
        if category and category in adjustments.get('by_category', {}):
            category_adj = adjustments['by_category'][category]
            base = base * category_adj
        
        return base
    
    def get_learning_insights(self) -> Dict[str, Any]:
        """Get insights from learning data"""
        
        if not self.edits_history:
            return {'message': 'No edits tracked yet'}
        
        # Calculate statistics
        total_edits = len(self.edits_history)
        edit_types = Counter(edit.edit_type for edit in self.edits_history)
        avg_similarity = np.mean([edit.edit_similarity for edit in self.edits_history])
        
        # Acceptance rate (minor_tweak + moderate_change = accepted)
        accepted = edit_types.get('minor_tweak', 0) + edit_types.get('moderate_change', 0)
        acceptance_rate = (accepted / total_edits) * 100 if total_edits > 0 else 0
        
        # Method performance
        method_performance = defaultdict(lambda: {'total': 0, 'accepted': 0})
        for edit in self.edits_history:
            method = edit.generation_method
            method_performance[method]['total'] += 1
            if edit.edit_type in ['minor_tweak', 'moderate_change']:
                method_performance[method]['accepted'] += 1
        
        insights = {
            'total_edits_tracked': total_edits,
            'overall_acceptance_rate': f"{acceptance_rate:.1f}%",
            'average_similarity': f"{avg_similarity:.2f}",
            'edit_type_distribution': dict(edit_types),
            'method_performance': {
                method: {
                    'total': stats['total'],
                    'acceptance_rate': f"{(stats['accepted']/stats['total']*100):.1f}%"
                }
                for method, stats in method_performance.items()
            },
            'learning_confidence': self.user_preferences['learning_metadata']['learning_confidence'],
            'preferred_reply_length': self.user_preferences['structural_preferences']['avg_reply_length']
        }
        
        return insights
    
    def _save_data(self):
        """Save all learning data"""
        
        try:
            # Save edits
            with open(self.edits_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(edit) for edit in self.edits_history], f, indent=2)
            
            # Save preferences
            with open(self.preferences_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_preferences, f, indent=2)
            
            # Save stats
            stats = self.get_learning_insights()
            with open(self.learning_stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2)
            
        except Exception as e:
            print(f"[ERROR] Failed to save learning data: {e}")


# =============================================================================
# TESTING FUNCTION
# =============================================================================

def test_learning_tracker():
    """Test the learning tracker"""
    
    print("\n" + "=" * 80)
    print("TESTING REPLY LEARNING TRACKER (PHASE 3)")
    print("=" * 80)
    
    tracker = ReplyLearningTracker()
    
    # Simulate some edits
    test_cases = [
        {
            'email': {'subject': 'Meeting Request', 'sender_name': 'Sarah'},
            'original': "Hi Sarah,\n\nThanks for your email about the meeting. I'll check my schedule and get back to you.\n\nBest",
            'edited': "Hi Sarah,\n\nThanks for reaching out about the meeting! I'll check my calendar and send you some times that work.\n\nBest regards",
            'metadata': {'generation_method': 'ai_enhanced', 'confidence_score': 0.85, 'tone': 'business', 'email_category': 'meeting_request'}
        },
        {
            'email': {'subject': 'Quick Question', 'sender_name': 'Mike'},
            'original': "Hi Mike,\n\nThanks for your question. I'll look into this and get back to you.\n\nBest",
            'edited': "Hey Mike,\n\nGreat question! Let me dig into this and I'll get back to you soon.\n\nThanks!",
            'metadata': {'generation_method': 'ai_enhanced', 'confidence_score': 0.75, 'tone': 'business', 'email_category': 'question'}
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n[TEST {i}] Tracking edit...")
        edit = tracker.track_reply_edit(
            case['email'],
            case['original'],
            case['edited'],
            case['metadata']
        )
        print(f"  Edit Type: {edit.edit_type}")
        print(f"  Similarity: {edit.edit_similarity:.2f}")
        print(f"  Length Change: {edit.changes_detected['length_change']} chars")
    
    # Get insights
    print("\n" + "=" * 80)
    print("LEARNING INSIGHTS")
    print("=" * 80)
    insights = tracker.get_learning_insights()
    print(json.dumps(insights, indent=2))
    
    print("\n[OK] Learning tracker test complete!")


if __name__ == "__main__":
    test_learning_tracker()
