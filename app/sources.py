"""Downloads conflict and military data: UCDP/PRIO armed conflicts, Wikidata
(disputed territories, armed forces, special forces, equipment) and World Bank
military indicators."""
import csv
import datetime
import io
import json
import os
import re
import time
import urllib.parse
import urllib.request
import zipfile

UA = {"User-Agent": "WorldMapApp/1.1 (https://github.com/eyad28607-cell/world-map)"}
WB = "https://api.worldbank.org/v2/"
WDQS = "https://query.wikidata.org/sparql"


def _get(url, timeout=90):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _sparql(query, tries=3):
    url = WDQS + "?" + urllib.parse.urlencode({"query": query})
    req = urllib.request.Request(url, headers={**UA, "Accept": "text/csv"})
    for n in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return list(csv.DictReader(io.StringIO(r.read().decode("utf-8"))))
        except OSError:
            if n == tries - 1:
                raise
            time.sleep(5)


def _qid(uri):
    return uri.rsplit("/", 1)[-1]


def commons_file(url):
    """Wikimedia Commons file name from a Wikidata image URL."""
    return urllib.parse.unquote(url.rsplit("/", 1)[-1]) if url else ""


# ---------- World Bank military indicators ----------

MIL_INDICATORS = {
    "mil_pct_gdp": "MS.MIL.XPND.GD.ZS",
    "mil_usd": "MS.MIL.XPND.CD",
    "mil_personnel": "MS.MIL.TOTL.P1",
    "arms_imports": "MS.MIL.MPRT.KD",
    "arms_exports": "MS.MIL.XPRT.KD",
}


def fetch_military_wb():
    """{iso3: {field: [value, year]}} with the latest value of each indicator."""
    year = datetime.date.today().year
    out = {}
    for field, ind in MIL_INDICATORS.items():
        data = json.loads(_get(WB + f"country/all/indicator/{ind}?format=json&per_page=20000&date={year - 10}:{year}"))[1]
        for r in data or []:
            i, v = r["countryiso3code"], r["value"]
            if not i or v is None:
                continue
            y = int(r["date"])
            cur = out.setdefault(i, {}).get(field)
            if cur is None or y > cur[1]:
                out[i][field] = [round(v, 2), y]
    return out


# ---------- UCDP/PRIO armed conflicts ----------

