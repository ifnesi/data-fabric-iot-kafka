CREATE STREAM IF NOT EXISTS `$KAFKA_SYSLOG_TOPIC` (
    `extension` MAP<VARCHAR, VARCHAR>,
    `deviceVendor` VARCHAR,
    `deviceProduct` VARCHAR,
    `deviceVersion` VARCHAR,
    `timestamp` TIMESTAMP
) WITH (
    KAFKA_TOPIC = '$KAFKA_SYSLOG_TOPIC',
    VALUE_FORMAT = 'AVRO'
);
