# Business descriptions in source

The live explanation service reads structured English function and test docstrings
from the same verified source it shows. It does not call a model. These descriptions
are reviewed commentary, never an alternative implementation or proof of correctness.
No separate narratives are generated or saved. Existing source freshness and release
checks also cover docstring bytes. Reload the running service after source changes.

## Functions

Keep descriptions at the function that executes the rule. Tool adapters reuse that
function's evidence; do not duplicate descriptions per API, Chat, MCP or Web entry.

```python
def check_limit(limit, exposure):
    """
    BUSINESS PURPOSE:
    Determine whether this customer's stated limit is exceeded.

    BUSINESS RULE credit.limit:
    IF the limit is positive AND exposure is greater than the limit:
        Report a limit breach.
    ELSE:
        Report no breach. Equality is allowed; zero records no limit.
    """
    # reality-rule: credit.limit
    return limit > 0 and exposure > limit
```

Use exact stable, globally unique `reality-rule` markers immediately before the
executing statement. A BUSINESS RULE must refer to a node in its own function.
Describe prerequisites, selection, formula operands, units, strict/inclusive limits,
refusals, effects and results where relevant. Use IF / THEN / ELSE only when the
cited statement actually establishes those branches. Keep helper behavior in the
helper; do not infer a call sequence between independent rules. Do not annotate
mechanical Python initialization as a business step. Original code remains inspectable.

The parser accepts BUSINESS PURPOSE and BUSINESS RULE <marker> sections. A purpose
is required for an annotated function. Each section must be nonempty and at most
4,000 UTF-8 bytes; the docstring is bounded to 24,000 bytes. Unknown, malformed and
duplicate sections or unresolved bindings are reported rather than displayed.

## Tests

```python
def test_exact_limit_is_allowed():
    """
    BUSINESS TEST:
    The exact limit remains allowed.
    GIVEN:
    The credit limit and exposure are both 100 EUR.
    WHEN:
    Check whether the limit is exceeded.
    THEN:
    No breach is reported.
    BUSINESS RULES:
    credit.limit
    """
    assert not check_limit(100, 100)
```

BUSINESS TEST, GIVEN, WHEN and THEN are required together. BUSINESS RULES is optional;
list exact marker IDs one per line. Descriptions must follow actual setup/actions and
assertions, including fixture and parameter assumptions. Each parameter variant keeps
its own original evidence. Authored THEN text is not a measured assertion mapping;
assertion-linked relationships and recorded execution evidence remain independent.
The live read never executes tests. A missing description leaves the executable test
visible with its original setup and assertions, without invented business prose.

## Review and preparation

Run `make business-annotations-check` for format/reference validation. Missing
registered root or approved test descriptions fail the gate, as do missing source bindings.
Run `PYTHONPATH=packages/reality-core/src .venv/bin/python
scripts/check_business_annotations.py --coverage` for a complete current root/test
worklist. This is a repository audit, not a claim about deployed source or passing tests.

All current registered roots and approved direct test sources are prepared in source.
This does not claim that every helper branch or other repository test is described.
Review description changes with code changes. Format/reference validation cannot
prove semantic agreement between prose and code. New roots/tests require descriptions
before advertising them as professionally explained. Preserve unknowns and inspect
related helper source rather than guessing domain behavior.
