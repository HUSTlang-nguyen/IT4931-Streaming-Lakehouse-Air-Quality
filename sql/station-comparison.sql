-- Chỉ so sánh cùng giờ mà cả hai trạm có dữ liệu hợp lệ, tránh lệch độ phủ.
SELECT a.parameter_name,
       count(*) AS paired_hours,
       avg(a.value) AS dhbk_mean,
       avg(b.value) AS nhan_chinh_mean,
       avg(a.value - b.value) AS paired_difference
FROM iceberg.live.hourly a
JOIN iceberg.live.hourly b
  ON a.period_end = b.period_end AND a.parameter_name = b.parameter_name
WHERE a.location_id = 4946813 AND b.location_id = 4946812
  AND a.has_data AND b.has_data
  AND a.period_end >= current_timestamp - INTERVAL '7' DAY
GROUP BY a.parameter_name
