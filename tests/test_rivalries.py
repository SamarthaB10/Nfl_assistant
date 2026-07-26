from nflviewer.rivalries import (
    CONFERENCE_OR_INTERCONFERENCE,
    DIVISIONAL,
    HISTORIC_OR_REGIONAL,
    classify_rivalry,
    load_rivalries,
)


def test_rivalry_seed_contains_all_35_non_divisional_pairs() -> None:
    rivalries = load_rivalries()

    assert len(rivalries) == 35


def test_divisional_matchup_has_strongest_value() -> None:
    category, value = classify_rivalry("BUF", "NE", is_divisional=True)

    assert category == DIVISIONAL
    assert value == 0.20


def test_named_conference_rivalry_has_medium_value() -> None:
    category, value = classify_rivalry("KC", "BUF", is_divisional=False)

    assert category == CONFERENCE_OR_INTERCONFERENCE
    assert value == 0.12


def test_historic_or_regional_rivalry_has_small_value() -> None:
    category, value = classify_rivalry("NYJ", "NYG", is_divisional=False)

    assert category == HISTORIC_OR_REGIONAL
    assert value == 0.06


def test_divisional_value_wins_instead_of_stacking() -> None:
    category, value = classify_rivalry("NE", "BUF", is_divisional=True)

    assert category == DIVISIONAL
    assert value == 0.20


def test_unrelated_teams_have_no_rivalry_value() -> None:
    category, value = classify_rivalry("CAR", "LAC", is_divisional=False)

    assert category is None
    assert value == 0.0
