# NWS Slack Alerts

A resilient multi-site **National Weather Service alert monitoring service** that posts selected alerts to Slack.

Designed for unattended operation on low-power systems such as **Raspberry Pi**, the system continuously monitors NWS alerts, filters them by configurable criteria, and sends notifications to Slack channels.

The service is designed to tolerate API interruptions, script failures, and restarts while preventing duplicate notifications.

---

# What This Project Solves

National Weather Service alerts are powerful but difficult to monitor programmatically across multiple locations without custom tooling.

This project provides a lightweight service that:

* Monitors multiple geographic areas
* Filters alerts by hazard type
* Sends actionable notifications to Slack
* Suppresses duplicate notifications
* Tracks alert lifecycle and **All Clear** events
* Operates reliably on small systems like Raspberry Pi

The result is a **hands-off alert monitoring system** that can run continuously with minimal maintenance.

---

# Features

* Multi-site monitoring using per-site configuration
* Alert filtering by event type
* Duplicate suppression across zones and restarts
* Active alert lifecycle tracking
* **All Clear** notifications when hazards expire
* Protection against false clears during API outages
* Independent Slack routing per site
* Operational monitoring channel for failures
* Detection of stalled or crashed scripts
* Automatic recovery notifications
* Designed for unattended Raspberry Pi deployment
* No database required (filesystem state tracking)

---

# Quick Install

Clone the repository and install dependencies:

```id="quick-install"
git clone https://github.com/Metspy/nws-slack-alerts.git
cd nws-slack-alerts
pip install -r requirements.txt
```

