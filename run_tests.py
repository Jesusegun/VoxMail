"""
Test Runner - Choose which test to run
Run: python run_tests.py
"""

import sys

def show_menu():
    """Show test menu"""
    print("\n" + "=" * 80)
    print("PRIORITY TESTING SUITE - Test Menu")
    print("=" * 80)
    print("\nAvailable Tests:\n")
    print("  1. Quick Test           - Single email test (fastest, ~30 seconds)")
    print("  2. Comprehensive Test   - All 4 priorities tested (thorough, ~3 minutes)")
    print("  3. Before/After Demo    - See improvements (visual, ~1 minute)")
    print("  4. Run ALL Tests        - Everything (complete, ~5 minutes)")
    print("\n  0. Exit")
    print("\n" + "=" * 80)

def run_quick_test():
    """Run quick test"""
    print("\n[RUNNING] Quick Test...\n")
    import quick_test
    quick_test.quick_test()

def run_comprehensive_test():
    """Run comprehensive test"""
    print("\n[RUNNING] Comprehensive Test Suite...\n")
    import test_priorities
    test_priorities.main()

def run_before_after():
    """Run before/after demo"""
    print("\n[RUNNING] Before/After Comparison...\n")
    import before_after_test
    before_after_test.show_improvements()

def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("RUNNING ALL TESTS")
    print("=" * 80)
    
    print("\n>>> TEST 1/3: Quick Test <<<")
    run_quick_test()
    
    print("\n>>> TEST 2/3: Before/After Demo <<<")
    run_before_after()
    
    print("\n>>> TEST 3/3: Comprehensive Test <<<")
    run_comprehensive_test()
    
    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETE!")
    print("=" * 80 + "\n")

def main():
    """Main runner"""
    while True:
        show_menu()
        
        try:
            choice = input("Select test (0-4): ").strip()
            
            if choice == '0':
                print("\n[EXIT] Goodbye!\n")
                sys.exit(0)
            elif choice == '1':
                run_quick_test()
            elif choice == '2':
                run_comprehensive_test()
            elif choice == '3':
                run_before_after()
            elif choice == '4':
                run_all_tests()
            else:
                print("\n[ERROR] Invalid choice. Please select 0-4.")
                continue
            
            # Ask to continue
            print("\n" + "=" * 80)
            again = input("Run another test? (y/n): ").strip().lower()
            if again != 'y':
                print("\n[EXIT] Goodbye!\n")
                break
                
        except KeyboardInterrupt:
            print("\n\n[EXIT] Interrupted by user. Goodbye!\n")
            break
        except Exception as e:
            print(f"\n[ERROR] Test failed: {e}")
            print("Check that all dependencies are installed and data files exist.\n")
            again = input("Try another test? (y/n): ").strip().lower()
            if again != 'y':
                break

if __name__ == "__main__":
    main()