UCDP_NAME_FIX = {
    "united states of america": "United States", "russia": "Russian Federation", "soviet union": "Russian Federation",
    "dr congo": "Congo, Dem. Rep.", "zaire": "Congo, Dem. Rep.", "congo": "Congo, Rep.", "iran": "Iran, Islamic Rep.",
    "egypt": "Egypt, Arab Rep.", "syria": "Syrian Arab Republic", "yemen": "Yemen, Rep.", "north yemen": "Yemen, Rep.",
    "south yemen": "Yemen, Rep.", "turkey": "Turkiye", "türkiye": "Turkiye", "vietnam": "Viet Nam",
    "north vietnam": "Viet Nam", "south vietnam": "Viet Nam", "laos": "Lao PDR", "north korea": "Korea, Dem. People's Rep.",
    "south korea": "Korea, Rep.", "venezuela": "Venezuela, RB", "gambia": "Gambia, The", "kyrgyzstan": "Kyrgyz Republic",
    "ivory coast": "Cote d'Ivoire", "bosnia-herzegovina": "Bosnia and Herzegovina", "serbia": "Serbia",
    "yugoslavia": "Serbia", "myanmar": "Myanmar", "burma": "Myanmar", "cambodia": "Cambodia", "kampuchea": "Cambodia",
    "zimbabwe": "Zimbabwe", "rhodesia": "Zimbabwe", "madagascar": "Madagascar", "malagasy": "Madagascar",
    "macedonia": "North Macedonia", "macedonia, fyr": "North Macedonia", "swaziland": "Eswatini", "east timor": "Timor-Leste",
    "slovakia": "Slovak Republic", "brunei": "Brunei Darussalam", "cape verde": "Cabo Verde", "bahamas": "Bahamas, The",
    "micronesia": "Micronesia, Fed. Sts.", "czechoslovakia": "Czechia", "czech republic": "Czechia",
    "east germany": "Germany", "west germany": "Germany", "german democratic republic": "Germany",
    "south sudan": "South Sudan", "papua new guinea": "Papua New Guinea", "united kingdom": "United Kingdom",
    "hyderabad": "India", "taiwan": "Taiwan, China", "palestine": "West Bank and Gaza", "somaliland": "Somalia",
}
# Gleditsch-Ward state codes used by UCDP; codes not listed here are learned from the data
GW_ISO = {
    "2": "USA", "20": "CAN", "40": "CUB", "41": "HTI", "42": "DOM", "70": "MEX", "90": "GTM", "91": "HND",
    "92": "SLV", "93": "NIC", "94": "CRI", "95": "PAN", "100": "COL", "101": "VEN", "130": "ECU", "135": "PER",
    "140": "BRA", "145": "BOL", "150": "PRY", "155": "CHL", "160": "ARG", "165": "URY", "200": "GBR",
    "205": "IRL", "210": "NLD", "211": "BEL", "212": "LUX", "220": "FRA", "225": "CHE", "230": "ESP",
    "235": "PRT", "255": "DEU", "260": "DEU", "265": "DEU", "290": "POL", "305": "AUT", "310": "HUN",
    "315": "CZE", "316": "CZE", "317": "SVK", "325": "ITA", "339": "ALB", "341": "MNE", "343": "MKD",
    "344": "HRV", "345": "SRB", "346": "BIH", "349": "SVN", "350": "GRC", "352": "CYP", "355": "BGR",
    "359": "MDA", "360": "ROU", "365": "RUS", "366": "EST", "367": "LVA", "368": "LTU", "369": "UKR",
    "370": "BLR", "371": "ARM", "372": "GEO", "373": "AZE", "375": "FIN", "380": "SWE", "385": "NOR",
    "390": "DNK", "395": "ISL", "432": "MLI", "433": "SEN", "434": "BEN", "435": "MRT", "436": "NER",
    "437": "CIV", "438": "GIN", "439": "BFA", "450": "LBR", "451": "SLE", "452": "GHA", "461": "TGO",
    "471": "CMR", "475": "NGA", "481": "GAB", "482": "CAF", "483": "TCD", "484": "COG", "490": "COD",
    "500": "UGA", "501": "KEN", "510": "TZA", "516": "BDI", "517": "RWA", "520": "SOM", "522": "DJI",
    "530": "ETH", "531": "ERI", "540": "AGO", "541": "MOZ", "551": "ZMB", "552": "ZWE", "553": "MWI",
    "560": "ZAF", "565": "NAM", "570": "LSO", "571": "BWA", "572": "SWZ", "580": "MDG", "581": "COM",
    "600": "MAR", "615": "DZA", "616": "TUN", "620": "LBY", "625": "SDN", "626": "SSD", "630": "IRN",
    "640": "TUR", "645": "IRQ", "651": "EGY", "652": "SYR", "660": "LBN", "663": "JOR", "666": "ISR",
    "670": "SAU", "678": "YEM", "680": "YEM", "690": "KWT", "692": "BHR", "694": "QAT", "696": "ARE",
    "698": "OMN", "700": "AFG", "701": "TKM", "702": "TJK", "703": "KGZ", "704": "UZB", "705": "KAZ",
    "710": "CHN", "712": "MNG", "713": "TWN", "731": "PRK", "732": "KOR", "740": "JPN", "750": "IND",
    "770": "PAK", "771": "BGD", "775": "MMR", "780": "LKA", "790": "NPL", "800": "THA", "811": "KHM",
    "812": "LAO", "816": "VNM", "817": "VNM", "820": "MYS", "830": "SGP", "840": "PHL", "850": "IDN",
    "860": "TLS", "900": "AUS", "910": "PNG", "920": "NZL", "940": "SLB", "950": "FJI",
}
INCOMPAT = {"1": "Territory", "2": "Government", "3": "Territory and government"}
CTYPE = {"1": "Colonial (extrasystemic)", "2": "Between countries (interstate)", "3": "Civil war (intrastate)",
         "4": "Civil war with foreign troops (internationalized)"}


