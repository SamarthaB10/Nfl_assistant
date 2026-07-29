import { GameCard } from "@/components/game-card";
import {
  buildGameKey,
  type GameSummary,
  type RankingsRequest,
  type SelectionMode,
} from "@/lib/rankings";

interface GameListProps {
  games: GameSummary[];
  request: RankingsRequest;
}

function modeLabel(mode: SelectionMode, count: number): string {
  if (mode === "all") {
    return "All games";
  }
  return `${mode === "top" ? "Top" : "Bottom"} ${count}`;
}

export function GameList({ games, request }: GameListProps) {
  return (
    <section className="results" aria-labelledby="results-heading">
      <header className="results-header">
        <div>
          <p className="eyebrow">2025 regular season</p>
          <h2 id="results-heading">
            Week {request.week} · {modeLabel(request.mode, request.count)}
          </h2>
        </div>
        <p className="weight-legend">
          <span>Quality 55%</span>
          <span aria-hidden="true">·</span>
          Context 45%
        </p>
      </header>

      {games.length === 0 ? (
        <div className="empty-state" role="status">
          <strong>No matchups found.</strong>
          <span>Try another week or selection.</span>
        </div>
      ) : (
        <ol className="game-list">
          {games.map((game, index) => (
            <GameCard
              game={game}
              gameKey={buildGameKey(request.week, Object.keys(game.records))}
              key={game.matchup}
              rank={index + 1}
            />
          ))}
        </ol>
      )}
    </section>
  );
}
