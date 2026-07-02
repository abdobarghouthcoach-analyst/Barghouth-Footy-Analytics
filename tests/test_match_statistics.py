import ast
from pathlib import Path

from app.domain.football.rules import ProviderNeutralEvent
from app.domain.football.statistics import MatchStatisticsCalculator, StatisticName


def test_match_statistics_are_derived_from_events():
    calculator = MatchStatisticsCalculator.with_default_rules()
    events = (
        ProviderNeutralEvent(id="goal-1", event_type="goal"),
        ProviderNeutralEvent(id="shot-1", event_type="shot"),
        ProviderNeutralEvent(id="shot-2", event_type="shot_on_goal"),
        ProviderNeutralEvent(id="corner-1", event_type="corner"),
        ProviderNeutralEvent(id="foul-1", event_type="foul"),
        ProviderNeutralEvent(id="offside-1", event_type="offside"),
        ProviderNeutralEvent(id="yellow-1", event_type="yellow_card"),
        ProviderNeutralEvent(id="red-1", event_type="red_card"),
    )

    summary = calculator.calculate(events)

    assert summary.get(StatisticName.GOALS).value == 1  # type: ignore[union-attr]
    assert summary.get(StatisticName.SHOTS).value == 2  # type: ignore[union-attr]
    assert summary.get(StatisticName.SHOTS_ON_TARGET).value == 1  # type: ignore[union-attr]
    assert summary.get(StatisticName.CORNERS).value == 1  # type: ignore[union-attr]
    assert summary.get(StatisticName.FOULS).value == 1  # type: ignore[union-attr]
    assert summary.get(StatisticName.OFFSIDES).value == 1  # type: ignore[union-attr]
    assert summary.get(StatisticName.YELLOW_CARDS).value == 1  # type: ignore[union-attr]
    assert summary.get(StatisticName.RED_CARDS).value == 1  # type: ignore[union-attr]


def test_unknown_or_incomplete_events_do_not_inflate_statistics():
    calculator = MatchStatisticsCalculator.with_default_rules()
    events = (
        ProviderNeutralEvent(id="unknown-1", event_type="throw_in"),
        ProviderNeutralEvent(id="missing-type", event_type=None),
        ProviderNeutralEvent(id=None, event_type="goal"),
        ProviderNeutralEvent(id="shot-1", event_type="shot", raw_payload={"outcome": "on_target"}),
        ProviderNeutralEvent(id="card-1", event_type="card"),
    )

    summary = calculator.calculate(events)

    assert summary.get(StatisticName.GOALS).value == 0  # type: ignore[union-attr]
    assert summary.get(StatisticName.SHOTS).value == 1  # type: ignore[union-attr]
    assert summary.get(StatisticName.SHOTS_ON_TARGET).value == 0  # type: ignore[union-attr]
    assert summary.get(StatisticName.YELLOW_CARDS).value == 0  # type: ignore[union-attr]
    assert summary.get(StatisticName.RED_CARDS).value == 0  # type: ignore[union-attr]


def test_statistics_include_event_fact_and_rule_explanations():
    calculator = MatchStatisticsCalculator.with_default_rules()
    summary = calculator.calculate([ProviderNeutralEvent(id="shot-1", event_type="shot_on_goal")])

    shots_on_target = summary.get(StatisticName.SHOTS_ON_TARGET)

    assert shots_on_target is not None
    assert shots_on_target.value == 1
    assert shots_on_target.explanation.contributing_event_ids == ("shot-1",)
    assert shots_on_target.explanation.contributing_fact_refs == ("football.shot.recognition.v1:shot-1:shot",)
    assert shots_on_target.explanation.rule_ids == ("football.shot.recognition.v1",)
    assert shots_on_target.explanation.rule_names == ("Shot event recognition",)
    assert shots_on_target.explanation.derivation_path == (
        "football_rules_engine",
        "filter_matching_facts",
        "statistic:shots_on_target",
    )


def test_statistics_are_deterministic():
    calculator = MatchStatisticsCalculator.with_default_rules()
    events = (
        ProviderNeutralEvent(id="goal-1", event_type="goal"),
        ProviderNeutralEvent(id="shot-1", event_type="shot_on_goal"),
    )

    first = calculator.calculate(events)
    second = calculator.calculate(events)

    assert first == second


def test_statistics_layer_does_not_depend_on_api_database_or_provider_layers():
    statistics_root = Path("app/domain/football/statistics")
    forbidden_import_prefixes = (
        "app.api",
        "app.imports",
        "app.models",
        "app.repositories",
        "app.services",
        "fastapi",
        "sqlalchemy",
    )

    for path in statistics_root.glob("*.py"):
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


def test_statistics_are_not_persisted_as_canonical_database_truth():
    assert not Path("app/models/statistic.py").exists()
    assert not Path("app/models/match_statistic.py").exists()

    for migration in Path("alembic/versions").glob("*.py"):
        content = migration.read_text().lower()
        assert "create_table(\"match_statistics\"" not in content
        assert "create_table(\"statistics\"" not in content
