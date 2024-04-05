CREATE STREAM IF NOT EXISTS `data-fabric-syslog-devices` (
    `extension` MAP<VARCHAR, VARCHAR>,
    `deviceVendor` VARCHAR,
    `deviceProduct` VARCHAR,
    `deviceVersion` VARCHAR,
    `timestamp` TIMESTAMP
) WITH (
    KAFKA_TOPIC = 'data-fabric-syslog-devices',
    VALUE_FORMAT = 'AVRO'
);
