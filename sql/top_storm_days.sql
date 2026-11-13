-- ten biggest storm days and their share of all damage
-- ::numeric because round(x, 1) does not work on double precision in postgres
SELECT
    storm_date,
    damage_usd,
    ROUND((100 * damage_usd / SUM(damage_usd) OVER ())::numeric, 1) AS percent_of_all_damage
FROM storm_days
ORDER BY damage_usd DESC
LIMIT 10;
