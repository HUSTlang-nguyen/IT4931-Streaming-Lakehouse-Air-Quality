-- Hai giờ thiếu liên tiếp có cùng end_time - row_number * 1h.
-- Kết quả là các khoảng không có số đo hợp lệ, không điền value=0.
WITH missing AS (
    SELECT sensor_id, station_name, parameter_name, period_start, period_end,
           row_number() OVER (PARTITION BY sensor_id ORDER BY period_end) AS rn
    FROM iceberg.live.hourly
    WHERE NOT has_data
), groups AS (
    SELECT *, period_end - rn * INTERVAL '1' HOUR AS gap_group
    FROM missing
)
SELECT sensor_id, station_name, parameter_name,
       min(period_start) AS missing_from_utc,
       max(period_end) AS missing_to_utc,
       count(*) AS missing_hours
FROM groups
GROUP BY sensor_id, station_name, parameter_name, gap_group
ORDER BY missing_hours DESC
