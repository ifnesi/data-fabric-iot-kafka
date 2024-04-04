#!/bin/bash

echo ""
echo "Killing processes..."
ps aux  |  grep -i  ' iot_'  |  awk '{print $2}'  |  xargs kill -9 >/dev/null 2>&1 &
ps aux  |  grep -i  ' coap_server.py'  |  awk '{print $2}'  |  xargs kill -9 >/dev/null 2>&1 &

echo ""
echo "Stopping docker compose..."
docker compose down

echo ""
echo "Cleaning up old data files..."
find coap-data/finished/telemetry* -ctime +1 -type d  -exec rm -rf {} \;
echo ""
