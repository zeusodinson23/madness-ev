"""
Team Name Normalization for MadnessEV

Single source of truth for all team name variations across the project.
Every data source spells team names differently:
  - The Odds API:  "Michigan Wolverines", "UConn Huskies"
  - CBBD API:      "Michigan", "UConn"
  - Barttorvik:    "Michigan", "Connecticut"
  - Kaggle:        "Michigan", "Connecticut"
  - User input:    "michigan", "uconn", "the wolverines"

This module normalizes ALL variations to CBBD's spelling,
which is our master reference throughout the project.

Usage:
    from src.team_names import normalize_team_name
    normalize_team_name("Michigan Wolverines")  →  "Michigan"
    normalize_team_name("uconn")               →  "UConn"
"""

# ============================================================
# NICKNAME SUFFIXES TO STRIP
# ============================================================
# The Odds API appends full mascot names to every team.
# We strip these first before doing any alias lookup.

NICKNAME_SUFFIXES = [
    # Big Ten
    "Wolverines", "Buckeyes", "Badgers", "Hawkeyes", "Gophers",
    "Hoosiers", "Boilermakers", "Spartans", "Fighting Illini",
    "Cornhuskers", "Terrapins", "Nittany Lions", "Wildcats",
    "Scarlet Knights",

    # ACC
    "Blue Devils", "Tar Heels", "Cavaliers", "Yellow Jackets",
    "Hokies", "Demon Deacons", "Orange", "Eagles", "Cardinals",
    "Hurricanes", "Panthers", "Seminoles",

    # Big 12
    "Longhorns", "Sooners", "Cyclones", "Red Raiders", "Bears",
    "Horned Frogs", "Cowboys", "Mountaineers", "Jayhawks",
    "Cougars", "Buffaloes", "Tigers",

    # SEC
    "Crimson Tide", "Bulldogs", "Volunteers", "Gators",
    "Gamecocks", "Razorbacks", "Aggies", "Rebels", "Tigers",
    "Golden Eagles", "Commodores", "Auburn Tigers",

    # Big East
    "Huskies", "Bluejays", "Blue Demons", "Golden Eagles",
    "Red Storm", "Friars", "Hoyas", "Musketeers", "Billikens",
    "Bulldogs",

    # Pac-12 / West Coast
    "Trojans", "Bruins", "Sun Devils", "Utes", "Ducks",
    "Beavers", "Cougars", "Huskies", "Bears", "Cardinal",
    "Bulldogs", "Zags",

    # Others
    "Runnin Rebels", "Wolf Pack", "Aztecs", "Lobos",
    "Cowboys", "Pirates", "Monarchs", "Phoenix", "Flyers",
    "Spiders", "Rams", "Owls", "Rockets", "Falcons",
    "Thunderbirds", "Bison", "Vikings", "Penguins",
    "Golden Hurricane", "Redbirds", "Scarlet Knights",
]

# ============================================================
# NAME ALIASES
# ============================================================
# Maps every known variation → CBBD's exact spelling
# Keys are lowercase for case-insensitive matching

