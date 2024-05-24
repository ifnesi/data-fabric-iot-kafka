#!/bin/bash

function logging() {
  TIMESTAMP=`date "+%Y-%m-%d %H:%M:%S.000"`
  LEVEL=${2-"INFO"}
  if [[ $3 == "-n" ]]; then
    echo -n "[stop] $TIMESTAMP [$LEVEL]: $1"
  else
    echo "[stop] $TIMESTAMP [$LEVEL]: $1"
  fi
}

echo ""
logging "Killing processes"
ps aux  |  grep -i  ' iot_'  |  awk '{print $2}'  |  xargs kill -9 >/dev/null 2>&1 &
ps aux  |  grep -i  ' coap_server.py'  |  awk '{print $2}'  |  xargs kill -9 >/dev/null 2>&1 &
ps aux  |  grep -i  ' ksqldb_provisioning.py'  |  awk '{print $2}'  |  xargs kill -9 >/dev/null 2>&1 &
ps aux  |  grep -i  ' elastic_geopoint.py'  |  awk '{print $2}'  |  xargs kill -9 >/dev/null 2>&1 &

logging "Cleaning up old data files"
rm -rf coap-data/finished/telemetry*

logging "Stopping docker compose"
if docker compose down ; then
    kill -9 $(ps aux | grep 'pycrm:app' | awk '{print $2}') >/dev/null 2>&1
    logging "Demo successfully stopped"
    echo ""
    exit 0
else
    logging "Please start Docker Desktop!" "ERROR"
    echo ""
    exit -1
fi