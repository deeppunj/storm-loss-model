-- storm days and total damage per year
SELECT
    year,
    COUNT(*)        AS storm_days,
    SUM(damage_usd) AS total_damage_usd
FROM storm_days
GROUP BY year
ORDER BY year;
