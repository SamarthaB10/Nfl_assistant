import type { FormEvent } from "react";

import type { RankingsRequest, SelectionMode } from "@/lib/rankings";

interface RankingControlsProps {
  request: RankingsRequest;
  loading: boolean;
  onChange: (request: RankingsRequest) => void;
  onSubmit: () => void;
}

const MODES: Array<{ value: SelectionMode; label: string }> = [
  { value: "all", label: "All" },
  { value: "top", label: "Top" },
  { value: "bottom", label: "Bottom" },
];

export function RankingControls({
  request,
  loading,
  onChange,
  onSubmit,
}: RankingControlsProps) {
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit();
  }

  return (
    <form className="ranking-controls" onSubmit={submit}>
      <label className="control-field">
        <span>Week</span>
        <select
          aria-label="Week"
          value={request.week}
          onChange={(event) =>
            onChange({ ...request, week: Number(event.target.value) })
          }
        >
          {Array.from({ length: 18 }, (_, index) => index + 1).map((week) => (
            <option key={week} value={week}>
              {week}
            </option>
          ))}
        </select>
      </label>

      <fieldset className="mode-field">
        <legend>Show</legend>
        <div className="mode-switch">
          {MODES.map((mode) => (
            <button
              aria-pressed={request.mode === mode.value}
              key={mode.value}
              onClick={() => onChange({ ...request, mode: mode.value })}
              type="button"
            >
              {mode.label}
            </button>
          ))}
        </div>
      </fieldset>

      <label className="control-field count-field">
        <span>Number of games</span>
        <input
          aria-label="Number of games"
          disabled={request.mode === "all"}
          max={16}
          min={1}
          onChange={(event) =>
            onChange({ ...request, count: Number(event.target.value) })
          }
          type="number"
          value={request.count}
        />
      </label>

      <button className="rank-button" disabled={loading} type="submit">
        {loading ? "Ranking…" : "Rank matchups"}
      </button>
    </form>
  );
}
