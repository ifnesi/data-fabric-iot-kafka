CREATE STREAM IF NOT EXISTS `data-fabric-http-devices` (
    `tm` TIMESTAMP,
    `temp` DOUBLE,
    `mnf` VARCHAR,
    `prd` VARCHAR,
    `loc` VARCHAR,
    `sn` VARCHAR,
    `lt` DOUBLE,
    `lg` DOUBLE
) WITH (
    KAFKA_TOPIC = 'data-fabric-http-devices',
    VALUE_FORMAT = 'JSON'
);