NAME_ALIASES = {

    # --- UConn ---
    "uconn":                        "UConn",
    "connecticut":                  "UConn",
    "conn":                         "UConn",
    "uconn huskies":                "UConn",
    "connecticut huskies":          "UConn",
    "university of connecticut":    "UConn",

    # --- Iowa State ---
    "iowa st":                      "Iowa State",
    "iowa st.":                     "Iowa State",
    "isu":                          "Iowa State",
    "iowa state cyclones":          "Iowa State",

    # --- North Carolina ---
    "unc":                          "North Carolina",
    "tar heels":                    "North Carolina",
    "north carolina tar heels":     "North Carolina",

    # --- St. John's ---
    "st johns":                     "St. John's",
    "st. johns":                    "St. John's",
    "saint johns":                  "St. John's",
    "saint john's":                 "St. John's",
    "st. john's red storm":         "St. John's",

    # --- Michigan ---
    "michigan wolverines":          "Michigan",
    "umich":                        "Michigan",
    "u of m":                       "Michigan",

    # --- Michigan State ---
    "michigan st":                  "Michigan State",
    "michigan st spartans":         "Michigan State",
    "msu":                          "Michigan State",

    # --- Illinois ---
    "illinois fighting illini":     "Illinois",
    "illini":                       "Illinois",
    "u of i":                       "Illinois",

    # --- Arizona ---
    "arizona wildcats":             "Arizona",
    "zona":                         "Arizona",
    "u of a":                       "Arizona",

    # --- Duke ---
    "duke blue devils":             "Duke",

    # --- Auburn ---
    "auburn tigers":                "Auburn",

    # --- Houston ---
    "houston cougars":              "Houston",
    "uh":                           "Houston",

    # --- Florida ---
    "florida gators":               "Florida",
    "uf":                           "Florida",
    "gators":                       "Florida",

    # --- Tennessee ---
    "tennessee volunteers":         "Tennessee",
    "vols":                         "Tennessee",
    "ut":                           "Tennessee",

    # --- Alabama ---
    "alabama crimson tide":         "Alabama",
    "bama":                         "Alabama",
    "tide":                         "Alabama",

    # --- Kentucky ---
    "kentucky wildcats":            "Kentucky",
    "uk":                           "Kentucky",
    "cats":                         "Kentucky",

    # --- Purdue ---
    "purdue boilermakers":          "Purdue",
    "boilermakers":                 "Purdue",

    # --- Gonzaga ---
    "gonzaga bulldogs":             "Gonzaga",
    "zags":                         "Gonzaga",

    # --- Baylor ---
    "baylor bears":                 "Baylor",
    "bears":                        "Baylor",

    # --- Texas Tech ---
    "texas tech red raiders":       "Texas Tech",
    "ttu":                          "Texas Tech",
    "red raiders":                  "Texas Tech",

    # --- Marquette ---
    "marquette golden eagles":      "Marquette",
    "mu":                           "Marquette",

    # --- Creighton ---
    "creighton bluejays":           "Creighton",
    "bluejays":                     "Creighton",

    # --- North Carolina ---
    "north carolina tar heels":     "North Carolina",

    # --- Iowa ---
    "iowa hawkeyes":                "Iowa",

    # --- Abbreviations ---
    "lsu":                          "LSU",
    "usc":                          "Southern California",
    "ucla":                         "UCLA",
    "vcu":                          "Virginia Commonwealth",
    "smu":                          "Southern Methodist",
    "tcu":                          "TCU",
    "byu":                          "BYU",
    "unlv":                         "UNLV",
    "utep":                         "UTEP",
    "uab":                          "UAB",
    "ucf":                          "UCF",
    "fiu":                          "Florida International",
    "fau":                          "Florida Atlantic",
    "fgcu":                         "Florida Gulf Coast",
    "unf":                          "North Florida",

# --- CBBD spelling fixes ---
    "cal baptist":              "California Baptist",
    "long island":              "Long Island University",
    "miami fl":                 "Miami",
    "miami oh":                 "Miami (OH)",
    "miami ohio":               "Miami (OH)",
    "penn":                     "Pennsylvania",
    "prairie view am":          "Prairie View A&M",
    "prairie view a&m":         "Prairie View A&M",
    "queens":                   "Queens University",
    "southern methodist":       "SMU",
    "texas am":                 "Texas A&M",
    "texas a&m":                "Texas A&M",
    "virginia commonwealth":    "VCU",
    "hawaii":                   None,  # Not in CBBD — will use fallback



}


def normalize_team_name(name: str) -> str:
    """
    Normalizes any team name variation to CBBD's exact spelling.

    Two-step process:
    1. Strip nickname suffix ("Michigan Wolverines" → "Michigan")
    2. Check alias table ("uconn" → "UConn")

    If neither step finds a match, returns the cleaned input as-is.
    This means unknown teams pass through unchanged rather than crashing.

    Args:
        name: Any variation of a team name

    Returns:
        CBBD-standard team name
    """
    if not name:
        return name

    # Step 1 — strip nickname suffix
    # Try longest suffixes first to avoid partial matches
    cleaned = name.strip()
    suffixes_sorted = sorted(NICKNAME_SUFFIXES, key=len, reverse=True)

    for suffix in suffixes_sorted:
        if cleaned.lower().endswith(suffix.lower()):
            cleaned = cleaned[: -len(suffix)].strip()
            break

    # Step 2 — check alias table (case-insensitive)
    alias_result = NAME_ALIASES.get(cleaned.lower())
    if alias_result:
        return alias_result

    # Step 3 — return cleaned name as-is
    # Unknown team, but at least the suffix is stripped
    return cleaned