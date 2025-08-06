import requests
import json
from datetime import datetime, timedelta, timezone
import os

# === CONFIG ===
BASE_DIR = "/Users/USERNAME/path/to/script" # Update!
ALERT_LOG_FILE = os.path.join(BASE_DIR, "alert_log.json")
ALERT_TYPE_FILE = os.path.join(BASE_DIR, "alert_config.json")
ALERT_EXPIRY_HOURS = 12
AREA = "INZ002"  # NWS Zone Code; see https://alerts.weather.gov/ and search land areas with codes
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/YOURUNIQUESLACKWEBHOOKURL"

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
        "Extreme Heart Watch": False,
        "Air Quality Alert": False,
        "Red Flag Warning": False,
        "Dense Smoke Advisory": False,
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
def load_alert_log(filename=ALERT_LOG_FILE):
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
            if now - t < timedelta(hours=ALERT_EXPIRY_HOURS):
                valid[aid] = ts
        except ValueError:
            continue
    return valid

def save_alert_log(log, filename=ALERT_LOG_FILE):
    with open(filename, "w") as f:
        json.dump(log, f, indent=2)

def has_been_alerted(aid, log):
    return aid in log

def mark_alert_sent(aid, log):
    log[aid] = datetime.now(timezone.utc).isoformat()

# === FETCH ALERTS ===
def fetch_alerts(area_code):
    url = f"https://api.weather.gov/alerts/active?zone={area_code}"
    response = requests.get(url, headers={"User-Agent": "weather-alert-script"})
    if response.status_code == 200:
        return response.json().get("features", [])
    print(f"Error fetching alerts: HTTP {response.status_code}")
    return []

# === SLACK ===
def send_alert_to_slack(props):
    msg = f"*{props.get('event', 'Alert')}*\n{props.get('headline', '')}\n{props.get('description', '')}\nMore info: {props.get('id')}"
    r = requests.post(SLACK_WEBHOOK_URL, json={"text": msg})
    if r.status_code != 200:
        print(f"Slack error {r.status_code}: {r.text}")

# === MAIN ===
def main():
    alert_flags = load_alert_type_flags()
    log = load_alert_log()
    alerts = fetch_alerts(AREA) or []
    # print(f"[{datetime.now(timezone.utc).isoformat()}] Cron job running.") #crontab debug
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
    save_alert_log(log)

if __name__ == "__main__":
    main()