Create a `.env` file containing your [Slack webhook](https://docs.slack.dev/messaging/sending-messages-using-incoming-webhooks/) URLs.

Example:

```id="env-example"
SITEA_SLACK_WEBHOOK=https://hooks.slack.com/services/XXX/YYY/ZZZ
SITEB_SLACK_WEBHOOK=https://hooks.slack.com/services/XXX/YYY/ZZZ
SITEC_SLACK_WEBHOOK=https://hooks.slack.com/services/XXX/YYY/ZZZ
ALERTMON_SLACK_WEBHOOK=https://hooks.slack.com/services/XXX/YYY/ZZZ
```

Load the environment variables:

```id="env-load"
set -a
source .env
set +a
```

Run the script manually:

```id="run-manual"
python nws_alerts.py --config configs/SITEA.json
```

---

# Architecture Overview

The system polls the **NWS Alerts API** and processes alerts locally.

```id="architecture"
cron
 ├─ run_site.sh (per site)
 │      └─ nws_alerts.py
 │             ├─ query NWS API
 │             ├─ filter alerts by configured [UGC codes](https://www.weather.gov/media/documentation/docs/NWS_Geolocation.pdf)
 │             ├─ filter by enabled alert types
 │             ├─ detect new alerts
 │             ├─ detect expired alerts
 │             └─ send Slack notifications
 │
 ├─ monitor_health.sh
 │      └─ detects stalled scripts and reports failures
 │
 └─ cleanup_logs.sh
        └─ manages log size
```

---

# Project Structure

```id="project-structure"
nws-slack-alerts/
├── configs/            # Per-site configuration (Note 1)
│   ├── DST.json
│   ├── BNF.json
│   └── SGP.json
│
├── alert_types/        # Alert filtering configuration
│
├── state/              # Runtime alert state
│
├── logs/               # Runtime logs and heartbeat files
│
├── tools/              # Helper utilities
│   ├── expand_zone_to_county.py              # (Note 2)
│   └── daily_alert_summary.py
│
├── nws_alerts.py       # Main alert processor
├── run_site.sh
├── monitor_health.sh
├── cleanup_logs.sh
└── requirements.txt
```

Note 1: This repository is pre-populated with 3 `SITE.json` configuration files unique to areas of interest to the author. Feel free to use these configuration files to test your build.

Note 2: This project was first written to query NWS Public Forecast Zones ("Z codes") for Watches, Warnings and Advisory (WWA) products. In practice, many alerts are issued instead using a Universal Geographic Code (UGC) which is the NWS equivalent of the FIPS standard. This is formatted with a two letter state abbreviation, "C" for county, and the counties FIPS number. A list of all state FIPS codes can be found on the [US Census Bureau Website](https://www.census.gov/geographies/reference-files/2019/demo/popest/2019-fips.html). If you would like, or if you have already done so based on the previous release, you can build your SITE.json using the "Z codes" and use the `expand_zone_to_county.py` script to expand the configuration to include the "C codes". To do so, simply rename `SITE.json` to `SITE.json.Zcodes` and run `python tools/expand_zone_to_county.py configs/SITE.json.Zcodes`. Just be sure to remove `*.Zcodes` once you have confirmed your new configuration file. You can explore the NWS County and Zone borders using the NWS ArcGIS Online Map viewer linked on the [NWS Reference Map MapServer page](https://mapservices.weather.noaa.gov/static/rest/services/nws_reference_maps/nws_reference_map/MapServer) to help identify the codes that are right for your implementation. You can read more about NWS GIS products on the [NWS GIS Portal](https://www.weather.gov/gis).

---

# Configuring NWS Zones and Counties

The National Weather Service issues alerts using **UGC (Universal Geographic Code)** identifiers. (See footnote 2 in [Project Structure](#project-structure).) 

Examples:

```
OKZ029 → Forecast Zone
ALC033 → County
```

Alerts are sometimes issued for **zones**, but many warnings are issued only for **counties**.

To ensure alerts are not missed, this project supports monitoring **both zone and county codes**.

Helpful resources for locating UGC codes:

Forecast Zone Maps
https://www.weather.gov/gis/PublicZones

Zone–County Correlation File
https://www.weather.gov/gis/ZoneCounty

NWS GIS Viewer
https://viewer.weather.noaa.gov/

NWS Reference Maps
https://mapservices.weather.noaa.gov/static/rest/services/nws_reference_maps/nws_reference_map/MapServer

When you have identified all UGC identifiers you wish to track, for your `SITE`, build your `SITE.json` following this example:

```id="config-file"
configs/SITE.json
```

Example configuration:

```json id="site-json"
{
  "areas": [
    "ALC033",
    "ALC043",
    "ALC057",
    "ALC075",
    "ALC079",
    "ALC083",
    "ALC093",
    "ALC103",
    "ALC127",
    "ALC133",
    "ALZ002",
    "ALZ004",
    "ALZ005",
    "ALZ007",
    "ALZ011",
    "ALZ012",
    "ALZ013",
    "ALZ014",
    "ALZ015",
    "ALZ016",
    "MSC057",
    "MSC095",
    "MSC141",
    "MSZ006",
    "MSZ017",
    "MSZ024"
  ],
  "alert_expiry_hours": 12,
  "alert_type_file": "alert_types/SITE_alert_types.json",
  "alert_log_file": "state/SITE_alert_log.json",
  "webhook_env_var": "SITE_SLACK_WEBHOOK" # (Note 3)
}
```

Note 3: You must update your .env to include `SITE_SLACK_WEBHOOK` or your alerts will not know where to go and you will get the error "Slack webhook environment variable not set". See `.env.example` in [Quick Start](#quick-start). Don't forget to then reset your environment variables.

>**IMPORTANT: If you wish to contribute to this project, be sure to protect your Slack webhook links by assuring that they are only stored in .env and that .env is included in your .gitignore.**
---

## Tip: Expanding Zones to Counties

If you start with forecast zones, the helper script can automatically add the corresponding counties:

```id="zone-expand"
python tools/expand_zone_to_county.py configs/zcodes/DST.json
```

This produces a configuration that monitors both **zones and counties**, ensuring alerts issued using county UGC codes are detected. (Again, see footnote 2 in [Project Structure](#project-structure).)

---

# Alert Type Filtering

Alert types are controlled using JSON files in `alert_types/`. 

>NOTE: If you build a new configuration file in `configs/` `nws_alert.py` will build a new generic `SITE_alert_types.json` file in `alert_types/` with all flags set to `false`. 

Example:

```id="alert-types-file"
alert_types/SITE_alert_types.json
```

Example configuration:

```json id="alert-types-json"
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
  "Winter Storm Watch": false,
  "Blizzard Warning": true,
  "Ice Storm Warning": true,
  "Heat Advisory": false,
  "Excessive Heat Watch": false,
  "Extreme Heat Warning": true,
  "Extreme Heat Watch": true,
  "Air Quality Alert": false,
  "Red Flag Warning": false,
  "Dense Smoke Advisory": true,
  "Dust Storm Warning": true,
  "Extreme Wind Warning": true,
  "High Wind Warning": true,
  "High Wind Watch": false,
  "Snow Squall Warning": false,
  "Special Weather Statement": false,
  "Hazardous Weather Outlook": false,
  "Hurricane Watch": true,
  "Hurricane Warning": false,
  "Tropical Storm Watch": true,
  "Tropical Storm Warning": false,
  "Storm Surge Watch": false,
  "Storm Surge Warning": false,
  "Severe Weather Statement": false,
  "Coastal Flood Advisory": false,
  "Fire Weather Watch": false,
  "Child Abduction Emergency": false,
  "Civil Danger Warning": false,
  "Blue Alert": false
}
```

Only alerts marked **true** will trigger Slack notifications.

---

# Running Automatically (Cron)

To enable cron to properly parse the Slack webhooks stored in `.env`, a wrapper script, `run_site.sh` is employed which sets the variables before executing `nws_alerts.py`.

Example cron configuration:

```id="cron-example"
*/2 * * * * /path/nws-slack-alerts/run_site.sh SITEA
*/2 * * * * /path/nws-slack-alerts/run_site.sh SITEB
*/2 * * * * /path/nws-slack-alerts/run_site.sh SITEC
* * * * * /path/nws-slack-alerts/monitor_health.sh
```

Each site runs independently, and the health monitor reports failures only when a state change occurs. The above example runs each site every 2 minutes.

---

# Log Maintenance

Logs accumulate during long-term operation.

The included maintenance script trims logs and removes abandoned files:

```id="log-maintenance"
cleanup_logs.sh
```

Example cron:

```id="log-cron"
0 * * * * /path/nws-slack-alerts/cleanup_logs.sh
```
---

# Daily Alert Digest

The repository includes a diagnostic tool that produces a daily operational summary of alert activity across all configured sites.

```id="daily-summary-file"
tools/daily_alert_summary.py
```

This script compares alerts issued by the NWS against the alerts processed by the local monitoring system over the previous 24 hours.

The digest is useful for verifying that:

* All expected alerts were detected
* Alert filtering is working as intended
* No alerts were missed due to script errors or API outages

The script automatically reads all site configuration files in `configs/` and compares them against the local alert state files stored in `state/`.

---

For each site, the report includes four metrics:

| Metric | Description |
| ------ | ----------- |
| Issued | Number of NWS alerts issued in the last 24 hours that intersect the configured zones/counties |
| Sent | Alerts that were actually delivered to Slack |
| Filtered | Alerts intentionally suppressed by the alert type filter configuration |
| Missed | Alerts that intersected the monitored areas but were neither sent nor filtered |

The following relationship should normally hold: Issued = Sent + Filtered + Missed

A non-zero Missed value may indicate:

* A temporary NWS API outage
* A script runtime error
* A configuration problem
* A cron scheduling issue

---

Example Output:

```id="daily-summary-example"
🌤 NWS Alert Digest (last 24h)

SITE: SITEA
Issued: 21 | Sent: 8 | Filtered: 9 | Missed: 4
• Flood Warning (6)
• Severe Thunderstorm Watch (6)
• Special Weather Statement (9) (Filtered)

SITE: SITEB
Issued: 2 | Sent: 0 | Filtered: 2 | Missed: 0
• Special Weather Statement (1) (Filtered)
• Wind Advisory (1) (Filtered)
```

Alerts are grouped by type and show how many times each alert product was issued.

---

Running the Digest Manually:

```id="daily-summary-run-example"
python tools/daily_alert_summary.py
```

The script will:
1. Query the NWS Alerts API
2. Identify alerts intersecting configured zones/counties
3. Compare them with locally recorded alert history
4. Generate a reconciliation summary

The summary is printed to the console and sent to the OPS Slack webhook (if configured).

---

Running the Digest Automatically

You may schedule the digest to run once per day using cron. A wrapper script `run_daily_summary.sh` is included in the repo and acts simlilarly to `run_site.sh` by setting the variables in `.env` prior to execution.

Example:

```id="daily-summary-cron"
0 12 * * * /bin/bash /your/path/to/nws-slack-alerts/run_daily_summary.sh
```

This example runs the digest daily at 12:00 UTC daily.

The report will be posted to the OPS monitoring Slack channel (or a Slack channel of your choice; simply edit `OPS_WEBHOOK_ENV = "OPS_SLACK_WEBHOOK"` in `daily_alert_summary.py` to point to the `ALERTMON_SLACK_WEBHOOK` variable you have defined in your `.env`.

---

Note: The digest uses the NWS Alerts API and **may not return alerts that have aged out of the API window.** Alert counts represent alert products issued, not unique hazards. NWS frequently updates active alerts, which can increase the count during severe weather events. The digest is intended as an operational health check rather than a permanent historical archive.

---

# Failure Modes

This system detects:

* Python crashes
* API failures
* stalled execution

This system **cannot detect**:

* complete power loss
* network outage on the host

External uptime monitoring is recommended for full availability monitoring.

---

# Troubleshooting

### No alerts appearing

* Verify alert types are enabled
* Confirm environment variables are loaded
* Run the script manually and inspect logs

### Duplicate alerts

Delete the alert history file once:

```
state/SITE_alert_log.json
```

### Unexpected All Clears

Check logs for:

```
All NWS fetches failed
```

The system suppresses clears during full API outages.

---

# Author

Mark Garling Spychala

This project was developed for professional exploration of the **NWS Alerts API** and Slack integrations.
