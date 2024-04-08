INSERT INTO `$KAFKA_ALL_DEVICES`
    SELECT
        EXTRACTJSONFIELD(SUBSTRING(`payload`, 6, LEN(`payload`)), '$.serno') AS `id`,
        AS_VALUE(EXTRACTJSONFIELD(SUBSTRING(`payload`, 6, LEN(`payload`)), '$.serno')) AS `serial_number`,
        PARSE_TIMESTAMP(EXTRACTJSONFIELD(SUBSTRING(`payload`, 6, LEN(`payload`)), '$.timestamp'), 'yyyy-MM-dd HH:mm:ss.SSSSSS') AS `timestamp`,
        CAST(EXTRACTJSONFIELD(SUBSTRING(`payload`, 6, LEN(`payload`)), '$.temp') AS DOUBLE) AS `temperature_c`,
        EXTRACTJSONFIELD(SUBSTRING(`payload`, 6, LEN(`payload`)), '$.provider') AS `manufacturer`,
        EXTRACTJSONFIELD(SUBSTRING(`payload`, 6, LEN(`payload`)), '$.product') AS `product`,EXTRACTJSONFIELD(SUBSTRING(`payload`, 6, LEN(`payload`)), '$.region') AS `city`,
        'RABBITMQ' AS `device_type`,
        CAST(EXTRACTJSONFIELD(SUBSTRING(`payload`, 6, LEN(`payload`)), '$.lat') AS DOUBLE) AS `latitude`,
        CAST(EXTRACTJSONFIELD(SUBSTRING(`payload`, 6, LEN(`payload`)), '$.lon') AS DOUBLE) AS `longitude`
    FROM `$KAFKA_RABBITMQ_TOPIC`
    PARTITION BY EXTRACTJSONFIELD(SUBSTRING(`payload`, 6, LEN(`payload`)), '$.serno');