def _wb_lookup(names):
    """Maps a UCDP country name to a World Bank country name."""
    norm = lambda s: re.sub(r"[^a-z]", "", s.lower())
    table = {norm(n): n for n in names}
    for n in names:
        table.setdefault(norm(n.split(",")[0]), n)

    def find(name):
        base = re.sub(r"\s*\(.*?\)", "", name).strip()
        for cand in (name.lower(), base.lower()):
            if cand in UCDP_NAME_FIX:
                return UCDP_NAME_FIX[cand]
        for cand in (name, base):
            if norm(cand) in table:
                return table[norm(cand)]
        inner = re.findall(r"\((.*?)\)", name)
        return find(inner[0]) if inner else None
    return find


def fetch_ucdp():
    """Raw rows of the newest UCDP/PRIO Armed Conflict Dataset available."""
    yy = datetime.date.today().year % 100
    for v in (yy + 1, yy, yy - 1, yy - 2):
        try:
            z = zipfile.ZipFile(io.BytesIO(_get(f"https://ucdp.uu.se/downloads/ucdpprio/ucdp-prio-acd-{v}1-csv.zip")))
        except (OSError, zipfile.BadZipFile):
            continue
        name = next(n for n in z.namelist() if n.endswith(".csv"))
        return list(csv.DictReader(io.TextIOWrapper(z.open(name), encoding="utf-8"))), f"{v}.1"
    raise OSError("UCDP download failed")


def build_conflicts(rows, wb_names, name_to_iso):
    """Groups UCDP yearly rows into one record per conflict, linked to ISO3 codes."""
    find = _wb_lookup(wb_names)
    gw = {k: v for k, v in GW_ISO.items() if v in name_to_iso.values()}  # Gleditsch-Ward code -> ISO3
    for r in rows:
        for side, codes in (("side_a", "gwno_a"), ("side_b", "gwno_b"), ("side_a_2nd", "gwno_a_2nd"), ("side_b_2nd", "gwno_b_2nd")):
            names = [s.strip() for s in r[side].split(", ") if s.strip()]
            nums = [c.strip() for c in r[codes].split(",") if c.strip()]
            # only single-country entries: in lists, UCDP's name and code orders don't always match
            if len(names) == len(nums) == 1 and names[0].startswith("Government of "):
                wbn = find(names[0][len("Government of "):])
                if wbn and wbn in name_to_iso:
                    gw.setdefault(nums[0], name_to_iso[wbn])
    for r in rows:  # location names fill gaps for countries that only appear as places
        nums = [c.strip() for c in r["gwno_loc"].split(",") if c.strip()]
        if len(nums) == 1 and "," not in r["location"]:
            wbn = find(r["location"])
            if wbn and wbn in name_to_iso:
                gw.setdefault(nums[0], name_to_iso[wbn])

    codes = lambda s: [gw[c.strip()] for c in s.split(",") if c.strip() in gw]
    out = {}
    for r in rows:
        c = out.setdefault(r["conflict_id"], {
            "id": r["conflict_id"], "location": r["location"], "territory": r["territory_name"],
            "incompatibility": INCOMPAT.get(r["incompatibility"], ""), "type": CTYPE.get(r["type_of_conflict"], ""),
            "start": r["start_date"], "years": [], "war_years": [], "side_a": set(), "side_b": set(),
            "countries_loc": set(), "countries_a": set(), "countries_b": set(), "span": {},
        })
        y = int(r["year"])
        for i in set(codes(r["gwno_loc"]) + codes(r["gwno_a"]) + codes(r["gwno_a_2nd"]) + codes(r["gwno_b"]) + codes(r["gwno_b_2nd"])):
            s = c["span"].setdefault(i, [y, y])
            s[0], s[1] = min(s[0], y), max(s[1], y)
        c["years"].append(y)
        if r["intensity_level"] == "2":
            c["war_years"].append(y)
        for k, src in (("side_a", "side_a"), ("side_a", "side_a_2nd"), ("side_b", "side_b"), ("side_b", "side_b_2nd")):
            c[k].update(s.strip() for s in r[src].split(", ") if s.strip())
        c["countries_loc"].update(codes(r["gwno_loc"]))
        c["countries_a"].update(codes(r["gwno_a"]) + codes(r["gwno_a_2nd"]))
        c["countries_b"].update(codes(r["gwno_b"]) + codes(r["gwno_b_2nd"]))
    last = max(int(r["year"]) for r in rows)
    result = []
    for c in out.values():
        ys = sorted(set(c["years"]))
        result.append({
            "id": c["id"], "location": c["location"], "territory": c["territory"],
            "incompatibility": c["incompatibility"], "type": c["type"], "start": c["start"],
            "first": ys[0], "last": ys[-1], "active": ys[-1] == last, "years_active": len(ys),
            "war_years": len(set(c["war_years"])),
            "side_a": sorted(c["side_a"]), "side_b": sorted(c["side_b"]),
            "loc": sorted(c["countries_loc"]), "involved": sorted(c["countries_a"] | c["countries_b"] | c["countries_loc"]),
            "span": c["span"],  # years each country was involved
        })
    result.sort(key=lambda c: (-c["last"], -c["years_active"]))
    return result, last


