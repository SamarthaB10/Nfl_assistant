from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime

from nflviewer.models import RankedGame, RecordSummary, ScoreBreakdown
from nflviewer.records import build_team_rating
from nflviewer.rivalries import (
    CONFERENCE_OR_INTERCONFERENCE,
    DIVISIONAL,
    HISTORIC_OR_REGIONAL,
    classify_rivalry,
)


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


def score_matchup(
    matchup: MatchupInput,
    previous_records: Mapping[str, RecordSummary],
    current_records: Mapping[str, RecordSummary],
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
    raw_score = record_quality + (1 - record_quality) * rivalry_value
    display_score = round(min(max(raw_score, 0.0), 1.0), 2)

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

    return RankedGame(
        rank=1,
        game_id=matchup.game_id,
        kickoff=matchup.kickoff,
        away_team=away,
        home_team=home,
        watchability_score=display_score,
        breakdown=ScoreBreakdown(
            record_quality=record_quality,
            rivalry_category=rivalry_category,
            rivalry_value=rivalry_value,
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
    top: int | None = None,
) -> list[RankedGame]:
    if top is not None and top < 1:
        raise ValueError("top must be at least 1")

    scored = [score_matchup(matchup, previous_records, current_records) for matchup in matchups]
    scored.sort(
        key=lambda game: (
            -game.breakdown.raw_score,
            -game.breakdown.record_quality,
            -game.breakdown.rivalry_value,
            game.kickoff,
            game.game_id,
        )
    )
    ranked = [game.model_copy(update={"rank": rank}) for rank, game in enumerate(scored, 1)]
    return ranked if top is None else ranked[:top]
