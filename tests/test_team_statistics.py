import ast
from pathlib import Path

from app.domain.football.rules import ProviderNeutralEvent
from app.domain.football.statistics import StatisticName, TeamStatisticsCalculator


HOME_TEAM = "home-team"
AWAY_TEAM = "away-team"


def test_team_statistics_are_counted_by_team():
    calculator = TeamStatisticsCalculator.with_default_rules()
    events = (
        ProviderNeutralEvent(id="home-goal", team_id=HOME_TEAM, event_type="goal"),
        ProviderNeutralEvent(id="home-shot", team_id=HOME_TEAM, event_type="shot_on_goal"),
        ProviderNeutralEvent(id="home-corner", team_id=HOME_TEAM, event_type="corner"),
        ProviderNeutralEvent(id="home-foul", team_id=HOME_TEAM, event_type="foul"),
        ProviderNeutralEvent(id="home-offside", team_id=HOME_TEAM, event_type="offside"),
        ProviderNeutralEvent(id="home-yellow", team_id=HOME_TEAM, event_type="yellow_card"),
        ProviderNeutralEvent(id="away-red", team_id=AWAY_TEAM, event_type="red_card"),
        ProviderNeutralEvent(id="away-shot", team_id=AWAY_TEAM, event_type="shot"),
    )

    summary = calculator.calculate(events)

    assert summary.get(HOME_TEAM, StatisticName.GOALS).value == 1  # type: ignore[union-attr]
    assert summary.get(HOME_TEAM, StatisticName.SHOTS).value == 1  # type: ignore[union-attr]
    assert summary.get(HOME_TEAM, StatisticName.SHOTS_ON_TARGET).value == 1  # type: ignore[union-attr]
    assert summary.get(HOME_TEAM, StatisticName.CORNERS).value == 1  # type: ignore[union-attr]
    assert summary.get(HOME_TEAM, StatisticName.FOULS).value == 1  # type: ignore[union-attr]
    assert summary.get(HOME_TEAM, StatisticName.OFFSIDES).value == 1  # type: ignore[union-attr]
    assert summary.get(HOME_TEAM, StatisticName.YELLOW_CARDS).value == 1  # type: ignore[union-attr]
    assert summary.get(HOME_TEAM, StatisticName.RED_CARDS).value == 0  # type: ignore[union-attr]
    assert summary.get(AWAY_TEAM, StatisticName.SHOTS).value == 1  # type: ignore[union-attr]
    assert summary.get(AWAY_TEAM, StatisticName.RED_CARDS).value == 1  # type: ignore[union-attr]


def test_events_without_team_attribution_do_not_inflate_team_statistics():
    calculator = TeamStatisticsCalculator.with_default_rules()
    events = (
        ProviderNeutralEvent(id="unknown-goal", team_id=None, event_type="goal"),
        ProviderNeutralEvent(id="blank-shot", team_id=" ", event_type="shot_on_goal"),
        ProviderNeutralEvent(id="home-shot", team_id=HOME_TEAM, event_type="shot"),
        ProviderNeutralEvent(id="unknown-card", team_id=None, event_type="yellow_card"),
    )

    summary = calculator.calculate(events)

    assert len(summary.statistics) == 8
    assert {statistic.team_id for statistic in summary.statistics} == {HOME_TEAM}
    assert summary.get(HOME_TEAM, StatisticName.GOALS).value == 0  # type: ignore[union-attr]
    assert summary.get(HOME_TEAM, StatisticName.SHOTS).value == 1  # type: ignore[union-attr]
    assert summary.get(HOME_TEAM, StatisticName.SHOTS_ON_TARGET).value == 0  # type: ignore[union-attr]
    assert summary.get(HOME_TEAM, StatisticName.YELLOW_CARDS).value == 0  # type: ignore[union-attr]


def test_no_team_statistic_is_fabricated_when_no_events_have_team():
    calculator = TeamStatisticsCalculator.with_default_rules()
    events = (
        ProviderNeutralEvent(id="unknown-goal", team_id=None, event_type="goal"),
        ProviderNeutralEvent(id="unknown-shot", team_id="", event_type="shot"),
    )

    summary = calculator.calculate(events)

    assert summary.statistics == ()


def test_team_statistic_explanation_includes_team_events_and_rules():
    calculator = TeamStatisticsCalculator.with_default_rules()
    summary = calculator.calculate([ProviderNeutralEvent(id="shot-1", team_id=HOME_TEAM, event_type="shot_on_goal")])

    shots_on_target = summary.get(HOME_TEAM, StatisticName.SHOTS_ON_TARGET)

    assert shots_on_target is not None
    assert shots_on_target.team_id == HOME_TEAM
    assert shots_on_target.value == 1
    assert shots_on_target.explanation.contributing_event_ids == ("shot-1",)
    assert shots_on_target.explanation.contributing_fact_refs == ("football.shot.recognition.v1:shot-1:shot",)
    assert shots_on_target.explanation.rule_ids == ("football.shot.recognition.v1",)
    assert shots_on_target.explanation.rule_names == ("Shot event recognition",)
    assert shots_on_target.explanation.derivation_path == (
        "football_rules_engine",
        "filter_team_attributed_facts",
        f"team:{HOME_TEAM}",
        "statistic:shots_on_target",
    )


def test_team_statistics_are_deterministic():
    calculator = TeamStatisticsCalculator.with_default_rules()
    events = (
        ProviderNeutralEvent(id="home-goal", team_id=HOME_TEAM, event_type="goal"),
        ProviderNeutralEvent(id="away-shot", team_id=AWAY_TEAM, event_type="shot"),
    )

    first = calculator.calculate(events)
    second = calculator.calculate(events)

    assert first == second


def test_statistics_layer_still_has_no_api_database_or_provider_imports():
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


def test_team_statistics_are_not_persisted_as_canonical_database_truth():
    assert not Path("app/models/team_statistic.py").exists()

    for migration in Path("alembic/versions").glob("*.py"):
        content = migration.read_text().lower()
        assert "create_table(\"team_statistics\"" not in content
