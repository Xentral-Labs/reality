"""The references the operational exception queue leans on, and the paths that set them.

Four references on the queue's own records are nullable, meaningful and unenforced. A missing one
does not make one thing go wrong, it makes two opposite things go wrong: a class that concludes
from absence reports work that was actually done, and a class that starts from the reference never
looks at the record at all.

These gates do not make the references required — every one of those records legitimately exists
without its link. They make three other things impossible: a new nullable reference nobody has
classified, a new writing path that drops one, and a surface that cannot carry one.

Each gate composes one fact discovered from the mapper or the source with one fact a person
declared, and each fails in both directions. A stale entry is as much a failure as a missing one,
because a stale exemption hides the next real gap.
"""

import ast
import pathlib

import pytest
import yaml

from reality import catalogs
from reality.config import config_text
from reality.db import core as db
from reality.services import exceptions

SOURCE_ROOT = pathlib.Path(exceptions.__file__).resolve().parents[1]

# The records the queue reasons about. Every nullable foreign key on them has to
# be classified; nothing else is in scope, because nothing else is read to
# conclude that something is wrong.
GOVERNED_MODELS = (
    db.DocumentLine,
    db.Movement,
    db.Commitment,
    db.ReturnAnnouncement,
)

# One module per adapter. An adapter that cannot name a reference in its own
# schema cannot send it, whatever the service accepts.
ADAPTER_MODULES = {
    "API": "web/api.py",
    "Web": "web/api.py",
    "MCP": "mcp/catalog.py",
    "Chat": "tools/application.py",
    "CLI": "cli/app.py",
}


def _catalog() -> dict:
    return yaml.safe_load(config_text("reference_catalog.yaml"))


def _discovered_references() -> dict[str, set[str]]:
    """Every nullable foreign key on the governed records, from the mapper.

    Discovered rather than listed, because a list beside the code is exactly
    what drifts. A migration adding a nullable reference makes this gate fail
    until somebody says what the reference is for.
    """
    found: dict[str, set[str]] = {}
    for model in GOVERNED_MODELS:
        for column in model.__table__.columns:
            if column.foreign_keys and column.nullable:
                found.setdefault(model.__name__, set()).add(column.name)
    return found


def _load_bearing(catalog: dict | None = None) -> dict[str, dict]:
    catalog = catalog or _catalog()
    return {
        f"{record}.{name}": entry
        for record, references in catalog["records"].items()
        for name, entry in references.items()
        if entry.get("classification") == "load_bearing"
    }


def _module_functions(path: pathlib.Path) -> dict[str, ast.AST]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _names_field(node: ast.AST, fields: set[str]) -> set[str]:
    """Field names a function names itself, however it names them.

    Both spellings matter: `shipped_not_billed` reads the column through a
    helper's attribute access, and `invoice_price_differs` names it in a query.
    """
    found = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Attribute) and child.attr in fields:
            found.add(child.attr)
        if isinstance(child, ast.Constant) and child.value in fields:
            found.add(child.value)
    return found


def _callees(node: ast.AST) -> set[str]:
    names = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            if isinstance(child.func, ast.Name):
                names.add(child.func.id)
            elif isinstance(child.func, ast.Attribute):
                names.add(child.func.attr)
    return names


def _reaches(
    name: str,
    functions: dict[str, ast.AST],
    fields: set[str],
    seen: set[str] | None = None,
) -> set[str]:
    seen = set() if seen is None else seen
    if name in seen:
        return set()
    seen.add(name)
    node = functions.get(name)
    if node is None:
        return set()
    found = _names_field(node, fields)
    for callee in _callees(node):
        found |= _reaches(callee, functions, fields, seen)
    return found


def _discovered_consumers() -> dict[str, set[str]]:
    """Which classes read which load-bearing reference, from the source.

    Only load-bearing references are walked. A trace-only reference like
    `source_record_id` is read by almost every class to fill in its evidence,
    and walking those would name thirty-one of thirty-two classes and mean
    nothing. Keeping that distinction honest is the first gate's job.
    """
    fields = {name.split(".", 1)[1] for name in _load_bearing()}
    functions = _module_functions(pathlib.Path(exceptions.__file__))
    consumers: dict[str, set[str]] = {field: set() for field in fields}
    for class_id, derivator in exceptions.DERIVATION_REGISTRY.items():
        for field in _reaches(derivator.__name__, functions, fields):
            consumers[field].add(class_id)
    return consumers


