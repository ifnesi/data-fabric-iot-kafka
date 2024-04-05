CREATE STREAM IF NOT EXISTS `data-fabric-kafka-devices` WITH (
    KAFKA_TOPIC = 'data-fabric-kafka-devices',
    VALUE_FORMAT = 'AVRO'
);

