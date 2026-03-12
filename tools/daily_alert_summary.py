import requests
import json
import glob
import os
from datetime import datetime, timedelta, timezone

API = "https://api.weather.gov/alerts"
HEADERS = {"User-Agent": "nws-alert-summary"}

OPS_WEBHOOK_ENV = "OPS_SLACK_WEBHOOK"


def load_sites():

    sites = {}

    for f in glob.glob("configs/[A-Z]*.json"):

        with open(f) as j:
            cfg = json.load(j)

        name = os.path.basename(f).replace(".json","")

        # load alert type configuration
        try:
            with open(cfg["alert_type_file"]) as af:
                alert_types = json.load(af)
        except:
            alert_types = {}

        sites[name] = {
            "areas": set(cfg.get("areas", [])),
            "alert_types": alert_types
        }

    return sites


def load_alert_log(site):

    path = f"state/{site}_alert_log.json"

    try:
        with open(path) as f:
            return json.load(f)
    except:
        return {}


def states_from_sites(sites):

    states = set()

    for s in sites.values():
        for area in s["areas"]:
            states.add(area[:2])

    return sorted(states)


def fetch_state_alerts(state):

    url = f"{API}?area={state}"

    r = requests.get(url, headers=HEADERS)

    if r.status_code != 200:
        return []

    return r.json().get("features", [])


def cutoff_time():

    return datetime.now(timezone.utc) - timedelta(hours=24)


def build_alert_key(props):

    return "|".join([
        props.get("event",""),
        props.get("onset",""),
        props.get("expires",""),
        props.get("senderName",""),
        props.get("headline","")
    ])


def summarize():

    sites = load_sites()

    cutoff = cutoff_time()

    states = states_from_sites(sites)

    alerts = []

    for s in states:
        alerts.extend(fetch_state_alerts(s))

    lines = []
    lines.append("🌤 *NWS Alert Digest (last 24h)*")
    lines.append("")

    for site, cfg in sites.items():

        sent_log = load_alert_log(site)

        issued = 0
        sent = 0
        filtered = 0

        event_counts = {}
        event_filtered = {}

        for a in alerts:

            props = a["properties"]

            sent_time = datetime.fromisoformat(
                props["sent"].replace("Z","+00:00")
            )

            if sent_time < cutoff:
                continue

            ugc = set(props.get("geocode", {}).get("UGC", []))

            if not ugc.intersection(cfg["areas"]):
                continue

            event = props["event"]
            aid = build_alert_key(props)

            issued += 1
            event_counts[event] = event_counts.get(event, 0) + 1

            if not cfg["alert_types"].get(event, False):
                filtered += 1
                event_filtered[event] = True
                continue

            if aid in sent_log:
                sent += 1

        missed = issued - sent - filtered

        lines.append(f"*SITE: {site}*")
        lines.append(
            f"Issued: {issued} | Sent: {sent} | Filtered: {filtered} | Missed: {missed}"
        )

        if event_counts:

            for event in sorted(event_counts):

                count = event_counts[event]

                label = f"• {event} ({count})"

                if event_filtered.get(event):
                    label += " (Filtered)"

                lines.append(label)

        lines.append("")

    return "\n".join(lines)


def send_to_slack(text):

    webhook = os.environ.get(OPS_WEBHOOK_ENV)

    if not webhook:
        print("OPS webhook not defined")
        return

    requests.post(webhook, json={"text": text})


if __name__ == "__main__":

    report = summarize()

    print(report)

    send_to_slack(report)
