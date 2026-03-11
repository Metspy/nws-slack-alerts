import json
import requests
import sys
from pathlib import Path

HEADERS = {
    "User-Agent": "ugc-expansion-script (markspychala@gmail.com)"
}

def get_counties_for_zone(zone):

    url = f"https://api.weather.gov/zones/forecast/{zone}"

    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()

    data = r.json()

    counties = []

    for county_url in data["properties"].get("county", []):
        counties.append(county_url.split("/")[-1])

    return counties


def main(config_file):

    config_path = Path(config_file)

    with open(config_path) as f:
        config = json.load(f)

    zones = [a for a in config["areas"] if "Z" in a]

    counties = set()

    print("Zones found:", zones)
    print()

    for zone in zones:

        try:
            zone_counties = get_counties_for_zone(zone)

            print(f"{zone} -> {zone_counties}")

            counties.update(zone_counties)

        except Exception as e:

            print("Failed for", zone, e)

    new_areas = sorted(set(config["areas"]) | counties)

    config["areas"] = new_areas

    output_file = config_file.replace(".Zcodes", "")

    with open(output_file, "w") as f:
        json.dump(config, f, indent=2)

    print()
    print("New config written:", output_file)


if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Usage: python expand_zones_to_counties.py SITE.json.Zcodes")
        sys.exit(1)

    main(sys.argv[1])
