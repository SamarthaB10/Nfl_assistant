"use client";

import Image from "next/image";
import { useId, useState } from "react";

import { selectFeaturedPlayers } from "@/lib/featured-players";
import type { GameSummary, PlayerSpotlight } from "@/lib/rankings";

interface GameCardProps {
  game: GameSummary;
  rank: number;
}

export function GameCard({ game, rank }: GameCardProps) {
  const [open, setOpen] = useState(false);
  const detailsId = useId();
  const names = game.matchup.split(" vs ");
  const teams = Object.entries(game.records).map(([teamId, record], index) => ({
    id: teamId,
    logoUrl: game.logos[teamId],
    name: names[index] ?? teamId,
    record,
  }));
  const headline = game.reasons.find((reason) => reason.startsWith("Headline:"));
  const reasons = game.reasons.filter((reason) => !reason.startsWith("Headline:"));
  const players: PlayerSpotlight[] =
    game.playersToWatch && game.playersToWatch.length > 0
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
          {teams.map((team) => (
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
                <strong>{team.name}</strong>
                <span>
                  {team.id} · {team.record}
                </span>
              </span>
            </span>
          ))}
        </span>

        <span className="rating-block">
          <span>Watch rating</span>
          <strong>{game.score.toFixed(2)}</strong>
          <span>out of 10</span>
          <progress
            aria-label={`${game.matchup} watchability score`}
            max={10}
            value={game.score}
          >
            {game.score} out of 10
          </progress>
        </span>

        <span className="expand-mark" aria-hidden="true">
          {open ? "−" : "+"}
        </span>
      </button>

      {open && (
        <div className="game-details" id={detailsId}>
          <div className="insight-copy">
            <p className="detail-label">Why it ranks here</p>
            <h3>{game.matchup}</h3>
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
          </div>

          {players.length > 0 && (
            <div className="players">
              <p className="detail-label">Players to watch</p>
              <div className="player-grid">
                {players.map((player) => (
                  <a
                    className="player"
                    href={player.profileUrl}
                    key={player.teamId}
                    rel="noreferrer"
                    target="_blank"
                  >
                    <Image
                      alt={player.name}
                      height={220}
                      loading="eager"
                      src={player.imageUrl}
                      width={220}
                    />
                    <span>
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
        </div>
      )}
    </li>
  );
}
