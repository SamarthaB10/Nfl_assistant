"use client";

import Image from "next/image";
import { useId, useState } from "react";

import { GameComments } from "@/components/game-comments";
import {
  selectFeaturedPlayers,
  selectStartingQuarterbacks,
} from "@/lib/featured-players";
import type { GameSummary, PlayerSpotlight } from "@/lib/rankings";

interface GameCardProps {
  game: GameSummary;
  gameKey: string;
  rank: number;
}

function formatKickoff(kickoff?: string): string {
  if (!kickoff) return "Time TBD";
  return new Intl.DateTimeFormat(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZoneName: "short",
  }).format(new Date(kickoff));
}

export function GameCard({ game, gameKey, rank }: GameCardProps) {
  const [open, setOpen] = useState(false);
  const detailsId = useId();
  const names = game.matchup.split(" vs ");
  const teams = Object.entries(game.records).map(([teamId, record], index) => ({
    id: teamId,
    logoUrl: game.logos[teamId],
    name: names[index] ?? teamId,
    record,
  }));
  const finalScores = game.finalScores ?? {};
  const hasFinalScores =
    teams.length === 2 &&
    teams.every((team) => Number.isInteger(finalScores[team.id]));
  const winningScore =
    hasFinalScores && finalScores[teams[0].id] !== finalScores[teams[1].id]
      ? Math.max(finalScores[teams[0].id], finalScores[teams[1].id])
      : null;
  const isSchedule = typeof game.score !== "number";
  const kickoff = formatKickoff(game.kickoff);
  const headline = game.reasons?.find((reason) =>
    reason.startsWith("Headline:"),
  );
  const reasons =
    game.reasons?.filter((reason) => !reason.startsWith("Headline:")) ?? [];
  let ratingClass = "";
  if (game.score !== undefined && game.score >= 7) {
    ratingClass = " is-high-rating";
  } else if (game.score !== undefined && game.score >= 5.5) {
    ratingClass = " is-mid-rating";
  }
  const players: PlayerSpotlight[] =
    isSchedule
      ? selectStartingQuarterbacks(teams.map((team) => team.id)).map((player) => ({
          playerId: player.id,
          teamId: player.teamId,
          name: player.name,
          position: player.position,
          imageUrl: player.imageUrl,
          profileUrl: player.profileUrl,
          details: [],
        }))
      : game.playersToWatch && game.playersToWatch.length > 0
        ? game.playersToWatch
        : selectFeaturedPlayers(
            teams.map((team) => team.id),
            game.unavailablePlayerIds,
          ).map((player) => ({
            playerId: player.id,
            teamId: player.teamId,
            name: player.name,
            position: player.position,
            imageUrl: player.imageUrl,
            profileUrl: player.profileUrl,
            details: [],
          }));

  return (
    <li className={`game-card${open ? " is-open" : ""}`}>
      <button
        aria-controls={detailsId}
        aria-expanded={open}
        aria-label={`${open ? "Hide" : "View"} details for ${game.matchup}`}
        className="game-summary"
        onClick={() => setOpen((current) => !current)}
        type="button"
      >
        <span className="sr-only">{game.matchup}</span>
        <span className="game-rank" aria-hidden="true">
          {String(rank).padStart(2, "0")}
        </span>

        <span className="team-stack">
          {teams.map((team) => {
            const finalScore = hasFinalScores ? finalScores[team.id] : null;
            const isWinner =
              finalScore !== null &&
              winningScore !== null &&
              finalScore === winningScore;

            return (
              <span className="team-line" key={team.id}>
                <span className="team-logo">
                  {team.logoUrl ? (
                    <Image
                      alt={`${team.id} logo`}
                      height={56}
                      src={team.logoUrl}
                      width={56}
                    />
                  ) : (
                    <span aria-hidden="true">{team.id}</span>
                  )}
                </span>
                <span className="team-copy">
                  <span className="team-name-line">
                    <strong>{team.name}</strong>
                    {finalScore !== null && (
                      <span
                        aria-label={`${team.name} final score ${finalScore}${
                          isWinner ? ", winner" : ""
                        }`}
                        className={`team-final-score${
                          isWinner ? " is-winner" : ""
                        }`}
                      >
                        – {finalScore}
                      </span>
                    )}
                  </span>
                  <span className="team-record">
                    {team.id} · {team.record}
                  </span>
                </span>
              </span>
            );
          })}
        </span>

        {isSchedule ? (
          <span className="rating-block is-scheduled">
            <span>Schedule</span>
            <strong>—</strong>
            <span>{kickoff}</span>
          </span>
        ) : (
          <span className={`rating-block${ratingClass}`}>
            <span>Watch rating</span>
            <strong>{game.score?.toFixed(2)}</strong>
            <span>out of 10</span>
            <progress
              aria-label={`${game.matchup} watchability score`}
              max={10}
              value={game.score}
            >
              {game.score} out of 10
            </progress>
          </span>
        )}

        <span className="expand-mark" aria-hidden="true">
          {open ? "−" : "+"}
        </span>
      </button>

      {open && (
        <div className="game-details" id={detailsId}>
          <div className="insight-copy">
            <p className="detail-label">
              {isSchedule ? "Game details" : "Why it ranks here"}
            </p>
            <h3>{game.matchup}</h3>
            {isSchedule ? (
              <p className="schedule-details">{kickoff}</p>
            ) : (
              <>
                <ul className="reason-list">
                  {reasons.map((reason) => (
                    <li key={reason}>{reason}</li>
                  ))}
                </ul>

                {headline && (
                  <blockquote className="headline">
                    <span>Pregame headline</span>
                    <p>{headline.replace("Headline:", "").trim()}</p>
                  </blockquote>
                )}
              </>
            )}
          </div>

          {players.length > 0 && (
            <div className="players">
              <p className="detail-label">
                {isSchedule ? "Starting quarterbacks" : "Players to watch"}
              </p>
              <div className="player-grid">
                {players.map((player) => (
                  <a
                    className="player"
                    href={player.profileUrl}
                    key={player.teamId}
                    rel="noreferrer"
                    target="_blank"
                  >
                    <span className="player-portrait">
                      <Image
                        alt={player.name}
                        height={220}
                        loading="eager"
                        src={player.imageUrl}
                        width={220}
                      />
                    </span>
                    <span className="player-copy">
                      <strong>{player.name}</strong>
                      <small>
                        {player.teamId} · {player.position}
                      </small>
                      {player.details.length > 0 && (
                        <ul className="player-facts">
                          {player.details.map((detail) => (
                            <li key={detail}>{detail}</li>
                          ))}
                        </ul>
                      )}
                    </span>
                  </a>
                ))}
              </div>
            </div>
          )}

          <GameComments gameKey={gameKey} />
        </div>
      )}
    </li>
  );
}