# ---------- Wikidata ----------

FORCE_TYPES = {
    "Q234497": "Special forces", "Q12336613": "Special forces", "Q772547": "Armed forces",
    "Q61883": "Air force", "Q4508": "Navy", "Q37726": "Army", "Q781132": "Other branch",
}
FORCE_ORDER = ["Special forces", "Armed forces", "Army", "Navy", "Air force", "Other branch"]


def fetch_forces():
    """{iso3: [{name, desc, kind, ended}]} for armed forces, branches and special forces."""
    best = {}
    for t, kind in FORCE_TYPES.items():
        rows = _sparql(f"""SELECT DISTINCT ?u ?uLabel ?desc ?iso ?ended WHERE {{ hint:Query hint:optimizer "None" .
          ?sub wdt:P279* wd:{t} . ?u wdt:P31 ?sub . ?u wdt:P17 ?c . ?c wdt:P298 ?iso .
          OPTIONAL {{ ?u rdfs:label ?uLabel FILTER(lang(?uLabel)="en") }}
          OPTIONAL {{ ?u schema:description ?desc FILTER(lang(?desc)="en") }}
          OPTIONAL {{ ?u wdt:P576 ?ended }} OPTIONAL {{ ?u wdt:P154|wdt:P94|wdt:P18 ?img }} }}""".replace(
            "SELECT DISTINCT ?u ?uLabel ?desc ?iso ?ended", "SELECT DISTINCT ?u ?uLabel ?desc ?iso ?ended ?img"))
        for r in rows:
            if not r["uLabel"]:
                continue
            key = (r["iso"], _qid(r["u"]))
            prev = best.get(key)
            if prev is None or FORCE_ORDER.index(kind) < FORCE_ORDER.index(prev["kind"]):
                best[key] = {"name": r["uLabel"], "desc": r["desc"], "kind": kind,
                             "ended": r["ended"][:4] if r["ended"] else "", "q": _qid(r["u"]),
                             "img": commons_file(r["img"])}
            elif not prev["img"] and r["img"]:
                prev["img"] = commons_file(r["img"])
    out = {}
    for (iso, _), v in best.items():
        out.setdefault(iso, []).append(v)
    for v in out.values():
        v.sort(key=lambda x: (FORCE_ORDER.index(x["kind"]), bool(x["ended"]), x["name"]))
    return out


