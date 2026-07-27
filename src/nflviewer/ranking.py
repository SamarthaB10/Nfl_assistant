from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime

from nflviewer.data import TeamMetrics
from nflviewer.matchup_quality import calculate_matchup_quality
from nflviewer.models import RankedGame, RecordSummary, ScoreBreakdown
from nflviewer.records import build_team_rating
from nflviewer.rivalries import (
    CONFERENCE_OR_INTERCONFERENCE,
    DIVISIONAL,
    HISTORIC_OR_REGIONAL,
    classify_rivalry,
)
from nflviewer.standings import TeamStanding, matchup_leverage

MATCHUP_QUALITY_WEIGHT = 0.55
CONTEXT_WEIGHT = 0.45
LOW_WATCHABILITY_THRESHOLD = 3.20
BELOW_AVERAGE_STRENGTH = 0.40
LOW_CONTEXT_THRESHOLD = 0.15
BLOWOUT_RISK_CLOSENESS = 0.55


@dataclass(frozen=True)
class MatchupInput:
    game_id: str
    week: int
    kickoff: datetime
    home_team_id: str
    home_team_name: str
    home_logo_url: str | None
    away_team_id: str
    away_team_name: str
    away_logo_url: str | None
    is_divisional: bool


def _record_profile(win_rate: float) -> str:
    if win_rate >= 0.75:
        return "elite record"
    if win_rate >= 0.625:
        return "strong record"
    if win_rate > 0.50:
        return "winning record"
    if win_rate == 0.50:
        return ".500 record"
    return "losing record"


def _unit_profile(percentile: float, unit: str) -> str:
    if percentile >= 0.80:
        return f"top-tier {unit}"
    if percentile >= 0.60:
        return f"above-average {unit}"
    if percentile >= 0.40:
        return f"middle-of-the-pack {unit}"
    return f"below-average {unit}"


def _team_profile_reason(
    team_name: str,
    win_rate: float,
    metrics: TeamMetrics,
) -> str:
    return (
        f"{team_name} profile: {_record_profile(win_rate)}, "
        f"{_unit_profile(metrics.offense_percentile, 'offense')}, "
        f"{_unit_profile(metrics.defense_percentile, 'defense')}"
    )


