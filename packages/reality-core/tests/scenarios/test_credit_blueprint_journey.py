"""Live credit rule evidence across operations; static tests never imply coverage."""
from reality.services.business_blueprints import explain


def test_credit_reference_has_actual_guard_sources_and_explicit_branch_gaps():
    blueprints=[explain("command", "credit_exposure"),explain("tool","fulfillment_readiness"),explain("command","release_credit_holds"), explain("projection","fulfillment_queue"), explain("tool","proposal_approve_and_execute"), explain("tool","credit_hold_release_propose")]
    sources={s.function:s for b in blueprints for s in b.sources}
    for name in ("credit_exposures","_order_rows","_invoiced_quantities","fulfillment_readiness","stock_cover","ready_by_location","release_credit_holds","preview_credit_release"):
        assert any(f.endswith('.'+name) for f in sources),name
    credit=blueprints[0]
    assert any('exposure > limit' in n.expression and 'limit > ZERO' in n.expression for n in credit.nodes)
    assert any('gross_amount' in s.code and 'uninvoiced' in s.code for s in credit.sources)
    assert credit.scenarios
    for b in blueprints:
        assert b.status != 'outdated'
        for n in b.nodes:
            assert n.evidence_id in {s.id for s in b.sources}
            if n.kind=='decision':
                assert n.id in b.test_gaps or any(n.id in t.rules for t in b.scenarios)
        assert all(t.run['outcome']=='unknown' for t in b.scenarios)
        assert any('assert' in t.code for t in b.scenarios)


def test_reference_obligation_symbols_are_present_or_named_as_unresolved():
    """Planning citations define the denominator, never the generated business answer."""
    import re
    from pathlib import Path
    boundary=Path(__file__).resolve().parents[4]/'specs/343-business-logic-blueprints/contracts/reference-boundary.md'
    obligations=re.findall(r'^\| (B\d+) \|.*?\[`([^`]+)`\]\(',boundary.read_text(),re.MULTILINE)
    assert len(obligations)==53
    entries=[('command','credit_exposure'),('tool','fulfillment_readiness'),('command','release_credit_holds'),('tool','credit_hold_release_propose'),('tool','proposal_approve_and_execute'),('command','create_manual_order'),('command','revise_commitment'),('command','record_movement'),('tool','proposal_execution_status')]
    results=[explain(kind,key) for kind,key in entries]
    symbols={s.function.rsplit('.',1)[-1] for b in results for s in b.sources}
    # The public graph is bounded. A named omission is unknown coverage, not a
    # missing business guard or a claim that its rule was inspected.
    prefixes=(
        'Analysis boundary reached; omitted dependency: ',
        'Source response boundary reached; omitted dependency: ',
    )
    omitted={
        limitation.removeprefix(prefix).rsplit('.',1)[-1]
        for blueprint in results
        for limitation in blueprint.limitations
        for prefix in prefixes
        if limitation.startswith(prefix)
    }
    missing=[(identity,name) for identity,name in obligations if name not in symbols and name not in omitted]
    assert not missing,missing