EQUIP_RULES = [  # (category, keywords in the Wikidata type label); first match wins
    (None, ["embassy", "consulate", "commission", "nunciature", "mission", "list", "person", "airport", "aerodrome",
            "sports", "venue", "shipwreck", "museum", "preserved", "position", "rate", "sloop", "brig",
            "schooner", "ship of the line", "steamship", "galley", "frigate (sail", "privateer", "clipper"]),
    ("Nuclear tests", ["nuclear weapons test", "nuclear test"]),
    ("Incidents: crashes, shootdowns & sinkings", ["crash", "shootdown", "accident", "incident", "disaster", "sinking",
                                                   "collision", "explosion", "attack", "hijacking"]),
    ("Bases", ["base", "air force station", "barracks", "fort", "garrison", "naval station", "military installation"]),
    ("Aircraft & drones", ["aircraft", "helicopter", "fighter", "bomber", "airplane", "aeroplane", "drone",
                           "unmanned aerial", "airship", "glider", "jet", "fleet"]),
    ("Missiles, rockets & torpedoes", ["missile", "rocket", "torpedo", "bomb", "warhead", "mine "]),
    ("Satellites & space", ["satellite", "spacecraft", "space"]),
    ("Submarines", ["submarine"]),
    ("Warships & boats", ["ship", "destroyer", "frigate", "corvette", "cruiser", "carrier", "minesweeper",
                          "minehunter", "patrol", "gunboat", "naval vessel", "boat", "vessel", "cutter", "tug",
                          "oiler", "tender", "monitor", "battleship", "watercraft", "landing craft", "icebreaker"]),
    ("Tanks & armoured vehicles", ["tank", "armoured", "armored", "combat vehicle", "infantry fighting",
                                   "personnel carrier", "military vehicle", "vehicle"]),
    ("Artillery", ["artillery", "howitzer", "mortar", "cannon", "gun model", "air defense", "anti-aircraft"]),
    ("Small arms", ["rifle", "firearm", "pistol", "revolver", "machine gun", "submachine", "carbine", "shotgun",
                    "grenade", "weapon", "knife", "bayonet", "launcher"]),
    ("Radar, electronics & other tech", ["radar", "sonar", "system", "computer", "software", "communication",
                                         "electronic", "sensor"]),
]
EQUIP_ORDER = [c for c, _ in EQUIP_RULES if c]


def _equip_category(label):
    l = (label or "").lower()
    if not l:
        return None
    for cat, words in EQUIP_RULES:
        if any(w in l for w in words):
            return cat
    return None


