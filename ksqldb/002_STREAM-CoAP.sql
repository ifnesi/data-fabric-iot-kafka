CREATE STREAM IF NOT EXISTS `$KAFKA_COAP_TOPIC` (
    `timestamp` TIMESTAMP,
    `tmp` DOUBLE,
    `manufacturer` VARCHAR,
    `family` VARCHAR,
    `pos` VARCHAR,
    `sn` VARCHAR,
    `lat` DOUBLE,
    `long` DOUBLE
) WITH (
    KAFKA_TOPIC = '$KAFKA_COAP_TOPIC',
    VALUE_FORMAT = 'JSON'
);