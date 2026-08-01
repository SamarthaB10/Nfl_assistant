export interface FeaturedPlayer {
  id: string;
  name: string;
  position: string;
  imageUrl: string;
  profileUrl: string;
}

export interface SelectedFeaturedPlayer extends FeaturedPlayer {
  teamId: string;
}

export const NFL_TEAM_IDS = [
  "ARI",
  "ATL",
  "BAL",
  "BUF",
  "CAR",
  "CHI",
  "CIN",
  "CLE",
  "DAL",
  "DEN",
  "DET",
  "GB",
  "HOU",
  "IND",
  "JAX",
  "KC",
  "LAC",
  "LAR",
  "LV",
  "MIA",
  "MIN",
  "NE",
  "NO",
  "NYG",
  "NYJ",
  "PHI",
  "PIT",
  "SEA",
  "SF",
  "TB",
  "TEN",
  "WAS",
] as const;

type NflTeamId = (typeof NFL_TEAM_IDS)[number];

function featuredPlayer(
  id: string,
  name: string,
  position: string,
  slug: string,
): FeaturedPlayer {
  return {
    id,
    name,
    position,
    imageUrl: `https://a.espncdn.com/i/headshots/nfl/players/full/${id}.png`,
    profileUrl: `https://www.espn.com/nfl/player/_/id/${id}/${slug}`,
  };
}

const COMPLETE_PLAYER_CANDIDATES = {
  ARI: [featuredPlayer("4361307", "Trey McBride", "TE", "trey-mcbride")],
  ATL: [featuredPlayer("4430807", "Bijan Robinson", "RB", "bijan-robinson")],
  BAL: [featuredPlayer("3916387", "Lamar Jackson", "QB", "lamar-jackson")],
  BUF: [featuredPlayer("3918298", "Josh Allen", "QB", "josh-allen")],
  CAR: [featuredPlayer("4685720", "Bryce Young", "QB", "bryce-young")],
  CHI: [featuredPlayer("4431611", "Caleb Williams", "QB", "caleb-williams")],
  CIN: [featuredPlayer("3915511", "Joe Burrow", "QB", "joe-burrow")],
  CLE: [featuredPlayer("3122132", "Myles Garrett", "DE", "myles-garrett")],
  DAL: [featuredPlayer("4241389", "CeeDee Lamb", "WR", "ceedee-lamb")],
  DEN: [featuredPlayer("4426338", "Bo Nix", "QB", "bo-nix")],
  DET: [
    featuredPlayer("4374302", "Amon-Ra St. Brown", "WR", "amon-ra-st-brown"),
  ],
  GB: [featuredPlayer("4036378", "Jordan Love", "QB", "jordan-love")],
  HOU: [featuredPlayer("4432577", "C.J. Stroud", "QB", "cj-stroud")],
  IND: [featuredPlayer("4242335", "Jonathan Taylor", "RB", "jonathan-taylor")],
  JAX: [featuredPlayer("4360310", "Trevor Lawrence", "QB", "trevor-lawrence")],
  KC: [featuredPlayer("3139477", "Patrick Mahomes", "QB", "patrick-mahomes")],
  LAC: [featuredPlayer("4038941", "Justin Herbert", "QB", "justin-herbert")],
  LAR: [featuredPlayer("4426515", "Puka Nacua", "WR", "puka-nacua")],
  LV: [featuredPlayer("4432665", "Brock Bowers", "TE", "brock-bowers")],
  MIA: [featuredPlayer("4241479", "Tua Tagovailoa", "QB", "tua-tagovailoa")],
  MIN: [featuredPlayer("4262921", "Justin Jefferson", "WR", "justin-jefferson")],
  NE: [featuredPlayer("4431452", "Drake Maye", "QB", "drake-maye")],
  NO: [featuredPlayer("3054850", "Alvin Kamara", "RB", "alvin-kamara")],
  NYG: [
    featuredPlayer("4595348", "Malik Nabers", "WR", "malik-nabers"),
    featuredPlayer("4689114", "Jaxson Dart", "QB", "jaxson-dart"),
  ],
  NYJ: [featuredPlayer("4569618", "Garrett Wilson", "WR", "garrett-wilson")],
  PHI: [featuredPlayer("4040715", "Jalen Hurts", "QB", "jalen-hurts")],
  PIT: [featuredPlayer("3045282", "T.J. Watt", "LB", "tj-watt")],
  SEA: [
    featuredPlayer(
      "4430878",
      "Jaxon Smith-Njigba",
      "WR",
      "jaxon-smith-njigba",
    ),
  ],
  SF: [
    featuredPlayer(
      "3117251",
      "Christian McCaffrey",
      "RB",
      "christian-mccaffrey",
    ),
  ],
  TB: [featuredPlayer("3052587", "Baker Mayfield", "QB", "baker-mayfield")],
  TEN: [featuredPlayer("4688380", "Cam Ward", "QB", "cam-ward")],
  WAS: [featuredPlayer("4426348", "Jayden Daniels", "QB", "jayden-daniels")],
} satisfies Record<NflTeamId, readonly FeaturedPlayer[]>;