# Readable kinds inside each category, matched against the item's description and type; first match wins
KIND_RULES = {
    "Aircraft & drones": [
        ("Drones (unmanned aircraft)", ["unmanned", "drone", "uav", "ucav"]),
        ("Helicopters", ["helicopter", "rotorcraft", "tiltrotor"]),
        ("Fighter jets", ["fighter", "interceptor", "multirole combat"]),
        ("Bombers", ["bomber"]),
        ("Attack aircraft", ["attack aircraft", "ground-attack", "ground attack", "close air support", "strike aircraft"]),
        ("Spy, patrol & early-warning aircraft", ["reconnaissance", "surveillance", "early warning", "awacs",
                                                  "maritime patrol", "patrol aircraft", "electronic warfare", "spy"]),
        ("Tankers & transport aircraft", ["tanker", "transport", "cargo", "airlifter", "refuel", "airliner", "utility"]),
        ("Training aircraft", ["trainer", "training"]),
    ],
    "Warships & boats": [
        ("Aircraft carriers", ["aircraft carrier", "helicopter carrier", "carrier"]),
        ("Battleships", ["battleship", "dreadnought", "battlecruiser"]),
        ("Cruisers", ["cruiser"]),
        ("Destroyers", ["destroyer"]),
        ("Frigates", ["frigate"]),
        ("Corvettes", ["corvette"]),
        ("Amphibious & landing ships", ["landing", "amphibious", "dock"]),
        ("Mine warfare ships", ["mine"]),
        ("Patrol boats & coast guard", ["patrol", "cutter", "coast guard", "gunboat", "fast attack", "missile boat",
                                        "torpedo boat"]),
        ("Support & supply ships", ["oiler", "tender", "tug", "replenishment", "supply", "hospital", "auxiliary",
                                    "transport", "cargo", "survey", "research", "icebreaker", "training"]),
    ],
    "Submarines": [
        ("Nuclear missile submarines", ["ballistic missile submarine", "ballistic"]),
        ("Nuclear attack submarines", ["nuclear"]),
        ("Diesel-electric submarines", ["diesel", "conventional"]),
    ],
    "Tanks & armoured vehicles": [
        ("Infantry fighting vehicles", ["infantry fighting"]),
        ("Armoured personnel carriers", ["personnel carrier", "apc"]),
        ("Self-propelled guns & rocket launchers", ["self-propelled", "multiple rocket", "rocket launcher"]),
        ("Recovery & engineering vehicles", ["recovery", "engineering", "bridge", "mine-clearing"]),
        ("Main battle tanks", ["main battle tank"]),
        ("Light & other tanks", ["tank"]),
        ("Scout & armoured cars", ["armoured car", "armored car", "reconnaissance", "scout"]),
        ("Trucks & utility vehicles", ["truck", "utility", "jeep", "light vehicle", "transport"]),
    ],
    "Missiles, rockets & torpedoes": [
        ("Intercontinental & ballistic missiles", ["ballistic"]),
        ("Cruise missiles", ["cruise"]),
        ("Anti-ship missiles", ["anti-ship"]),
        ("Air-to-air missiles", ["air-to-air"]),
        ("Surface-to-air & air-defence missiles", ["surface-to-air", "anti-aircraft", "air defense", "air defence",
                                                    "anti-ballistic", "sam "]),
        ("Anti-tank missiles", ["anti-tank", "antitank"]),
        ("Air-to-ground missiles", ["air-to-surface", "air-to-ground"]),
        ("Torpedoes", ["torpedo"]),
        ("Bombs", ["bomb"]),
        ("Rockets", ["rocket"]),
    ],
    "Artillery": [
        ("Howitzers", ["howitzer"]),
        ("Mortars", ["mortar"]),
        ("Rocket artillery", ["rocket"]),
        ("Air-defence guns", ["anti-aircraft", "air defense", "air defence"]),
        ("Anti-tank guns", ["anti-tank"]),
        ("Field guns & cannons", ["gun", "cannon"]),
    ],
    "Small arms": [
        ("Sniper rifles", ["sniper", "marksman"]),
        ("Assault rifles", ["assault rifle"]),
        ("Submachine guns", ["submachine"]),
        ("Machine guns", ["machine gun"]),
        ("Battle & other rifles", ["rifle", "carbine"]),
        ("Pistols & revolvers", ["pistol", "revolver", "handgun"]),
        ("Shotguns", ["shotgun"]),
        ("Grenades & grenade launchers", ["grenade"]),
        ("Rocket & anti-tank launchers", ["launcher", "anti-tank", "rocket"]),
        ("Knives & bayonets", ["knife", "bayonet"]),
    ],
    "Satellites & space": [
        ("Spy & reconnaissance satellites", ["reconnaissance", "spy", "intelligence", "surveillance", "imaging"]),
        ("Communication satellites", ["communication"]),
        ("Navigation satellites", ["navigation", "gps", "glonass", "positioning"]),
        ("Early-warning satellites", ["early warning", "missile warning"]),
        ("Weather satellites", ["weather", "meteorolog"]),
    ],
    "Radar, electronics & other tech": [
        ("Radars", ["radar"]),
        ("Sonars", ["sonar"]),
        ("Electronic warfare & jamming", ["jammer", "countermeasure", "electronic warfare", "decoy"]),
        ("Communications", ["communication", "radio"]),
        ("Computers & software", ["computer", "software"]),
    ],
    "Bases": [
        ("Air bases", ["air base", "airbase", "air force station", "airfield", "air station"]),
        ("Naval bases", ["naval", "navy", "port"]),
        ("Army bases & barracks", ["barracks", "army", "fort", "garrison", "camp"]),
    ],
    "Nuclear tests": [
        ("Underground tests", ["underground"]),
        ("Atmospheric & other tests", []),
    ],
    "Incidents: crashes, shootdowns & sinkings": [
        ("Shootdowns", ["shootdown", "shot down"]),
        ("Crashes", ["crash", "accident"]),
        ("Sinkings & ship disasters", ["sinking", "sank", "collision", "explosion", "disaster"]),
    ],
}


