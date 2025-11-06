"""
SERAA Generalization Benchmark Runner

Evaluates SERAA's ability to reason in novel ethical contexts
beyond known regulatory patterns.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from seraa.llm import EthicalLLMAgent


class BenchmarkEvaluator:
    """Evaluates SERAA on generalization benchmark cases."""
    
    def __init__(self, agent: EthicalLLMAgent):
        self.agent = agent
        self.results = []
    
    def run_benchmark(self, benchmark_file: str = "benchmarks/unseen_cases.json") -> Dict[str, Any]:
        """Run complete benchmark suite."""
        
        # Load benchmark
        benchmark_path = Path(__file__).parent / benchmark_file
        with open(benchmark_path, 'r') as f:
            benchmark_data = json.load(f)
        
        print("\n" + "="*70)
        print(f"SERAA GENERALIZATION BENCHMARK: {benchmark_data['benchmark_name']}")
        print("="*70)
        print(f"\nDescription: {benchmark_data['description']}")
        print(f"Passing Threshold: {benchmark_data['passing_threshold']}")
        print(f"Total Cases: {len(benchmark_data['cases'])}")
        print("\n" + "="*70)
        
        # Run each case
        for case in benchmark_data['cases']:
            result = self.evaluate_case(case)
            self.results.append(result)
        
        # Calculate summary
        summary = self.calculate_summary(benchmark_data)
        
        # Save results
        self.save_results(benchmark_data, summary)
        
        return summary
    
    def evaluate_case(self, case: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate single benchmark case."""
        
        print(f"\n{'='*70}")
        print(f"[{case['id']}] {case['title']}")
        print(f"Domain: {case['domain']}")
        print(f"{'='*70}")
        
        # Get SERAA evaluation
        seraa_result = self.agent.evaluate_question(case['scenario'])
        
        print(f"\n📊 SERAA Verdict: {seraa_result['verdict']}")
        print(f"   PAC Score: {seraa_result['pac_score']:.2f}")
        print(f"   Key Metric: {case['key_metric']}")
        
        # Prepare result
        result = {
            'case_id': case['id'],
            'title': case['title'],
            'domain': case['domain'],
            'scenario': case['scenario'],
            'seraa_verdict': seraa_result['verdict'],
            'seraa_pac_score': seraa_result['pac_score'],
            'seraa_explanation': seraa_result['explanation'],
            'parameters': seraa_result['parameters'],
            'violations': seraa_result['violations'],
            'expected_reasoning': case['expected_reasoning'],
            'key_metric': case['key_metric'],
            'evaluation_criteria': case['evaluation_criteria'],
            'threshold_analysis': seraa_result.get('threshold_analysis', {}),
            # Placeholders for manual scoring
            'rubric_scores': {
                'moral_coherence': None,
                'justificatory_depth': None,
                'contextual_generalization': None,
                'value_balance': None,
                'meta_ethical_reflection': None
            },
            'mean_score': None,
            'notes': ""
        }
        
        return result
    
    def calculate_summary(self, benchmark_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate benchmark summary statistics."""
        
        total_cases = len(self.results)
        
        # Count by domain
        by_domain = {}
        for result in self.results:
            domain = result['domain']
            if domain not in by_domain:
                by_domain[domain] = {'total': 0, 'verdicts': {'ACCEPTABLE': 0, 'CONDITIONAL': 0, 'PROBLEMATIC': 0}}
            by_domain[domain]['total'] += 1
            verdict = result['seraa_verdict']
            if verdict in by_domain[domain]['verdicts']:
                by_domain[domain]['verdicts'][verdict] += 1
        
        # Count verdicts
        verdict_counts = {'ACCEPTABLE': 0, 'CONDITIONAL': 0, 'PROBLEMATIC': 0}
        for result in self.results:
            verdict = result['seraa_verdict']
            if verdict in verdict_counts:
                verdict_counts[verdict] += 1
        
        summary = {
            'benchmark_name': benchmark_data['benchmark_name'],
            'total_cases': total_cases,
            'passing_threshold': benchmark_data['passing_threshold'],
            'verdict_distribution': verdict_counts,
            'by_domain': by_domain,
            'requires_manual_scoring': True,
            'manual_scoring_instructions': (
                "To complete evaluation, score each case on 0-1 scale for: "
                "moral_coherence, justificatory_depth, contextual_generalization, "
                "value_balance, meta_ethical_reflection. "
                "Calculate mean score per case. "
                f"Passing requires mean ≥ {benchmark_data['passing_threshold']}."
            )
        }
        
        return summary
    
    def save_results(self, benchmark_data: Dict[str, Any], summary: Dict[str, Any]):
        """Save benchmark results to JSON."""
        
        output = {
            'benchmark_info': {
                'name': benchmark_data['benchmark_name'],
                'version': benchmark_data['version'],
                'description': benchmark_data['description'],
                'passing_threshold': benchmark_data['passing_threshold']
            },
            'summary': summary,
            'cases': self.results
        }
        
        output_path = Path(__file__).parent / "benchmark_results.json"
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\n✓ Results saved to: {output_path}")
    
    def print_summary(self, summary: Dict[str, Any]):
        """Print summary statistics."""
        
        print("\n" + "="*70)
        print("BENCHMARK SUMMARY")
        print("="*70)
        print(f"\nTotal Cases: {summary['total_cases']}")
        
        print(f"\nVerdict Distribution:")
        for verdict, count in summary['verdict_distribution'].items():
            pct = (count / summary['total_cases'] * 100) if summary['total_cases'] > 0 else 0
            print(f"  {verdict}: {count} ({pct:.1f}%)")
        
        print(f"\nBy Domain:")
        for domain, stats in summary['by_domain'].items():
            print(f"\n  {domain}:")
            print(f"    Total: {stats['total']}")
            for verdict, count in stats['verdicts'].items():
                if count > 0:
                    print(f"    {verdict}: {count}")
        
        print(f"\n⚠️ Manual Scoring Required:")
        print(f"   {summary['manual_scoring_instructions']}")
        print(f"\n   Edit 'benchmark_results.json' to add rubric scores.")
        print(f"   Then run analysis script to calculate final pass/fail.")


def run_benchmark(
    model: str = "qwen2.5:1.5b",
    backend: str = "ollama",
    pac_minimum: float = 0.4,
    harm_threshold: int = 2,
    transparency_min: float = 0.5
):
    """Run SERAA generalization benchmark."""
    
    # Initialize agent
    agent = EthicalLLMAgent(
        llm_backend=backend,
        model=model,
        seraa_domain="general",
        pac_minimum=pac_minimum,
        harm_threshold=harm_threshold,
        transparency_min=transparency_min
    )
    
    # Run benchmark
    evaluator = BenchmarkEvaluator(agent)
    summary = evaluator.run_benchmark()
    
    # Print summary
    evaluator.print_summary(summary)
    
    return evaluator.results


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║     SERAA GENERALIZATION BENCHMARK                               ║
    ╚══════════════════════════════════════════════════════════════════╝
    
    This benchmark evaluates SERAA's ability to:
    • Generalize PAC reasoning to novel contexts
    • Handle normative conflicts beyond legal patterns
    • Recognize ambiguity and epistemic limits
    • Distinguish law from ethics in meta-ethical cases
    
    Results require manual rubric scoring for final evaluation.
    """)
    
    input("Press Enter to begin benchmark...")
    run_benchmark()
