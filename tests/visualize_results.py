"""
Create visualizations of SERAA regulatory test results
"""

import json
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import numpy as np

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")


def load_results(filepath: str = "regulatory_test_results.json"):
    """Load test results from JSON"""
    with open(filepath, 'r') as f:
        return json.load(f)


def plot_overall_accuracy(metrics, save_path="figures/overall_accuracy.png"):
    """Bar chart of overall accuracy with verdict distribution"""
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Left: Overall accuracy
    accuracy = metrics['overall_accuracy'] * 100
    bars = ax1.bar(['SERAA vs\nRegulatory\nFrameworks'], [accuracy], 
                   color='#21808d', width=0.4, alpha=0.8)
    
    ax1.text(0, accuracy + 2, f'{accuracy:.1f}%', 
            ha='center', va='bottom', fontsize=16, fontweight='bold')
    ax1.set_ylim(0, 110)
    ax1.set_ylabel('Accuracy (%)', fontsize=14, fontweight='bold')
    ax1.set_title('SERAA Verdict Accuracy vs Regulatory Outcomes', 
                 fontsize=16, fontweight='bold', pad=20)
    ax1.axhline(y=50, color='gray', linestyle='--', alpha=0.3, label='Baseline (50%)')
    ax1.axhline(y=80, color='green', linestyle='--', alpha=0.3, label='Strong Performance (80%)')
    ax1.legend(loc='upper right')
    ax1.grid(axis='y', alpha=0.3)
    
    # Right: Verdict distribution
    verdict_counts = metrics['verdict_counts']
    verdicts = ['Acceptable', 'Conditional', 'Problematic']
    counts = [
        verdict_counts['acceptable'],
        verdict_counts['conditional'],
        verdict_counts['problematic']
    ]
    colors = ['#28a745', '#ffc107', '#dc3545']
    
    bars2 = ax2.bar(verdicts, counts, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    
    for bar, count in zip(bars2, counts):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.3,
                f'{count}',
                ha='center', va='bottom', fontsize=14, fontweight='bold')
    
    ax2.set_ylabel('Number of Cases', fontsize=14, fontweight='bold')
    ax2.set_title('SERAA Verdict Distribution', fontsize=16, fontweight='bold', pad=20)
    ax2.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    Path(save_path).parent.mkdir(exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {save_path}")
    plt.close()


def plot_framework_comparison(metrics, save_path="figures/framework_comparison.png"):
    """Stacked bar chart comparing verdicts across frameworks"""
    
    frameworks = list(metrics['by_framework'].keys())
    
    acceptable = [metrics['by_framework'][fw]['acceptable'] for fw in frameworks]
    conditional = [metrics['by_framework'][fw]['conditional'] for fw in frameworks]
    problematic = [metrics['by_framework'][fw]['problematic'] for fw in frameworks]
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    x = np.arange(len(frameworks))
    width = 0.6
    
    # Create stacked bars
    p1 = ax.bar(x, acceptable, width, label='✅ Acceptable', 
                color='#28a745', alpha=0.9, edgecolor='black', linewidth=1.5)
    p2 = ax.bar(x, conditional, width, bottom=acceptable, label='⚠️ Conditional',
                color='#ffc107', alpha=0.9, edgecolor='black', linewidth=1.5)
    p3 = ax.bar(x, problematic, width, 
                bottom=np.array(acceptable) + np.array(conditional),
                label='❌ Problematic', color='#dc3545', alpha=0.9, 
                edgecolor='black', linewidth=1.5)
    
    # Add accuracy percentages on top
    for i, fw in enumerate(frameworks):
        total = metrics['by_framework'][fw]['total']
        accuracy = metrics['by_framework'][fw]['accuracy'] * 100
        ax.text(i, total + 0.3, f'{accuracy:.0f}%',
                ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    ax.set_ylabel('Number of Cases', fontsize=14, fontweight='bold')
    ax.set_xlabel('Regulatory Framework', fontsize=14, fontweight='bold')
    ax.set_title('SERAA Verdict Distribution by Regulatory Framework', 
                 fontsize=16, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(frameworks, rotation=0)
    ax.legend(loc='upper right', fontsize=12)
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    Path(save_path).parent.mkdir(exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {save_path}")
    plt.close()


def plot_confusion_matrix(results, save_path="figures/confusion_matrix.png"):
    """Confusion matrix treating CONDITIONAL as not-problematic"""
    
    # Map three-level verdicts to binary for regulatory comparison
    # ACCEPTABLE or CONDITIONAL → not problematic
    # PROBLEMATIC → problematic
    
    tp = sum(1 for r in results if r['regulatory_verdict'] == 'violation' and r['seraa_verdict'] == 'PROBLEMATIC')
    tn = sum(1 for r in results if r['regulatory_verdict'] == 'compliant' and r['seraa_verdict'] in ['ACCEPTABLE', 'CONDITIONAL'])
    fp = sum(1 for r in results if r['regulatory_verdict'] == 'compliant' and r['seraa_verdict'] == 'PROBLEMATIC')
    fn = sum(1 for r in results if r['regulatory_verdict'] == 'violation' and r['seraa_verdict'] in ['ACCEPTABLE', 'CONDITIONAL'])
    
    confusion = np.array([[tp, fn], [fp, tn]])
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Create heatmap
    sns.heatmap(confusion, annot=True, fmt='d', cmap='Blues', 
                cbar_kws={'label': 'Count'},
                xticklabels=['SERAA: Problematic', 'SERAA: Acceptable/Conditional'],
                yticklabels=['Regulatory: Violation', 'Regulatory: Compliant'],
                annot_kws={'size': 20, 'weight': 'bold'},
                linewidths=2, linecolor='black',
                ax=ax)
    
    ax.set_title('SERAA vs Regulatory Verdicts\nConfusion Matrix', 
                 fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('SERAA Verdict', fontsize=14, fontweight='bold')
    ax.set_ylabel('Regulatory Outcome', fontsize=14, fontweight='bold')
    
    # Add accuracy metrics
    accuracy = (tp + tn) / (tp + tn + fp + fn) * 100 if (tp + tn + fp + fn) > 0 else 0
    precision = tp / (tp + fp) * 100 if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) * 100 if (tp + fn) > 0 else 0
    
    metrics_text = f"Accuracy: {accuracy:.1f}%\nPrecision: {precision:.1f}%\nRecall: {recall:.1f}%"
    ax.text(2.5, 0.5, metrics_text, fontsize=12, 
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    Path(save_path).parent.mkdir(exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {save_path}")
    plt.close()


def plot_pac_score_distribution(results, save_path="figures/pac_distribution.png"):
    """Distribution of PAC scores by verdict type"""
    
    acceptable = [r['seraa_pac_score'] for r in results if r['seraa_verdict'] == 'ACCEPTABLE']
    conditional = [r['seraa_pac_score'] for r in results if r['seraa_verdict'] == 'CONDITIONAL']
    problematic = [r['seraa_pac_score'] for r in results if r['seraa_verdict'] == 'PROBLEMATIC']
    
    fig, ax = plt.subplots(figsize=(12, 7))
    
    bins = np.linspace(0, 1, 11)
    
    # Create histograms
    ax.hist(acceptable, bins=bins, alpha=0.7, color='#28a745', 
            label=f'✅ Acceptable (n={len(acceptable)})', edgecolor='black')
    ax.hist(conditional, bins=bins, alpha=0.7, color='#ffc107', 
            label=f'⚠️ Conditional (n={len(conditional)})', edgecolor='black')
    ax.hist(problematic, bins=bins, alpha=0.7, color='#dc3545', 
            label=f'❌ Problematic (n={len(problematic)})', edgecolor='black')
    
    # Add mean lines
    if acceptable:
        ax.axvline(np.mean(acceptable), color='#28a745', linestyle='--', 
                   linewidth=2, label=f'Mean Acceptable: {np.mean(acceptable):.2f}')
    if conditional:
        ax.axvline(np.mean(conditional), color='#ffc107', linestyle='--', 
                   linewidth=2, label=f'Mean Conditional: {np.mean(conditional):.2f}')
    if problematic:
        ax.axvline(np.mean(problematic), color='#dc3545', linestyle='--', 
                   linewidth=2, label=f'Mean Problematic: {np.mean(problematic):.2f}')
    
    ax.set_xlabel('PAC Score (Preservation of Agentic Capacity)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Count', fontsize=14, fontweight='bold')
    ax.set_title('PAC Score Distribution by SERAA Verdict', 
                 fontsize=16, fontweight='bold', pad=20)
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    Path(save_path).parent.mkdir(exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {save_path}")
    plt.close()


def plot_flagged_for_review(metrics, save_path="figures/flagged_review.png"):
    """Show cases flagged for review (CONDITIONAL but regulatory compliant)"""
    
    fig, ax = plt.subplots(figsize=(12, 7))
    
    frameworks = list(metrics['by_framework'].keys())
    flagged = [metrics['by_framework'][fw]['flagged_review'] for fw in frameworks]
    total = [metrics['by_framework'][fw]['total'] for fw in frameworks]
    
    x = np.arange(len(frameworks))
    width = 0.6
    
    bars = ax.bar(x, flagged, width, color='#ffc107', alpha=0.8, 
                  edgecolor='black', linewidth=1.5)
    
    # Add labels
    for i, (bar, flag, tot) in enumerate(zip(bars, flagged, total)):
        height = bar.get_height()
        percentage = (flag / tot * 100) if tot > 0 else 0
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{flag}\n({percentage:.0f}%)',
                ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    ax.set_ylabel('Number of Cases', fontsize=14, fontweight='bold')
    ax.set_xlabel('Regulatory Framework', fontsize=14, fontweight='bold')
    ax.set_title('Cases Flagged for Review\n(SERAA: CONDITIONAL | Regulator: Compliant)', 
                 fontsize=16, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(frameworks, rotation=0)
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    Path(save_path).parent.mkdir(exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {save_path}")
    plt.close()


def plot_summary_dashboard(metrics, results, save_path="figures/summary_dashboard.png"):
    """Create a comprehensive summary dashboard"""
    
    fig = plt.figure(figsize=(18, 12))
    gs = fig.add_gridspec(3, 3, hspace=0.35, wspace=0.3)
    
    # 1. Overall Accuracy (top left)
    ax1 = fig.add_subplot(gs[0, 0])
    accuracy = metrics['overall_accuracy'] * 100
    ax1.bar(['Overall\nAccuracy'], [accuracy], color='#21808d', alpha=0.8)
    ax1.set_ylim(0, 100)
    ax1.set_ylabel('Accuracy (%)', fontweight='bold')
    ax1.set_title('Overall Accuracy', fontweight='bold', fontsize=14)
    ax1.text(0, accuracy + 3, f'{accuracy:.1f}%', ha='center', fontweight='bold', fontsize=16)
    ax1.axhline(y=80, color='green', linestyle='--', alpha=0.3)
    ax1.grid(axis='y', alpha=0.3)
    
    # 2. Verdict Distribution Pie Chart (top middle)
    ax2 = fig.add_subplot(gs[0, 1])
    verdict_counts = metrics['verdict_counts']
    labels = ['Acceptable', 'Conditional', 'Problematic']
    sizes = [verdict_counts['acceptable'], verdict_counts['conditional'], verdict_counts['problematic']]
    colors = ['#28a745', '#ffc107', '#dc3545']
    explode = (0.05, 0.05, 0.05)
    
    ax2.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.0f%%',
            shadow=True, startangle=90, textprops={'fontsize': 11, 'weight': 'bold'})
    ax2.set_title('Verdict Distribution', fontweight='bold', fontsize=14)
    
    # 3. Flagged for Review (top right)
    ax3 = fig.add_subplot(gs[0, 2])
    flagged_total = metrics['flagged_for_review']
    total_cases = metrics['total_cases']
    flagged_pct = (flagged_total / total_cases * 100) if total_cases > 0 else 0
    
    ax3.bar(['Flagged\nfor Review'], [flagged_total], color='#ffc107', alpha=0.8)
    ax3.set_ylabel('Cases', fontweight='bold')
    ax3.set_title('Flagged for Review', fontweight='bold', fontsize=14)
    ax3.text(0, flagged_total + 0.3, f'{flagged_total}\n({flagged_pct:.0f}%)', 
            ha='center', fontweight='bold', fontsize=14)
    ax3.grid(axis='y', alpha=0.3)
    
    # 4. Framework Comparison Stacked (middle row, spans all)
    ax4 = fig.add_subplot(gs[1, :])
    frameworks = list(metrics['by_framework'].keys())
    acceptable = [metrics['by_framework'][fw]['acceptable'] for fw in frameworks]
    conditional = [metrics['by_framework'][fw]['conditional'] for fw in frameworks]
    problematic = [metrics['by_framework'][fw]['problematic'] for fw in frameworks]
    
    x = np.arange(len(frameworks))
    width = 0.6
    
    p1 = ax4.bar(x, acceptable, width, label='Acceptable', color='#28a745', alpha=0.9)
    p2 = ax4.bar(x, conditional, width, bottom=acceptable, label='Conditional', color='#ffc107', alpha=0.9)
    p3 = ax4.bar(x, problematic, width, bottom=np.array(acceptable) + np.array(conditional),
                label='Problematic', color='#dc3545', alpha=0.9)
    
    ax4.set_ylabel('Cases', fontweight='bold')
    ax4.set_xlabel('Framework', fontweight='bold')
    ax4.set_title('Verdict Distribution by Framework', fontweight='bold', fontsize=14)
    ax4.set_xticks(x)
    ax4.set_xticklabels(frameworks)
    ax4.legend(loc='upper right')
    ax4.grid(axis='y', alpha=0.3)
    
    # 5. PAC Score Box Plot (bottom left)
    ax5 = fig.add_subplot(gs[2, 0])
    acceptable_pac = [r['seraa_pac_score'] for r in results if r['seraa_verdict'] == 'ACCEPTABLE']
    conditional_pac = [r['seraa_pac_score'] for r in results if r['seraa_verdict'] == 'CONDITIONAL']
    problematic_pac = [r['seraa_pac_score'] for r in results if r['seraa_verdict'] == 'PROBLEMATIC']
    
    data_to_plot = [acceptable_pac, conditional_pac, problematic_pac]
    bp = ax5.boxplot(data_to_plot, labels=['Accept', 'Cond', 'Problem'],
                     patch_artist=True, notch=True)
    
    for patch, color in zip(bp['boxes'], ['#28a745', '#ffc107', '#dc3545']):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax5.set_ylabel('PAC Score', fontweight='bold')
    ax5.set_title('PAC Score by Verdict', fontweight='bold', fontsize=14)
    ax5.grid(axis='y', alpha=0.3)
    
    # 6. Key Metrics Table (bottom middle)
    ax6 = fig.add_subplot(gs[2, 1])
    ax6.axis('off')
    metrics_text = f"""
    Overall Metrics:
    
    Total Cases: {metrics['total_cases']}
    Matches: {metrics['total_matches']}
    Accuracy: {metrics['overall_accuracy']*100:.1f}%
    Flagged: {metrics['flagged_for_review']}
    
    Verdicts:
    ✅ Acceptable: {verdict_counts['acceptable']}
    ⚠️ Conditional: {verdict_counts['conditional']}
    ❌ Problematic: {verdict_counts['problematic']}
    """
    ax6.text(0.1, 0.5, metrics_text, fontsize=11, family='monospace',
             verticalalignment='center',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
    
    # 7. Framework Breakdown Table (bottom right)
    ax7 = fig.add_subplot(gs[2, 2])
    ax7.axis('off')
    breakdown_text = "Framework Accuracy:\n\n"
    for fw, stats in metrics['by_framework'].items():
        breakdown_text += f"{fw}:\n  {stats['matches']}/{stats['total']} ({stats['accuracy']*100:.0f}%)\n"
    ax7.text(0.1, 0.5, breakdown_text, fontsize=10, family='monospace',
             verticalalignment='center',
             bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))
    
    plt.suptitle('SERAA Regulatory Validation Dashboard', 
                 fontsize=20, fontweight='bold', y=0.98)
    
    Path(save_path).parent.mkdir(exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {save_path}")
    plt.close()


def generate_all_visualizations(results_file="regulatory_test_results.json"):
    """Generate all visualization files"""
    
    print("\n" + "="*70)
    print("GENERATING VISUALIZATIONS")
    print("="*70 + "\n")
    
    # Load results
    data = load_results(results_file)
    metrics = data['metrics']
    results = data['results']
    
    # Create figures directory
    Path("figures").mkdir(exist_ok=True)
    
    # Generate all plots
    plot_overall_accuracy(metrics)
    plot_framework_comparison(metrics)
    plot_confusion_matrix(results)
    plot_pac_score_distribution(results)
    plot_flagged_for_review(metrics)
    plot_summary_dashboard(metrics, results)
    
    print("\n" + "="*70)
    print("VISUALIZATION COMPLETE")
    print("="*70)
    print("\nAll figures saved to: figures/")
    print("\nGenerated files:")
    print("  • overall_accuracy.png - Accuracy + verdict distribution")
    print("  • framework_comparison.png - Stacked verdict distribution by framework")
    print("  • confusion_matrix.png - SERAA vs regulatory comparison")
    print("  • pac_distribution.png - PAC scores by verdict type")
    print("  • flagged_review.png - Cases requiring escalation")
    print("  • summary_dashboard.png - Comprehensive overview (use this for presentations!)")
    print("\nReady to share in papers, presentations, and social media!")


if __name__ == "__main__":
    generate_all_visualizations()
