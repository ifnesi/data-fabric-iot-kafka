#!/bin/bash

echo ""
echo "Killing processes..."
ps aux  |  grep -i  ' iot_'  |  awk '{print $2}'  |  xargs kill -9 >/dev/null 2>&1 &
ps aux  |  grep -i  ' coap_server.py'  |  awk '{print $2}'  |  xargs kill -9 >/dev/null 2>&1 &

echo ""
echo "Starting docker compose..."
docker compose up -d

# Waiting services to be ready
echo ""
while [[ "$(curl -s -o /dev/null -w ''%{http_code}'' http://localhost:8081)" != "200" ]]
do
    echo "Waiting Schema Registry to be ready..."
    sleep 2
done

echo ""
while [[ "$(curl -s -o /dev/null -w ''%{http_code}'' http://localhost:8088/info)" != "200" ]]
do
    echo "Waiting ksqlDB Cluster to be ready..."
    sleep 2
done

echo ""
while [[ "$(curl -s -o /dev/null -w ''%{http_code}'' http://localhost:8083)" != "200" ]]
do
    echo "Waiting Connect Cluster 1 to be ready..."
    sleep 2
done

echo ""
while [[ "$(curl -s -o /dev/null -w ''%{http_code}'' http://localhost:18083)" != "200" ]]
do
    echo "Waiting Connect Cluster 2 to be ready..."
    sleep 2
done

echo ""
while [[ "$(curl -s -o /dev/null -w ''%{http_code}'' http://localhost:9021)" != "200" ]]
do
    echo "Waiting Confluent Control Center to be ready..."
    sleep 2
done

echo ""
echo "Loading environment variables"
source .env

echo ""
echo "Activating Virtual Environment / install Python requirements"
source .venv/bin/activate
pip install -r requirements.txt
sleep 1

# Kafka IoT Device
echo ""
echo "Starting Kafka IoT device"
python3 iot_kafka.py >/dev/null 2>&1 &

# HTTP IoT Device
echo ""
echo "Starting HTTP IoT device"
python3 iot_http.py >/dev/null 2>&1 &

# SysLog Connector
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
curl -s http://localhost:8083/connectors/syslog_source/status
sleep 1
echo ""
echo "Starting SysLog IoT device"
python3 iot_syslog.py >/dev/null 2>&1 &

# Spooldir Connector / Iot Device
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
sleep 1
echo ""
echo "Starting CoAP Server"
python3 coap_server.py >/dev/null 2>&1 &
sleep 2
echo ""
echo "Starting CoAP IoT device"
python3 iot_coap.py >/dev/null 2>&1 &
curl -s http://localhost:18083/connectors/spooldir_source/status

# MQTT Connector / Iot Device
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
curl -s http://localhost:8083/connectors/mqtt_source/status
sleep 1
echo ""
echo "Starting MQTT IoT device"
python3 iot_mqtt.py >/dev/null 2>&1 &

# RabbitMQ Connector / Iot Device
echo ""
echo "Starting RabbitMQ IoT device"
python3 iot_rabbitmq.py >/dev/null 2>&1 &
sleep 3
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
curl -s http://localhost:8083/connectors/rabbitmq_source/status

# ksqlDB Statements
source ./ksql_rest.sh ksqldb_statements.sql

# Elastic Connector
echo ""
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
curl -s http://localhost:8083/connectors/elastic_sink/status

# Postgres Connector
echo ""
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
curl -s http://localhost:8083/connectors/postgres_sink/status

echo ""
echo ""
echo "Creating Kibana/Elastic Dashboard"
sleep 10
curl -X POST "http://localhost:5601/api/saved_objects/_import?createNewCopies=true" -H "kbn-xsrf: true" --form file=@kibana_dashboard.ndjson
echo ""
echo ""

deactivate