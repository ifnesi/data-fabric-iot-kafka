CREATE STREAM IF NOT EXISTS `$KAFKA_ALL_DEVICES` (
    `id` VARCHAR KEY,
    `serial_number` VARCHAR,
    `timestamp` TIMESTAMP,
    `temperature_c` DOUBLE,
    `manufacturer` VARCHAR,
    `product` VARCHAR,
    `city` VARCHAR,
    `device_type` VARCHAR,
    `latitude` DOUBLE,
    `longitude` DOUBLE
) WITH (
    KAFKA_TOPIC = '$KAFKA_ALL_DEVICES',
    PARTITIONS=1,
    KEY_FORMAT = 'KAFKA',
    VALUE_FORMAT = 'AVRO'
);
