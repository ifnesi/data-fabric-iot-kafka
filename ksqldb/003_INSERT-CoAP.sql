INSERT INTO `$KAFKA_ALL_DEVICES`
    SELECT
        `sn` AS `id`,
        AS_VALUE(`sn`) AS `serial_number`,
        `timestamp` AS `timestamp`,
        `tmp` AS `temperature_c`,
        `manufacturer` AS `manufacturer`,
        `family` AS `product`,
        `pos` AS `city`,
        'COAP' AS `device_type`,
        `lat` AS `latitude`,
        `long` AS `longitude`
    FROM `$KAFKA_COAP_TOPIC`
    PARTITION BY `sn`;