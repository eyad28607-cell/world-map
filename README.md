# World Map: Offline & Palantir

A Windows desktop app with an interactive world map showing two things for every country:

- **% offline**: the share of people who don't use the internet, how many people that is, the country's rank and the trend since 2015 (World Bank / ITU data).
- **Palantir**: every reported government contract, lawsuit, controversy, protest and policy decision involving Palantir, each with its date, status and a link to the source.

Click a country, or search for it, to see its full details.

## Download

Get `WorldMap.exe` from the [Releases](../../releases) page and run it. No install needed, and it works offline.

## Yearly updates

- **In the app:** once a year, on launch, the app downloads fresh World Bank data and the latest `palantir.json` from this repository, then reloads the map. Data is kept in `%APPDATA%\WorldMap`.
- **On GitHub:** a workflow runs every 1 January. It refreshes the data, commits it and publishes a new release with a rebuilt `WorldMap.exe`.

## Updating the Palantir list

Edit [`app/assets/palantir.json`](app/assets/palantir.json). Each country has a `level` (4 = extensive use, 3 = active contracts, 2 = limited / ending / letter of intent, 1 = rejected or issues only) and a list of `items` with `type` (Contract, Legal, Controversy, Protest, Policy, Issue), `title`, `detail`, `date`, `status` and `source`. Installed apps pick up the change at their next yearly update.

The list is hand-compiled from news reports, company filings and official records. It is not complete, and some items rest on a single source.

## Build it yourself

```bash
cd app
pip install pywebview pyinstaller pillow
python make_icon.py
python build_data.py
pyinstaller --noconfirm --onefile --windowed --name WorldMap --icon icon.ico --add-data "assets;assets" --add-data "icon.ico;." main.py
```
