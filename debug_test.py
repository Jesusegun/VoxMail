"""
Debug test to trace exactly what's happening in reply generation
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from smart_reply_generator import SmartReplyGenerator, SmartReplyConfig

def debug_reply_generation():
    """Test with detailed debug output"""
    
    print("\n" + "="*80)
    print("DEBUG TEST - Trace Reply Generation Steps")
    print("="*80 + "\n")
    
    # Initialize generator
    config = SmartReplyConfig()
    config.learning_enabled = True
    config.learning_data_dir = 'ai_data'
    
    generator = SmartReplyGenerator(config)
    
    # Test email
    email_data = {
        'subject': 'Q4 Budget Timeline',
        'body': """Hi,

I need the Q4 budget numbers for the upcoming board meeting. When can you send them to me?

It would be great to have them by tomorrow afternoon if possible.

Thanks,
Sarah""",
        'sender_email': 'sarah.johnson@company.com',
        'sender_name': 'Sarah Johnson'
    }
    
    print("[TEST EMAIL]:")
    print(f"Subject: {email_data['subject']}")
    print(f"From: {email_data['sender_name']}")
    print(f"Body: {email_data['body'][:100]}...")
    print()
    
    # Generate reply
    result = generator.generate_smart_reply(email_data)
    
    print("\n" + "="*80)
    print("GENERATED REPLY:")
    print("="*80)
    print(result['reply_text'])
    print()
    print(f"Confidence: {result['confidence_score']:.2f}")
    print(f"Method: {result['generation_method']}")
    print()
    
    # Now let's manually trace through the steps
    print("\n" + "="*80)
    print("MANUAL STEP-BY-STEP TRACE:")
    print("="*80 + "\n")
    
    # Step 1: Extract context
    context = generator.context_extractor.extract_context(email_data)
    print("[STEP 1: Context Extraction]")
    print(f"  Questions: {context.get('questions', [])[0] if context.get('questions') else 'None'}")
    print(f"  Action items: {context.get('action_items', [])[0] if context.get('action_items') else 'None'}")
    print(f"  Deadlines: {context.get('deadlines', [])}")
    print(f"  Main topic: {context.get('main_topic', '')[:50]}...")
    print()
    
    # Step 2: Build content-specific reply
    print("[STEP 2: Content-Specific Reply Builder]")
    
    # Build without learned phrases
    raw_reply = generator.content_reply_builder.build_reply(
        context,
        'business',
        None,
        None
    )
    
    print("Raw reply (before learned phrases):")
    print(raw_reply)
    print()
    
    # Step 3: Apply learned phrases
    print("[STEP 3: Learned Phrase Injection]")
    enhanced_reply = generator.phrase_injector.inject_learned_phrases(raw_reply, context)
    print("After learned phrases:")
    print(enhanced_reply)
    print()
    
    # Step 4: Category adaptation
    print("[STEP 4: Category Adaptation]")
    email_category = context.get('email_category', 'general')
    final_reply, _ = generator.category_adapter.adapt_for_category(
        enhanced_reply, email_category, confidence=0.5
    )
    print("Final reply:")
    print(final_reply)
    print()

if __name__ == "__main__":
    debug_reply_generation()
