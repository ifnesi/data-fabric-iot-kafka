INSERT INTO `$KAFKA_ALL_DEVICES`
    SELECT
        `sn` AS `id`,
        AS_VALUE(`sn`) AS `serial_number`,
        `tm` AS `timestamp`,
        `temp` AS `temperature_c`,
        `mnf` AS `manufacturer`,
        `prd` AS `product`,
        `loc` AS `city`,
        'HTTP' AS `device_type`,
        `lt` AS `latitude`,
        `lg` AS `longitude`
    FROM `$KAFKA_HTTP_TOPIC`
    PARTITION BY `sn`;