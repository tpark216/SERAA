<!-- .github/copilot-instructions.md for the SERAA project -->

This file gives practical, codebase-specific guidance to AI coding agents working on SERAA.

High-level intent
- SERAA is a small Python library that encodes a ternary-native ethical reasoning architecture (NEGATIVE/NEUTRAL/POSITIVE).
- Core concepts live in `seraa/core/` (ternary primitives and monitoring), axioms live in `seraa/axioms/` (ethical constraints), and utilities/examples live at the repo root (`examples/`, `tests/`).

Key files and why they matter
- `core/ternary.py` — canonical Ternary types and logic (TernaryState, TernaryValue, ternary_and/or/not). Use this for any representation or conversions (binary pair / quantum basis).
- `core/monitor.py` — SubconsciousMonitor and ConsciousLayer. Central to how components escalate to attention. Follow its escalation_callback pattern when adding monitors.
- `axioms/choice.py` — Example axiom implementation (ChoiceConstraint, ChoiceDiversityTracker) showing evaluation patterns, entropy normalization, and result shaping (`ChoiceEvaluationResult`). Use this as template for adding other axioms.
- `examples/basic_usage.py` and `tests/` — concrete usage and unit tests. Mirror tests when adding or refactoring behavior.

Repository conventions and patterns
- Ternary-first: types use `TernaryState`/`TernaryValue`. Prefer constructing via `TernaryValue(TernaryState.NEUTRAL)` or integer literals (-1/0/1).
- Binary compatibility: `to_binary_pair()` / `from_binary_pair()` encode ternary into two bits; preserve this mapping when adding integrations with hardware or other modules.
- Monitoring/escalation pattern: monitors expose `escalation_callback` and append (name, TernaryValue) tuples to the conscious layer's `attention_queue`. New monitors should set `escalation_callback` in `ConsciousLayer.add_monitor()` to integrate.
- Assessment objects: axiom evaluators return a result object (e.g., `ChoiceEvaluationResult`) rather than raw tuples. Keep this shape for serialization (`to_dict()`) and repr consistency.

Developer workflows (commands discovered in repo)
- Install dev dependencies and run tests (from repo root):
  - pip install -e ".[dev]"
  - pytest tests/

Quick examples to follow
- Add a monitor and query conscious layer:
  - Create SubconsciousMonitor(name, optimal_checker)
  - Register with ConsciousLayer.add_monitor(monitor)
  - Call monitor.check(output) and use conscious.get_attention_queue() to inspect escalations

Testing and expectations
- Tests live in `tests/` and follow pytest style. When changing core behavior (ternary logic, monitor escalation, axiom thresholds), update or add tests in `tests/` mirroring existing test structure.
- Tests assume deterministic outputs (no async or external services). Keep changes local and pure where possible.

Style and API stability notes
- Public API surfaces to be treated carefully: symbols imported from `seraa.core` and `seraa.axioms` (for example `TernaryValue`, `SubconsciousMonitor`, `evaluate_choice_preservation`) are used in examples and tests—avoid breaking signature changes without updating callers and tests.
- Prefer small, well-tested changes and preserve result objects (with `to_dict()` implementations) for reproducibility.

When in doubt
- Follow `core/ternary.py` and `core/monitor.py` patterns for state handling and callbacks.
- Reference `axioms/choice.py` for evaluation, entropy normalization, and threshold-based ternary mapping.

If you need more context, open `setup_seraa_repository.py` — it contains a canonical README template and notes on project goals and examples.

Please ask for clarification or point to a specific file/feature you want to modify.
 
Concrete examples (copy/paste-ready)

1) Ternary values and binary pair conversion

```python
from seraa.core.ternary import TernaryValue, TernaryState

# Construct via enum or integer
v = TernaryValue(TernaryState.NEUTRAL)
v2 = TernaryValue(1)

assert v.value == 0
assert v2.to_binary_pair() == (1, 0)

# Roundtrip
bits = v2.to_binary_pair()
restored = TernaryValue.from_binary_pair(*bits)
assert restored == v2
```

2) Subconscious monitor + ConsciousLayer integration

```python
from seraa.core.monitor import SubconsciousMonitor, ConsciousLayer

def is_optimal(output):
  # monitor.check receives arbitrary subprocess output
  return output.get('score', 0) > 0.8

conscious = ConsciousLayer()
monitor = SubconsciousMonitor('ethics', optimal_checker=is_optimal)
conscious.add_monitor(monitor)

# Run checks; non-optimal results will escalate into conscious.attention_queue
monitor.check({'score': 0.9})  # stays subconscious
monitor.check({'score': 0.4})  # escalates
print(conscious.get_attention_queue())
```

Notes: `ConsciousLayer.add_monitor()` sets the monitor's `escalation_callback` to the internal receiver. Escalations are stored as `(monitor_name, TernaryValue)` tuples; sort/trim logic enforces `max_attention_items`.

3) Evaluating choice preservation (Axiom 9)

```python
from seraa.axioms.choice import evaluate_choice_preservation

class Action:
  def __init__(self, pac_score, is_viable=True):
    self.pac_score = pac_score
    self.is_viable = is_viable

actions = [Action(0.8), Action(0.95), Action(0.75)]
moral_state = {'fairness': 0.3, 'autonomy': 0.4, 'care': 0.3}

result = evaluate_choice_preservation(
  moral_state,
  actions,
  pac_evaluator=lambda a: a.pac_score,
  viability_checker=lambda a: a.is_viable,
)

print(result)                # ChoiceEvaluationResult(...)
print(result.to_dict())      # Serializable dict for logging
```

Testing commands (repo root)

```powershell
# install dev deps
pip install -e ".[dev]"

# run all tests
pytest tests/
```

Small PR checklist for contributors
- Update or add tests under `tests/` that capture behavior changes (use patterns in existing tests).
- Preserve public result objects (implement `to_dict()` if adding new ones) for consistent serialization.
- If adding a new monitor, ensure it uses `escalation_callback` to integrate with `ConsciousLayer`.
