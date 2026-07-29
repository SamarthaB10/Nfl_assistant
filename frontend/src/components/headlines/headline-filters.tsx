import type { HeadlineSourceFilter } from "@/lib/headlines";
import { NFL_TEAMS } from "@/lib/nfl-teams";

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
          {NFL_TEAMS.map((teamOption) => (
            <option key={teamOption.code} value={teamOption.code}>
              {teamOption.name}
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
