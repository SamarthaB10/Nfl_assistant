export interface FeaturedPlayer {
  name: string;
  position: string;
  imageUrl: string;
  profileUrl: string;
}

export const FEATURED_PLAYERS: Partial<Record<string, FeaturedPlayer>> = {
  SEA: {
    name: "Jaxon Smith-Njigba",
    position: "WR",
    imageUrl:
      "https://a.espncdn.com/i/headshots/nfl/players/full/4430878.png",
    profileUrl:
      "https://www.espn.com/nfl/player/_/id/4430878/jaxon-smith-njigba",
  },
  SF: {
    name: "Christian McCaffrey",
    position: "RB",
    imageUrl:
      "https://a.espncdn.com/i/headshots/nfl/players/full/3117251.png",
    profileUrl:
      "https://www.espn.com/nfl/player/_/id/3117251/christian-mccaffrey",
  },
  BAL: {
    name: "Lamar Jackson",
    position: "QB",
    imageUrl:
      "https://a.espncdn.com/i/headshots/nfl/players/full/3916387.png",
    profileUrl:
      "https://www.espn.com/nfl/player/_/id/3916387/lamar-jackson",
  },
  BUF: {
    name: "Josh Allen",
    position: "QB",
    imageUrl:
      "https://a.espncdn.com/i/headshots/nfl/players/full/3918298.png",
    profileUrl:
      "https://www.espn.com/nfl/player/_/id/3918298/josh-allen",
  },
  GB: {
    name: "Jordan Love",
    position: "QB",
    imageUrl:
      "https://a.espncdn.com/i/headshots/nfl/players/full/4036378.png",
    profileUrl:
      "https://www.espn.com/nfl/player/_/id/4036378/jordan-love",
  },
  MIN: {
    name: "Justin Jefferson",
    position: "WR",
    imageUrl:
      "https://a.espncdn.com/i/headshots/nfl/players/full/4262921.png",
    profileUrl:
      "https://www.espn.com/nfl/player/_/id/4262921/justin-jefferson",
  },
};