def score_matchup(
    matchup: MatchupInput,
    previous_records: Mapping[str, RecordSummary],
    current_records: Mapping[str, RecordSummary],
    *,
    standings: Mapping[str, TeamStanding] | None = None,
    team_metrics: Mapping[str, TeamMetrics] | None = None,
) -> RankedGame:
    home = build_team_rating(
        team_id=matchup.home_team_id,
        team_name=matchup.home_team_name,
        logo_url=matchup.home_logo_url,
        previous_record=previous_records[matchup.home_team_id],
        current_record=current_records[matchup.home_team_id],
        week=matchup.week,
    )
    away = build_team_rating(
        team_id=matchup.away_team_id,
        team_name=matchup.away_team_name,
        logo_url=matchup.away_logo_url,
        previous_record=previous_records[matchup.away_team_id],
        current_record=current_records[matchup.away_team_id],
        week=matchup.week,
    )

    both_good = home.is_good and away.is_good
    record_quality = min(home.scoring_win_rate, away.scoring_win_rate) if both_good else 0.0
    rivalry_category, rivalry_value = classify_rivalry(
        matchup.home_team_id,
        matchup.away_team_id,
        is_divisional=matchup.is_divisional,
    )
    leverage = (
        matchup_leverage(
            matchup.home_team_id,
            matchup.away_team_id,
            week=matchup.week,
            standings=standings,
        )
        if standings is not None
        else None
    )
    leverage_value = leverage.value if leverage else 0.0
    neutral_metrics = TeamMetrics(
        points_for_per_game=0,
        points_allowed_per_game=0,
        offense_percentile=0.5,
        defense_percentile=0.5,
    )
    home_metrics = (
        team_metrics.get(matchup.home_team_id, neutral_metrics)
        if team_metrics is not None
        else neutral_metrics
    )
    away_metrics = (
        team_metrics.get(matchup.away_team_id, neutral_metrics)
        if team_metrics is not None
        else neutral_metrics
    )
    quality = calculate_matchup_quality(
        home_win_rate=home.scoring_win_rate,
        away_win_rate=away.scoring_win_rate,
        home_metrics=home_metrics,
        away_metrics=away_metrics,
    )
    context_value = leverage_value + (1 - leverage_value) * rivalry_value
    raw_score = MATCHUP_QUALITY_WEIGHT * quality.value + CONTEXT_WEIGHT * context_value
    normalized_score = min(max(raw_score, 0.0), 1.0)
    display_score = round(1 + 9 * normalized_score, 2)

    reasons: list[str] = []
    if both_good:
        if matchup.week <= 5:
            reasons.append("Both teams rate above .500 using early-season adjusted records")
        else:
            reasons.append("Both teams have winning records")
    if rivalry_category == DIVISIONAL:
        reasons.append("Divisional matchup")
    elif rivalry_category == CONFERENCE_OR_INTERCONFERENCE:
        reasons.append("Recognized conference or interconference rivalry")
    elif rivalry_category == HISTORIC_OR_REGIONAL:
        reasons.append("Historic or regional rivalry")
    if leverage and leverage.reason and leverage.value > 0:
        reasons.append(leverage.reason)
    if quality.value >= 0.65:
        reasons.extend(
            [
                _team_profile_reason(
                    matchup.away_team_name,
                    away.scoring_win_rate,
                    away_metrics,
                ),
                _team_profile_reason(
                    matchup.home_team_name,
                    home.scoring_win_rate,
                    home_metrics,
                ),
                (f"Projected matchup closeness: {quality.competitive_closeness:.2f}/1.00"),
            ]
        )
    elif display_score > LOW_WATCHABILITY_THRESHOLD and quality.competitive_closeness >= 0.85:
        reasons.append("Offense-defense profiles project a close game")
    if display_score <= LOW_WATCHABILITY_THRESHOLD:
        low_reasons: list[str] = []
        if (
            quality.home_team_strength < BELOW_AVERAGE_STRENGTH
            and quality.away_team_strength < BELOW_AVERAGE_STRENGTH
        ):
            low_reasons.append("Both teams rate below average in overall team quality")
        if quality.competitive_closeness < BLOWOUT_RISK_CLOSENESS:
            low_reasons.append("Team profiles indicate elevated blowout risk")
        if context_value < LOW_CONTEXT_THRESHOLD:
            low_reasons.append("Limited rivalry or standings stakes")
        if not low_reasons:
            low_reasons.append(
                "Combined team quality and game stakes rate below the weekly standard"
            )
        reasons.extend(low_reasons)

    return RankedGame(
        rank=1,
        game_id=matchup.game_id,
        kickoff=matchup.kickoff,
        away_team=away,
        home_team=home,
        watchability_score=display_score,
        breakdown=ScoreBreakdown(
            record_quality=record_quality,
            home_team_strength=quality.home_team_strength,
            away_team_strength=quality.away_team_strength,
            competitive_closeness=quality.competitive_closeness,
            matchup_quality=quality.value,
            rivalry_category=rivalry_category,
            rivalry_value=rivalry_value,
            leverage_value=leverage_value,
            leverage_reason=leverage.reason if leverage else None,
            context_value=context_value,
            raw_score=raw_score,
            display_score=display_score,
        ),
        reasons=reasons,
    )


def rank_matchups(
    matchups: Sequence[MatchupInput],
    previous_records: Mapping[str, RecordSummary],
    current_records: Mapping[str, RecordSummary],
    *,
    standings: Mapping[str, TeamStanding] | None = None,
    team_metrics: Mapping[str, TeamMetrics] | None = None,
    top: int | None = None,
    bottom: int | None = None,
) -> list[RankedGame]:
    if top is not None and top < 1:
        raise ValueError("top must be at least 1")
    if bottom is not None and bottom < 1:
        raise ValueError("bottom must be at least 1")
    if top is not None and bottom is not None:
        raise ValueError("top and bottom are mutually exclusive")

    scored = [
        score_matchup(
            matchup,
            previous_records,
            current_records,
            standings=standings,
            team_metrics=team_metrics,
        )
        for matchup in matchups
    ]
    scored.sort(
        key=lambda game: (
            -game.breakdown.raw_score,
            -game.breakdown.context_value,
            -game.breakdown.matchup_quality,
            -game.breakdown.competitive_closeness,
            -game.breakdown.record_quality,
            -game.breakdown.leverage_value,
            -game.breakdown.rivalry_value,
            game.kickoff,
            game.game_id,
        )
    )
    ranked = [game.model_copy(update={"rank": rank}) for rank, game in enumerate(scored, 1)]
    if top is not None:
        return ranked[:top]
    if bottom is not None:
        return list(reversed(ranked[-bottom:]))
    return ranked
