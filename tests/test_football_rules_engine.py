import ast
from pathlib import Path

from app.domain.football.rules import FactCategory, FootballRulesEngine, ProviderNeutralEvent


def test_default_rules_are_pure_and_deterministic():
    engine = FootballRulesEngine.with_default_rules()
    events = (
        ProviderNeutralEvent(id="event-1", event_type="Goal"),
        ProviderNeutralEvent(id="event-2", event_type="Shot-on-goal"),
        ProviderNeutralEvent(id="event-3", event_type="pass"),
    )

    first = engine.derive_facts(events)
    second = engine.derive_facts(events)

    assert first == second
    assert events[0] == ProviderNeutralEvent(id="event-1", event_type="Goal")


def test_supported_event_types_produce_event_level_facts():
    engine = FootballRulesEngine.with_default_rules()
    events = (
        ProviderNeutralEvent(id="goal-1", event_type="goal"),
        ProviderNeutralEvent(id="shot-1", event_type="shot_on_goal"),
        ProviderNeutralEvent(id="card-1", event_type="yellow_card"),
        ProviderNeutralEvent(id="corner-1", event_type="corner"),
        ProviderNeutralEvent(id="foul-1", event_type="foul"),
        ProviderNeutralEvent(id="offside-1", event_type="offside"),
    )

    facts = engine.derive_facts(events)

    assert [(fact.event_id, fact.category) for fact in facts] == [
        ("goal-1", FactCategory.GOAL),
        ("shot-1", FactCategory.SHOT),
        ("card-1", FactCategory.CARD),
        ("corner-1", FactCategory.CORNER),
        ("foul-1", FactCategory.FOUL),
        ("offside-1", FactCategory.OFFSIDE),
    ]
    assert all(fact.value is True for fact in facts)


def test_unknown_or_incomplete_events_do_not_create_fabricated_facts():
    engine = FootballRulesEngine.with_default_rules()
    events = (
        ProviderNeutralEvent(id="unknown-1", event_type="throw_in"),
        ProviderNeutralEvent(id="missing-type", event_type=None),
        ProviderNeutralEvent(id=None, event_type="goal"),
        ProviderNeutralEvent(id="", event_type="shot"),
    )

    facts = engine.derive_facts(events)

    assert facts == ()


def test_explanations_include_event_id_and_rule_identity():
    engine = FootballRulesEngine.with_default_rules()
    facts = engine.derive_facts([ProviderNeutralEvent(id="event-1", event_type="Goal")])

    assert len(facts) == 1
    fact = facts[0]
    assert fact.explanation.contributing_event_ids == ("event-1",)
    assert fact.explanation.rule_id == "football.goal.recognition.v1"
    assert fact.explanation.rule_name == "Goal event recognition"
    assert fact.explanation.derivation_path == ("normalize_event_type", "match:goal", "fact:goal")
    assert fact.attributes == {"normalized_event_type": "goal"}


def test_rules_module_does_not_depend_on_api_database_or_provider_layers():
    rules_root = Path("app/domain/football/rules")
    forbidden_import_prefixes = (
        "app.api",
        "app.imports",
        "app.models",
        "app.repositories",
        "app.services",
        "fastapi",
        "sqlalchemy",
    )

    for path in rules_root.glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            module = None
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name
                    assert not module.startswith(forbidden_import_prefixes), f"{path} imports {module}"
            elif isinstance(node, ast.ImportFrom):
                module = node.module
                if module:
                    assert not module.startswith(forbidden_import_prefixes), f"{path} imports {module}"
