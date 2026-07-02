import ast
from pathlib import Path

from app.domain.football.rules import ProviderNeutralEvent
from app.domain.football.statistics import (
    MatchStatisticsCalculator,
    PlayerStatisticsCalculator,
    StatisticName,
    StatisticScope,
    TeamStatisticsCalculator,
)


TEAM_ID = "team-a"
PLAYER_ID = "player-a"
ASSIST_PLAYER_ID = "player-b"


def test_match_statistic_explanation_detail_is_complete():
    summary = MatchStatisticsCalculator.with_default_rules().calculate(
        [ProviderNeutralEvent(id="goal-1", event_type="goal")]
    )

    detail = summary.explain(StatisticName.GOALS)

    assert detail is not None
    assert detail.statistic_name == StatisticName.GOALS
    assert detail.value == 1
    assert detail.scope == StatisticScope.MATCH
    assert detail.team_id is None
    assert detail.player_id is None
    assert detail.contributing_event_ids == ("goal-1",)
    assert detail.contributing_fact_refs == ("football.goal.recognition.v1:goal-1:goal",)
    assert detail.rule_ids == ("football.goal.recognition.v1",)
    assert detail.rule_names == ("Goal event recognition",)
    assert detail.derivation_path == ("football_rules_engine", "filter_matching_facts", "statistic:goals")
    assert detail.incomplete_attribution_notes == ()


def test_team_statistic_explanation_detail_is_complete_with_attribution_notes():
    summary = TeamStatisticsCalculator.with_default_rules().calculate(
        [
            ProviderNeutralEvent(id="team-shot", team_id=TEAM_ID, event_type="shot"),
            ProviderNeutralEvent(id="unknown-shot", team_id=None, event_type="shot"),
        ]
    )

    detail = summary.explain(TEAM_ID, StatisticName.SHOTS)

    assert detail is not None
    assert detail.statistic_name == StatisticName.SHOTS
    assert detail.value == 1
    assert detail.scope == StatisticScope.TEAM
    assert detail.team_id == TEAM_ID
    assert detail.player_id is None
    assert detail.contributing_event_ids == ("team-shot",)
    assert detail.rule_ids == ("football.shot.recognition.v1",)
    assert detail.rule_names == ("Shot event recognition",)
    assert detail.derivation_path == (
        "football_rules_engine",
        "filter_team_attributed_facts",
        f"team:{TEAM_ID}",
        "statistic:shots",
    )
    assert detail.incomplete_attribution_notes == (
        "1 shots fact(s) excluded because team attribution is missing: unknown-shot.",
    )


def test_player_statistic_explanation_detail_is_complete_with_assist_attribution_notes():
    summary = PlayerStatisticsCalculator.with_default_rules().calculate(
        [
            ProviderNeutralEvent(
                id="goal-with-assist",
                player_id=PLAYER_ID,
                assist_player_id=ASSIST_PLAYER_ID,
                event_type="goal",
            ),
            ProviderNeutralEvent(id="goal-without-assist", player_id=PLAYER_ID, event_type="goal"),
        ]
    )

    detail = summary.explain(ASSIST_PLAYER_ID, StatisticName.ASSISTS)

    assert detail is not None
    assert detail.statistic_name == StatisticName.ASSISTS
    assert detail.value == 1
    assert detail.scope == StatisticScope.PLAYER
    assert detail.team_id is None
    assert detail.player_id == ASSIST_PLAYER_ID
    assert detail.contributing_event_ids == ("goal-with-assist",)
    assert detail.rule_ids == ("football.goal.recognition.v1",)
    assert detail.rule_names == ("Goal event recognition",)
    assert detail.derivation_path == (
        "football_rules_engine",
        "filter_player_attributed_facts",
        f"player:{ASSIST_PLAYER_ID}",
        "statistic:assists",
    )
    assert detail.incomplete_attribution_notes == (
        "1 assists fact(s) excluded because assist player attribution is missing: goal-without-assist.",
    )


def test_missing_attribution_remains_non_fabricated_and_explain_returns_none():
    team_summary = TeamStatisticsCalculator.with_default_rules().calculate(
        [ProviderNeutralEvent(id="unknown-goal", team_id=None, event_type="goal")]
    )
    player_summary = PlayerStatisticsCalculator.with_default_rules().calculate(
        [ProviderNeutralEvent(id="unknown-goal", player_id=None, event_type="goal")]
    )

    assert team_summary.statistics == ()
    assert team_summary.explain(TEAM_ID, StatisticName.GOALS) is None
    assert player_summary.statistics == ()
    assert player_summary.explain(PLAYER_ID, StatisticName.GOALS) is None


def test_explanation_retrieval_is_deterministic():
    events = [ProviderNeutralEvent(id="shot-1", team_id=TEAM_ID, event_type="shot_on_goal")]
    calculator = TeamStatisticsCalculator.with_default_rules()

    first = calculator.calculate(events).explain(TEAM_ID, StatisticName.SHOTS_ON_TARGET)
    second = calculator.calculate(events).explain(TEAM_ID, StatisticName.SHOTS_ON_TARGET)

    assert first == second


def test_statistics_domain_has_no_api_database_or_provider_imports():
    roots = (Path("app/domain/football/statistics"), Path("app/domain/football/rules"))
    forbidden_import_prefixes = (
        "app.api",
        "app.imports",
        "app.models",
        "app.repositories",
        "app.services",
        "fastapi",
        "sqlalchemy",
    )

    for root in roots:
        for path in root.glob("*.py"):
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


def test_explainability_adds_no_statistics_persistence():
    forbidden_model_files = (
        Path("app/models/statistic.py"),
        Path("app/models/match_statistic.py"),
        Path("app/models/team_statistic.py"),
        Path("app/models/player_statistic.py"),
    )
    for path in forbidden_model_files:
        assert not path.exists()

    for migration in Path("alembic/versions").glob("*.py"):
        content = migration.read_text().lower()
        assert "create_table(\"statistics\"" not in content
        assert "create_table(\"match_statistics\"" not in content
        assert "create_table(\"team_statistics\"" not in content
        assert "create_table(\"player_statistics\"" not in content
