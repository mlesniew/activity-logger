import sys

import numpy as np
import pandas as pd

ACTIVITY_PATTERNS = {
    "chat": "^microsoft teams - preview.Microsoft Teams - Preview",
    "confluence": "^Navigator.Firefox.*- Confluence — Mozilla Firefox$",
    "gitlab": "^Navigator.Firefox.*· GitLab — Mozilla Firefox$",
    "jira": "^Navigator.Firefox.*- JIRA — Mozilla Firefox$",
    "terminal": "^xfce4-terminal.Xfce4-terminal",
    "outlook": "^Navigator.Firefox.*Outlook — Mozilla Firefox$",
}
ACTIVITY_NAMES = ["break", "meeting"] + list(ACTIVITY_PATTERNS) + ["other"]

data = pd.read_csv(
    sys.stdin,
    delimiter="\t",
    header=0,
    names=[
        "timestamp",
        "idletime",
        "teams",
        "spotify",
        "wifi_ssid",
        "eth_ip",
        "wifi_ip",
        "vpn_ip",
        "active_window",
    ],
    parse_dates=["timestamp"],
    index_col=0,
)

data.index = data.index.tz_localize("UTC")

# convert idletime to timedelta
data["idletime"] = pd.to_timedelta(data["idletime"], "s")

# calculate time step between rows
data["timedelta"] = data.index.to_frame().diff(1) / pd.Timedelta(1, "s")

# only consider these entries in statistics
data["valid"] = (data["timedelta"] <= 60) & (~data["timedelta"].isnull())

# drop invalid records
data = data.loc[data["valid"]]

# ...and the valid column itself
del data["valid"]

# convert to local time
data.index = data.index.tz_convert("CET")

# make timestamps naive again
data.index = data.index.tz_localize(None)

# drop all data before 2021-03-01
data = data.loc[data.index >= np.datetime64("2021-03-01")]

# I was working if I was in a meeting OR teams was running or VPN was connected
vpn_connected = (data["vpn_ip"] != "NON-IP") & (data["vpn_ip"] != "") & ~data["vpn_ip"].isnull()
krakow_network = (data["wifi_ssid"] == "CAMLIN-KRK") | data["eth_ip"].str.startswith("10.7.")

working = (
    (data["teams"] != "stopped") & vpn_connected
    | krakow_network
)

# only keep rows when working
data = data.loc[working]

result = pd.DataFrame()

# was I in a meeting?
result["meeting"] = data["teams"] == "meeting"

# When idle time was above 3 minutes during working time and I was not in a meeting, then I was in a break
result["break"] = working & (data["idletime"] > pd.Timedelta(3, "m"))

# detect remaining activities based on active window
for name, pattern in ACTIVITY_PATTERNS.items():
    result[name] = data["active_window"].str.match(pattern)

# break overrides other activities except for meeting
for name in ACTIVITY_NAMES:
    if name not in {"break", "meeting", "other"}:
        result[name] = result[name] & ~result["break"]

# meeting overrides all other activities
for name in ACTIVITY_NAMES:
    if name not in {"meeting", "other"}:
        result[name] = result[name] & ~result["meeting"]

# select other if working and no other activity flag set
result["other"] = working
for name in ACTIVITY_NAMES:
    if name != "other":
        result["other"] = result["other"] & ~result[name]

result.insert(0, "timedelta", data["timedelta"])

result.to_csv(sys.stdout)
