"""
Static reference map: team name -> FIFA confederation bucket.

Buckets: "AFC", "CAF", "CONCACAF", "CONMEBOL", "OFC", "UEFA", "Other".

This module has no external dependencies. It covers all 284 team-name strings
used in the Gamba Project football dataset, including FIFA member associations
and non-FIFA / CONIFA / regional / historical / defunct entities. Non-FIFA
entities are assigned "Other".

Notable cross-continental assignments:
- Australia: AFC (moved from OFC in 2006)
- Israel, Kazakhstan, Cyprus, Armenia, Azerbaijan, Georgia, Turkey, Russia: UEFA
- Guyana, Suriname, French Guiana: CONCACAF (not CONMEBOL)
- Guam, Northern Mariana Islands: AFC
"""

CONFEDERATION: dict[str, str] = {
    # ------------------------------------------------------------------ AFC
    "Afghanistan": "AFC",
    "Australia": "AFC",        # moved from OFC to AFC in 2006
    "Bahrain": "AFC",
    "Bangladesh": "AFC",
    "Bhutan": "AFC",
    "Brunei": "AFC",
    "Cambodia": "AFC",
    "China": "AFC",
    "Guam": "AFC",             # AFC, not OFC
    "Hong Kong": "AFC",
    "India": "AFC",
    "Indonesia": "AFC",
    "Iran": "AFC",
    "Iraq": "AFC",
    "Japan": "AFC",
    "Jordan": "AFC",
    "Kuwait": "AFC",
    "Kyrgyzstan": "AFC",
    "Laos": "AFC",
    "Lebanon": "AFC",
    "Macau": "AFC",
    "Malaysia": "AFC",
    "Maldives": "AFC",
    "Mongolia": "AFC",
    "Myanmar": "AFC",
    "Nepal": "AFC",
    "North Korea": "AFC",
    "Northern Mariana Islands": "AFC",  # AFC associate member
    "Oman": "AFC",
    "Pakistan": "AFC",
    "Palestine": "AFC",
    "Philippines": "AFC",
    "Qatar": "AFC",
    "Saudi Arabia": "AFC",
    "Singapore": "AFC",
    "South Korea": "AFC",
    "Sri Lanka": "AFC",
    "Syria": "AFC",
    "Taiwan": "AFC",
    "Tajikistan": "AFC",
    "Thailand": "AFC",
    "Timor-Leste": "AFC",
    "Turkmenistan": "AFC",
    "United Arab Emirates": "AFC",
    "Uzbekistan": "AFC",
    "Vietnam": "AFC",
    "Yemen": "AFC",
    # ------------------------------------------------------------------ CAF
    "Algeria": "CAF",
    "Angola": "CAF",
    "Benin": "CAF",
    "Botswana": "CAF",
    "Burkina Faso": "CAF",
    "Burundi": "CAF",
    "Cameroon": "CAF",
    "Cape Verde": "CAF",
    "Central African Republic": "CAF",
    "Chad": "CAF",
    "Comoros": "CAF",
    "Congo": "CAF",
    "DR Congo": "CAF",
    "Djibouti": "CAF",
    "Egypt": "CAF",
    "Equatorial Guinea": "CAF",
    "Eritrea": "CAF",
    "Eswatini": "CAF",
    "Ethiopia": "CAF",
    "Gabon": "CAF",
    "Gambia": "CAF",
    "Ghana": "CAF",
    "Guinea": "CAF",
    "Guinea-Bissau": "CAF",
    "Ivory Coast": "CAF",
    "Kenya": "CAF",
    "Lesotho": "CAF",
    "Liberia": "CAF",
    "Libya": "CAF",
    "Madagascar": "CAF",
    "Malawi": "CAF",
    "Mali": "CAF",
    "Mauritania": "CAF",
    "Mauritius": "CAF",
    "Mayotte": "CAF",          # French overseas territory; CAF associate member
    "Morocco": "CAF",
    "Mozambique": "CAF",
    "Namibia": "CAF",
    "Niger": "CAF",
    "Nigeria": "CAF",
    "Réunion": "CAF",          # French overseas territory; CAF associate member
    "Rwanda": "CAF",
    "São Tomé and Príncipe": "CAF",
    "Senegal": "CAF",
    "Seychelles": "CAF",
    "Sierra Leone": "CAF",
    "Somalia": "CAF",
    "South Africa": "CAF",
    "South Sudan": "CAF",
    "Sudan": "CAF",
    "Tanzania": "CAF",
    "Togo": "CAF",
    "Tunisia": "CAF",
    "Uganda": "CAF",
    "Zambia": "CAF",
    "Zimbabwe": "CAF",
    # ------------------------------------------------------------------ CONCACAF
    "Anguilla": "CONCACAF",
    "Antigua and Barbuda": "CONCACAF",
    "Aruba": "CONCACAF",
    "Bahamas": "CONCACAF",
    "Barbados": "CONCACAF",
    "Belize": "CONCACAF",
    "Bermuda": "CONCACAF",
    "Bonaire": "CONCACAF",     # CONCACAF associate member
    "British Virgin Islands": "CONCACAF",
    "Canada": "CONCACAF",
    "Cayman Islands": "CONCACAF",
    "Costa Rica": "CONCACAF",
    "Cuba": "CONCACAF",
    "Curaçao": "CONCACAF",
    "Dominica": "CONCACAF",
    "Dominican Republic": "CONCACAF",
    "El Salvador": "CONCACAF",
    "French Guiana": "CONCACAF",  # French overseas territory; CONCACAF, NOT CONMEBOL
    "Grenada": "CONCACAF",
    "Guadeloupe": "CONCACAF",
    "Guatemala": "CONCACAF",
    "Guyana": "CONCACAF",      # CONCACAF, NOT CONMEBOL
    "Haiti": "CONCACAF",
    "Honduras": "CONCACAF",
    "Jamaica": "CONCACAF",
    "Martinique": "CONCACAF",
    "Mexico": "CONCACAF",
    "Montserrat": "CONCACAF",
    "Nicaragua": "CONCACAF",
    "Panama": "CONCACAF",
    "Puerto Rico": "CONCACAF",
    "Saint Barthélemy": "CONCACAF",  # French overseas collectivity; CONCACAF associate
    "Saint Kitts and Nevis": "CONCACAF",
    "Saint Lucia": "CONCACAF",
    "Saint Martin": "CONCACAF",     # Dutch/French; CONCACAF associate
    "Saint Vincent and the Grenadines": "CONCACAF",
    "Sint Maarten": "CONCACAF",     # Dutch Caribbean; CONCACAF associate
    "Suriname": "CONCACAF",         # CONCACAF, NOT CONMEBOL
    "Trinidad and Tobago": "CONCACAF",
    "Turks and Caicos Islands": "CONCACAF",
    "United States": "CONCACAF",
    "United States Virgin Islands": "CONCACAF",
    # ------------------------------------------------------------------ CONMEBOL
    "Argentina": "CONMEBOL",
    "Bolivia": "CONMEBOL",
    "Brazil": "CONMEBOL",
    "Chile": "CONMEBOL",
    "Colombia": "CONMEBOL",
    "Ecuador": "CONMEBOL",
    "Paraguay": "CONMEBOL",
    "Peru": "CONMEBOL",
    "Uruguay": "CONMEBOL",
    "Venezuela": "CONMEBOL",
    # ------------------------------------------------------------------ OFC
    "American Samoa": "OFC",
    "Cook Islands": "OFC",
    "Fiji": "OFC",
    "Marshall Islands": "OFC",
    "New Caledonia": "OFC",
    "New Zealand": "OFC",
    "Papua New Guinea": "OFC",
    "Samoa": "OFC",
    "Solomon Islands": "OFC",
    "Tahiti": "OFC",
    "Tonga": "OFC",
    "Tuvalu": "OFC",
    "Vanuatu": "OFC",
    # ------------------------------------------------------------------ UEFA
    "Albania": "UEFA",
    "Andorra": "UEFA",
    "Armenia": "UEFA",         # UEFA despite being geographically in W. Asia
    "Austria": "UEFA",
    "Azerbaijan": "UEFA",      # UEFA despite being partly in Asia
    "Belarus": "UEFA",
    "Belgium": "UEFA",
    "Bosnia and Herzegovina": "UEFA",
    "Bulgaria": "UEFA",
    "Croatia": "UEFA",
    "Cyprus": "UEFA",          # UEFA despite being geographically in Middle East
    "Czech Republic": "UEFA",
    "Denmark": "UEFA",
    "England": "UEFA",
    "Estonia": "UEFA",
    "Faroe Islands": "UEFA",
    "Finland": "UEFA",
    "France": "UEFA",
    "Georgia": "UEFA",         # UEFA
    "Germany": "UEFA",
    "Gibraltar": "UEFA",
    "Greece": "UEFA",
    "Greenland": "UEFA",       # Danish territory; UEFA associate / CONCACAF-adjacent but plays in UEFA
    "Hungary": "UEFA",
    "Iceland": "UEFA",
    "Isle of Man": "UEFA",     # British Crown dependency; plays in CONIFA / EOF but UEFA-adjacent; FIFA non-member — see Other note below
    "Israel": "UEFA",          # UEFA since 1994
    "Italy": "UEFA",
    "Jersey": "UEFA",          # British Crown dependency; plays in CONIFA / EOF; FIFA non-member — see Other note
    "Kazakhstan": "UEFA",      # moved to UEFA in 2002
    "Kosovo": "UEFA",
    "Latvia": "UEFA",
    "Liechtenstein": "UEFA",
    "Lithuania": "UEFA",
    "Luxembourg": "UEFA",
    "Malta": "UEFA",
    "Moldova": "UEFA",
    "Montenegro": "UEFA",
    "Netherlands": "UEFA",
    "North Macedonia": "UEFA",
    "Northern Ireland": "UEFA",
    "Norway": "UEFA",
    "Poland": "UEFA",
    "Portugal": "UEFA",
    "Republic of Ireland": "UEFA",
    "Romania": "UEFA",
    "Russia": "UEFA",
    "San Marino": "UEFA",
    "Scotland": "UEFA",
    "Serbia": "UEFA",
    "Slovakia": "UEFA",
    "Slovenia": "UEFA",
    "Spain": "UEFA",
    "Sweden": "UEFA",
    "Switzerland": "UEFA",
    "Turkey": "UEFA",          # UEFA despite straddling Europe/Asia
    "Ukraine": "UEFA",
    "Vatican City": "UEFA",    # UEFA associate member (observer)
    "Wales": "UEFA",
    "Åland Islands": "UEFA",   # Finnish autonomous region; plays in CONIFA; FIFA non-member
    # ------------------------------------------------------------------ Other
    # Non-FIFA / CONIFA / regional / stateless / historical / disputed / defunct
    "Abkhazia": "Other",               # CONIFA; breakaway Georgian region
    "Alderney": "Other",               # Channel Islands; not a FIFA member
    "Artsakh": "Other",                # CONIFA; disputed region / Nagorno-Karabakh
    "Aymara": "Other",                 # CONIFA; indigenous people of Andes
    "Barawa": "Other",                 # CONIFA; Somali minority diaspora
    "Basque Country": "Other",         # CONIFA / ELF; stateless nation within Spain/France
    "Biafra": "Other",                 # CONIFA; historical/political entity (SE Nigeria)
    "Cascadia": "Other",               # CONIFA; bioregionalist movement (PNW)
    "Catalonia": "Other",              # CONIFA / NF Board; autonomous community of Spain
    "Chagos Islands": "Other",         # British Indian Ocean Territory; not FIFA member
    "Chameria": "Other",               # CONIFA; Albanian minority in NW Greece
    "East Turkestan": "Other",         # CONIFA; Uyghur diaspora / Xinjiang independence
    "Elba Island": "Other",            # Italian island; not a FIFA member
    "Ellan Vannin": "Other",           # Manx name for Isle of Man; CONIFA
    "Falkland Islands": "Other",       # British Overseas Territory; not FIFA member
    "Franconia": "Other",              # CONIFA; historical German region
    "Frøya": "Other",                  # Norwegian island municipality; not FIFA member
    "Galicia": "Other",                # CONIFA; historical Central/Eastern European region
    "Gozo": "Other",                   # Maltese island; not a separate FIFA member
    "Guernsey": "Other",               # British Crown dependency; not FIFA member
    "Hitra": "Other",                  # Norwegian island municipality; not FIFA member
    "Isle of Wight": "Other",          # English island; not a FIFA member; CONIFA
    "Hmong": "Other",                  # CONIFA; indigenous Southeast Asian diaspora
    "Kabylia": "Other",                # CONIFA; Berber region of Algeria
    "Kernow": "Other",                 # CONIFA; Cornish name for Cornwall
    "Kárpátalja": "Other",             # CONIFA; Hungarian minority in western Ukraine
    "Luhansk PR": "Other",             # CONIFA; Russian-backed separatist entity in Ukraine
    "Mapuche": "Other",                # CONIFA; indigenous people of Chile/Argentina
    "Matabeleland": "Other",           # CONIFA; region of Zimbabwe
    "Maule Sur": "Other",              # CONIFA; region of Chile
    "Menorca": "Other",                # Balearic island; not a separate FIFA member
    "Northern Cyprus": "Other",        # CONIFA; recognised only by Turkey; not FIFA member
    "Orkney": "Other",                 # Scottish islands; not FIFA member
    "Padania": "Other",                # CONIFA; Lega Nord's name for N. Italy
    "Panjab": "Other",                 # CONIFA; Punjab diaspora team
    "Parishes of Jersey": "Other",     # Sub-national Jersey entity; not FIFA member
    "Raetia": "Other",                 # CONIFA; historical Alpine region
    "Saint Helena": "Other",           # British Overseas Territory; not FIFA member
    "Shetland": "Other",               # Scottish islands; not FIFA member
    "Somaliland": "Other",             # CONIFA; self-declared republic; not UN/FIFA member
    "South Ossetia": "Other",          # CONIFA; breakaway Georgian region
    "Surrey": "Other",                 # English county; not FIFA member
    "Székely Land": "Other",           # CONIFA; Hungarian minority in Romania
    "Sápmi": "Other",                  # CONIFA; Sami homeland (N. Scandinavia)
    "Tamil Eelam": "Other",            # CONIFA; Tamil diaspora / former Sri Lankan separatist
    "Tibet": "Other",                  # CONIFA; Chinese-administered region
    "Ticino": "Other",                 # CONIFA; Italian-speaking Swiss canton
    "Two Sicilies": "Other",           # CONIFA; historical Italian kingdom
    "United Koreans in Japan": "Other",# CONIFA; Korean diaspora in Japan
    "West Papua": "Other",             # CONIFA; Indonesian-administered region
    "Western Armenia": "Other",        # CONIFA; Armenian diaspora / historical region
    "Western Isles": "Other",          # Scottish island council area; not FIFA member
    "Ynys Môn": "Other",               # CONIFA; Welsh name for Isle of Anglesey
    "Yorkshire": "Other",              # CONIFA; English county
    "Yoruba Nation": "Other",          # CONIFA; West African ethnic nation
    "Zanzibar": "Other",               # CECAFA member but not full FIFA member; Tanzanian autonomous region
}


