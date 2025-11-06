"""
Interactive benchmark scoring interface

Allows human evaluators to score cases on the 5-dimension rubric.
"""

import json
from pathlib import Path
from typing import Dict


def score_case_interactive(case: Dict) -> Dict[str, float]:
    """Interactive scoring for single case."""
    
    print(f"\n{'='*70}")
    print(f"SCORING: [{case['case_id']}] {case['title']}")
    print(f"{'='*70}")
    
    print(f"\nScenario: {case['scenario'][:200]}...")
    print(f"\nSERAA Verdict: {case['seraa_verdict']}")
    print(f"PAC Score: {case['seraa_pac_score']:.2f}")
    print(f"\nExplanation:\n{case['seraa_explanation']}")
    
    print(f"\n\nExpected Reasoning:")
    for reason in case['expected_reasoning']:
        print(f"  • {reason}")
    
    print(f"\n\nEvaluation Criteria:")
    for criterion, description in case['evaluation_criteria'].items():
        print(f"  {criterion}: {description}")
    
    print(f"\n{'='*70}")
    print("SCORE EACH DIMENSION (0.0-1.0)")
    print(f"{'='*70}")
    
    scores = {}
    criteria = [
        ('moral_coherence', 'Moral Coherence'),
        ('justificatory_depth', 'Justificatory Depth'),
        ('contextual_generalization', 'Contextual Generalization'),
        ('value_balance', 'Value Balance'),
        ('meta_ethical_reflection', 'Meta-Ethical Reflection')
    ]
    
    for key, name in criteria:
        while True:
            try:
                score = input(f"{name} (0.0-1.0): ").strip()
                score = float(score)
                if 0.0 <= score <= 1.0:
                    scores[key] = score
                    break
                else:
                    print("  Score must be between 0.0 and 1.0")
            except ValueError:
                print("  Invalid input, please enter a number")
    
    notes = input("\nOptional notes: ").strip()
    
    return scores, notes


def score_benchmark_interactive():
    """Score all benchmark cases interactively."""
    
    results_path = Path(__file__).parent / "benchmark_results.json"
    
    if not results_path.exists():
        print("Error: benchmark_results.json not found. Run benchmark first.")
        return
    
    with open(results_path, 'r') as f:
        data = json.load(f)
    
    print(f"\n{'='*70}")
    print(f"INTERACTIVE BENCHMARK SCORING")
    print(f"{'='*70}")
    print(f"\nBenchmark: {data['benchmark_info']['name']}")
    print(f"Total Cases: {len(data['cases'])}")
    print(f"Passing Threshold: {data['benchmark_info']['passing_threshold']}")
    
    # Score each case
    for case in data['cases']:
        if case['mean_score'] is not None:
            skip = input(f"\n{case['case_id']} already scored ({case['mean_score']:.2f}). Re-score? (y/N): ")
            if skip.lower() != 'y':
                continue
        
        scores, notes = score_case_interactive(case)
        
        # Update case
        case['rubric_scores'] = scores
        case['mean_score'] = sum(scores.values()) / len(scores)
        case['notes'] = notes
        
        print(f"\n✓ Mean Score: {case['mean_score']:.2f}")
    
    # Calculate overall results
    scored_cases = [c for c in data['cases'] if c['mean_score'] is not None]
    if scored_cases:
        overall_mean = sum(c['mean_score'] for c in scored_cases) / len(scored_cases)
        passed = overall_mean >= data['benchmark_info']['passing_threshold']
        
        data['summary']['overall_mean_score'] = overall_mean
        data['summary']['passed'] = passed
        data['summary']['scored_cases'] = len(scored_cases)
        
        print(f"\n{'='*70}")
        print(f"OVERALL RESULTS")
        print(f"{'='*70}")
        print(f"Scored Cases: {len(scored_cases)}/{len(data['cases'])}")
        print(f"Overall Mean Score: {overall_mean:.3f}")
        print(f"Passing Threshold: {data['benchmark_info']['passing_threshold']}")
        print(f"Status: {'✅ PASSED' if passed else '❌ FAILED'}")
    
    # Save updated results
    with open(results_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✓ Scores saved to: {results_path}")


if __name__ == "__main__":
    score_benchmark_interactive()
