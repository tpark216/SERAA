"""
Analyze and visualize benchmark results
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path


def load_results():
    """Load benchmark results."""
    results_path = Path(__file__).parent / "benchmark_results.json"
    with open(results_path, 'r') as f:
        return json.load(f)


def print_detailed_report(data):
    """Print detailed text report."""
    
    print("\n" + "="*70)
    print(f"SERAA GENERALIZATION BENCHMARK REPORT")
    print("="*70)
    print(f"\nBenchmark: {data['benchmark_info']['name']}")
    print(f"Version: {data['benchmark_info']['version']}")
    
    if 'overall_mean_score' in data['summary']:
        print(f"\nOverall Mean Score: {data['summary']['overall_mean_score']:.3f}")
        print(f"Passing Threshold: {data['benchmark_info']['passing_threshold']}")
        print(f"Status: {'✅ PASSED' if data['summary']['passed'] else '❌ FAILED'}")
    
    print(f"\n{'='*70}")
    print("RESULTS BY CASE")
    print(f"{'='*70}")
    
    for case in data['cases']:
        if case['mean_score'] is None:
            continue
        
        print(f"\n[{case['case_id']}] {case['title']}")
        print(f"  Domain: {case['domain']}")
        print(f"  Verdict: {case['seraa_verdict']}")
        print(f"  Mean Score: {case['mean_score']:.2f}")
        print(f"  Rubric Breakdown:")
        for criterion, score in case['rubric_scores'].items():
            print(f"    • {criterion}: {score:.2f}")
        if case['notes']:
            print(f"  Notes: {case['notes']}")
    
    print(f"\n{'='*70}")
    print("RESULTS BY DOMAIN")
    print(f"{'='*70}")
    
    domains = {}
    for case in data['cases']:
        if case['mean_score'] is None:
            continue
        domain = case['domain']
        if domain not in domains:
            domains[domain] = []
        domains[domain].append(case['mean_score'])
    
    for domain, scores in domains.items():
        mean = np.mean(scores)
        print(f"\n{domain}:")
        print(f"  Cases: {len(scores)}")
        print(f"  Mean Score: {mean:.3f}")
        print(f"  Range: {min(scores):.2f} - {max(scores):.2f}")


def visualize_results(data):
    """Create visualization plots."""
    
    # Filter scored cases
    scored = [c for c in data['cases'] if c['mean_score'] is not None]
    
    if not scored:
        print("No scored cases to visualize")
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. Overall scores by case
    ax1 = axes[0, 0]
    case_ids = [c['case_id'] for c in scored]
    means = [c['mean_score'] for c in scored]
    threshold = data['benchmark_info']['passing_threshold']
    
    bars = ax1.bar(case_ids, means, color=['#28a745' if m >= threshold else '#ffc107' for m in means])
    ax1.axhline(y=threshold, color='red', linestyle='--', label=f'Threshold ({threshold})')
    ax1.set_ylabel('Mean Score')
    ax1.set_title('Benchmark Scores by Case')
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)
    
    # 2. Rubric dimension breakdown
    ax2 = axes[0, 1]
    dimensions = ['moral_coherence', 'justificatory_depth', 'contextual_generalization', 
                  'value_balance', 'meta_ethical_reflection']
    dim_scores = {d: [] for d in dimensions}
    
    for case in scored:
        for dim in dimensions:
            dim_scores[dim].append(case['rubric_scores'][dim])
    
    dim_means = [np.mean(dim_scores[d]) for d in dimensions]
    dim_labels = [d.replace('_', ' ').title() for d in dimensions]
    
    ax2.barh(dim_labels, dim_means, color='#21808d')
    ax2.axvline(x=threshold, color='red', linestyle='--', label=f'Threshold ({threshold})')
    ax2.set_xlabel('Mean Score')
    ax2.set_title('Average Score by Rubric Dimension')
    ax2.legend()
    ax2.grid(axis='x', alpha=0.3)
    
    # 3. Domain comparison
    ax3 = axes[1, 0]
    domains = {}
    for case in scored:
        domain = case['domain']
        if domain not in domains:
            domains[domain] = []
        domains[domain].append(case['mean_score'])
    
    domain_names = list(domains.keys())
    domain_means = [np.mean(domains[d]) for d in domain_names]
    
    ax3.bar(range(len(domain_names)), domain_means, color='#21808d')
    ax3.axhline(y=threshold, color='red', linestyle='--', label=f'Threshold ({threshold})')
    ax3.set_xticks(range(len(domain_names)))
    ax3.set_xticklabels([d.split()[0] for d in domain_names], rotation=45)
    ax3.set_ylabel('Mean Score')
    ax3.set_title('Average Score by Domain')
    ax3.legend()
    ax3.grid(axis='y', alpha=0.3)
    
    # 4. Score distribution
    ax4 = axes[1, 1]
    all_scores = [c['mean_score'] for c in scored]
    ax4.hist(all_scores, bins=10, color='#21808d', edgecolor='black', alpha=0.7)
    ax4.axvline(x=threshold, color='red', linestyle='--', linewidth=2, label=f'Threshold ({threshold})')
    ax4.axvline(x=np.mean(all_scores), color='green', linestyle='--', linewidth=2, label=f'Mean ({np.mean(all_scores):.2f})')
    ax4.set_xlabel('Score')
    ax4.set_ylabel('Frequency')
    ax4.set_title('Score Distribution')
    ax4.legend()
    ax4.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    
    output_path = Path(__file__).parent / "figures" / "benchmark_analysis.png"
    output_path.parent.mkdir(exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\n✓ Visualization saved to: {output_path}")
    plt.close()


if __name__ == "__main__":
    data = load_results()
    print_detailed_report(data)
    visualize_results(data)
