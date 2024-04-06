CREATE STREAM IF NOT EXISTS `data-fabric-ALL-devices` (
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
    KAFKA_TOPIC = 'data-fabric-ALL-devices',
    PARTITIONS=1,
    KEY_FORMAT = 'KAFKA',
    VALUE_FORMAT = 'AVRO'
);
