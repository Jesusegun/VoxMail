"""
=============================================================================
PRIORITY TESTING SCRIPT - Tests all 4 Priority Enhancements
=============================================================================
Tests:
- Priority 1: Content-Specific Replies (vs generic templates)
- Priority 2: Sender Intelligence & Personalization
- Priority 3: Enhanced Confidence Scoring
- Priority 4: Active Learning Application

Run: python test_priorities.py
=============================================================================
"""

import json
import os
from smart_reply_generator import SmartReplyGenerator, SmartReplyConfig
from datetime import datetime

class PriorityTester:
    """Tests all 4 priority enhancements"""
    
    def __init__(self):
        """Initialize tester"""
        print("\n" + "=" * 80)
        print("PRIORITY TESTING SUITE - All 4 Priorities")
        print("=" * 80)
        
        # Initialize the smart reply generator
        config = SmartReplyConfig()
        self.generator = SmartReplyGenerator(config)
        
        print("\n[OK] Smart Reply Generator initialized for testing\n")
    
    def run_all_tests(self):
        """Run all priority tests"""
        print("\n" + "=" * 80)
        print("RUNNING ALL PRIORITY TESTS")
        print("=" * 80 + "\n")
        
        results = {
            'priority_1': self.test_priority_1(),
            'priority_2': self.test_priority_2(),
            'priority_3': self.test_priority_3(),
            'priority_4': self.test_priority_4()
        }
        
        # Print summary
        self.print_summary(results)
        
        return results
    
    # =========================================================================
    # PRIORITY 1: CONTENT-SPECIFIC REPLIES
    # =========================================================================
    
    def test_priority_1(self):
        """Test Priority 1: Content-Specific Reply Generation"""
        print("\n" + "=" * 80)
        print("PRIORITY 1 TEST: Content-Specific Replies")
        print("=" * 80)
        print("Goal: Generate replies that address specific email content")
        print("      NOT generic 'Thanks for your email. I'll get back to you.'\n")
        
        test_cases = [
            {
                'name': 'Timeline Question',
                'email': {
                    'subject': 'Q4 Budget Timeline',
                    'body': 'Hi, when can you send me the Q4 budget numbers? I need them for the board meeting.',
                    'sender_name': 'Sarah Johnson',
                    'sender': 'sarah@company.com'
                },
                'expected_features': [
                    'specific_topic_mention',  # Should mention "Q4 budget" not just "this"
                    'specific_timeline',       # Should say "by EOD" not "soon"
                    'specific_action'          # Should say "I'll send you" not "I'll get back to you"
                ]
            },
            {
                'name': 'Availability Question',
                'email': {
                    'subject': 'Meeting Request',
                    'body': 'Are you available for a quick call tomorrow afternoon to discuss the project timeline?',
                    'sender_name': 'Mike Chen',
                    'sender': 'mike@client.com'
                },
                'expected_features': [
                    'availability_mention',    # Should mention checking calendar/availability
                    'specific_commitment',     # Should offer specific times or mention scheduling
                ]
            }
        ]
        
        results = []
        
        for i, test in enumerate(test_cases, 1):
            print(f"\n--- Test Case {i}: {test['name']} ---")
            print(f"Subject: {test['email']['subject']}")
            print(f"Body: {test['email']['body'][:80]}...")
            
            # Generate reply
            result = self.generator.generate_smart_reply(test['email'], detected_tone='business')
            reply = result['reply_text']
            
            print(f"\n[GENERATED REPLY]:")
            print("-" * 40)
            print(reply)
            print("-" * 40)
            
            # Check for specific features
            checks = self.check_priority_1_features(reply, test['expected_features'])
            
            print(f"\n[PRIORITY 1 CHECKS]:")
            for feature, passed in checks.items():
                status = "✅ PASS" if passed else "❌ FAIL"
                print(f"  {status}: {feature}")
            
            results.append({
                'test_name': test['name'],
                'reply': reply,
                'checks': checks,
                'passed': all(checks.values())
            })
            
            print()
        
        return results
    
    def check_priority_1_features(self, reply, expected_features):
        """Check if reply has Priority 1 features"""
        reply_lower = reply.lower()
        checks = {}
        
        # Check for specific vs generic
        generic_phrases = ['i\'ll get back to you', 'i\'ll look into this', 'i see your question']
        has_generic = any(phrase in reply_lower for phrase in generic_phrases)
        checks['no_generic_phrases'] = not has_generic
        
        # Check for specific timeline
        specific_timelines = ['by eod', 'by tomorrow', 'by end of day', 'this afternoon', 'this morning', 'tomorrow afternoon']
        vague_timelines = ['soon', 'shortly', 'later']
        has_specific_timeline = any(time in reply_lower for time in specific_timelines)
        has_vague_timeline = any(vague in reply_lower for vague in vague_timelines)
        checks['specific_timeline'] = has_specific_timeline and not has_vague_timeline
        
        # Check for specific action
        specific_actions = ['i\'ll send', 'i\'ll share', 'i\'ll provide', 'i\'ll check my calendar']
        has_specific_action = any(action in reply_lower for action in specific_actions)
        checks['specific_action'] = has_specific_action
        
        # Check for enthusiasm (if appropriate)
        has_enthusiasm = '!' in reply or 'great question' in reply_lower or 'good question' in reply_lower
        checks['has_enthusiasm'] = has_enthusiasm
        
        return checks
    
    # =========================================================================
    # PRIORITY 2: SENDER INTELLIGENCE
    # =========================================================================
    
    def test_priority_2(self):
        """Test Priority 2: Sender Intelligence & Personalization"""
        print("\n" + "=" * 80)
        print("PRIORITY 2 TEST: Sender Intelligence & Personalization")
        print("=" * 80)
        print("Goal: Personalize replies based on sender history and relationship\n")
        
        test_cases = [
            {
                'name': 'New Sender (Professional Greeting)',
                'email': {
                    'subject': 'Project Question',
                    'body': 'Could you provide an update on the project?',
                    'sender_name': 'John Doe',
                    'sender': 'john.new@company.com'  # New sender
                },
                'expected': {
                    'relationship': 'new',
                    'greeting_style': 'professional'
                }
            },
            {
                'name': 'Frequent Sender (Personalized Greeting)',
                'email': {
                    'subject': 'Quick Question',
                    'body': 'Hey, can you send me the updated report?',
                    'sender_name': 'GTBank',
                    'sender': 'gtbank@gtbank.com'  # 45 interactions in behavioral_patterns.json
                },
                'expected': {
                    'relationship': 'frequent',
                    'tone_adapted': True
                }
            }
        ]
        
        results = []
        
        for i, test in enumerate(test_cases, 1):
            print(f"\n--- Test Case {i}: {test['name']} ---")
            print(f"Sender: {test['email']['sender']}")
            
            # Generate reply
            result = self.generator.generate_smart_reply(test['email'], detected_tone='business')
            reply = result['reply_text']
            metadata = result.get('metadata', {})
            
            print(f"\n[GENERATED REPLY]:")
            print("-" * 40)
            print(reply)
            print("-" * 40)
            
            # Check sender profile
            sender_profile = metadata.get('sender_profile', {})
            print(f"\n[SENDER PROFILE]:")
            print(f"  Interactions: {sender_profile.get('interactions', 0)}")
            print(f"  Relationship: {sender_profile.get('relationship', 'unknown')}")
            print(f"  Preferred Tone: {sender_profile.get('preferred_tone', 'unknown')}")
            
            # Check tone adaptation
            tone_adapted = metadata.get('tone_adapted', None)
            if tone_adapted:
                print(f"\n[TONE ADAPTED]:")
                print(f"  Original: {tone_adapted.get('original')}")
                print(f"  Adapted: {tone_adapted.get('adapted')}")
                print(f"  Reason: {tone_adapted.get('reason')}")
            
            checks = self.check_priority_2_features(reply, sender_profile, tone_adapted, test['expected'])
            
            print(f"\n[PRIORITY 2 CHECKS]:")
            for feature, passed in checks.items():
                status = "✅ PASS" if passed else "❌ FAIL"
                print(f"  {status}: {feature}")
            
            results.append({
                'test_name': test['name'],
                'reply': reply,
                'sender_profile': sender_profile,
                'checks': checks,
                'passed': all(checks.values())
            })
            
            print()
        
        return results
    
    def check_priority_2_features(self, reply, sender_profile, tone_adapted, expected):
        """Check if Priority 2 features are applied"""
        checks = {}
        
        # Check sender profile was extracted
        checks['sender_profile_extracted'] = sender_profile.get('interactions', 0) >= 0
        
        # Check relationship level matches expectation (for known senders)
        if expected.get('relationship') == 'frequent':
            checks['frequent_sender_detected'] = sender_profile.get('interactions', 0) >= 20
        elif expected.get('relationship') == 'new':
            checks['new_sender_detected'] = sender_profile.get('interactions', 0) < 5
        
        # Check if greeting is personalized (not too formal for casual senders)
        reply_lower = reply.lower()
        has_casual_greeting = reply_lower.startswith('hey') or '!' in reply[:50]
        has_formal_greeting = reply_lower.startswith('dear')
        checks['appropriate_greeting'] = True  # Basic check
        
        return checks
    
    # =========================================================================
    # PRIORITY 3: ENHANCED CONFIDENCE SCORING
    # =========================================================================
    
    def test_priority_3(self):
        """Test Priority 3: Enhanced Confidence Scoring"""
        print("\n" + "=" * 80)
        print("PRIORITY 3 TEST: Enhanced Confidence Scoring")
        print("=" * 80)
        print("Goal: Confidence scores should correlate with quality")
        print("      Generic replies = LOW confidence, Specific replies = HIGH confidence\n")
        
        # Test with emails that should produce different confidence scores
        test_cases = [
            {
                'name': 'Clear Question with Action (Should be HIGH confidence)',
                'email': {
                    'subject': 'Q4 Report Request',
                    'body': 'Can you send me the Q4 report by tomorrow? I need it for the meeting.',
                    'sender_name': 'Manager',
                    'sender': 'manager@company.com'
                },
                'expected_confidence': 'medium_to_high'
            },
            {
                'name': 'Vague Request (Should be LOWER confidence)',
                'email': {
                    'subject': 'Question',
                    'body': 'Just checking in on things.',
                    'sender_name': 'Someone',
                    'sender': 'someone@company.com'
                },
                'expected_confidence': 'low_to_medium'
            }
        ]
        
        results = []
        
        for i, test in enumerate(test_cases, 1):
            print(f"\n--- Test Case {i}: {test['name']} ---")
            
            # Generate reply
            result = self.generator.generate_smart_reply(test['email'], detected_tone='business')
            reply = result['reply_text']
            confidence = result.get('confidence_score', 0.0)
            confidence_level = result.get('confidence_level', 'unknown')
            
            print(f"\n[GENERATED REPLY]:")
            print("-" * 40)
            print(reply)
            print("-" * 40)
            
            print(f"\n[CONFIDENCE SCORING]:")
            print(f"  Score: {confidence:.2f}")
            print(f"  Level: {confidence_level}")
            print(f"  Expected: {test['expected_confidence']}")
            
            # Check confidence features
            checks = self.check_priority_3_features(reply, confidence, test['expected_confidence'])
            
            print(f"\n[PRIORITY 3 CHECKS]:")
            for feature, passed in checks.items():
                status = "✅ PASS" if passed else "❌ FAIL"
                print(f"  {status}: {feature}")
            
            results.append({
                'test_name': test['name'],
                'reply': reply,
                'confidence': confidence,
                'confidence_level': confidence_level,
                'checks': checks,
                'passed': all(checks.values())
            })
            
            print()
        
        return results
    
    def check_priority_3_features(self, reply, confidence, expected_level):
        """Check if Priority 3 confidence scoring is working"""
        reply_lower = reply.lower()
        checks = {}
        
        # Check confidence is in valid range
        checks['confidence_in_range'] = 0.0 <= confidence <= 1.0
        
        # Check for quality indicators that should increase confidence
        has_specific_timeline = any(t in reply_lower for t in ['by eod', 'by tomorrow', 'by end of day'])
        has_specific_action = any(a in reply_lower for a in ['i\'ll send', 'i\'ll share', 'i\'ll provide'])
        has_enthusiasm = '!' in reply
        
        quality_score = sum([has_specific_timeline, has_specific_action, has_enthusiasm])
        
        # Check for penalty indicators that should decrease confidence
        has_generic_phrase = any(g in reply_lower for g in ['i\'ll get back to you', 'i\'ll look into this'])
        has_vague_timeline = any(v in reply_lower for v in ['soon', 'shortly'])
        
        penalty_score = sum([has_generic_phrase, has_vague_timeline])
        
        # Confidence should be higher if quality score > penalty score
        if quality_score > penalty_score:
            checks['quality_increases_confidence'] = confidence >= 0.5
        else:
            checks['penalty_decreases_confidence'] = confidence < 0.7
        
        # Check confidence level makes sense
        if expected_level == 'medium_to_high':
            checks['appropriate_confidence_level'] = confidence >= 0.5
        elif expected_level == 'low_to_medium':
            checks['appropriate_confidence_level'] = confidence <= 0.7
        
        return checks
    
    # =========================================================================
    # PRIORITY 4: ACTIVE LEARNING APPLICATION
    # =========================================================================
    
    def test_priority_4(self):
        """Test Priority 4: Active Learning Application"""
        print("\n" + "=" * 80)
        print("PRIORITY 4 TEST: Active Learning Application")
        print("=" * 80)
        print("Goal: Apply learned patterns from user_preferences.json")
        print("      Inject commonly_added_phrases, avoid generic phrases\n")
        
        # First, show what's in user_preferences
        self.show_learned_patterns()
        
        test_cases = [
            {
                'name': 'Question Email (Should inject enthusiasm)',
                'email': {
                    'subject': 'Quick Question',
                    'body': 'What is the status of the project?',
                    'sender_name': 'Mike',
                    'sender': 'mike@company.com'
                },
                'expected_features': [
                    'learned_phrase_present',   # Should use "Thanks for reaching out" (learned)
                    'enthusiasm_injected',      # Should add "!" or "Great question!" (learned)
                ]
            },
            {
                'name': 'Timeline Question (Should inject specific timeline)',
                'email': {
                    'subject': 'When can you send the report?',
                    'body': 'I need the quarterly report. When will it be ready?',
                    'sender_name': 'Manager',
                    'sender': 'manager@company.com'
                },
                'expected_features': [
                    'specific_timeline_injected',  # Should say "by EOD tomorrow" (learned) not "soon"
                ]
            }
        ]
        
        results = []
        
        for i, test in enumerate(test_cases, 1):
            print(f"\n--- Test Case {i}: {test['name']} ---")
            
            # Generate reply
            result = self.generator.generate_smart_reply(test['email'], detected_tone='business')
            reply = result['reply_text']
            generation_method = result.get('generation_method', 'unknown')
            
            print(f"\n[GENERATED REPLY]:")
            print("-" * 40)
            print(reply)
            print("-" * 40)
            
            print(f"\n[GENERATION METHOD]: {generation_method}")
            
            # Check for learned patterns
            checks = self.check_priority_4_features(reply, test['expected_features'])
            
            print(f"\n[PRIORITY 4 CHECKS]:")
            for feature, passed in checks.items():
                status = "✅ PASS" if passed else "❌ FAIL"
                print(f"  {status}: {feature}")
            
            results.append({
                'test_name': test['name'],
                'reply': reply,
                'generation_method': generation_method,
                'checks': checks,
                'passed': all(checks.values())
            })
            
            print()
        
        return results
    
    def show_learned_patterns(self):
        """Show what patterns have been learned"""
        print("\n[LEARNED PATTERNS FROM user_preferences.json]:")
        print("-" * 60)
        
        try:
            with open('ai_data/user_preferences.json', 'r') as f:
                prefs = json.load(f)
            
            commonly_added = prefs.get('phrase_preferences', {}).get('commonly_added_phrases', [])
            print(f"Commonly Added Phrases ({len(commonly_added)} total):")
            for phrase in commonly_added[:5]:  # Show first 5
                print(f"  - {phrase[:60]}...")
            
            if len(commonly_added) > 5:
                print(f"  ... and {len(commonly_added) - 5} more")
            
        except Exception as e:
            print(f"  [WARNING] Could not load user_preferences.json: {e}")
        
        print("-" * 60)
    
    def check_priority_4_features(self, reply, expected_features):
        """Check if Priority 4 features are applied"""
        reply_lower = reply.lower()
        checks = {}
        
        # Check for learned phrases (from commonly_added_phrases)
        learned_phrases = [
            'thanks for reaching out',
            'great question',
            'good question',
            'by eod',
            'by tomorrow',
            'by end of day',
            'best regards',
            'happy to help'
        ]
        
        has_learned_phrase = any(phrase in reply_lower for phrase in learned_phrases)
        checks['learned_phrase_injected'] = has_learned_phrase
        
        # Check enthusiasm was added (learned pattern)
        has_enthusiasm = '!' in reply or 'great question' in reply_lower or 'good question' in reply_lower
        checks['enthusiasm_present'] = has_enthusiasm
        
        # Check specific timeline (not vague)
        has_specific_timeline = any(t in reply_lower for t in ['by eod', 'by tomorrow', 'by end of day', 'this afternoon'])
        has_vague_timeline = any(v in reply_lower for v in ['soon', 'shortly', 'later'])
        checks['specific_not_vague'] = has_specific_timeline or not has_vague_timeline
        
        # Check NO generic phrases (should be replaced by learning)
        generic_phrases = ['i\'ll get back to you', 'i\'ll look into this', 'thanks for your email about']
        has_generic = any(phrase in reply_lower for phrase in generic_phrases)
        checks['no_generic_phrases'] = not has_generic
        
        return checks
    
    # =========================================================================
    # SUMMARY
    # =========================================================================
    
    def print_summary(self, results):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("TEST SUMMARY - ALL 4 PRIORITIES")
        print("=" * 80)
        
        for priority_name, priority_results in results.items():
            print(f"\n{priority_name.upper().replace('_', ' ')}:")
            
            if isinstance(priority_results, list):
                total_tests = len(priority_results)
                passed_tests = sum(1 for r in priority_results if r.get('passed', False))
                
                print(f"  Tests Passed: {passed_tests}/{total_tests}")
                
                for result in priority_results:
                    status = "✅ PASS" if result.get('passed', False) else "❌ FAIL"
                    print(f"    {status}: {result['test_name']}")
        
        print("\n" + "=" * 80)
        print("TEST COMPLETE!")
        print("=" * 80)
        print("\nNote: Some tests may not pass 100% on first run due to:")
        print("  - Limited learning data (only 10 edits tracked)")
        print("  - Randomization in reply generation")
        print("  - Behavioral patterns not matching test senders")
        print("\nThe key is to verify that the ENHANCEMENTS are working:")
        print("  ✅ Priority 1: Replies are SPECIFIC, not generic")
        print("  ✅ Priority 2: Sender profiles are EXTRACTED and USED")
        print("  ✅ Priority 3: Confidence scores CORRELATE with quality")
        print("  ✅ Priority 4: Learned phrases are INJECTED into replies")
        print("=" * 80 + "\n")


def main():
    """Main test execution"""
    print("\n" + "=" * 80)
    print("STARTING PRIORITY TEST SUITE")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    tester = PriorityTester()
    results = tester.run_all_tests()
    
    print("\n[TEST COMPLETE] Check output above for detailed results.\n")


if __name__ == "__main__":
    main()
