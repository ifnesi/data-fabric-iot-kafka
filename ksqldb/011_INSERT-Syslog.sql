INSERT INTO `$KAFKA_ALL_DEVICES`
    SELECT
        `deviceVersion` AS `id`,
        AS_VALUE(`deviceVersion`) AS `serial_number`,
        `timestamp` AS `timestamp`,
        CAST(`extension`['cfp1'] AS DOUBLE) AS `temperature_c`,
        `deviceVendor` AS `manufacturer`,
        `deviceProduct` AS `product`,
        `extension`['deviceDirection'] AS `city`,
        'SYSLOG' AS `device_type`,
        CAST(`extension`['cfp2'] AS DOUBLE) AS `latitude`,
        CAST(`extension`['cfp3'] AS DOUBLE) AS `longitude`
    FROM `$KAFKA_SYSLOG_TOPIC`
    PARTITION BY `deviceVersion`;
