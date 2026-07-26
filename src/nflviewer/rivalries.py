import json
from functools import lru_cache
from pathlib import Path
from typing import Final

from nflviewer.models import RivalryCategory

DIVISIONAL: Final = "DIVISIONAL"
CONFERENCE_OR_INTERCONFERENCE: Final = "CONFERENCE_OR_INTERCONFERENCE"
HISTORIC_OR_REGIONAL: Final = "HISTORIC_OR_REGIONAL"

RIVALRY_VALUES: Final[dict[RivalryCategory, float]] = {
    DIVISIONAL: 0.20,
    CONFERENCE_OR_INTERCONFERENCE: 0.12,
    HISTORIC_OR_REGIONAL: 0.06,
}

DEFAULT_RIVALRIES_PATH = Path(__file__).resolve().parents[2] / "data" / "rivalries.json"


def canonical_pair(team_a: str, team_b: str) -> str:
    return "-".join(sorted((team_a.upper(), team_b.upper())))


@lru_cache
def load_rivalries(path: Path = DEFAULT_RIVALRIES_PATH) -> dict[str, RivalryCategory]:
    with path.open(encoding="utf-8") as rivalry_file:
        raw_rivalries = json.load(rivalry_file)

    rivalries: dict[str, RivalryCategory] = {}
    for category, pairs in raw_rivalries.items():
        if category not in RIVALRY_VALUES:
            raise ValueError(f"Unsupported rivalry category: {category}")
        for pair in pairs:
            team_a, team_b = pair.split("-")
            key = canonical_pair(team_a, team_b)
            if key in rivalries:
                raise ValueError(f"Duplicate rivalry pair: {key}")
            rivalries[key] = category
    return rivalries


def classify_rivalry(
    home_team_id: str,
    away_team_id: str,
    *,
    is_divisional: bool,
) -> tuple[RivalryCategory | None, float]:
    if is_divisional:
        return DIVISIONAL, RIVALRY_VALUES[DIVISIONAL]

    category = load_rivalries().get(canonical_pair(home_team_id, away_team_id))
    if category is None:
        return None, 0.0
    return category, RIVALRY_VALUES[category]
