INSERT INTO `data-fabric-ALL-devices`
    SELECT
        `sn` AS `id`,
        AS_VALUE(`sn`) AS `serial_number`,
        `timestamp` AS `timestamp`,
        `tmp` AS `temperature_c`,
        `manufacturer` AS `manufacturer`,
        `family` AS `product`,
        `pos` AS `city`,
        'COAP' AS `device_type`,
        CAST(`lat` AS VARCHAR) + ',' + CAST(`long` AS VARCHAR) AS `location`
    FROM `data-fabric-coap-devices`
    PARTITION BY `sn`;