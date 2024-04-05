CREATE STREAM IF NOT EXISTS `data-fabric-mqtt-devices` (
    `key` VARCHAR KEY,
    `payload` VARCHAR
) WITH (
    KAFKA_TOPIC = 'data-fabric-mqtt-devices',
    VALUE_FORMAT = 'KAFKA'
);