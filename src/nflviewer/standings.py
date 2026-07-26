from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from nflviewer.models import RecordSummary

REGULAR_SEASON_GAMES = 17
MAX_LEVERAGE = 0.82
PLAYOFF_TEAMS_PER_CONFERENCE = 7


class TeamLike(Protocol):
    conference: str
    division: str


class RecordLike(Protocol):
    wins: int
    losses: int
    ties: int


@dataclass(frozen=True, slots=True)
class TeamStanding:
    team_id: str
    conference: str
    division: str
    record: RecordSummary
    point_differential: int
    conference_rank: int
    division_rank: int

    @property
    def effective_wins(self) -> float:
        return self.record.wins + 0.5 * self.record.ties

    @property
    def games_played(self) -> int:
        return self.record.wins + self.record.losses + self.record.ties

    @property
    def win_rate(self) -> float:
        if self.games_played == 0:
            return 0.5
        return self.effective_wins / self.games_played


@dataclass(frozen=True, slots=True)
class LeverageResult:
    value: float
    reason: str | None


def build_standings(
    teams: Mapping[str, TeamLike],
    records: Mapping[str, RecordLike],
    point_differentials: Mapping[str, int],
) -> dict[str, TeamStanding]:
    conference_ranks: dict[str, int] = {}
    division_ranks: dict[str, int] = {}

    def sort_key(team_id: str) -> tuple[float, int, str]:
        record = records[team_id]
        games = record.wins + record.losses + record.ties
        rate = (record.wins + 0.5 * record.ties) / games if games else 0.5
        return (-rate, -point_differentials.get(team_id, 0), team_id)

    conferences = {team.conference for team in teams.values()}
    for conference in conferences:
        members = sorted(
            (team_id for team_id, team in teams.items() if team.conference == conference),
            key=sort_key,
        )
        conference_ranks.update(
            {team_id: rank for rank, team_id in enumerate(members, start=1)}
        )

    divisions = {team.division for team in teams.values()}
    for division in divisions:
        members = sorted(
            (team_id for team_id, team in teams.items() if team.division == division),
            key=sort_key,
        )
        division_ranks.update({team_id: rank for rank, team_id in enumerate(members, start=1)})

    return {
        team_id: TeamStanding(
            team_id=team_id,
            conference=team.conference,
            division=team.division,
            record=RecordSummary(
                wins=records[team_id].wins,
                losses=records[team_id].losses,
                ties=records[team_id].ties,
            ),
            point_differential=point_differentials.get(team_id, 0),
            conference_rank=conference_ranks[team_id],
            division_rank=division_ranks[team_id],
        )
        for team_id, team in teams.items()
    }


def _ranked_group(
    standings: Mapping[str, TeamStanding],
    *,
    conference: str | None = None,
    division: str | None = None,
) -> list[TeamStanding]:
    members = [
        standing
        for standing in standings.values()
        if (conference is None or standing.conference == conference)
        and (division is None or standing.division == division)
    ]
    rank_attribute = "division_rank" if division is not None else "conference_rank"
    return sorted(members, key=lambda standing: getattr(standing, rank_attribute))


def _boundary_team(
    team: TeamStanding,
    standings: Mapping[str, TeamStanding],
    objective: str,
) -> TeamStanding | None:
    if objective == "division":
        group = _ranked_group(standings, division=team.division)
        target_rank = 2 if team.division_rank == 1 else 1
    elif objective == "playoff":
        group = _ranked_group(standings, conference=team.conference)
        if len(group) <= PLAYOFF_TEAMS_PER_CONFERENCE:
            return None
        target_rank = 8 if team.conference_rank <= PLAYOFF_TEAMS_PER_CONFERENCE else 7
    else:
        group = _ranked_group(standings, conference=team.conference)
        target_rank = 2 if team.conference_rank == 1 else 1

    return next(
        (
            standing
            for standing in group
            if getattr(
                standing,
                "division_rank" if objective == "division" else "conference_rank",
            )
            == target_rank
        ),
        None,
    )


def _objective_impact(
    team: TeamStanding,
    opponent_id: str,
    boundary: TeamStanding | None,
) -> float:
    if boundary is None or boundary.team_id == team.team_id:
        return 0.0

    boundary_is_opponent = boundary.team_id == opponent_id
    margin_after_win = team.effective_wins + 1 - boundary.effective_wins
    margin_after_loss = team.effective_wins - (
        boundary.effective_wins + (1 if boundary_is_opponent else 0)
    )
    remaining_games = max(1, REGULAR_SEASON_GAMES - team.games_played)
    proximity = max(
        0.0,
        1 - min(abs(margin_after_win), abs(margin_after_loss)) / remaining_games,
    )
    crosses_boundary = (margin_after_win >= 0 > margin_after_loss) or (
        margin_after_loss >= 0 > margin_after_win
    )
    result_swing = abs(margin_after_win - margin_after_loss)
    consequence = 1.0 if crosses_boundary or result_swing >= 2 else 0.5
    return min(1.0, proximity * consequence)


def _team_objective(
    team_id: str,
    opponent_id: str,
    standings: Mapping[str, TeamStanding],
) -> tuple[float, str | None, str | None]:
    team = standings[team_id]
    best_value = 0.0
    best_objective: str | None = None
    best_boundary: str | None = None
    for objective in ("division", "playoff", "top_seed"):
        boundary = _boundary_team(team, standings, objective)
        value = _objective_impact(team, opponent_id, boundary)
        if value > best_value:
            best_value = value
            best_objective = objective
            best_boundary = boundary.team_id if boundary else None
    return best_value, best_objective, best_boundary


def matchup_leverage(
    home_team_id: str,
    away_team_id: str,
    *,
    week: int,
    standings: Mapping[str, TeamStanding],
) -> LeverageResult:
    if week <= 1 or home_team_id not in standings or away_team_id not in standings:
        return LeverageResult(value=0.0, reason=None)

    home_value, home_objective, home_boundary = _team_objective(
        home_team_id, away_team_id, standings
    )
    away_value, away_objective, away_boundary = _team_objective(
        away_team_id, home_team_id, standings
    )
    game_impact = 1 - (1 - home_value) * (1 - away_value)
    maturity = min(max((week - 1) / 17, 0.0), 1.0)
    value = MAX_LEVERAGE * maturity * game_impact

    objectives = {home_objective, away_objective}
    direct_division_race = (
        "division" in objectives
        and (home_boundary == away_team_id or away_boundary == home_team_id)
    )
    if direct_division_race:
        reason = "Direct division race matchup"
    elif "playoff" in objectives:
        reason = "Playoff cutoff implications"
    elif "top_seed" in objectives:
        reason = "Conference top-seed implications"
    elif "division" in objectives:
        reason = "Division race implications"
    else:
        reason = None
    return LeverageResult(value=value, reason=reason)