def _kind(cat, desc, type_label):
    text = f"{desc or ''} {type_label or ''}".lower()
    for kind, words in KIND_RULES.get(cat, []):
        if not words or any(w in text for w in words):
            return kind
    return "Other " + cat.split(":")[0].split(" & ")[0].split(",")[0].lower()


def fetch_equipment():
    """{iso3: {category: [[name, kind, description, origin iso3], ...]}} for equipment a country or its forces operate."""
    fields = """OPTIONAL { ?e wdt:P31 ?t . ?t rdfs:label ?tLabel FILTER(lang(?tLabel)="en") }
      OPTIONAL { ?e schema:description ?desc FILTER(lang(?desc)="en") }
      OPTIONAL { ?e wdt:P495 ?o . ?o wdt:P298 ?origin }
      OPTIONAL { ?e wdt:P18 ?img }
      ?e rdfs:label ?eLabel FILTER(lang(?eLabel)="en") }"""
    head = 'SELECT DISTINCT ?e ?eLabel ?tLabel ?desc ?origin ?img ?iso WHERE { hint:Query hint:optimizer "None" .'
    # operated by a country directly
    rows = _sparql(f"{head} ?c wdt:P298 ?iso . ?e wdt:P137 ?c . {fields}")
    # operated by one of a country's forces (one query per kind of force keeps each under the time limit)
    for ot in ("Q772547", "Q781132", "Q61883", "Q4508", "Q37726", "Q8473", "Q176799"):
        rows += _sparql(f"{head} ?op wdt:P31 wd:{ot} . ?op wdt:P17 ?c . ?c wdt:P298 ?iso . ?e wdt:P137 ?op . {fields}")
    items = {}  # an item can have several types; keep the first one that maps to a category
    for r in rows:
        name = r["eLabel"]
        if not name or re.fullmatch(r"Q\d+", name):
            continue
        it = items.setdefault((r["iso"], _qid(r["e"])), {"name": name, "types": [], "desc": "", "origin": "", "img": ""})
        if r["tLabel"] and r["tLabel"] not in it["types"]:
            it["types"].append(r["tLabel"])
        it["desc"] = it["desc"] or r["desc"]
        it["origin"] = it["origin"] or r["origin"]
        it["img"] = it["img"] or commons_file(r["img"])
    out = {}
    for (iso, _), it in items.items():
        cat, typ = None, ""
        for t in it["types"]:
            cat = _equip_category(t)
            if cat:
                typ = t
                break
        if not cat:
            continue
        out.setdefault(iso, {}).setdefault(cat, []).append(
            [it["name"], _kind(cat, it["desc"], typ), it["desc"], it["origin"] if it["origin"] != iso else "", it["img"]])
    for cats in out.values():
        for v in cats.values():
            v.sort(key=lambda x: (x[1], x[0].lower()))
    return out


def fetch_disputes():
    """{iso3: [{name, desc, claimants:[iso3]}]} for territories claimed by more than one country."""
    rows = _sparql("""SELECT DISTINCT ?d ?dLabel ?desc ?iso WHERE { hint:Query hint:optimizer "None" .
      ?d wdt:P1336 ?c . ?c wdt:P298 ?iso .
      OPTIONAL { ?d rdfs:label ?dLabel FILTER(lang(?dLabel)="en") }
      OPTIONAL { ?d schema:description ?desc FILTER(lang(?desc)="en") } }""")
    rows += _sparql("""SELECT DISTINCT ?d ?dLabel ?desc ?iso WHERE { hint:Query hint:optimizer "None" .
      ?d wdt:P1336 ?x . ?d wdt:P17 ?c . ?c wdt:P298 ?iso .
      OPTIONAL { ?d rdfs:label ?dLabel FILTER(lang(?dLabel)="en") }
      OPTIONAL { ?d schema:description ?desc FILTER(lang(?desc)="en") } }""")
    items = {}
    for r in rows:
        if not r["dLabel"]:
            continue
        d = items.setdefault(_qid(r["d"]), {"name": r["dLabel"], "desc": r["desc"], "claimants": set()})
        d["claimants"].add(r["iso"])
    out = {}
    skip = re.compile(r"\b(street|cemetery|village|human settlement|rural (commune|locality)|municipality|town in|"
                      r"place in|settlement|school|church|building|monument|museum|hospital|station)\b", re.I)
    for d in items.values():
        desc = d["desc"] or ""
        if len(d["claimants"]) < 2 or skip.search(desc) or (desc.lower().startswith("city in") and d["name"] != "Jerusalem"):
            continue
        rec = {"name": d["name"], "desc": d["desc"], "claimants": sorted(d["claimants"])}
        for iso in rec["claimants"]:
            out.setdefault(iso, []).append(rec)
    for v in out.values():
        v.sort(key=lambda x: x["name"])
    return out


