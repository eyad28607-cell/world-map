# World Map

A desktop app for **Windows, macOS and Linux** with an interactive world map. It works fully offline. Click any country, or search for it, to see everything about it:

- **% offline:** the share of people who don't use the internet, how many people that is, the country's rank and the trend since 2015.
- **Conflicts:** every armed conflict from 1946 to today (wars between countries and civil wars), who fought whom, the years, and whether it is still active. Also territories claimed by more than one country.
- **Military:** spending, personnel and arms trade; armed forces, branches and special forces units; and weapons, equipment and tech: aircraft and drones, warships, submarines, tanks, artillery, missiles, small arms, satellites, radar, bases, nuclear tests, plus crashes, shootdowns and sinkings.
- **Palantir:** reported government contracts, lawsuits, controversies, protests and policy decisions, each with a source link.

## Download

Get the latest version from the [Releases](../../releases) page:

| System | File | How to open |
|---|---|---|
| Windows | `WorldMap.exe` | Double-click it. |
| macOS | `WorldMap-macOS.zip` | Unzip, then right-click `WorldMap.app` and choose **Open** the first time (the app is not signed). |
| Linux | `WorldMap-linux.tar.gz` | Extract, then run `WorldMap/WorldMap`. |

## Data sources

| Topic | Source |
|---|---|
| Internet use, population | World Bank / ITU |
| Armed conflicts | [UCDP/PRIO Armed Conflict Dataset](https://ucdp.uu.se/downloads/), Uppsala University (conflicts with 25+ battle deaths in a year) |
| Military spending, personnel, arms trade | World Bank / SIPRI |
| Disputed territories, forces, special forces, equipment | [Wikidata](https://www.wikidata.org) (community-edited: coverage varies by country and includes historic items) |
| Palantir | Hand-compiled from news reports, company filings and official records ([`app/assets/palantir.json`](app/assets/palantir.json)) |

## Yearly updates

- **In the app:** once a year, on launch, the app downloads all the data again (including the latest `palantir.json` from this repository) and reloads the map. Data is kept in `%APPDATA%\WorldMap` (Windows), `~/Library/Application Support/WorldMap` (macOS) or `~/.local/share/WorldMap` (Linux).
- **On GitHub:** a workflow runs every 1 January. It refreshes the data, commits it, and publishes a new release for all three systems. Pushing a `v*` tag also builds a release.

## Updating the Palantir list

Edit [`app/assets/palantir.json`](app/assets/palantir.json). Each country has a `level` (4 = extensive use, 3 = active contracts, 2 = limited / ending / letter of intent, 1 = rejected or issues only) and a list of `items` with `type` (Contract, Legal, Controversy, Protest, Policy, Issue), `title`, `detail`, `date`, `status` and `source`.

## Build it yourself

```bash
pip install pywebview pyinstaller pillow   # Linux: pip install "pywebview[qt]" pyinstaller pillow
python app/build_data.py                   # optional: refresh all data
python app/build.py                        # output goes to dist/
```
