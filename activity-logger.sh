#!/usr/bin/env bash

teams_status() {
    if [ "$(pgrep -cfl '^/usr/share/teams/teams')" = 0 ]
    then
        echo "stopped"
    else
        if pactl list source-outputs | tr '\n' '|' | sed -E 's#[|][\t ]+#;#g' | tr '|' '\n' | grep -iF skype | grep -qF 'Corked: no;'
        then
            echo "meeting"
        else
            echo "running"
        fi
    fi
}

get_active_window() {
    ACTIVE_WINDOW_ID=$(printf '0x%08x\n' "$(xdotool getwindowfocus)")
    wmctrl -x -l | grep "^${ACTIVE_WINDOW_ID}" | head -n1 | cut -c15- | tr '\t' ' '
}

spotify_status() {
    {
        STATUS=$(dbus-send --print-reply --dest=org.mpris.MediaPlayer2.spotify /org/mpris/MediaPlayer2 org.freedesktop.DBus.Properties.Get string:'org.mpris.MediaPlayer2.Player' string:'PlaybackStatus'|grep 'string "[^"]*"'|sed 's/.*"\(.*\)"[^"]*$/\1/' | tr '[:upper:]' '[:lower:]')
        if [ -z "$STATUS" ]
        then
            echo "stopped"
        else
            echo "$STATUS"
        fi
    } 2>/dev/null
}

wifi_ssid() {
    nmcli -t -f active,ssid dev wifi | grep '^yes:' | cut -d: -f2- | head -n1
}

{
    while true;
    do
        # time, idle time, teams status, tun0 address, active window
        printf "$(date -u --iso=seconds | cut -d+ -f1)\t$(xprintidle)\t$(teams_status)\t$(spotify_status)\t$(wifi_ssid)\t$(ifdata -pa enp0s25)\t$(ifdata -pa wlo1)\t$(ifdata -pa tun0)\t$(get_active_window)\n"
        sleep 10
    done;
} >> ~/.activity.log
