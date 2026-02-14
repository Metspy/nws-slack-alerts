# NWS Slack Alerts

Multi-site National Weather Service (NWS) alert monitoring with Slack notifications.

This project queries the NWS API for active alerts across configured zones and posts selected alert types to Slack using incoming webhooks.

Designed for deployment across multiple environments using site-specific configurations.

---

## Features
- Target areas are set by NWS location zones (See a GIS map [here](https://geospatial-nws-noaa.opendata.arcgis.com/datasets/noaas-national-weather-service-public-forecast-zones/explore) or search all zones [here](https://alerts.weather.gov/))
- Filters alerts by type (configurable in `AREA_alert_types.json`)
- Avoids repeat notifications with ID tracking
- Filters out expired alerts
- Runs unattended via `cron`
- Sends messages directly to Slack using environment-based webhook management

## Architecture Overview

- NWS API provides active alert data via REST.
- Site-specific config defines zones and filtering behavior.
- Alert types are toggled in a generated JSON file.
- Slack notifications are sent via incoming webhooks.
- Alert IDs are logged locally to prevent duplicate notifications.

## Project Structure

```
nws-slack-alerts/
├── configs/
│   ├── DST.json
│   ├── BNF.json
│   ├── SGP.json
│   ├── DST_alert_types.json      # created on first run; toggle desired alerts true/false
│   └── DST_alert_log.json        # created on first run; tracks previously sent alerts
├── nws_alerts.py
├── cron.log     # Optional log of cron job output
├── .env.example
├── requirements.txt
└── README.md      # you're reading this
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
Adjust true/false as needed.

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

Create a `.env` file with each AREA_SLACK_WEBHOOK. See details about using incoming webhooks in slack at [docs.slack.dev](https://docs.slack.dev/messaging/sending-messages-using-incoming-webhooks/)

Example `.env`:

```bash
DST_SLACK_WEBHOOK=https://hooks.slack.com/services/XXXXX/YYYYY/ZZZZZ
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

We can use a small wrapper script to be sure the `.env` variables are gathered each time this runs on cron.

Example (`run_dst.sh`):

```bash
#!/bin/bash
cd /path/to/nws-slack-alerts
set -a
source .env
set +a
/usr/bin/python3 nws_alerts.py --config configs/DST.json
```

Then use `crontab -e` to add a job like:

```bash
* * * * * /path/to/run_dst.sh >> /path/to/nws-slack-alerts/cron.log 2>&1
```

>**NOTE: you may need to adjust the path to Python. To check, run:**
>
>```bash
>which python3
>```

This checks for alerts every minute.

## Notes

- The script uses timezone-aware datetimes (UTC).
- Alert history is tracked in `AREA_alert_log.json`. This is auto-managed.
- Slack messages are sent **only** for alert types marked `true` in the config.

## Author

Mark Garling Spychala  
*This is a personal project for professional development using NWS and Slack APIs.*
