#!/usr/bin/env bash

cd "$(dirname "$0")"

export PYTHONUNBUFFERED=1

run-one-constantly ./activity-logger.py > ~/.activity.log