def _constructions() -> list[tuple[str, str, str, set[str]]]:
    """Every construction of a governed record: module, function, record, keywords.

    Found by syntax tree rather than by text search, so a keyword spread over
    several lines still counts. The enclosing function matters because an
    exemption belongs to the path that builds the record, not to the file.
    """
    records = {model.__name__ for model in GOVERNED_MODELS}
    found: list[tuple[str, str, str, set[str]]] = []
    for path in sorted(SOURCE_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        holders: list[tuple[str, ast.AST]] = [
            (node.name, node)
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        seen: set[int] = set()
        for holder, node in holders:
            for child in ast.walk(node):
                if (
                    isinstance(child, ast.Call)
                    and isinstance(child.func, ast.Name)
                    and child.func.id in records
                    and any(keyword.arg for keyword in child.keywords)
                    and id(child) not in seen
                ):
                    seen.add(id(child))
                    found.append(
                        (
                            str(path.relative_to(SOURCE_ROOT)),
                            holder,
                            child.func.id,
                            {kw.arg for kw in child.keywords if kw.arg},
                        )
                    )
    return found


def _writing_commands() -> dict[str, dict]:
    """Commands whose service constructs a governed record, with their adapters."""
    commands = yaml.safe_load(config_text(catalogs.CATALOG_FILES["commands"]))
    constructing: dict[str, set[tuple[str, str]]] = {}
    for module, holder, record, _ in _constructions():
        constructing.setdefault(holder, set()).add((module, record))
    return {
        entry["service"]: {
            "adapters": entry.get("adapters", []),
            "constructions": constructing[entry["service"]],
        }
        for entry in commands["commands"]
        if entry.get("service") in constructing
    }


# ---------------------------------------------------------------------------
# Gate one: every nullable reference is classified.


def test_every_nullable_reference_is_classified():
    catalog = _catalog()
    declared = {
        record: set(references) for record, references in catalog["records"].items()
    }
    discovered = _discovered_references()

    assert declared == discovered, (
        "Reference catalog drift. Undeclared: "
        f"{ {record: sorted(names - declared.get(record, set())) for record, names in discovered.items() if names - declared.get(record, set())} }. "
        "Stale: "
        f"{ {record: sorted(names - discovered.get(record, set())) for record, names in declared.items() if names - discovered.get(record, set())} }"
    )
    for record, references in catalog["records"].items():
        for name, entry in references.items():
            assert entry["classification"] in {"load_bearing", "trace_only"}, (
                f"{record}.{name} is neither load-bearing nor trace-only"
            )
            assert str(entry.get("meaning", "")).strip(), (
                f"{record}.{name} does not say what it means"
            )
            if entry["classification"] == "trace_only":
                # A judgement somebody must be able to disagree with: the
                # consumer gate does not walk these, so a wrong call here is
                # not caught by anything else.
                assert str(entry.get("reason", "")).strip(), (
                    f"{record}.{name} is trace-only with no reason"
                )


# ---------------------------------------------------------------------------
# Gate two: the declared consumers are the discovered consumers.


def test_declared_consumers_are_the_discovered_consumers():
    discovered = _discovered_consumers()
    for reference, entry in _load_bearing().items():
        field = reference.split(".", 1)[1]
        declared = set(entry["consumers"])
        assert declared == discovered[field], (
            f"{reference}: declared {sorted(declared)}, "
            f"discovered {sorted(discovered[field])}"
        )
        for class_id, direction in entry["consumers"].items():
            assert class_id in exceptions.CLASS_ORDER, (
                f"{reference} names an unknown class: {class_id}"
            )
            # The most useful field in the file, and the one thing only a
            # person can say: reporting absence cries wolf, requiring presence
            # goes blind, and tracing costs nothing. Discovery proves the read;
            # it cannot tell a conclusion from a mention.
            assert direction in catalogs.REFERENCE_READINGS, (
                f"{reference}/{class_id} has no supported reading: {direction}"
            )


# ---------------------------------------------------------------------------
# Gate three: every writing path passes the reference through.


def _writer_exemptions(catalog: dict) -> dict[tuple[str, str, str, str], dict]:
    return {
        (entry["module"], entry["function"], entry["record"], entry["reference"]): entry
        for entry in catalog.get("writers_that_do_not_set_a_reference", [])
    }


def _required_by_record() -> dict[str, set[str]]:
    required: dict[str, set[str]] = {}
    for reference in _load_bearing():
        record, field = reference.split(".", 1)
        required.setdefault(record, set()).add(field)
    return required


def test_every_writer_passes_the_reference_through():
    catalog = _catalog()
    exempt = _writer_exemptions(catalog)
    required = _required_by_record()

    missing = []
    used = set()
    for module, holder, record, keywords in _constructions():
        for field in sorted(required.get(record, set())):
            if field in keywords:
                continue
            key = (module, holder, record, field)
            if key in exempt:
                used.add(key)
                assert str(exempt[key].get("reason", "")).strip(), (
                    f"{holder} builds a {record} without {field} and gives no reason"
                )
                continue
            missing.append(f"{module}:{holder} builds a {record} without {field}")
    assert not missing, "Writers dropping a reference the queue leans on: " + "; ".join(
        sorted(missing)
    )
    stale = sorted(
        f"{module}:{holder}/{record}.{field}"
        for module, holder, record, field in exempt
        if (module, holder, record, field) not in used
    )
    assert not stale, "Stale writer exemptions hide the next real one: " + "; ".join(
        stale
    )


# ---------------------------------------------------------------------------
# Gate four: every surface can carry the reference.


def _service_references() -> dict[str, set[str]]:
    """What each writing service must be able to be told.

    Composed with the writer exemptions: a service whose construction is
    deliberately not allowed to set a reference needs no surface that can carry
    it. Without that composition the gate would demand that a movement
    correction be able to claim it settles a return.
    """
    catalog = _catalog()
    exempt = _writer_exemptions(catalog)
    required = _required_by_record()
    wanted: dict[str, set[str]] = {}
    for service, entry in _writing_commands().items():
        for module, record in entry["constructions"]:
            for field in required.get(record, set()):
                if (module, service, record, field) in exempt:
                    continue
                wanted.setdefault(service, set()).add(field)
    return wanted


def test_every_reference_is_in_the_shared_input_glossary():
    """The one place this repository says what a parameter means.

    A load-bearing reference absent from the glossary is a reference described
    nowhere, and the glossary is what the generated MCP reference and the
    command contracts read their descriptions from. There is no exemption from
    this one.

    Its limit is worth knowing: the generator renders descriptions for top-level
    parameters, so a nested line field is described here and rendered nowhere
    yet. Described-and-unrendered is still better than undescribed, and the
    rendering is a separate piece of work.
    """
    commands = yaml.safe_load(config_text(catalogs.CATALOG_FILES["commands"]))
    described = set(commands["parameter_descriptions"])
    wanted = {field for fields in _service_references().values() for field in fields}

    missing = sorted(wanted - described)
    assert not missing, (
        "References the queue leans on that the shared input glossary never "
        "describes: " + ", ".join(missing)
    )


def test_every_adapter_can_carry_the_reference():
    catalog = _catalog()
    exempt = {
        (entry["service"], entry["adapter"], entry["reference"]): entry
        for entry in catalog.get("adapters_that_forward_without_naming", [])
    }
    adapters = {
        service: entry["adapters"] for service, entry in _writing_commands().items()
    }
    sources = {
        module: (SOURCE_ROOT / module).read_text(encoding="utf-8")
        for module in set(ADAPTER_MODULES.values())
    }
    missing = []
    used = set()
    for service, fields in sorted(_service_references().items()):
        for adapter in adapters[service]:
            module = ADAPTER_MODULES.get(adapter)
            if module is None:
                continue
            for field in sorted(fields):
                if field in sources[module]:
                    continue
                key = (service, adapter, field)
                if key in exempt:
                    used.add(key)
                    continue
                missing.append(f"{service} via {adapter} cannot carry {field}")
    assert not missing, "Surfaces that cannot set a reference: " + "; ".join(
        sorted(missing)
    )
    stale = sorted(
        f"{service}/{adapter}/{field}"
        for service, adapter, field in exempt
        if (service, adapter, field) not in used
    )
    assert not stale, "Stale adapter exemptions: " + "; ".join(stale)


def test_an_mcp_passthrough_is_not_an_exemption():
    """A passthrough is a capability for a person and an absence for an agent.

    MCP forwards whatever a caller sends, so the field has always worked if
    somebody knew to send it. No agent ever did, because an agent knows only
    what a schema names. So a human adapter may be exempted for forwarding and
    MCP may never be.
    """
    catalog = _catalog()
    for entry in catalog.get("adapters_that_forward_without_naming", []):
        assert entry["adapter"] != "MCP", (
            "An MCP schema cannot be exempted: an agent can only send what the "
            "schema names."
        )
        assert str(entry.get("reason", "")).strip(), (
            f"{entry['service']} via {entry['adapter']} is exempt with no reason"
        )


# ---------------------------------------------------------------------------
# Both directions.


def test_the_reference_catalog_fails_in_both_directions():
    """The gate has to refuse a missing entry and a stale one alike."""
    catalog = _catalog()
    record = next(iter(catalog["records"]))
    reference = next(iter(catalog["records"][record]))

    # A reference nobody classified.
    without = {
        **catalog,
        "records": {
            **catalog["records"],
            record: {
                name: entry
                for name, entry in catalog["records"][record].items()
                if name != reference
            },
        },
    }
    with pytest.raises(ValueError, match="not classified"):
        catalogs.load_reference_catalog(without)

    # A reference that no longer exists.
    invented = {
        **catalog,
        "records": {
            **catalog["records"],
            record: {
                **catalog["records"][record],
                "invented_reference_id": {
                    "classification": "trace_only",
                    "meaning": "Nothing.",
                    "reason": "Nothing.",
                },
            },
        },
    }
    with pytest.raises(ValueError, match="no longer exists"):
        catalogs.load_reference_catalog(invented)

    # The positive control: the catalog as it stands loads.
    assert catalogs.load_reference_catalog(catalog)


def test_the_loader_refuses_a_broken_catalog():
    """Validation lives in the loader, so anything that loads gets the refusal."""
    catalog = _catalog()
    record, references = next(iter(catalog["records"].items()))
    name, entry = next(iter(references.items()))

    def replaced(**changes):
        return {
            **catalog,
            "records": {
                **catalog["records"],
                record: {**references, name: {**entry, **changes}},
            },
        }

    with pytest.raises(ValueError, match="classification"):
        catalogs.load_reference_catalog(replaced(classification="probably_fine"))
    with pytest.raises(ValueError, match="means"):
        catalogs.load_reference_catalog(replaced(meaning="   "))
    if entry["classification"] == "trace_only":
        with pytest.raises(ValueError, match="reason"):
            catalogs.load_reference_catalog(replaced(reason=""))
    else:
        with pytest.raises(ValueError, match="consumers"):
            catalogs.load_reference_catalog(replaced(consumers={}))
        with pytest.raises(ValueError, match="direction"):
            catalogs.load_reference_catalog(
                replaced(
                    consumers={class_id: "sometimes" for class_id in entry["consumers"]}
                )
            )

    # The positive control.
    assert catalogs.load_reference_catalog(catalog)


def test_the_production_reference_catalog_is_the_measured_one():
    """The figures the specification quotes, pinned.

    Written down because the risk this feature came from said three references
    and three classes. Discovering them changed both numbers, and a reader
    should be able to see the current ones without running anything.
    """
    load_bearing = _load_bearing()
    consumers = {
        class_id for entry in load_bearing.values() for class_id in entry["consumers"]
    }
    directions = [
        direction
        for entry in load_bearing.values()
        for direction in entry["consumers"].values()
    ]

    assert len(load_bearing) == 4
    assert len(exceptions.CLASS_ORDER) == 39
    # Nineteen classes read one of the four references; twelve reason from one.
    assert len(consumers) == 19
    concluding = {
        class_id
        for entry in load_bearing.values()
        for class_id, reading in entry["consumers"].items()
        if reading != "traces_only"
    }
    assert len(concluding) == 12
    assert len(directions) == 29
    assert directions.count("reports_absence") == 8
    assert directions.count("requires_presence") == 13
    assert directions.count("traces_only") == 8
