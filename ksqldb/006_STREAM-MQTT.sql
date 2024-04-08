CREATE STREAM IF NOT EXISTS `$KAFKA_MQTT_TOPIC` (
    `key` VARCHAR KEY,
    `payload` VARCHAR
) WITH (
    KAFKA_TOPIC = '$KAFKA_MQTT_TOPIC',
    VALUE_FORMAT = 'KAFKA'
);