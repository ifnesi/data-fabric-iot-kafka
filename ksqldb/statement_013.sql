INSERT INTO `data-fabric-ALL-devices`
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
        CAST(`LAT` AS VARCHAR) + ',' + CAST(`LNG` AS VARCHAR) AS `location`
    FROM `data-fabric-kafka-devices`
    PARTITION BY `ID`;