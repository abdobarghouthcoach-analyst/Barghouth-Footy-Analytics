import ast
from pathlib import Path

from app.domain.football.rules import ProviderNeutralEvent
from app.domain.football.statistics import PlayerStatisticsCalculator, StatisticName


PLAYER_ONE = "player-one"
PLAYER_TWO = "player-two"
ASSIST_PLAYER = "assist-player"


def test_player_goals_shots_and_cards_are_counted_from_player_attribution():
    calculator = PlayerStatisticsCalculator.with_default_rules()
    events = (
        ProviderNeutralEvent(id="goal-1", player_id=PLAYER_ONE, event_type="goal"),
        ProviderNeutralEvent(id="shot-1", player_id=PLAYER_ONE, event_type="shot_on_goal"),
        ProviderNeutralEvent(id="yellow-1", player_id=PLAYER_ONE, event_type="yellow_card"),
        ProviderNeutralEvent(id="red-1", player_id=PLAYER_TWO, event_type="red_card"),
        ProviderNeutralEvent(id="shot-2", player_id=PLAYER_TWO, event_type="shot"),
    )

    summary = calculator.calculate(events)

    assert summary.get(PLAYER_ONE, StatisticName.GOALS).value == 1  # type: ignore[union-attr]
    assert summary.get(PLAYER_ONE, StatisticName.SHOTS).value == 1  # type: ignore[union-attr]
    assert summary.get(PLAYER_ONE, StatisticName.YELLOW_CARDS).value == 1  # type: ignore[union-attr]
    assert summary.get(PLAYER_ONE, StatisticName.RED_CARDS).value == 0  # type: ignore[union-attr]
    assert summary.get(PLAYER_TWO, StatisticName.GOALS).value == 0  # type: ignore[union-attr]
    assert summary.get(PLAYER_TWO, StatisticName.SHOTS).value == 1  # type: ignore[union-attr]
    assert summary.get(PLAYER_TWO, StatisticName.RED_CARDS).value == 1  # type: ignore[union-attr]


def test_assists_are_counted_only_with_explicit_assist_attribution():
    calculator = PlayerStatisticsCalculator.with_default_rules()
    events = (
        ProviderNeutralEvent(id="goal-1", player_id=PLAYER_ONE, assist_player_id=ASSIST_PLAYER, event_type="goal"),
        ProviderNeutralEvent(id="goal-2", player_id=PLAYER_TWO, event_type="goal"),
    )

    summary = calculator.calculate(events)

    assert summary.get(ASSIST_PLAYER, StatisticName.ASSISTS).value == 1  # type: ignore[union-attr]
    assert summary.get(PLAYER_ONE, StatisticName.ASSISTS) is None
    assert summary.get(PLAYER_TWO, StatisticName.ASSISTS) is None


def test_missing_player_attribution_does_not_inflate_player_statistics():
    calculator = PlayerStatisticsCalculator.with_default_rules()
    events = (
        ProviderNeutralEvent(id="unknown-goal", player_id=None, event_type="goal"),
        ProviderNeutralEvent(id="blank-shot", player_id=" ", event_type="shot_on_goal"),
        ProviderNeutralEvent(id="known-shot", player_id=PLAYER_ONE, event_type="shot"),
        ProviderNeutralEvent(id="unknown-card", player_id=None, event_type="yellow_card"),
    )

    summary = calculator.calculate(events)

    assert {statistic.player_id for statistic in summary.statistics} == {PLAYER_ONE}
    assert summary.get(PLAYER_ONE, StatisticName.GOALS).value == 0  # type: ignore[union-attr]
    assert summary.get(PLAYER_ONE, StatisticName.SHOTS).value == 1  # type: ignore[union-attr]
    assert summary.get(PLAYER_ONE, StatisticName.YELLOW_CARDS).value == 0  # type: ignore[union-attr]


def test_missing_or_blank_assist_attribution_does_not_fabricate_assists():
    calculator = PlayerStatisticsCalculator.with_default_rules()
    events = (
        ProviderNeutralEvent(id="goal-1", player_id=PLAYER_ONE, assist_player_id=None, event_type="goal"),
        ProviderNeutralEvent(id="goal-2", player_id=PLAYER_TWO, assist_player_id=" ", event_type="goal"),
    )

    summary = calculator.calculate(events)

    assert summary.get(PLAYER_ONE, StatisticName.ASSISTS) is None
    assert summary.get(PLAYER_TWO, StatisticName.ASSISTS) is None


def test_no_player_statistic_is_fabricated_when_no_events_have_player_attribution():
    calculator = PlayerStatisticsCalculator.with_default_rules()
    events = (
        ProviderNeutralEvent(id="unknown-goal", player_id=None, event_type="goal"),
        ProviderNeutralEvent(id="unknown-shot", player_id="", event_type="shot"),
    )

    summary = calculator.calculate(events)

    assert summary.statistics == ()


def test_player_statistic_explanation_includes_player_events_and_rules():
    calculator = PlayerStatisticsCalculator.with_default_rules()
    summary = calculator.calculate([ProviderNeutralEvent(id="goal-1", player_id=PLAYER_ONE, event_type="goal")])

    goals = summary.get(PLAYER_ONE, StatisticName.GOALS)

    assert goals is not None
    assert goals.player_id == PLAYER_ONE
    assert goals.value == 1
    assert goals.explanation.contributing_event_ids == ("goal-1",)
    assert goals.explanation.contributing_fact_refs == ("football.goal.recognition.v1:goal-1:goal",)
    assert goals.explanation.rule_ids == ("football.goal.recognition.v1",)
    assert goals.explanation.rule_names == ("Goal event recognition",)
    assert goals.explanation.derivation_path == (
        "football_rules_engine",
        "filter_player_attributed_facts",
        f"player:{PLAYER_ONE}",
        "statistic:goals",
    )


def test_player_statistics_are_deterministic():
    calculator = PlayerStatisticsCalculator.with_default_rules()
    events = (
        ProviderNeutralEvent(id="goal-1", player_id=PLAYER_ONE, event_type="goal"),
        ProviderNeutralEvent(id="shot-1", player_id=PLAYER_TWO, event_type="shot"),
    )

    first = calculator.calculate(events)
    second = calculator.calculate(events)

    assert first == second


def test_statistics_layer_remains_free_of_api_database_or_provider_imports():
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


def test_player_statistics_are_not_persisted_as_canonical_database_truth():
    assert not Path("app/models/player_statistic.py").exists()

    for migration in Path("alembic/versions").glob("*.py"):
        content = migration.read_text().lower()
        assert "create_table(\"player_statistics\"" not in content
