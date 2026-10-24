# Lab 04 — Gold và chất lượng dữ liệu theo thời gian

## Mục tiêu/prerequisite

Có các bảng từ Lab03. Hiểu null/gap, count/coverage, freshness từng sensor và so sánh công bằng. Gold dùng `/hours` của OpenAQ, không tự bình quân raw intervals chồng nhau.

## Logic production

[hourly_gold](../src/air_quality/processing/transforms.py) tạo một grid theo giờ từ min/max giờ nguồn và bốn sensor, left join Silver hours. Value chỉ hiện khi không có quality_flags; thiếu/invalid giữ null và has_data=false. Source observed_count được giữ để truy vết, không coi coverage API trên100% là chất lượng.

[daily_gold](../src/air_quality/processing/transforms.py) lấy mean các giờ hợp lệ. End time trừ một giây trước khi đổi sang Asia/Ho_Chi_Minh để giờ kết thúc nửa đêm thuộc ngày vừa kết thúc. Luôn có valid_hours, expected_hours=24, window_bins và coverage_percent; biên dataset/ngày hiện tại chưa đủ24giờ không được so sánh như ngày hoàn chỉnh.

Gold full refresh sau Silver có chủ ý: quy mô hai trạm nhỏ, dễ kiểm chứng late/correction kể cả sửa thành invalid. Không tuyên bố đây là tối ưu cho hàng tỷ dòng. Mỗi lần overwrite là snapshot atomic, không truncate rồi append.

## Truy vấn thật

```powershell
.venv/Scripts/python.exe -m air_quality.cli query 'SELECT count(*) AS bins, count(value) AS valid_bins FROM iceberg.live.hourly'
.venv/Scripts/python.exe -m air_quality.cli query (Get-Content sql/missing-hours.sql -Raw)
.venv/Scripts/python.exe -m air_quality.cli query (Get-Content sql/station-comparison.sql -Raw)
```

Ở snapshot180ngày ban đầu: 17.280 bins, 16.096 có nguồn, 1.184 null. Khoảng giữa hai quan trắc hourly xa nhất87giờ; số bin thiếu liên tiếp có thể86 vì hai đầu vẫn là hàng có dữ liệu. Không nhầm khoảng cách timestamp với số hàng thiếu.

Query so sánh chỉ ghép cùng giờ cả hai trạm đều hợp lệ, không so trung bình của hai tập thời gian khác nhau. Freshness lưu timestamp theo sensor/resource; tuổi dữ liệu tính ở query time, không đóng băng số phút lúc ingest.

## Kiểm chứng/chẩn đoán/bài tập

Test late-data trong test_lakehouse.py bắt đầu giờ1/3, xác nhận giờ2null, thêm giờ2đến muộn rồi đối chiếu hourly/daily. Invalid correction phải xóa giá trị Gold cũ. Cả raw, Silver flags và snapshot còn để giải thích kết quả.

Nếu dashboard nối qua gap: kiểm data query còn hàng null hay đã filter mất, rồi kiểm connect_nulls; không chữa bằng zero. Bài tập: giải thích vì sao expected24 và valid_hours phải đi cùng mean_value; tìm một ngày biên/thiếu nhiều giờ trong dữ liệu thật.
