import type { HeadlineSourceFilter } from "@/lib/headlines";

const TEAM_OPTIONS = [
  ["ARI", "Arizona Cardinals"],
  ["ATL", "Atlanta Falcons"],
  ["BAL", "Baltimore Ravens"],
  ["BUF", "Buffalo Bills"],
  ["CAR", "Carolina Panthers"],
  ["CHI", "Chicago Bears"],
  ["CIN", "Cincinnati Bengals"],
  ["CLE", "Cleveland Browns"],
  ["DAL", "Dallas Cowboys"],
  ["DEN", "Denver Broncos"],
  ["DET", "Detroit Lions"],
  ["GB", "Green Bay Packers"],
  ["HOU", "Houston Texans"],
  ["IND", "Indianapolis Colts"],
  ["JAX", "Jacksonville Jaguars"],
  ["KC", "Kansas City Chiefs"],
  ["LAC", "Los Angeles Chargers"],
  ["LAR", "Los Angeles Rams"],
  ["LV", "Las Vegas Raiders"],
  ["MIA", "Miami Dolphins"],
  ["MIN", "Minnesota Vikings"],
  ["NE", "New England Patriots"],
  ["NO", "New Orleans Saints"],
  ["NYG", "New York Giants"],
  ["NYJ", "New York Jets"],
  ["PHI", "Philadelphia Eagles"],
  ["PIT", "Pittsburgh Steelers"],
  ["SEA", "Seattle Seahawks"],
  ["SF", "San Francisco 49ers"],
  ["TB", "Tampa Bay Buccaneers"],
  ["TEN", "Tennessee Titans"],
  ["WAS", "Washington Commanders"],
] as const;

interface HeadlineFiltersProps {
  loading: boolean;
  onSourceChange: (source: HeadlineSourceFilter) => void;
  onSubmit: () => void;
  onTeamChange: (team: string) => void;
  source: HeadlineSourceFilter;
  team: string;
}

export function HeadlineFilters({
  loading,
  onSourceChange,
  onSubmit,
  onTeamChange,
  source,
  team,
}: HeadlineFiltersProps) {
  return (
    <form
      className="headline-filters"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit();
      }}
    >
      <label>
        <span>Publisher</span>
        <select
          aria-label="Publisher"
          onChange={(event) =>
            onSourceChange(event.target.value as HeadlineSourceFilter)
          }
          value={source}
        >
          <option value="ALL">All publishers</option>
          <option value="ESPN">ESPN</option>
          <option value="CBS">CBS Sports</option>
          <option value="FOX">FOX Sports</option>
        </select>
      </label>
      <label>
        <span>Team</span>
        <select
          aria-label="Team"
          onChange={(event) => onTeamChange(event.target.value)}
          value={team}
        >
          <option value="ALL">All NFL teams</option>
          {TEAM_OPTIONS.map(([code, name]) => (
            <option key={code} value={code}>
              {name}
            </option>
          ))}
        </select>
      </label>
      <button disabled={loading} type="submit">
        {loading ? "Updating…" : "Update feed"}
      </button>
    </form>
  );
}