const STARTING_QUARTERBACKS = {
  ARI: featuredPlayer("2578570", "Jacoby Brissett", "QB", "jacoby-brissett"),
  ATL: featuredPlayer("4241479", "Tua Tagovailoa", "QB", "tua-tagovailoa"),
  BAL: featuredPlayer("3916387", "Lamar Jackson", "QB", "lamar-jackson"),
  BUF: featuredPlayer("3918298", "Josh Allen", "QB", "josh-allen"),
  CAR: featuredPlayer("4685720", "Bryce Young", "QB", "bryce-young"),
  CHI: featuredPlayer("4431611", "Caleb Williams", "QB", "caleb-williams"),
  CIN: featuredPlayer("3915511", "Joe Burrow", "QB", "joe-burrow"),
  CLE: featuredPlayer("3122840", "Deshaun Watson", "QB", "deshaun-watson"),
  DAL: featuredPlayer("2577417", "Dak Prescott", "QB", "dak-prescott"),
  DEN: featuredPlayer("4426338", "Bo Nix", "QB", "bo-nix"),
  DET: featuredPlayer("3046779", "Jared Goff", "QB", "jared-goff"),
  GB: featuredPlayer("4036378", "Jordan Love", "QB", "jordan-love"),
  HOU: featuredPlayer("4432577", "C.J. Stroud", "QB", "cj-stroud"),
  IND: featuredPlayer("3917792", "Daniel Jones", "QB", "daniel-jones"),
  JAX: featuredPlayer("4360310", "Trevor Lawrence", "QB", "trevor-lawrence"),
  KC: featuredPlayer("3139477", "Patrick Mahomes", "QB", "patrick-mahomes"),
  LAC: featuredPlayer("4038941", "Justin Herbert", "QB", "justin-herbert"),
  LAR: featuredPlayer("12483", "Matthew Stafford", "QB", "matthew-stafford"),
  LV: featuredPlayer("14880", "Kirk Cousins", "QB", "kirk-cousins"),
  MIA: featuredPlayer("4242512", "Malik Willis", "QB", "malik-willis"),
  MIN: featuredPlayer("3917315", "Kyler Murray", "QB", "kyler-murray"),
  NE: featuredPlayer("4431452", "Drake Maye", "QB", "drake-maye"),
  NO: featuredPlayer("4360689", "Tyler Shough", "QB", "tyler-shough"),
  NYG: featuredPlayer("4689114", "Jaxson Dart", "QB", "jaxson-dart"),
  NYJ: featuredPlayer("15864", "Geno Smith", "QB", "geno-smith"),
  PHI: featuredPlayer("4040715", "Jalen Hurts", "QB", "jalen-hurts"),
  PIT: featuredPlayer("8439", "Aaron Rodgers", "QB", "aaron-rodgers"),
  SEA: featuredPlayer("3912547", "Sam Darnold", "QB", "sam-darnold"),
  SF: featuredPlayer("4361741", "Brock Purdy", "QB", "brock-purdy"),
  TB: featuredPlayer("3052587", "Baker Mayfield", "QB", "baker-mayfield"),
  TEN: featuredPlayer("4688380", "Cam Ward", "QB", "cam-ward"),
  WAS: featuredPlayer("4426348", "Jayden Daniels", "QB", "jayden-daniels"),
} satisfies Record<NflTeamId, FeaturedPlayer>;

export const FEATURED_PLAYER_CANDIDATES: Readonly<
  Record<string, readonly FeaturedPlayer[]>
> = COMPLETE_PLAYER_CANDIDATES;

export function selectStartingQuarterbacks(
  teamIds: readonly string[],
): SelectedFeaturedPlayer[] {
  return teamIds.flatMap((teamId) => {
    const player = STARTING_QUARTERBACKS[teamId as NflTeamId];
    return player ? [{ ...player, teamId }] : [];
  });
}

export function selectFeaturedPlayers(
  teamIds: readonly string[],
  unavailablePlayerIds: readonly string[] = [],
): SelectedFeaturedPlayer[] {
  const unavailableIds = new Set(unavailablePlayerIds);

  return teamIds.flatMap((teamId) => {
    const player = FEATURED_PLAYER_CANDIDATES[teamId]?.find(
      (candidate) => !unavailableIds.has(candidate.id),
    );
    return player ? [{ ...player, teamId }] : [];
  });
}
