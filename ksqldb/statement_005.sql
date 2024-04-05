INSERT INTO `data-fabric-ALL-devices`
    SELECT
        `sn` AS `id`,
        AS_VALUE(`sn`) AS `serial_number`,
        `tm` AS `timestamp`,
        `temp` AS `temperature_c`,
        `mnf` AS `manufacturer`,
        `prd` AS `product`,
        `loc` AS `city`,
        'HTTP' AS `device_type`,
        CAST(`lt` AS VARCHAR) + ',' + CAST(`lg` AS VARCHAR) AS `location`
    FROM `data-fabric-http-devices`
    PARTITION BY `sn`;