#!/usr/bin/env bash

{
    while true;
    do
        echo '========='
        echo "time: $(date -u --iso=seconds | cut -d+ -f1)"
        echo "active_window: $(xdotool getwindowfocus)"
        echo "idle_time: $(xprintidle)"
        if pactl list source-outputs | tr '\n' '|' | sed -E 's#[|][\t ]+#;#g' | tr '|' '\n' | grep -iF skype | grep -qF 'Corked: no;'
        then
            echo "teams_meeting: 1"
        else
            echo "teams_meeting: 0"
        fi
        echo "tun0_address: $(ifdata -pa tun0)"
        echo 'windows:'
        wmctrl -x -l
        sleep 10
    done;
} >> ~/.activity.log
