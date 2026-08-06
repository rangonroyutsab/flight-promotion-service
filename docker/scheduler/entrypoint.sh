#!/bin/sh
set -e

# Load cron tab
crontab /app/docker/scheduler/crontab

# Start cron daemon in foreground
echo "Starting cron..."
exec cron -f
