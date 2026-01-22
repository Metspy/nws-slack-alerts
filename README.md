# NWS Alerts to Slack

This script checks for active National Weather Service (NWS) alerts for a given area and sends notifications to a Slack channel when alerts of interest are issued.

## Features
- Target area is set by NWS location zones (See a GIS map [here](https://geospatial-nws-noaa.opendata.arcgis.com/datasets/noaas-national-weather-service-public-forecast-zones/explore) or search all zones [here](https://alerts.weather.gov/))
- Filters alerts by type (configurable in `alert_config.json`)
- Avoids repeat notifications with ID tracking
- Filters out expired alerts
- Runs unattended via `cron`
- Sends messages directly to Slack

##  Project Structure

```
nws-alerts-slack/
├── nws_alert.py # Main script
├── alert_config.json # Which alerts to include (toggle on/off)
├── alert_log.json # Tracks previously sent alert IDs (auto-generated)
├── cron.log # Optional log of cron job output
├── .gitignore # Ignore log and state files
└── README.md # You're reading this
```

## Setup Instructions

### 1. Install Requirements

```bash
pip install requests
```

### 2. Edit Configuration

#### `alert_config.json` - Toggle alerts on or off:

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
  "Extreme Heart Watch": true,
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

#### Inside `nws_alert.py`, configure:

- `AREA` - your NWS zone code (See note in [Features](#Features))
- `SLACK_WEBHOOK_URL` - your Slack Incoming Webhook URL. (See details at [docs.slack.dev](https://docs.slack.dev/messaging/sending-messages-using-incoming-webhooks/))

### 3. Run It Manually

```bash
python3 nws_alert.py
```

### 4. Run It Automatically with Cron

Use `crontab -e` to add a job like:

```bash
* * * * * /usr/bin/python3 /Users/yourusername/path/to/nws_alert.py >> /Users/yourusername/path/to/cron.log 2>&1
```

>**NOTE: you may need to adjust the path to Python. To check, run:**
>
>```bash
>which python3
>```

This checks for alerts every minute.

## Notes

- The script uses timezone-aware datetimes (UTC).
- Alert history is tracked in `alert_log.json`. This is auto-managed.
- Slack messages are sent **only** for alert types marked `true` in the config.

## Author

Mark Garling Spychala  
*This is a personal project for professional development using NWS and Slack APIs.*
