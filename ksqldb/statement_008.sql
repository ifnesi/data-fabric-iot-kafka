CREATE STREAM IF NOT EXISTS `data-fabric-rabbitmq-devices` (
    `payload` VARCHAR
) WITH (
    KAFKA_TOPIC = 'data-fabric-rabbitmq-devices',
    VALUE_FORMAT = 'KAFKA'
);
