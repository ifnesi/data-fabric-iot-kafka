INSERT INTO `$KAFKA_ALL_DEVICES`
    SELECT
        `ID` AS `id`,
        AS_VALUE(`ID`) AS `serial_number`,
        PARSE_TIMESTAMP(`DATETIME`,
        'yyyy-MM-dd HH:mm:ss.SSSSSS') AS `timestamp`,
        `TEMPERATURE` AS `temperature_c`,
        `MANUFACTURER` AS `manufacturer`,
        `PRODUCT` AS `product`,
        `REGION` AS `city`,
        'KAFKA' AS `device_type`,
        `LAT` AS `latitude`,
        `LNG` AS `longitude`
    FROM `$KAFKA_TOPIC`
    PARTITION BY `ID`;