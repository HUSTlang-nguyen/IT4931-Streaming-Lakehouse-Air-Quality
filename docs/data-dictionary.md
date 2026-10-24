# Data dictionary dự kiến

Chưa phải schema thực thi hay DDL. Dựa trên đề xuất được lưu trong [proposal](proposal/README.md); P1 phải kiểm tra payload và kiểu dữ liệu thực tế, không coi field dưới đây luôn có trong từng API response.

## Địa điểm và sensor

| Trạm | location_id | PM2.5 sensor_id | PM10 sensor_id |
|---|---:|---:|---:|
| ĐHBK, số 1 Giải Phóng | 4946813 | 13502154 | 13502152 |
| Công viên Nhân Chính | 4946812 | 13502151 | 13502153 |

Đây là ID từ khảo sát 23/10/2026. Cần tái xác nhận metadata, availability và độ mới ở P1. Khí mở rộng chưa có sensor được chốt.

## Measurement và provenance

| Trường logic | Ý nghĩa | Quy tắc dự kiến |
|---|---|---|
| location_id, sensor_id | Trạm và kênh đo | Metadata liên kết ID, không suy từ tên trạm |
| parameter | PM2.5/PM10 hoặc khí phù hợp | Ánh xạ từ metadata đã kiểm tra |
| value, unit | Nồng độ và đơn vị | PM mặc định mong đợi µg/m³; khác đơn vị cần quy tắc minh bạch |
| period_start, period_end | Khoảng số đo đại diện | UTC, giữ cả đầu/cuối; không thay bằng ingested_at |
| reported_interval | Interval do nguồn báo | Giữ giá trị nguồn; chưa suy ra nhịp quan trắc |
| ingested_at | Lúc hệ thống thu thập | UTC; không chứng minh availability của lịch sử quá khứ |
| ingest_mode | live/backfill/replay | Replay tách namespace, không trộn metrics live |
| source/provenance | Provider, request range, raw reference | Truy xuất nguồn; không lưu key/header bí mật |
| quality_flags | Invalid/không đủ điều kiện cùng lý do | Bảo toàn raw; không âm thầm biến lỗi thành 0 |
| coordinates | Vị trí trạm | Có thể chỉ nằm ở metadata, measurement không bắt buộc có |

Khóa Silver dự kiến: `(sensor_id, period_start, period_end)` trong namespace dữ liệu tương ứng. Nếu nguồn sửa cùng khóa, phải có quy tắc chọn bản mới được kiểm chứng, không chọn ngẫu nhiên. Bronze giữ lần thu thập để truy vết; thu thập lặp có thể thêm raw nhưng không thêm bản ghi logic Silver.

## Gold và chất lượng

Lưu count, expected count theo cadence đã xác minh, coverage, last event time và freshness theo sensor. Nếu cadence chưa đủ cơ sở, chỉ báo số lượng/khoảng cách quan sát được, không gắn tỷ lệ coverage như chứng nhận chất lượng. Không tính mean giờ/ngày khi ý nghĩa khoảng đo chưa rõ; PM2.5/PM10 của hai điểm không đại diện toàn thành phố.

## ML và forecast

| Trường logic | Ý nghĩa |
|---|---|
| station/location_id | Model riêng từng trạm |
| feature_time | Mốc chuỗi giờ hợp lệ dùng tạo feature |
| target_time | feature_time + 1 giờ; không lệch theo dòng |
| issued_at | Lúc hệ thống phát hành dự báo |
| predicted_value, unit | PM2.5 dự báo, µg/m³ |
| model_version, data_snapshot | Truy xuất model/config và dữ liệu huấn luyện |
| evaluation_mode | backtest hoặc operational |
| actual_value, error | Bổ sung sau khi có actual hợp lệ |

Features dự kiến: PM2.5 hiện tại, lag 1/2/3/24 giờ và giờ trong ngày địa phương. Giữ null/gap minh bạch; không nội suy tương lai. Ghi split time range, số mẫu và MAE/RMSE model/persistence trên cùng mẫu; chưa có metric thực nghiệm nào ở scaffold.