def fetch_people():
    """{iso3: {"flag": file, "leaders": [{role, name, desc, img}]}}: each country's flag and current leaders."""
    rows = _sparql("""SELECT ?iso ?flag ?role ?p ?pLabel ?desc ?img WHERE { hint:Query hint:optimizer "None" .
      ?c wdt:P31 wd:Q3624078 . ?c wdt:P298 ?iso .
      OPTIONAL { ?c wdt:P41 ?flag }
      OPTIONAL { VALUES (?prop ?role) { (wdt:P35 "Head of state") (wdt:P6 "Head of government") }
                 ?c ?prop ?p . ?p rdfs:label ?pLabel FILTER(lang(?pLabel)="en")
                 OPTIONAL { ?p schema:description ?desc FILTER(lang(?desc)="en") }
                 OPTIONAL { ?p wdt:P18 ?img } } }""")
    out = {}
    for r in rows:
        c = out.setdefault(r["iso"], {"flag": "", "leaders": []})
        c["flag"] = c["flag"] or commons_file(r["flag"])
        if r["pLabel"] and not any(l["name"] == r["pLabel"] and l["role"] == r["role"] for l in c["leaders"]):
            c["leaders"].append({"role": r["role"], "name": r["pLabel"], "desc": r["desc"], "img": commons_file(r["img"])})
        elif r["pLabel"] and r["img"]:
            for l in c["leaders"]:
                if l["name"] == r["pLabel"] and not l["img"]:
                    l["img"] = commons_file(r["img"])
    for c in out.values():
        c["leaders"].sort(key=lambda l: l["role"] != "Head of state")
    return out


def download_images(files, img_dir, width=240, log=print):
    """Saves Commons thumbnails into img_dir. Returns {file name: saved file name}; already saved files are reused."""
    import concurrent.futures
    import hashlib
    os.makedirs(img_dir, exist_ok=True)
    have = {os.path.splitext(f)[0]: f for f in os.listdir(img_dir)}
    result = {}

    def one(name):
        key = hashlib.md5(name.encode("utf-8")).hexdigest()[:16]
        if key in have:
            return name, have[key]
        url = "https://commons.wikimedia.org/wiki/Special:FilePath/" + urllib.parse.quote(name) + f"?width={width}"
        for n in range(3):
            try:
                req = urllib.request.Request(url, headers=UA)
                with urllib.request.urlopen(req, timeout=60) as r:
                    data, ctype = r.read(), r.headers.get("Content-Type", "")
                break
            except OSError:
                if n == 2:
                    return name, None
                time.sleep(3 * (n + 1))
        ext = ".png" if "png" in ctype else ".gif" if "gif" in ctype else ".svg" if "svg" in ctype else ".jpg"
        with open(os.path.join(img_dir, key + ext), "wb") as f:
            f.write(data)
        return name, key + ext

    names = sorted({f for f in files if f})
    with concurrent.futures.ThreadPoolExecutor(4) as pool:
        for name, saved in pool.map(one, names):
            if saved:
                result[name] = saved
    log(f"images: {len(result)} of {len(names)} saved")
    return result
