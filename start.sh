#!/bin/bash

function logging() {
  TIMESTAMP=`date "+%Y-%m-%d %H:%M:%S.000"`
  LEVEL=${2-"INFO"}
  if [[ $3 == "-n" ]]; then
    echo -n "[start] $TIMESTAMP [$LEVEL]: $1"
  else
    echo "[start] $TIMESTAMP [$LEVEL]: $1"
  fi
}

echo ""
logging "Killing processes"
ps aux  |  grep -i  ' iot_'  |  awk '{print $2}'  |  xargs kill -9 >/dev/null 2>&1 &
ps aux  |  grep -i  ' coap_server.py'  |  awk '{print $2}'  |  xargs kill -9 >/dev/null 2>&1 &
ps aux  |  grep -i  ' ksqldb_provisioning.py'  |  awk '{print $2}'  |  xargs kill -9 >/dev/null 2>&1 &
ps aux  |  grep -i  ' elastic_geopoint.py'  |  awk '{print $2}'  |  xargs kill -9 >/dev/null 2>&1 &

logging "Loading environment variables"
source .env

logging "Starting docker compose"
if ! docker compose up -d --build ; then
    logging "Please start Docker Desktop!" "ERROR"
    exit -1
fi

# Waiting services to be ready
logging "Waiting Schema Registry to be ready" "INFO" -n
while [[ "$(curl -s -o /dev/null -w ''%{http_code}'' http://localhost:8081)" != "200" ]]
do
    echo -n "."
    sleep 1
done

echo ""
logging "Waiting ksqlDB Cluster to be ready" "INFO" -n
while [[ "$(curl -s -o /dev/null -w ''%{http_code}'' http://localhost:8088/info)" != "200" ]]
do
    echo -n "."
    sleep 1
done

echo ""
logging "Waiting Connect Cluster #1 to be ready" "INFO" -n
while [[ "$(curl -s -o /dev/null -w ''%{http_code}'' http://localhost:8083)" != "200" ]]
do
    echo -n "."
    sleep 1
done

echo ""
logging "Waiting Connect Cluster #2 to be ready" "INFO" -n
while [[ "$(curl -s -o /dev/null -w ''%{http_code}'' http://localhost:18083)" != "200" ]]
do
    echo -n "."
    sleep 1
done

echo ""
logging "Waiting Confluent Control Center to be ready" "INFO" -n
while [[ "$(curl -s -o /dev/null -w ''%{http_code}'' http://localhost:9021)" != "200" ]]
do
    echo -n "."
    sleep 1
done

echo ""
logging "Activating Virtual Environment / installing Python requirements"
source .venv/bin/activate
pip install -r requirements.txt
sleep 1

# Kafka IoT Device
logging "Starting Kafka IoT device"
python3 iot_kafka.py > ./logs/iot_kafka.log 2>&1 &

# HTTP IoT Device
logging "Starting HTTP IoT device"
python3 iot_http.py > ./logs/iot_http.log 2>&1 &

# SysLog Connector
logging "Starting Syslog Connector"
curl -i -X PUT http://localhost:8083/connectors/syslog_source/config \
     -H "Content-Type: application/json" \
     -d '{
            "connector.class": "io.confluent.connect.syslog.SyslogSourceConnector",
            "syslog.port": 1514,
            "syslog.listener": "TCP",
            "syslog.listen.address": "0.0.0.0",
            "topic": "data-fabric-syslog-devices",
            "syslog.queue.batch.size": 100,
            "syslog.queue.max.size": 100,
            "syslog.write.timeout.millis": 10000,
            "tasks.max": "1"
        }'
sleep 5
echo ""
curl -s http://localhost:8083/connectors/syslog_source/status | jq .
sleep 1

echo ""
logging "Starting SysLog IoT device"
python3 iot_syslog.py > ./logs/iot_syslog.log 2>&1 &

# Spooldir Connector / Iot Device
logging "Starting Spooldir Connector"
curl -i -X PUT http://localhost:18083/connectors/spooldir_source/config \
     -H "Content-Type: application/json" \
     -d '{
            "connector.class": "com.github.jcustenborder.kafka.connect.spooldir.SpoolDirSchemaLessJsonSourceConnector",
            "tasks.max": "1",
            "key.converter": "org.apache.kafka.connect.storage.StringConverter",
            "value.converter": "org.apache.kafka.connect.storage.StringConverter",
            "topic": "data-fabric-coap-devices",
            "input.path": "/tmp/coap-data",
            "finished.path": "/tmp/coap-data/finished",
            "error.path": "/tmp/coap-data/error",
            "input.file.pattern": "telemetry.[0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{2}-[0-9]{2}-[0-9]{2}",
            "halt.on.error": "false"
        }'
