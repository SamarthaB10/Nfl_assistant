from nflviewer.models import RecordSummary, TeamRating

PRIOR_GAMES = 4
ADJUSTED_RATE_MAX_WEEK = 5


def win_rate(record: RecordSummary) -> float:
    games = record.wins + record.losses + record.ties
    if games == 0:
        return 0.5
    return (record.wins + 0.5 * record.ties) / games


def adjusted_win_rate(
    previous_record: RecordSummary,
    current_record: RecordSummary,
) -> float:
    current_games = current_record.wins + current_record.losses + current_record.ties
    current_equivalent_wins = current_record.wins + 0.5 * current_record.ties
    return (PRIOR_GAMES * win_rate(previous_record) + current_equivalent_wins) / (
        PRIOR_GAMES + current_games
    )


def scoring_win_rate(
    previous_record: RecordSummary,
    current_record: RecordSummary,
    *,
    week: int,
) -> float:
    if week <= ADJUSTED_RATE_MAX_WEEK:
        return adjusted_win_rate(previous_record, current_record)
    return win_rate(current_record)


def build_team_rating(
    *,
    team_id: str,
    team_name: str,
    logo_url: str | None,
    previous_record: RecordSummary,
    current_record: RecordSummary,
    week: int,
) -> TeamRating:
    previous_rate = win_rate(previous_record)
    scoring_rate = scoring_win_rate(previous_record, current_record, week=week)
    return TeamRating(
        team_id=team_id,
        team_name=team_name,
        logo_url=logo_url,
        previous_record=previous_record,
        current_record=current_record,
        previous_win_rate=previous_rate,
        scoring_win_rate=scoring_rate,
        is_good=scoring_rate > 0.5,
    )
