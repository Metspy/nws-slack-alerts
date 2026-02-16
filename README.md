# NWS Slack Alerts

This project is a resilient multi-site National Weather Service alert monitoring service that posts selected alerts to Slack.
Each monitored site runs independently with duplicate alert suppression, state tracking, and automated failure detection/recovery notifications designed for unattended operation on low-power systems (e.g., Raspberry Pi).

---

## Features
- Multi-site monitoring using per-site configuration files
- Filters alerts by type (configurable per site)
- Duplicate suppression using alert ID tracking
- Expiration filtering
- Independent Slack routing per site
- Operational monitoring channel for failures
- Detects stalled or crashed scripts
- Sends recovery notifications when service resumes
- Designed for unattended Raspberry Pi deployment
- No database required (filesystem state tracking)


## Architecture Overview

- NWS API provides active alert data via REST.
- Site-specific config defines zones and filtering behavior.
- Alert types are toggled in a generated JSON file.
- Slack notifications are sent via incoming webhooks.
- Alert IDs are logged locally to prevent duplicate notifications.

## Process

Every 2 minutes (per site):
`run_site.sh`
    → queries NWS API
    → filters alerts
    → sends Slack messages (as needed)
    → updates logs
    → updates heartbeat

Every 1 minute:
monitor_health.sh
    → checks heartbeats
    → sends OPS alert only on state change


## Health Monitoring

Each site maintains a heartbeat file: `logs/AREA.last_success`. Every successful run updates this timestamp.

The monitor checks:
    current_time - last_success > threshold

If exceeded → failure alert sent to OPS channel  
If service resumes → recovery alert sent

This prevents alert spam while still notifying operators of outages.


## Project Structure

```
nws-slack-alerts/
├── configs/                # Per-site alert configuration
│   ├── DST.json
│   ├── BNF.json
│   └── SGP.json
├── logs/                   # Runtime state (auto-generated)
│   ├── *.log
│   ├── *.state
│   └── *.last_success
├── nws_alerts.py           # Main alert processor
├── run_site.sh             # Runs one site 
├── cleanup_logs.sh         # Pares down log volume via cron
├── requirements.txt.       # Quick reference of requirements   
└── monitor_health.sh       # Detects crashes/stalls and alerts Slack
```

## Setup Instructions

### 1. Clone the repository

```bash
git clone git@github.com:Metspy/nws-slack-alerts.git
cd nws-slack-alerts
```

### 2. Install Requirements

```bash
pip install -r requirements.txt
```

### 3. Configuration

#### `AREA.json` - Each site has its own config file in `configs/`. Set areas according to note in [Features](#features). Ensure `webhook_env_var` matches an environment variable defined in your `.env` file (e.g., `"DST_SLACK_WEBHOOK"`).

Example (`configs/DST.json`):

```json
{
  "areas": [
    "AZZ534",
    "AZZ537",
    "AZZ538",
    "AZZ539",
    "AZZ540",
    "AZZ541",
    "AZZ542",
    "AZZ543",
    "AZZ544",
    "AZZ546",
    "AZZ548",
    "AZZ549",
    "AZZ551"
  ],
  "alert_expiry_hours": 12,
  "alert_type_file": "configs/DST_alert_types.json",
  "alert_log_file": "configs/DST_alert_log.json",
  "webhook_env_var": "DST_SLACK_WEBHOOK"
}
```

#### `AREA_alert_types.json` - Toggle alerts on or off:

This file is automatically created on first run if it does not exist.

>**NOTE: The first run enables all alert types as `false` by default.**
>**You must edit this file to enable the alerts you care about.**

```json
{
  "Flash Flood Warning": true,
  "Flash Flood Watch": false,
  "Flood Warning": true,
  "Flood Watch": false,
  "Tornado Warning": true,
  "Tornado Watch": true,
  "Severe Thunderstorm Warning": true,
  "Severe Thunderstorm Watch": true,
  "Winter Storm Warning": true,
  "Winter Storm Watch": true,
  "Blizzard Warning": true,
  "Ice Storm Warning": true,
  "Heat Advisory": true,
  "Excessive Heat Watch": false,
  "Extreme Heat Warning": true,
  "Extreme Heat Watch": true,
  "Air Quality Alert": true,
  "Red Flag Warning": true,
  "Dense Smoke Advisory": true,
  "Dust Storm Warning": true,
  "Extreme Wind Warning": true,
  "High Wind Warning": true,
  "High Wind Watch": false,
  "Snow Squall Warning": true,
  "Special Weather Statement": true,
  "Hazardous Weather Outlook": true,
  "Hurricane Watch": false,
  "Hurricane Warning": false,
  "Tropical Storm Watch": false,
  "Tropical Storm Warning": false,
  "Storm Surge Watch": false,
  "Storm Surge Warning": false,
  "Severe Weather Statement": true,
  "Coastal Flood Advisory": false,
  "Fire Weather Watch": true,
  "Child Abduction Emergency": true,
  "Civil Danger Warning": true,
  "Blue Alert": false
}
```

