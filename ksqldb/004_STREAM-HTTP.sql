CREATE STREAM IF NOT EXISTS `$KAFKA_HTTP_TOPIC` (
    `tm` TIMESTAMP,
    `temp` DOUBLE,
    `mnf` VARCHAR,
    `prd` VARCHAR,
    `loc` VARCHAR,
    `sn` VARCHAR,
    `lt` DOUBLE,
    `lg` DOUBLE
) WITH (
    KAFKA_TOPIC = '$KAFKA_HTTP_TOPIC',
    VALUE_FORMAT = 'JSON'
);