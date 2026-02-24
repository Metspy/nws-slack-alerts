#raise RuntimeError("intentional test failure")
import requests
import argparse
import json
from datetime import datetime, timedelta, timezone
import os
import sys
import traceback

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

def has_been_alerted(aid, expires_iso, log):
    """
    Returns True only if we already alerted for THIS version
    of the alert (same ID AND same expiration time)
    """
    if aid not in log:
        return False
    return log[aid] == expires_iso

def mark_alert_sent(aid, expires_iso, log):
    log[aid] = expires_iso

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

# === Alert ID Builder (Stable across zones) ===
def build_alert_key(props):
    """
    Build a stable identifier for an NWS alert.
    This remains contant across zones and API polls.
    """
    return "|".join([
        props.get("event",""),
        props.get("onset",""),
        props.get("expires",""),
        props.get("senderName",""),
        props.get("headline","")
    ])

# === SLACK ===
def send_alert_to_slack(props):
    event = props.get("event", "Alert")
    area = props.get("areaDesc", "Unknown location")
    headline = props.get("headline", "")

    severity = props.get("severity","")
    certainty = props.get("certainty","")
    urgency = props.get("urgency","")

    triage = f"Severity: {severity} | Certainty: {certainty} | Urgency: {urgency}"

    web_url = props.get("web","")
    if web_url:
        more_info = f"<{web_url}|View official NWS alert>"
    else:
        more_info = ""

    msg = (
        f"*{event}*\n"
        f"{area}\n\n"
        f"{triage}\n\n"
        f"{headline}\n"
        f"{description}\n\n"
        f"{more_info}"
    )
    r = requests.post(SLACK_WEBHOOK_URL, json={"text": msg})
    if r.status_code != 200:
        print(f"Slack error {r.status_code}: {r.text}")

# === MAIN ===
def main():
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
    ACTIVE_STATE_FILE = alert_log_file + ".active"

    global ALERT_EXPIRY_HOURS, ALERT_TYPE_FILE, SLACK_WEBHOOK_URL
    ALERT_EXPIRY_HOURS = alert_expiry_hours
    ALERT_TYPE_FILE = alert_type_file
    SLACK_WEBHOOK_URL = slack_webhook_url

    alert_flags = load_alert_type_flags()
    log = load_alert_log(alert_log_file, alert_expiry_hours)

    # --- load previously active alerts ---
    if os.path.exists(ACTIVE_STATE_FILE):
        with open(ACTIVE_STATE_FILE, "r") as f:
            previous_active = json.load(f)
    else:
        previous_active = {}

    current_active = {}
    alerts = []
    any_fetch_success = False

    for area in areas:
        area_alerts, ok = fetch_alerts(area)
        if ok:
            any_fetch_success = True
        alerts.extend (area_alerts)

    # if API failed completely, abort run without changing state
    if not any_fetch_success:
        print("WARNING: All NWS fetches failed - preserving previous state")
        return True

    # --- process alerts ---
    for alert in alerts:
        props = alert.get("properties", {})
        aid = build_alert_key(props)
        event = props.get("event", "")

        if not alert_flags.get(event, False):
            continue

        # --- expiration handling ---
        exp = props.get("expires")
        if not exp:
            continue

        exp_iso = exp.replace("Z", "+00:00")
        et = datetime.fromisoformat(exp_iso)
        # skip expired alerts
        if et < datetime.now(timezone.utc):
            continue

        # strack active alert
        current_active[aid] = {
            "event": props.get("event","Unknown Alert"),
            "sender": props.get("senderName", "NWS"),
            "expires": exp_iso,
            "headline": props.get("headline","")
        }

        # send alert if new
        if not has_been_alerted(aid, exp_iso, log):
            send_alert_to_slack(props)
            mark_alert_sent(aid, exp_iso, log)

    # --- all clear detection ---
    ended_alerts = set(previous_active.keys()) - set(current_active.keys())

    for aid in ended_alerts:
        info = previous_active.get(aid, {})
        msg = (
            f":white_check_mark: *All clear - {info.get('event','Alert')}*\n"
            f"{info.get('headline','')}\n"
            f"Issued by: {info.get('sender','NWS')}\n"
            f"Expired: {info.get('expires','')}"
        )
        requests.post(SLACK_WEBHOOK_URL, json={"text":msg})

    # Save current active alerts
    save_alert_log(log, alert_log_file)
    with open(ACTIVE_STATE_FILE, "w") as f:
        json.dump(current_active, f, indent=2)


    return True


if __name__ == "__main__":
    try:
        main()
        print("STATUS: normal completion")
        sys.exit(0)
    except KeyboardInterrupt:
        print("Status: interrupted")
        sys.exit(0)
    except Exception:
        print("STATUS: runtime error but service still alive")
        traceback.print_exc()
        sys.exit(0)
