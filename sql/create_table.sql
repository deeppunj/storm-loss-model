-- one row per damaging storm day, starts empty every time
DROP TABLE IF EXISTS storm_days;

CREATE TABLE storm_days (
    storm_date  DATE,
    year        INTEGER,
    damage_usd  DOUBLE PRECISION,
    n_records   INTEGER
);
