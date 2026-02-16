#raise RuntimeError("intentional test failure")
import requests
import argparse
import json
from datetime import datetime, timedelta, timezone
import os

# === LOAD SITE CONFIG ===
def load_site_config(config_path):
    with open(config_path, "r") as f:
        return json.load(f)

# === LOAD ALERT TYPE CONFIG ===
def load_alert_type_flags():
    default_flags = {
        "Flash Flood Warning": False,
        "Flash Flood Watch": False,
        "Flood Warning": False,
        "Flood Watch": False,
        "Tornado Warning": False,
        "Tornado Watch": False,
        "Severe Thunderstorm Warning": False,
        "Severe Thunderstorm Watch": False,
        "Winter Storm Warning": False,
        "Winter Storm Watch": False,
        "Blizzard Warning": False,
        "Ice Storm Warning": False,
        "Heat Advisory": False,
        "Excessive Heat Watch": False,
        "Extreme Heat Warning": False,
        "Extreme Heat Watch": False,
        "Air Quality Alert": False,
        "Red Flag Warning": False,
        "Dense Smoke Advisory": False,
        "Dust Storm Warning": False,
        "Extreme Wind Warning": False,
        "High Wind Warning": False,
        "High Wind Watch": False,
        "Snow Squall Warning": False,
        "Special Weather Statement": False,
        "Hazardous Weather Outlook": False,
        "Hurricane Watch": False,
        "Hurricane Warning": False,
        "Tropical Storm Watch": False,
        "Tropical Storm Warning": False,
        "Storm Surge Watch": False,
        "Storm Surge Warning": False,
        "Severe Weather Statement": False,
        "Coastal Flood Advisory": False,
        "Fire Weather Watch": False,
        "Child Abduction Emergency": False,
        "Civil Danger Warning": False,
        "Blue Alert": False
    }
    if not os.path.exists(ALERT_TYPE_FILE):
        with open(ALERT_TYPE_FILE, "w") as f:
            json.dump(default_flags, f, indent=2)
        print(f"Created default alert config: {ALERT_TYPE_FILE}")
        return default_flags
    try:
        with open(ALERT_TYPE_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading {ALERT_TYPE_FILE}: {e}")
        return default_flags

# === ALERT LOG ===
def load_alert_log(filename, expiry_hours):
    now = datetime.now(timezone.utc)
    if not os.path.exists(filename):
        return {}
    with open(filename, "r") as f:
        try:
            log = json.load(f)
        except json.JSONDecodeError:
            return {}
    valid = {}
    for aid, ts in log.items():
        try:
            t = datetime.fromisoformat(ts)
            if now - t < timedelta(hours=expiry_hours):
                valid[aid] = ts
        except ValueError:
            continue
    return valid

def save_alert_log(log, filename):
    with open(filename, "w") as f:
        json.dump(log, f, indent=2)

def has_been_alerted(aid, log):
    return aid in log

def mark_alert_sent(aid, log):
    log[aid] = datetime.now(timezone.utc).isoformat()

# === FETCH ALERTS ===
def fetch_alerts(area_code):
    url = f"https://api.weather.gov/alerts/active?zone={area_code}"

    try:
        response = requests.get(
            url,
            headers={"User-Agent": "weather-alert-script"},
            timeout=15
        )
        response.raise_for_status()

        features = response.json().get("features", [])
        print(f"Fetched {len(features)} active alerts for {area_code}")
        return features, True

    except Exception as e:
        print(f"ERROR fetching alerts for {area_code}: {e}")
        return [], False


# === SLACK ===
def send_alert_to_slack(props):
    msg = f"*{props.get('event', 'Alert')}*\n{props.get('headline', '')}\n{props.get('description', '')}\nMore info: {props.get('id')}"
    r = requests.post(SLACK_WEBHOOK_URL, json={"text": msg})
    if r.status_code != 200:
        print(f"Slack error {r.status_code}: {r.text}")

# === MAIN ===
def main():
    overall_success = False
    parser = argparse.ArgumentParser(description="NWS Slack Alert Script")
    parser.add_argument("--config", required=True, help="Path to site config JSON")
    args = parser.parse_args()

    config = load_site_config(args.config)

    print(f"[{datetime.now(timezone.utc).isoformat()}] Checking alerts for {args.config}")

    areas = config["areas"]
    alert_expiry_hours = config.get("alert_expiry_hours", 12)
    slack_webhook_url = os.getenv(config["webhook_env_var"])
    if not slack_webhook_url:
        raise ValueError("Slack webhook environment variable not set")
    alert_type_file = config["alert_type_file"]
    alert_log_file = config["alert_log_file"]

    global ALERT_EXPIRY_HOURS
    ALERT_EXPIRY_HOURS = alert_expiry_hours

    global ALERT_TYPE_FILE
    ALERT_TYPE_FILE = alert_type_file

    global SLACK_WEBHOOK_URL
    SLACK_WEBHOOK_URL = slack_webhook_url

    alert_flags = load_alert_type_flags()
    log = load_alert_log(alert_log_file, alert_expiry_hours)
    alerts = []
    for area in areas:
        area_alerts, ok = fetch_alerts(area)

        if ok:
            any_fetch_success = True

        alerts.extend(area_alerts)

    for alert in alerts:
        props = alert.get("properties", {})
        aid = alert.get("id")
        event = props.get("event", "")

        if not alert_flags.get(event, False):
            continue
        if has_been_alerted(aid, log):
            continue

        exp = props.get("expires")
        if exp:
            et = datetime.fromisoformat(exp.replace("Z", "+00:00"))
            if et < datetime.now(timezone.utc):
                continue

        send_alert_to_slack(props)
        mark_alert_sent(aid, log)

    save_alert_log(log, alert_log_file)
    return any_fetch_success


if __name__ == "__main__":
    try:
        success = main()
        if success:
            exit(0)
        else:
            exit(2)  # ran but failed logically
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        exit(1)  # crashed
