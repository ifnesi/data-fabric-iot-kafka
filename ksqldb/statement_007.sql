INSERT INTO `data-fabric-ALL-devices`
    SELECT
        SPLIT(`key`, '/')[5] AS `id`,
        AS_VALUE(SPLIT(`key`, '/')[5]) AS `serial_number`,
        PARSE_TIMESTAMP(EXTRACTJSONFIELD(SUBSTRING(`payload`, 6, LEN(`payload`)), '$.epoch'), 'yyyy-MM-dd HH:mm:ss.SSSSSS') AS `timestamp`,
        (CAST(EXTRACTJSONFIELD(SUBSTRING(`payload`, 6, LEN(`payload`)), '$.temperature') AS DOUBLE) - 32) * 5/9 AS `temperature_c`,
        SPLIT(`key`, '/')[3] AS `manufacturer`,
        SPLIT(`key`, '/')[4] AS `product`,
        EXTRACTJSONFIELD(SUBSTRING(`payload`, 6, LEN(`payload`)), '$.location') AS `city`,
        'MQTT' AS `device_type`,
        CAST(EXTRACTJSONFIELD(SUBSTRING(`payload`, 6, LEN(`payload`)), '$.latitude') AS DOUBLE) AS `latitude`,
        CAST(EXTRACTJSONFIELD(SUBSTRING(`payload`, 6, LEN(`payload`)), '$.longitude') AS DOUBLE) AS `longitude`
    FROM `data-fabric-mqtt-devices`
    PARTITION BY SPLIT(`key`, '/')[5];
