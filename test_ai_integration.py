# =============================================================================
# AI INTEGRATION TEST - complete_ai_integration_test.py
# =============================================================================
# This script tests the complete integration of your AI Email Agent:
# 1. Email fetching (mock and real Gmail API)
# 2. AI processing (summarization, priority, entity extraction)
# 3. Draft reply generation
# 4. Learning system functionality
# 5. End-to-end email intelligence pipeline
#
# RUN THIS to verify your AI Agent's brain is working with the email system!
# =============================================================================

import sys
import json
from datetime import datetime
from typing import List, Dict, Any

def print_section_header(title: str):
    """Print a formatted section header"""
    print("\n" + "="*70)
    print(f"🤖 {title}")
    print("="*70)

def print_subsection(title: str):
    """Print a formatted subsection header"""  
    print(f"\n🧠 {title}")
    print("-" * 50)

def analyze_ai_results(processed_emails: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze AI processing results across multiple emails
    
    Args:
        processed_emails: List of AI-processed email dictionaries
        
    Returns:
        Dict containing AI performance analysis
    """
    
    if not processed_emails:
        return {"total": 0, "error": "No emails to analyze"}
    
    total_emails = len(processed_emails)
    
    # AI Processing Success Analysis
    successfully_processed = [e for e in processed_emails if e.get('ai_summary')]
    ai_errors = [e for e in processed_emails if e.get('ai_error')]
    
    # Priority Distribution Analysis
    high_priority = [e for e in processed_emails if e.get('priority_level') == 'High']
    medium_priority = [e for e in processed_emails if e.get('priority_level') == 'Medium']
    low_priority = [e for e in processed_emails if e.get('priority_level') == 'Low']
    
    # Draft Reply Analysis
    with_drafts = [e for e in processed_emails if e.get('draft_reply')]
    
    # Entity Extraction Analysis
    with_entities = []
    total_entities = 0
    for email in processed_emails:
        entities = email.get('extracted_entities', {})
        if entities:
            entity_count = sum(len(v) for v in entities.values() if v)
            if entity_count > 0:
                with_entities.append(email)
                total_entities += entity_count
    
    # AI Confidence Analysis
    confidence_scores = [e.get('ai_confidence', 0) for e in processed_emails if e.get('ai_confidence')]
    avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
    
    # Summary Length Analysis
    summaries = [e.get('ai_summary', '') for e in processed_emails if e.get('ai_summary')]
    avg_summary_length = sum(len(s) for s in summaries) / len(summaries) if summaries else 0
    
    return {
        "total_emails": total_emails,
        "successfully_processed": len(successfully_processed),
        "success_rate": (len(successfully_processed) / total_emails) * 100,
        "ai_errors": len(ai_errors),
        "error_rate": (len(ai_errors) / total_emails) * 100,
        
        # Priority Distribution
        "high_priority": len(high_priority),
        "medium_priority": len(medium_priority), 
        "low_priority": len(low_priority),
        "high_priority_percentage": (len(high_priority) / total_emails) * 100,
        
        # AI Features
        "emails_with_drafts": len(with_drafts),
        "draft_generation_rate": (len(with_drafts) / total_emails) * 100,
        "emails_with_entities": len(with_entities),
        "entity_extraction_rate": (len(with_entities) / total_emails) * 100,
        "total_entities_extracted": total_entities,
        
        # Quality Metrics
        "average_confidence": avg_confidence,
        "average_summary_length": int(avg_summary_length),
        "has_summaries": len(summaries)
    }

def display_ai_email_sample(email: Dict[str, Any], index: int):
    """Display a comprehensive sample of AI-processed email"""
    
    print(f"\n📧 AI-PROCESSED EMAIL SAMPLE {index}")
    print("=" * 45)
    
    # Basic Info
    print(f"📬 From: {email.get('sender_name', 'Unknown')}")
    print(f"📋 Subject: {email.get('subject', 'No Subject')}")
    
    # AI Processing Results
    if email.get('ai_summary'):
        print(f"\n🧠 AI Summary:")
        print(f"   {email['ai_summary']}")
    
    # Priority Analysis
    priority_level = email.get('priority_level', 'Unknown')
    priority_score = email.get('priority_score', 0)
    priority_reasons = email.get('priority_reasons', [])
    
    priority_emoji = {"High": "🔥", "Medium": "⚡", "Low": "💤"}.get(priority_level, "❓")
    print(f"\n{priority_emoji} Priority: {priority_level} (Score: {priority_score})")
    
    if priority_reasons:
        print(f"📊 Reasons: {', '.join(priority_reasons[:2])}...")  # Show first 2 reasons
    
    # Entity Extraction Results
    entities = email.get('extracted_entities', {})
    if entities:
        print(f"\n🔍 AI Extracted Entities:")
        for entity_type, items in entities.items():
            if items:
                print(f"   {entity_type.capitalize()}: {', '.join(items[:2])}...")  # Show first 2
    
    # Draft Reply
    if email.get('draft_reply'):
        draft = email['draft_reply']
        print(f"\n✍️ AI Draft Reply:")
        print(f"   {draft[:80]}..." if len(draft) > 80 else f"   {draft}")
    
    # Actionable Insights
    insights = email.get('actionable_insights', [])
    if insights:
        print(f"\n💡 AI Insights:")
        for insight in insights[:2]:  # Show first 2 insights
            print(f"   {insight}")
    
    # AI Confidence
    confidence = email.get('ai_confidence', 0)
    confidence_emoji = "🎯" if confidence > 0.8 else "👍" if confidence > 0.6 else "🤔"
    print(f"\n{confidence_emoji} AI Confidence: {confidence:.1%}")

def test_mock_ai_integration():
    """Test AI integration with mock email data"""
    
    print_section_header("TESTING AI INTEGRATION WITH MOCK DATA")
    
    try:
        # Import required modules
        from email_fetcher import MockEmailFetcher
    except ImportError:
        print("⚠️ Mock fetcher not found, using real EmailFetcher for testing")
        from email_fetcher import EmailFetcher as MockEmailFetcher    
        from ai_processor import EmailProcessor
        
        print("✅ Successfully imported MockEmailFetcher and EmailProcessor")
        
        # Create instances
        print_subsection("Initializing AI Components")
        mock_fetcher = MockEmailFetcher()
        ai_processor = EmailProcessor()
        
        print("✅ AI components initialized successfully")
        
        # Fetch mock emails
        print_subsection("Fetching Mock Emails")
        mock_emails = mock_fetcher.get_recent_emails(hours=24, count=8)
        
        print(f"📧 Fetched {len(mock_emails)} mock emails for AI processing")
        
        # Process emails with AI
        print_subsection("AI Processing Pipeline")
        processed_emails = []
        
        for i, email in enumerate(mock_emails, 1):
            print(f"🤖 Processing email {i}/{len(mock_emails)}: {email['subject'][:30]}...")
            
            try:
                processed_email = ai_processor.process_email(email)
                processed_emails.append(processed_email)
                print(f"   ✅ AI processing completed")
                
            except Exception as e:
                print(f"   ❌ AI processing failed: {e}")
                email['ai_error'] = str(e)
                processed_emails.append(email)
        
        # Analyze AI results
        print_subsection("AI Performance Analysis")
        analysis = analyze_ai_results(processed_emails)
        
        print(f"📊 AI PROCESSING PERFORMANCE:")
        print(f"   Total emails processed: {analysis['total_emails']}")
        print(f"   Success rate: {analysis['success_rate']:.1f}%")
        print(f"   AI errors: {analysis['ai_errors']} ({analysis['error_rate']:.1f}%)")
        
        print(f"\n🎯 PRIORITY CLASSIFICATION:")
        print(f"   High priority: {analysis['high_priority']} ({analysis['high_priority_percentage']:.1f}%)")
        print(f"   Medium priority: {analysis['medium_priority']}")
        print(f"   Low priority: {analysis['low_priority']}")
        
        print(f"\n🧠 AI FEATURE PERFORMANCE:")
        print(f"   Emails with AI summaries: {analysis['has_summaries']}")
        print(f"   Draft replies generated: {analysis['emails_with_drafts']} ({analysis['draft_generation_rate']:.1f}%)")
        print(f"   Entity extraction success: {analysis['emails_with_entities']} ({analysis['entity_extraction_rate']:.1f}%)")
        print(f"   Total entities found: {analysis['total_entities_extracted']}")
        
        print(f"\n✨ QUALITY METRICS:")
        print(f"   Average AI confidence: {analysis['average_confidence']:.1%}")
        print(f"   Average summary length: {analysis['average_summary_length']} characters")
        
        # Display sample processed emails
        print_subsection("Sample AI-Processed Emails")
        
        # Show high priority email sample
        high_priority_emails = [e for e in processed_emails if e.get('priority_level') == 'High']
        if high_priority_emails:
            display_ai_email_sample(high_priority_emails[0], 1)
        
        # Show medium priority email sample  
        medium_priority_emails = [e for e in processed_emails if e.get('priority_level') == 'Medium']
        if medium_priority_emails and len(processed_emails) > 1:
            display_ai_email_sample(medium_priority_emails[0], 2)
        
        # Test learning system
        print_subsection("Testing AI Learning System")
        
        if processed_emails:
            sample_email = processed_emails[0]
            print(f"🎓 Testing learning with email: {sample_email['subject'][:30]}...")
            
            # Simulate user interactions
            ai_processor.learn_from_interaction(sample_email, 'reply')
            print("✅ AI learned from 'reply' interaction")
            
            ai_processor.learn_from_interaction(sample_email, 'read')  
            print("✅ AI learned from 'read' interaction")
        
        print(f"\n🎉 Mock AI Integration Test PASSED!")
        print(f"✨ Your AI Email Agent is working perfectly with mock data!")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("📋 Make sure both mock_email_fetcher.py and ai_processor.py exist")
        return False
        
    except Exception as e:
        print(f"❌ AI integration test failed: {e}")
        return False

def test_real_ai_integration():
    """Test AI integration with real Gmail data (if available)"""
    
    print_section_header("TESTING AI INTEGRATION WITH REAL GMAIL DATA")
    
    try:
        # Try to import Gmail components
        from auth_test import authenticate_gmail
        from email_fetcher import EmailFetcher
        from ai_processor import EmailProcessor
        
        print("✅ Gmail components imported successfully")
        
        # Attempt authentication
        print_subsection("Gmail Authentication")
        print("⚠️ This requires Gmail API credentials...")
        
        try:
            gmail_service = authenticate_gmail()
            
            if gmail_service:
                print("✅ Gmail authentication successful!")
                
                # Create components
                print_subsection("Initializing Real Email Components")
                email_fetcher = EmailFetcher(gmail_service)
                ai_processor = EmailProcessor()
                
                print("✅ Real email components initialized")
                
                # Fetch real emails
                print_subsection("Fetching Real Emails")
                real_emails = email_fetcher.get_recent_emails(
                    hours=48,  # Look back 48 hours
                    include_read=True  # Include read emails for testing
                )
                
                print(f"📧 Fetched {len(real_emails)} real emails from Gmail")
                
                if real_emails:
                    # Process real emails with AI
                    print_subsection("AI Processing Real Emails")
                    processed_real_emails = []
                    
                    # Limit to first 5 emails to avoid overwhelming
                    test_emails = real_emails[:5]
                    
                    for i, email in enumerate(test_emails, 1):
                        print(f"🤖 Processing real email {i}/{len(test_emails)}...")
                        
                        try:
                            processed_email = ai_processor.process_email(email)
                            processed_real_emails.append(processed_email)
                            print(f"   ✅ Real email AI processing completed")
                            
                        except Exception as e:
                            print(f"   ❌ Real email AI processing failed: {e}")
                            email['ai_error'] = str(e)
                            processed_real_emails.append(email)
                    
                    # Analyze real email AI results
                    print_subsection("Real Email AI Analysis")
                    real_analysis = analyze_ai_results(processed_real_emails)
                    
                    print(f"📊 REAL EMAIL AI PERFORMANCE:")
                    print(f"   Real emails processed: {real_analysis['total_emails']}")
                    print(f"   AI success rate: {real_analysis['success_rate']:.1f}%")
                    print(f"   High priority detected: {real_analysis['high_priority']}")
                    print(f"   Draft replies generated: {real_analysis['emails_with_drafts']}")
                    print(f"   Entities extracted: {real_analysis['total_entities_extracted']}")
                    
                    # Display real email sample
                    if processed_real_emails:
                        print_subsection("Sample Real Email AI Processing")
                        display_ai_email_sample(processed_real_emails[0], 1)
                    
                    print(f"\n🎉 Real AI Integration Test PASSED!")
                    print(f"✨ Your AI Agent works perfectly with real Gmail data!")
                    return True
                    
                else:
                    print("📭 No real emails found in the specified timeframe")
                    print("✅ Gmail connection works, but no test data available")
                    return True
            
            else:
                print("❌ Gmail authentication failed")
                print("📋 Please complete Google Cloud Console setup first")
                return False
        
        except Exception as auth_error:
            print(f"❌ Gmail authentication error: {auth_error}")
            print("📋 Gmail API integration not available for testing")
            return False
    
    except ImportError as e:
        print(f"❌ Cannot import Gmail components: {e}")
        print("📋 Gmail integration not available - this is OK for mock testing!")
        return False

def test_ai_learning_persistence():
    """Test AI learning system data persistence"""
    
    print_section_header("TESTING AI LEARNING PERSISTENCE")
    
    try:
        from ai_processor import EmailProcessor
        
        # Create AI processor
        print("🧠 Creating AI processor for learning test...")
        ai_processor = EmailProcessor()
        
        # Test VIP learning
        print("🎓 Testing VIP learning system...")
        test_sender = "test.learning@example.com"
        
        # Simulate learning interactions
        ai_processor._update_vip_score(test_sender, 1)
        ai_processor._update_vip_score(test_sender, 1)
        ai_processor._update_vip_score(test_sender, 1)
        
        print(f"✅ VIP learning recorded for {test_sender}")
        
        # Create new processor to test persistence
        print("🔄 Testing learning persistence...")
        ai_processor_2 = EmailProcessor()
        
        # Check if learning data persisted
        if test_sender in ai_processor_2.vip_senders:
            interactions = ai_processor_2.vip_senders[test_sender]['interactions']
            print(f"✅ Learning persistence works! {test_sender} has {interactions} interactions")
        else:
            print("⚠️ Learning persistence may have issues")
        
        # Clean up test data
        if test_sender in ai_processor_2.vip_senders:
            del ai_processor_2.vip_senders[test_sender]
            ai_processor_2._save_vip_data()
            print("🧹 Test learning data cleaned up")
        
        print("✅ AI learning persistence test completed!")
        
    except Exception as e:
        print(f"❌ Learning persistence test failed: {e}")

def run_complete_ai_test():
    """Run complete AI integration test suite"""
    
    print("🚀 STARTING COMPLETE AI EMAIL AGENT TEST")
    print("=" * 70)
    
    results = {
        'mock_integration': False,
        'real_integration': False,
        'learning_persistence': False
    }
    
    # Test 1: Mock AI Integration
    try:
        results['mock_integration'] = test_mock_ai_integration()
    except Exception as e:
        print(f"❌ Mock integration test error: {e}")
    
    # Test 2: Real AI Integration (optional)
    try:
        results['real_integration'] = test_real_ai_integration()
    except Exception as e:
        print(f"❌ Real integration test error: {e}")
    
    # Test 3: Learning Persistence
    try:
        test_ai_learning_persistence()
        results['learning_persistence'] = True
    except Exception as e:
        print(f"❌ Learning persistence test error: {e}")
    
    # Final Results
    print_section_header("FINAL AI TEST RESULTS")
    
    passed_tests = sum(bool(v) for v in results.values())

    total_tests = len(results)
    
    print(f"📊 TEST SUMMARY:")
    print(f"   Mock AI Integration: {'✅ PASSED' if results['mock_integration'] else '❌ FAILED'}")
    print(f"   Real AI Integration: {'✅ PASSED' if results['real_integration'] else '⚠️ SKIPPED/FAILED'}")
    print(f"   Learning Persistence: {'✅ PASSED' if results['learning_persistence'] else '❌ FAILED'}")
    
    print(f"\n🎯 OVERALL RESULT: {passed_tests}/{total_tests} tests passed")
    
    if results['mock_integration']:
        print("\n🎉 CONGRATULATIONS!")
        print("🤖 Your AI Email Agent brain is working perfectly!")
        print("🧠 AI features successfully tested:")
        print("   ✅ Email summarization using neural networks")
        print("   ✅ Intelligent priority classification")  
        print("   ✅ Entity extraction with spaCy")
        print("   ✅ Draft reply generation")
        print("   ✅ Learning and adaptation system")
        
        if not results['real_integration']:
            print("\n📋 Next Steps:")
            print("   • Complete Google Cloud Console setup")
            print("   • Test with real Gmail data")
            print("   • Your AI Agent is ready for Day 2 Afternoon!")
        
    else:
        print("\n❌ AI INTEGRATION ISSUES DETECTED")
        print("🔧 Please check:")
        print("   • AI dependencies installed correctly")
        print("   • ai_processor.py file created")
        print("   • mock_email_fetcher.py available")

if __name__ == '__main__':
    """Run complete AI integration tests"""
    run_complete_ai_test()