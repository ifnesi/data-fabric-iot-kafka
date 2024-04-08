CREATE STREAM IF NOT EXISTS `$KAFKA_RABBITMQ_TOPIC` (
    `payload` VARCHAR
) WITH (
    KAFKA_TOPIC = '$KAFKA_RABBITMQ_TOPIC',
    VALUE_FORMAT = 'KAFKA'
);
