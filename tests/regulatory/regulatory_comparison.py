"""
Core testing framework for regulatory comparison
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
import json
from pathlib import Path
from seraa.llm import EthicalLLMAgent


@dataclass
class RegulatoryTestCase:
    """Single test case for regulatory comparison"""
    id: str
    name: str
    scenario: str
    framework: str
    regulatory_verdict: str  # "violation" or "compliant"
    regulatory_reasoning: str
    key_violations: List[str]
    fine: Optional[str] = None
    source_url: Optional[str] = None
    date: Optional[str] = None


class RegulatoryTester:
    """Test SERAA against regulatory frameworks"""
    
    def __init__(self, agent: EthicalLLMAgent):
        self.agent = agent
        self.results = []
    
    def run_test_case(self, case: RegulatoryTestCase) -> Dict:
        """Run single test case and compare results"""
        
        print(f"\n{'='*70}")
        print(f"Testing: {case.name} ({case.framework})")
        print(f"{'='*70}")
        
        # Get SERAA evaluation
        seraa_result = self.agent.evaluate_question(case.scenario)
        
        # Map three-level verdicts to binary for comparison
        # ACCEPTABLE → not problematic
        # CONDITIONAL → not problematic (with safeguards)
        # PROBLEMATIC → problematic
        seraa_problematic = seraa_result['verdict'] == 'PROBLEMATIC'
        regulatory_violation = case.regulatory_verdict == 'violation'
        
        # Primary match: does SERAA agree with regulator?
        verdict_match = seraa_problematic == regulatory_violation
        
        # Secondary analysis: did SERAA flag as CONDITIONAL where regulator was compliant?
        flagged_for_review = (
            seraa_result['verdict'] == 'CONDITIONAL' and 
            case.regulatory_verdict == 'compliant'
        )
        
        # Build result
        result = {
            "case_id": case.id,
            "case_name": case.name,
            "framework": case.framework,
            "seraa_verdict": seraa_result['verdict'],
            "seraa_pac_score": seraa_result['pac_score'],
            "seraa_violations": seraa_result['violations'],
            "regulatory_verdict": case.regulatory_verdict,
            "regulatory_violations": case.key_violations,
            "verdict_match": verdict_match,
            "flagged_for_review": flagged_for_review,
            "regulatory_fine": case.fine,
            "seraa_explanation": seraa_result['explanation'],
            "source_url": case.source_url,
            "threshold_analysis": seraa_result.get('threshold_analysis', {})
        }
        
        # Print comparison
        print(f"\n📋 Regulatory: {case.regulatory_verdict.upper()}")
        print(f"🤖 SERAA: {seraa_result['verdict']}")
        
        if verdict_match:
            print(f"✓ Match: YES")
        elif flagged_for_review:
            print(f"⚠️ SERAA flagged for review (regulator compliant)")
        else:
            print(f"✗ Match: NO")
        
        print(f"\nPAC Score: {seraa_result['pac_score']:.2f}")
        
        if seraa_result['violations']:
            print(f"SERAA Violations: {', '.join(seraa_result['violations'])}")
        if case.key_violations:
            print(f"Regulatory Violations: {', '.join(case.key_violations)}")
        
        self.results.append(result)
        return result
    
    def run_test_suite(self, cases: List[RegulatoryTestCase]) -> List[Dict]:
        """Run multiple test cases"""
        
        print("\n" + "="*70)
        print(f"RUNNING {len(cases)} TEST CASES")
        print("="*70)
        
        for case in cases:
            self.run_test_case(case)
        
        return self.results
    
    def calculate_metrics(self) -> Dict:
        """Calculate accuracy and alignment metrics"""
        
        if not self.results:
            return {}
        
        total = len(self.results)
        matches = sum(1 for r in self.results if r['verdict_match'])
        flagged_review = sum(1 for r in self.results if r['flagged_for_review'])
        
        # Count by SERAA verdict type
        acceptable = sum(1 for r in self.results if r['seraa_verdict'] == 'ACCEPTABLE')
        conditional = sum(1 for r in self.results if r['seraa_verdict'] == 'CONDITIONAL')
        problematic = sum(1 for r in self.results if r['seraa_verdict'] == 'PROBLEMATIC')
        
        accuracy = matches / total if total > 0 else 0
        
        # Breakdown by framework
        frameworks = {}
        for r in self.results:
            fw = r['framework']
            if fw not in frameworks:
                frameworks[fw] = {
                    'total': 0,
                    'matches': 0,
                    'flagged_review': 0,
                    'acceptable': 0,
                    'conditional': 0,
                    'problematic': 0,
                    'cases': []
                }
            frameworks[fw]['total'] += 1
            frameworks[fw]['cases'].append(r['case_name'])
            if r['verdict_match']:
                frameworks[fw]['matches'] += 1
            if r['flagged_for_review']:
                frameworks[fw]['flagged_review'] += 1
            
            # Count verdicts
            if r['seraa_verdict'] == 'ACCEPTABLE':
                frameworks[fw]['acceptable'] += 1
            elif r['seraa_verdict'] == 'CONDITIONAL':
                frameworks[fw]['conditional'] += 1
            elif r['seraa_verdict'] == 'PROBLEMATIC':
                frameworks[fw]['problematic'] += 1
        
        # Calculate per-framework accuracy
        for fw in frameworks:
            frameworks[fw]['accuracy'] = frameworks[fw]['matches'] / frameworks[fw]['total']
        
        metrics = {
            'total_cases': total,
            'total_matches': matches,
            'overall_accuracy': accuracy,
            'flagged_for_review': flagged_review,
            'verdict_counts': {
                'acceptable': acceptable,
                'conditional': conditional,
                'problematic': problematic
            },
            'by_framework': frameworks
        }
        
        return metrics
    
    def print_summary(self):
        """Print summary statistics"""
        
        metrics = self.calculate_metrics()
        
        print(f"\n{'='*70}")
        print("SUMMARY METRICS")
        print(f"{'='*70}")
        print(f"Total Cases: {metrics['total_cases']}")
        print(f"Verdict Matches: {metrics['total_matches']}")
        print(f"Overall Accuracy: {metrics['overall_accuracy']:.1%}")
        print(f"Flagged for Review: {metrics['flagged_for_review']}")
        
        print(f"\nSERAA Verdict Distribution:")
        print(f"  ✅ Acceptable: {metrics['verdict_counts']['acceptable']}")
        print(f"  ⚠️ Conditional: {metrics['verdict_counts']['conditional']}")
        print(f"  ❌ Problematic: {metrics['verdict_counts']['problematic']}")
        
        print(f"\nBy Framework:")
        for fw, stats in metrics['by_framework'].items():
            print(f"\n  {fw}:")
            print(f"    Matches: {stats['matches']}/{stats['total']} ({stats['accuracy']:.1%})")
            print(f"    Flagged for Review: {stats['flagged_review']}")
            print(f"    Verdicts: ✅{stats['acceptable']} ⚠️{stats['conditional']} ❌{stats['problematic']}")
        
        return metrics
    
    def save_results(self, filepath: str = "regulatory_test_results.json"):
        """Save results to JSON file"""
        
        metrics = self.calculate_metrics()
        
        output = {
            'metrics': metrics,
            'results': self.results
        }
        
        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\n✓ Results saved to {filepath}")


def load_test_cases_from_json(filepath: str) -> List[RegulatoryTestCase]:
    """Load test cases from JSON file"""
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    cases = []
    for case_data in data['cases']:
        case = RegulatoryTestCase(**case_data)
        cases.append(case)
    
    return cases


def run_all_tests(
    model: str = "qwen2.5:1.5b",
    backend: str = "ollama",
    pac_minimum: float = 0.4,
    harm_threshold: int = 2,
    transparency_min: float = 0.5
):
    """Run all regulatory tests with configurable thresholds"""
    
    # Initialize agent with thresholds
    agent = EthicalLLMAgent(
        llm_backend=backend,
        model=model,
        seraa_domain="general",
        pac_minimum=pac_minimum,
        harm_threshold=harm_threshold,
        transparency_min=transparency_min
    )
    
    print(f"\n{'='*70}")
    print("SERAA REGULATORY VALIDATION SUITE")
    print(f"{'='*70}")
    print(f"\nThreshold Configuration:")
    print(f"  PAC Minimum: {pac_minimum}")
    print(f"  Harm Threshold: {harm_threshold}")
    print(f"  Transparency Minimum: {transparency_min}")
    
    tester = RegulatoryTester(agent)
    
    # Load all test suites
    benchmark_dir = Path(__file__).parent.parent / "benchmarks"
    
    all_cases = []
    for json_file in benchmark_dir.glob("*.json"):
        print(f"\nLoading: {json_file.name}")
        cases = load_test_cases_from_json(json_file)
        all_cases.extend(cases)
        print(f"  Loaded {len(cases)} cases")
    
    # Run tests
    tester.run_test_suite(all_cases)
    
    # Print summary
    tester.print_summary()
    
    # Save results
    tester.save_results()
    
    return tester.results


if __name__ == "__main__":
    run_all_tests()
