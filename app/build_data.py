"""Builds data.js for the map from World Bank data and palantir.json.

Run directly to refresh the bundled data:  python build_data.py
"""
import csv
import datetime
import json
import os
import urllib.request

import sources

WB = "https://api.worldbank.org/v2/"
HERE = os.path.dirname(os.path.abspath(__file__))


def _get(url, timeout=30):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_worldbank():
    """Latest internet-use history and population per country."""
    year = datetime.date.today().year
    countries = _get(WB + "country?format=json&per_page=400")[1]
    net = _get(WB + f"country/all/indicator/IT.NET.USER.ZS?format=json&per_page=20000&date=2015:{year}")[1]
    pop = _get(WB + f"country/all/indicator/SP.POP.TOTL?format=json&per_page=20000&date={year - 6}:{year}")[1]
    return countries, net, pop


def build_rows(countries, net, pop):
    real = {c["id"]: c for c in countries if c["region"]["id"] != "NA"}
    hist, pops = {}, {}
    for r in net:
        i = r["countryiso3code"]
        if i in real and r["value"] is not None:
            hist.setdefault(i, {})[int(r["date"])] = round(r["value"], 1)
    for r in pop:
        i = r["countryiso3code"]
        if i in real and r["value"] is not None and int(r["date"]) > pops.get(i, (0, 0))[0]:
            pops[i] = (int(r["date"]), r["value"])
    rows = []
    for i, h in hist.items():
        y = max(h)
        off = round(100 - h[y], 1)
        p = pops.get(i)
        rows.append({
            "iso3": i, "name": real[i]["name"], "region": real[i]["region"]["value"],
            "online": h[y], "offline": off, "year": y,
            "pop": round(p[1]) if p else None,
            "offline_people": round(p[1] * off / 100) if p else None,
            "history": [[k, h[k]] for k in sorted(h)],
        })
    rows.sort(key=lambda r: -r["offline"])
    for n, r in enumerate(rows, 1):
        r["rank"] = n
    rows.sort(key=lambda r: r["name"])
    return rows


def write(rows, pal, out_dir, csv_path=None):
    meta = {"built": datetime.date.today().isoformat(), "palantir_updated": pal.get("updated", "")}
    with open(os.path.join(out_dir, "data.js"), "w", encoding="utf-8") as f:
        f.write("window.D=" + json.dumps(rows, ensure_ascii=False) + ";\n")
        f.write("window.PAL=" + json.dumps(pal, ensure_ascii=False) + ";\n")
        f.write("window.META=" + json.dumps(meta) + ";\n")
    with open(os.path.join(out_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f)
    if csv_path:
        names = {r["iso3"]: r["name"] for r in rows}
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["iso3", "country", "region", "offline_%", "online_%", "year", "population",
                        "people_offline", "offline_rank", "palantir_level"])
            for r in rows:
                lvl = pal["countries"].get(r["iso3"], {}).get("level", 0)
                w.writerow([r["iso3"], r["name"], r["region"], r["offline"], r["online"], r["year"],
                            r["pop"], r["offline_people"], r["rank"], pal["levels"].get(str(lvl), "none")])
            w.writerow([])
            w.writerow(["iso3", "country", "type", "date", "status", "title", "detail", "source"])
            for iso, c in pal["countries"].items():
                for it in c["items"]:
                    w.writerow([iso, names.get(iso, iso), it["type"], it.get("date", ""), it.get("status", ""),
                                it["title"], it["detail"], it["source"]])
    return meta


def refresh_extra(countries, out_dir, log=print):
    """Downloads conflicts and military data into extra.js. A source that fails keeps its previous data."""
    path = os.path.join(out_dir, "extra.json")
    try:
        with open(path, encoding="utf-8") as f:
            extra = json.load(f)
    except (OSError, ValueError):
        extra = {}
    real = {c["id"]: c["name"] for c in countries if c["region"]["id"] != "NA"}
    name_to_iso = {v: k for k, v in real.items()}

    def conflicts():
        rows, ver = sources.fetch_ucdp()
        conf, last = sources.build_conflicts(rows, list(real.values()), name_to_iso)
        extra["ucdp_version"], extra["ucdp_last_year"] = ver, last
        return conf

    steps = {"conflicts": conflicts, "disputes": sources.fetch_disputes, "forces": sources.fetch_forces,
             "equipment": sources.fetch_equipment, "military": sources.fetch_military_wb}
    for key, fn in steps.items():
        try:
            extra[key] = fn()
            extra.setdefault("updated", {})[key] = datetime.date.today().isoformat()
            log(f"{key}: ok ({len(extra[key])})")
        except Exception as e:  # keep going; old data for this source stays
            log(f"{key}: failed, keeping previous data ({e})")
    extra["equipment_order"] = sources.EQUIP_ORDER
    extra["force_order"] = sources.FORCE_ORDER
    with open(path, "w", encoding="utf-8") as f:
        json.dump(extra, f, ensure_ascii=False)
    with open(os.path.join(out_dir, "extra.js"), "w", encoding="utf-8") as f:
        f.write("window.X=" + json.dumps(extra, ensure_ascii=False) + ";\n")
    return extra


if __name__ == "__main__":
    assets = os.path.join(HERE, "assets")
    pal = json.load(open(os.path.join(assets, "palantir.json"), encoding="utf-8"))
    countries, net, pop = fetch_worldbank()
    rows = build_rows(countries, net, pop)
    print(write(rows, pal, assets, os.path.join(HERE, "..", "world-data.csv")), len(rows), "countries")
    refresh_extra(countries, assets)
