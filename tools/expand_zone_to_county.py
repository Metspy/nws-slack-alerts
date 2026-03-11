import requests
import json
import sys
from pathlib import Path

ZONECOUNTY_URL = "https://www.weather.gov/source/gis/Shapefiles/County/bp16ap26.dbx"
CACHE_FILE = Path("tools/zonecounty.dbx")


def download_file():

    if CACHE_FILE.exists():
        return CACHE_FILE.read_text()

    print("Downloading ZoneCounty correlation file...")

    headers = {"User-Agent": "nws-alert-tools"}

    r = requests.get(ZONECOUNTY_URL, headers=headers)
    r.raise_for_status()

    CACHE_FILE.write_text(r.text)

    return r.text

STATE_FIPS = {
    "01":"AL","02":"AK","04":"AZ","05":"AR","06":"CA","08":"CO",
    "09":"CT","10":"DE","11":"DC","12":"FL","13":"GA","15":"HI",
    "16":"ID","17":"IL","18":"IN","19":"IA","20":"KS","21":"KY",
    "22":"LA","23":"ME","24":"MD","25":"MA","26":"MI","27":"MN",
    "28":"MS","29":"MO","30":"MT","31":"NE","32":"NV","33":"NH",
    "34":"NJ","35":"NM","36":"NY","37":"NC","38":"ND","39":"OH",
    "40":"OK","41":"OR","42":"PA","44":"RI","45":"SC","46":"SD",
    "47":"TN","48":"TX","49":"UT","50":"VT","51":"VA","53":"WA",
    "54":"WV","55":"WI","56":"WY"
}

def build_lookup(data):

    lookup = {}

    for line in data.splitlines():

        parts = line.split("|")

        if len(parts) < 7:
            continue

        state = parts[0].strip()
        zone = parts[1].strip().zfill(3)
        fips = parts[6].strip()

        county = fips[2:]   # last 3 digits

        zone_code = f"{state}Z{zone}"
        county_code = f"{state}C{county}"

        lookup.setdefault(zone_code, set()).add(county_code)

    return lookup

def expand_config(config_file):

    data = download_file()
    lookup = build_lookup(data)

    with open(config_file) as f:
        config = json.load(f)

    zones = [a for a in config["areas"] if "Z" in a]

    counties = set()

    for z in zones:
        counties.update(lookup.get(z, []))

    config["areas"] = sorted(set(config["areas"]) | counties)

    output = config_file.replace(".Zcodes", "")

    with open(output, "w") as f:
        json.dump(config, f, indent=2)

    print("Zones:", zones)
    print("Added counties:", sorted(counties))
    print("New config written:", output)


if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Usage:")
        print("python tools/expand_zones_to_counties.py configs/SITE.json.Zcodes")
        sys.exit(1)

    expand_config(sys.argv[1])
