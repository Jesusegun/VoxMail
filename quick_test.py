"""
Quick Test - Single Email Test
Run: python quick_test.py
"""

from smart_reply_generator import SmartReplyGenerator, SmartReplyConfig

def quick_test():
    """Quick test with a single email"""
    
    print("\n" + "=" * 80)
    print("QUICK TEST - Single Email Reply Generation")
    print("=" * 80 + "\n")
    
    # Initialize generator
    print("[1/3] Initializing Smart Reply Generator...")
    config = SmartReplyConfig()
    generator = SmartReplyGenerator(config)
    
    # Test email
    email = {
        'subject': 'Q4 Budget Meeting - Timeline Question',
        'body': '''Hi,

I need the Q4 budget numbers for the upcoming board meeting. When can you send them to me? 

It would be great to have them by tomorrow afternoon if possible.

Thanks,
Sarah''',
        'sender_name': 'Sarah Johnson',
        'sender': 'sarah.johnson@company.com'
    }
    
    print("\n[2/3] Generating reply for email...")
    print("-" * 80)
    print(f"FROM: {email['sender_name']} <{email['sender']}>")
    print(f"SUBJECT: {email['subject']}")
    print(f"BODY:\n{email['body']}")
    print("-" * 80)
    
    # Generate reply
    result = generator.generate_smart_reply(email, detected_tone='business')
    
    print("\n[3/3] Reply Generated!")
    print("=" * 80)
    print("GENERATED REPLY:")
    print("=" * 80)
    print(result['reply_text'])
    print("=" * 80)
    
    print("\n[METADATA]")
    print(f"  Confidence: {result['confidence_score']:.2f} ({result['confidence_level']})")
    print(f"  Method: {result['generation_method']}")
    
    if 'sender_profile' in result.get('metadata', {}):
        profile = result['metadata']['sender_profile']
        print(f"\n[SENDER PROFILE]")
        print(f"  Interactions: {profile.get('interactions', 0)}")
        print(f"  Relationship: {profile.get('relationship', 'unknown')}")
        print(f"  Preferred Tone: {profile.get('preferred_tone', 'unknown')}")
    
    if 'tone_adapted' in result.get('metadata', {}):
        adapted = result['metadata']['tone_adapted']
        print(f"\n[TONE ADAPTED]")
        print(f"  {adapted['original']} → {adapted['adapted']} ({adapted['reason']})")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE!")
    print("=" * 80)
    
    # Check for quality indicators
    reply = result['reply_text'].lower()
    print("\n[QUALITY CHECK]")
    
    checks = {
        'Specific action (I\'ll send)': 'i\'ll send' in reply or 'i\'ll share' in reply,
        'Specific timeline (by EOD/tomorrow)': 'by eod' in reply or 'by tomorrow' in reply or 'by end of day' in reply,
        'Enthusiasm (!)': '!' in result['reply_text'],
        'No generic "I\'ll get back to you"': 'i\'ll get back to you' not in reply,
        'Topic mentioned (Q4 budget)': 'q4' in reply or 'budget' in reply,
    }
    
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {check}")
    
    print("\n")

if __name__ == "__main__":
    quick_test()