#### Environment Variables

Create a `.env` file with each AREA_SLACK_WEBHOOK. These webhooks are used to send messages to your desired slack channel. Be careful not to share your webhook! This should be stored in `.env` only. Double check that `.env` is included in `.gitignore`. 

Two webhook types are used:

SITE WEBHOOKS
    Used for sending weather alerts to users

OPS WEBHOOK
    Used only for system monitoring (failures and recovery)

This separation prevents operational noise from reaching end users.


>**NOTE: If the system running the cron jobs fails or loses connectivity, no slack notification can be sent without outside heartbeat monitoring services.**
>Failures such as these are documented in the site logs in `/logs`. See [Failure Modes](#failure-modes)

See details about using incoming webhooks in slack at [docs.slack.dev](https://docs.slack.dev/messaging/sending-messages-using-incoming-webhooks/)

Example `.env`:

```bash
DST_SLACK_WEBHOOK=https://hooks.slack.com/services/XXX/YYY/ZZZ
BNF_SLACK_WEBHOOK=https://hooks.slack.com/services/XXX/YYY/ZZZ
SGP_SLACK_WEBHOOK=https://hooks.slack.com/services/XXX/YYY/ZZZ
OPS_SLACK_WEBHOOK=https://hooks.slack.com/services/XXX/YYY/ZZZ
```

Load it:

```bash
set -a
source .env
set +a
```

### 4. Run It Manually

```bash
python nws_alerts.py --config configs/AREA.json
```
Replace AREA with your desired site, (e.g., `DST.json`)

The script will:

1. Query the NWS API for active alerts in the configured zones
2. Filter alerts based on enabled alert types
3. Post qualifying alerts to Slack
4. Log alert IDs to prevent duplicate notifications

### 5. Run It Automatically with Cron

Each site runs independently and a health monitor checks for failures.

Example crontab:

```bash
*/2 * * * * /your/path/to/nws-slack-alerts/run_site.sh DST
*/2 * * * * /your/path/to/nws-slack-alerts/run_site.sh BNF
*/2 * * * * /your/path/to/nws-slack-alerts/run_site.sh SGP
* * * * * /your/path/to/nws-slack-alerts/monitor_health.sh
```

The monitor sends alerts only when a state change occurs:
- OK → FAIL (stalled or crashed)
- FAIL → OK (recovered)

Running every 2 minutes is safe because duplicate alerts are suppressed.
The NWS API typically updates alerts on minute-scale intervals.
Running faster increases API load without improving alert latency.

>**NOTE: you may need to adjust the path to Python. To check, run:**
>
>```bash
>which python3
>```

## Log Maintenance

The system stores runtime state in the logs/ directory. These files grow indefinitely during long-term unattended operation and could potentially balloon quickly in the event of API failure. The included maintenance script, `cleanup_logs.sh` truncates each log to the most recent 200 lines and removes abandoned logs older than 7 days while retaining alert history, state tracking files and configuration JSONs. 

Recommended cron entry (run every hour):

```bash
0 * * * * /your/path/to/nws-slack-alerts/cleanup_logs.sh
```

## Notes

- The script uses timezone-aware datetimes (UTC).
- Alert history is tracked in `AREA_alert_log.json`. This is auto-managed.
- Slack messages are sent **only** for alert types marked `true` in the config.

## Failure Modes

This system detects:
- Python crashes
- API failures
- Stalled execution

**This system cannot detect:**
- Complete power loss
- Network outage on the host machine

External uptime monitoring is required for full availability monitoring.

## Troubleshooting

**No alerts appearing**
- Verify alert types are enabled in `AREA_alert_types.json`
- Run script manually and check output
- Confirm webhook environment variables are loaded

**Receiving duplicate alerts**
- Delete `AREA_alert_log.json` once (resets history)

**Monitor reports stalled**
- Confirm cron is running
- Check `logs/AREA.log`
- Verify last_success timestamp updates

**No failure notifications**
- OPS_SLACK_WEBHOOK not configured


## Author

Mark Garling Spychala  
*This is a personal project for professional development using NWS and Slack APIs.*
