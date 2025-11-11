"""
Core testing framework for regulatory comparison
"""

from dataclasses import dataclass, field
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
    domain: Optional[str] = None
    extra: dict = field(default_factory=dict)

    def __init__(self, **kwargs):
        for field_name in self.__dataclass_fields__:
            setattr(self, field_name, kwargs.pop(field_name, None))
            self.extra = kwargs

class RegulatoryTester:
    """Test SERAA against regulatory frameworks"""
    
    def __init__(self, agent: EthicalLLMAgent):
        self.agent = agent
        self.results = []
    
    def run_test_case(self, case: RegulatoryTestCase) -> Dict:
        """Run single test case and compare results"""
        
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
        
        # Defensive handling for possible UNKNOWN verdict
        valid_verdicts = {"violation", "compliant"}
        verdict_str = (case.regulatory_verdict or "UNKNOWN").upper()
        print(f"\n📋 Regulatory: {verdict_str}")
        print(f"🤖 SERAA: {seraa_result['verdict']}")

        if (case.regulatory_verdict or "").lower() in valid_verdicts:
            if verdict_match:
                print(f"✓ Match: YES")
            elif flagged_for_review:
                print(f"⚠️ SERAA flagged for review (regulator compliant)")
            else:
                print(f"✗ Match: NO")
        else:
            print("No regulatory grounding for this case—excluded from accuracy metric.")
        
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

        valid_verdicts = {"violation", "compliant"}
        results_to_score = [
            r for r in self.results
            if ((r['regulatory_verdict'] or '').lower() in valid_verdicts)
                and (r.get('case_name') or r.get('case_id'))  # Must have name or number!
                and ((r.get('case_name') or '').strip() or (str(r.get('case_id') or '').strip()))
        ]
        excluded_cases = [
            r for r in self.results
            if not ((r['regulatory_verdict'] or '').lower() in valid_verdicts
                and (r.get('case_name') or r.get('case_id'))
                and ((r.get('case_name') or '').strip() or (str(r.get('case_id') or '').strip())))
        ]
        total = len(results_to_score)
        matches = sum(1 for r in results_to_score if r['verdict_match'])
        flagged_review = sum(1 for r in results_to_score if r['flagged_for_review'])

        # Count by SERAA verdict type, frameworks (keep as before)
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
            'total_cases': len(self.results),
            'total_matches': matches,
            'overall_accuracy': accuracy,
            'flagged_for_review': flagged_review,
            'excluded_cases': len(excluded_cases),                     
            'excluded_case_summaries': [
                get_case_summary(r) for r in excluded_cases
            ],
            'verdict_counts': {
                'acceptable': acceptable,
                'conditional': conditional,
                'problematic': problematic
            },
            'by_framework': frameworks
        }

        return metrics
    
    def get_case_summary(case):
        # Prefer 'case_name', then 'title', then fallback to scenario snippet
        name = case.get('case_name') or case.get('title') or ''
        name = name.strip()
        if name:
            return name
        scenario = case.get('scenario') or case.get('question') or ''
        if scenario:
            return scenario[:60] + '...'
        return "(no case name/title, no scenario)"

    def print_case_explanations(self, only_excluded=False):
        print("\nDETAILED CASE EXPLANATIONS")
        for r in self.results:
            is_excluded = (r['regulatory_verdict'] or '').lower() not in {'violation', 'compliant'}
            if only_excluded and not is_excluded:
                continue
        print(f"\nCase: {r['case_name']}")
        print(f"Scenario: {r.get('scenario', '<not recorded>')}")
        print(f"SERAA Verdict: {r['seraa_verdict']}, Regulatory: {r['regulatory_verdict']}")
        print(f"Explanation:\n{r['seraa_explanation']}\n{'-'*40}")

    def print_summary(self):
        """Print summary statistics"""
        
        metrics = self.calculate_metrics()
        
        print(f"\n{'='*70}")
        print("SUMMARY METRICS")
        print(f"{'='*70}")
        print(f"Total Cases: {metrics['total_cases']}")
        print(f"Excluded (unknown/edge/no regulatory label): {metrics['excluded_cases']}")
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
        print(f"Excluded (unknown/edge/no regulatory label or lacking case name/ID): {metrics['excluded_cases']}")
        if metrics['excluded_cases'] > 0:
            print("Excluded cases (not scored):")
            for name in metrics['excluded_case_names']:
                print(f" - {name}")

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
    
def run_regulatory_benchmarks(
    model: str = "qwen2.5:1.5b",
    backend: str = "ollama",
    pac_minimum: float = 0.4,
    harm_threshold: int = 2,
    transparency_min: float = 0.5
):
    """Run only regulatory benchmarks (EXCLUDING edge/unseen cases)."""
    agent = EthicalLLMAgent(
        llm_backend=backend,
        model=model,
        seraa_domain="general",
        pac_minimum=pac_minimum,
        harm_threshold=harm_threshold,
        transparency_min=transparency_min
    )

    print(f"\n{'='*70}")
    print("SERAA REGULATORY BENCHMARKS ONLY")
    print(f"{'='*70}")
    print(f"\nThreshold Configuration:")
    print(f"  PAC Minimum: {pac_minimum}")
    print(f"  Harm Threshold: {harm_threshold}")
    print(f"  Transparency Minimum: {transparency_min}")

    tester = RegulatoryTester(agent)
    benchmark_dir = Path(__file__).parent.parent / "benchmarks"

    all_cases = load_cases(include_unseen=False)
    print(f"  Loaded {len(all_cases)} cases")
    tester.run_test_suite(all_cases)
    tester.print_summary()
    tester.save_results("regulatory_benchmark_results.json")
    return tester.results


def run_all_tests(
    model: str = "qwen2.5:1.5b",
    backend: str = "ollama",
    pac_minimum: float = 0.4,
    harm_threshold: int = 2,
    transparency_min: float = 0.5
):
    """Run all regulatory tests with configurable thresholds"""

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
        

    benchmark_dir = Path(__file__).parent.parent / "benchmarks"
        
    all_cases = load_cases(include_unseen=True)
    print(f"\nLoaded {len(all_cases)} cases total (regulatory + edge/unseen).\n")
    tester.run_test_suite(all_cases)
    tester.print_summary()
    tester.save_results()
    return tester.results

def load_cases(include_unseen: bool = False):
    benchmark_dir = Path(__file__).parent.parent / "benchmarks"
    cases = []
    for json_file in benchmark_dir.glob("*.json"):
        if not include_unseen and "unseen" in json_file.name.lower():
            continue
        print(f"Loading: {json_file.name}")
        new_cases = load_test_cases_from_json(json_file)
        cases.extend(new_cases)
        print(f"  Loaded {len(new_cases)} cases")
    return cases

if __name__ == "__main__":
    print("\nChoose test mode:")
    print("  1. Run REGULATORY BENCHMARKS ONLY (official benchmarks, excludes 'unseen' cases)")
    print("  2. Run ALL TESTS (regulatory + edge/unseen cases)")
    mode = input("Select mode [1/2, default 1]: ").strip() or "1"
    if mode == "2":
        run_all_tests()
    else:
        run_regulatory_benchmarks()
