from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from nflviewer.data import Repository


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Cache normalized 2024–2025 nflverse data.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Download and replace the cache even when local Parquet files exist.",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path("data/processed"),
        help="Directory for normalized Parquet files (default: data/processed).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repository = Repository(args.cache_dir)
    data = repository.get(force_refresh=args.force)
    matchup_count = sum(len(data.matchups_for_week(week)) for week in range(1, 19))
    print(
        f"Cached {len(data.teams)} teams and {matchup_count} regular-season games "
        f"in {args.cache_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