sleep 5
echo ""
curl -s http://localhost:18083/connectors/spooldir_source/status | jq .
sleep 1

echo ""
logging "Starting CoAP Server"
python3 coap_server.py > ./logs/coap_server.log 2>&1 &
sleep 2

logging "Starting CoAP IoT device"
python3 iot_coap.py > ./logs/iot_coap.log 2>&1 &

# MQTT Connector / Iot Device
logging "Starting MQTT Connector"
curl -i -X PUT http://localhost:8083/connectors/mqtt_source/config \
     -H "Content-Type: application/json" \
     -d '{
            "connector.class": "io.confluent.connect.mqtt.MqttSourceConnector",
            "mqtt.server.uri": "tcp://mosquitto:1883",
            "mqtt.topics": "python/mqtt/#",
            "kafka.topic": "data-fabric-mqtt-devices",
            "tasks.max": "1"
        }'
sleep 5
echo ""
curl -s http://localhost:8083/connectors/mqtt_source/status | jq .
sleep 1

echo ""
logging "Starting MQTT IoT device"
python3 iot_mqtt.py > ./logs/iot_mqtt.log 2>&1 &

# RabbitMQ Connector / Iot Device
logging "Starting RabbitMQ IoT device"
python3 iot_rabbitmq.py > ./logs/iot_rabbitmq.log 2>&1 &
sleep 3

logging "Starting RabbitMQ Connector"
curl -i -X PUT http://localhost:8083/connectors/rabbitmq_source/config \
     -H "Content-Type: application/json" \
     -d '{
            "connector.class": "io.confluent.connect.rabbitmq.RabbitMQSourceConnector",
            "rabbitmq.host": "rabbitmq",
            "rabbitmq.port": 5672,
            "rabbitmq.queue": "iot-rabbitmq",
            "kafka.topic": "data-fabric-rabbitmq-devices",
            "tasks.max": "1"
        }'
sleep 5
echo ""
curl -s http://localhost:8083/connectors/rabbitmq_source/status | jq .
sleep 1

# ksqlDB Statements
echo ""
logging "Submitting ksqlDB statements"
sleep 10
python3 ksqldb_provisioning.py

# Elastic Connector
logging "Starting Elastic Connector"
curl -i -X PUT http://localhost:8083/connectors/elastic_sink/config \
     -H "Content-Type: application/json" \
     -d '{
            "connector.class": "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector",
            "connection.url": "http://elasticsearch:9200",
            "key.ignore": "true",
            "topics": "data-fabric-ALL-devices",
            "drop.invalid.message": "true",
            "behavior.on.null.values": "IGNORE",
            "behavior.on.malformed.documents": "ignore",
            "write.method": "insert",
            "data.stream.dataset": "iot",
            "data.stream.type": "METRICS",
            "data.stream.timestamp.field": "timestamp",
            "tasks.max": "1"
        }'
sleep 5
echo ""
curl -s http://localhost:8083/connectors/elastic_sink/status | jq .
echo ""

# Postgres Connector
logging "Starting Postgres Connector"
curl -i -X PUT http://localhost:8083/connectors/postgres_sink/config \
     -H "Content-Type: application/json" \
     -d '{
            "connector.class": "io.confluent.connect.jdbc.JdbcSinkConnector",
            "topics": "data-fabric-ALL-devices",
            "connection.url": "jdbc:postgresql://postgres:5432/postgres?verifyServerCertificate=false&useSSL=false&requireSSL=false",
            "connection.user": "postgres",
            "connection.password": "postgres",
            "insert.mode": "insert",
            "auto.create": "true",
            "tasks.max": "1"
        }'
sleep 5
echo ""
curl -s http://localhost:8083/connectors/postgres_sink/status | jq .
echo ""

sleep 5
python3 elastic_geopoint.py &
sleep 5

logging "Creating Kibana/Elastic Dashboard"
sleep 10
# POST http://localhost:5601/api/saved_objects/_export {"type": "dashboard","includeReferencesDeep": true}
curl -X POST "http://localhost:5601/api/saved_objects/_import?createNewCopies=true" -H "kbn-xsrf: true" --form file=@$KIBANA_DASHBOARD


# Open browser with C3, Kibana and PGAdmin consoles
python3 -m webbrowser -t "http://localhost:5050"
python3 -m webbrowser -t "http://localhost:9021/clusters"
python3 -m webbrowser -t "http://localhost:5601/app/dashboards"

deactivate

logging "Demo successfully started"
echo ""