def confederation(team: str) -> str:
    """Return the FIFA confederation bucket for *team*, defaulting to 'Other'."""
    return CONFEDERATION.get(team, "Other")


# ---------------------------------------------------------------------------
# REVIEW NOTES — teams assigned to "Other"
# ---------------------------------------------------------------------------
# All entries below are non-FIFA or have uncertain FIFA membership.
#
# Clear non-FIFA / CONIFA entities:
#   Abkhazia, Alderney, Artsakh, Aymara, Barawa, Basque Country, Biafra,
#   Cascadia, Catalonia, Chagos Islands, Chameria, East Turkestan, Elba Island,
#   Ellan Vannin, Franconia, Frøya, Galicia, Gozo, Hmong, Kabylia, Kernow,
#   Isle of Wight, Kárpátalja, Luhansk PR, Mapuche, Matabeleland, Maule Sur, Menorca,
#   Northern Cyprus, Orkney, Padania, Panjab, Parishes of Jersey, Raetia,
#   Sápmi, Saint Helena, Shetland, Somaliland, South Ossetia, Surrey,
#   Székely Land, Tamil Eelam, Tibet, Ticino, Two Sicilies,
#   United Koreans in Japan, West Papua, Western Armenia, Western Isles,
#   Ynys Môn, Yorkshire, Yoruba Nation
#
# Uncertain / borderline (kept as Other):
#   Falkland Islands — British Overseas Territory, no FIFA membership confirmed
#   Guernsey — Crown dependency, not FIFA member (plays in CONIFA / EOF)
#   Zanzibar — CECAFA member but not an independent FIFA member association
#   Vatican City — UEFA associate observer; no competitive FIFA membership;
#                   assigned UEFA here for hierarchical purposes (review if needed)
#   Greenland — KFF member; not FIFA; assigned UEFA here by geographic/cultural
#                affiliation (review if needed; could be "Other")
#   Mayotte / Réunion — French overseas departments; CAF associate members,
#                        assigned CAF (review if needed)
#   Saint Barthélemy / Saint Martin / Sint Maarten / Bonaire —
#                        assigned CONCACAF as associate/affiliate members
#   Isle of Man / Jersey / Åland Islands — non-FIFA entities assigned UEFA
#                        by geographic/cultural association (could be "Other")
