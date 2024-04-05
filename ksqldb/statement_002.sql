CREATE STREAM IF NOT EXISTS `data-fabric-coap-devices` (
    `timestamp` TIMESTAMP,
    `tmp` DOUBLE,
    `manufacturer` VARCHAR,
    `family` VARCHAR,
    `pos` VARCHAR,
    `sn` VARCHAR,
    `lat` DOUBLE,
    `long` DOUBLE
) WITH (
    KAFKA_TOPIC = 'data-fabric-coap-devices',
    VALUE_FORMAT = 'JSON'
);