"""
Main script to run all regulatory tests
"""

import sys
from pathlib import Path

# Add tests directory to path
tests_dir = Path(__file__).parent
sys.path.insert(0, str(tests_dir))

from regulatory.regulatory_comparison import run_all_tests


def main():
    """Run complete regulatory test suite"""
    
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║     SERAA REGULATORY FRAMEWORK VALIDATION SUITE                  ║
    ╚══════════════════════════════════════════════════════════════════╝
    
    This test suite compares SERAA's ethical evaluations against 
    real regulatory outcomes from:
    
    • GDPR (EU Data Protection)
    • HIPAA (US Healthcare Privacy)  
    • EU AI Act (AI Regulation)
    • NIST AI RMF (Risk Management)
    
    Three-Level Verdict System:
    • ✅ ACCEPTABLE: Meets all thresholds
    • ⚠️ CONDITIONAL: Requires escalation and monitoring
    • ❌ PROBLEMATIC: Fails basic ethical criteria
    
    """)
    
    # Ask user if they want to customize thresholds
    use_custom = input("Use custom thresholds? (y/N): ").strip().lower()
    
    if use_custom == 'y':
        print("\nEnter thresholds (press Enter for defaults):")
        try:
            pac_min = input("  PAC Minimum [0.4]: ").strip()
            pac_min = float(pac_min) if pac_min else 0.4
            
            harm_max = input("  Harm Threshold [2]: ").strip()
            harm_max = int(harm_max) if harm_max else 2
            
            trans_min = input("  Transparency Minimum [0.5]: ").strip()
            trans_min = float(trans_min) if trans_min else 0.5
        except ValueError:
            print("Invalid input, using defaults.")
            pac_min, harm_max, trans_min = 0.4, 2, 0.5
    else:
        pac_min, harm_max, trans_min = 0.4, 2, 0.5
    
    print(f"\nUsing thresholds: PAC≥{pac_min}, Harm≤{harm_max}, Transparency≥{trans_min}")
    input("\nPress Enter to begin testing...")
    
    # Run all tests
    results = run_all_tests(
        model="qwen2.5:1.5b",
        backend="ollama",
        pac_minimum=pac_min,
        harm_threshold=harm_max,
        transparency_min=trans_min
    )
    
    print("\n" + "="*70)
    print("TESTING COMPLETE")
    print("="*70)
    print("\nResults saved to: regulatory_test_results.json")
    print("\nReview the results to see:")
    print("  • Overall accuracy vs regulatory outcomes")
    print("  • Per-framework performance")
    print("  • Three-level verdict distribution")
    print("  • Cases flagged for review (CONDITIONAL)")
    print("  • Detailed case-by-case comparisons")
    

if __name__ == "__main__":
    main()
