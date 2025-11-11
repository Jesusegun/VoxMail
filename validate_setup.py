"""
Setup Validator - Check if everything is ready for testing
Run: python validate_setup.py
"""

import os
import sys

def validate_setup():
    """Validate test setup"""
    print("\n" + "=" * 80)
    print("SETUP VALIDATION - Checking Prerequisites")
    print("=" * 80 + "\n")
    
    checks = {}
    
    # Check 1: Python version
    print("[1/7] Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 7:
        print(f"  ✅ Python {version.major}.{version.minor}.{version.micro} (OK)")
        checks['python'] = True
    else:
        print(f"  ❌ Python {version.major}.{version.minor}.{version.micro} (Need 3.7+)")
        checks['python'] = False
    
    # Check 2: Required files
    print("\n[2/7] Checking required files...")
    required_files = [
        'smart_reply_generator.py',
        'reply_learning_tracker.py',
        'requirements.txt'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} (MISSING)")
            checks['files'] = False
    
    if 'files' not in checks:
        checks['files'] = True
    
    # Check 3: Data directory
    print("\n[3/7] Checking data directory...")
    if os.path.exists('ai_data'):
        print(f"  ✅ ai_data/ directory exists")
        checks['data_dir'] = True
    else:
        print(f"  ❌ ai_data/ directory missing")
        checks['data_dir'] = False
    
    # Check 4: Data files
    print("\n[4/7] Checking data files...")
    data_files = [
        'ai_data/behavioral_patterns.json',
        'ai_data/user_preferences.json',
        'ai_data/learning_stats.json',
        'ai_data/reply_edits.json'
    ]
    
    data_files_ok = True
    for file in data_files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ⚠️  {file} (missing, will use defaults)")
            data_files_ok = False
    
    checks['data_files'] = data_files_ok
    
    # Check 5: Test files
    print("\n[5/7] Checking test files...")
    test_files = [
        'quick_test.py',
        'test_priorities.py',
        'before_after_test.py',
        'run_tests.py'
    ]
    
    for file in test_files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} (MISSING)")
            checks['test_files'] = False
    
    if 'test_files' not in checks:
        checks['test_files'] = True
    
    # Check 6: Dependencies
    print("\n[6/7] Checking dependencies...")
    try:
        import transformers
        print(f"  ✅ transformers")
    except ImportError:
        print(f"  ❌ transformers (run: pip install transformers)")
        checks['deps'] = False
    
    try:
        import spacy
        print(f"  ✅ spacy")
    except ImportError:
        print(f"  ❌ spacy (run: pip install spacy)")
        checks['deps'] = False
    
    try:
        import textblob
        print(f"  ✅ textblob")
    except ImportError:
        print(f"  ❌ textblob (run: pip install textblob)")
        checks['deps'] = False
    
    if 'deps' not in checks:
        checks['deps'] = True
    
    # Check 7: Can import main module
    print("\n[7/7] Checking main module import...")
    try:
        from smart_reply_generator import SmartReplyGenerator, SmartReplyConfig
        print(f"  ✅ smart_reply_generator imports successfully")
        checks['import'] = True
    except Exception as e:
        print(f"  ❌ Failed to import: {e}")
        checks['import'] = False
    
    # Summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    
    all_critical = checks.get('python', False) and checks.get('files', False) and checks.get('deps', False) and checks.get('import', False)
    
    if all_critical:
        print("\n✅ ALL CRITICAL CHECKS PASSED - Ready to test!")
        print("\nYou can now run:")
        print("  python run_tests.py")
        print("  or")
        print("  python quick_test.py")
    else:
        print("\n❌ SOME CRITICAL CHECKS FAILED")
        print("\nFix the issues above before running tests.")
        print("\nCommon fixes:")
        print("  - Install dependencies: pip install -r requirements.txt")
        print("  - Install spacy model: python -m spacy download en_core_web_sm")
    
    if not checks.get('data_files', True):
        print("\n⚠️  WARNING: Some data files missing")
        print("   Tests will still run but with default/empty data")
        print("   This is OK for initial testing")
    
    print("\n" + "=" * 80 + "\n")
    
    return all_critical

if __name__ == "__main__":
    validate_setup()
