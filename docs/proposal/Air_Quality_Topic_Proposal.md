# BÁO CÁO ĐỀ XUẤT ĐỀ TÀI\
**Tên đề tài:** Xây dựng hệ thống giám sát và phân tích chất lượng không khí tại Hà Nội theo kiến trúc Streaming Lakehouse\
**Nguồn dữ liệu:** OpenAQ API v3\

## 1. Bài toán và lý do lựa chọn

Dữ liệu quan trắc chất lượng không khí gồm nhiều chuỗi số đo theo thời gian, gắn với từng trạm và từng chất ô nhiễm. Việc khai thác dữ liệu này cần giải quyết các vấn đề về lưu trữ lịch sử, dữ liệu trùng lặp khi thu thập, bản ghi đến muộn, khoảng thời gian bị thiếu và sự khác nhau về mức độ cập nhật giữa các cảm biến.

Đề tài đề xuất xây dựng một nền tảng dữ liệu phục vụ giám sát và phân tích PM2.5, PM10 tại hai trạm ở Hà Nội. Hệ thống dự kiến kết hợp thu thập dữ liệu mới theo chu kỳ với xử lý dữ liệu lịch sử trên cùng kiến trúc Lakehouse. Dashboard là đầu ra để khai thác dữ liệu; trọng tâm kỹ thuật của đồ án là thiết kế pipeline, tổ chức lưu trữ và kiểm chứng quá trình xử lý.

## 2. Mục tiêu và câu hỏi phân tích

### 2.1. Mục tiêu

- Xây dựng pipeline thu thập dữ liệu OpenAQ và chuyển tiếp qua Kafka để xử lý bằng Spark.
- Tổ chức dữ liệu gốc, dữ liệu đã làm sạch và dữ liệu tổng hợp trong các bảng Iceberg trên MinIO.
- Xử lý trùng lặp, dữ liệu đến muộn và theo dõi độ đầy đủ, độ mới của từng chuỗi số đo.
- Cung cấp truy vấn bằng Trino và dashboard bằng Superset để phân tích diễn biến, so sánh hai trạm.
- Thực nghiệm các đặc tính lưu trữ liên quan môn học: partition pruning, compaction và time travel.
- Bổ sung dự báo PM2.5 trước một giờ bằng Random Forest Regression trên Spark MLlib, đối chiếu persistence bằng MAE/RMSE.

### 2.2. Câu hỏi phân tích

1. Nồng độ PM2.5 và PM10 tại mỗi trạm biến động như thế nào theo thời gian?
2. Hai trạm khác nhau như thế nào trong cùng khoảng thời gian có dữ liệu hợp lệ?
3. Các chuỗi số đo có những khoảng thiếu nào, và sensor nào đang cập nhật chậm?
4. Việc phân vùng và gom các file nhỏ ảnh hưởng như thế nào đến tổ chức lưu trữ và hiệu năng truy vấn?
5. Random Forest dự báo PM2.5 trước một giờ có MAE/RMSE như thế nào so với persistence trên cùng tập tương lai?

## 3. Phạm vi đề tài

| Nội dung | Phạm vi đề xuất |
|---|---|
| Địa điểm | Trạm ĐHBK, số 1 Giải Phóng; Công viên Nhân Chính – Khuất Duy Tiến |
| Chỉ số bắt buộc | PM2.5 và PM10 |
| Chỉ số mở rộng | NO₂, SO₂, O₃, CO, tùy độ sẵn có và độ mới của từng sensor |
| Dữ liệu lịch sử | Dự kiến thu thập 6 tháng gần nhất; thống kê độ phủ thực tế sau khi tải |
| Dữ liệu mới | Thu thập định kỳ khoảng 5 phút/lần, tùy hạn mức API và nhịp cập nhật nguồn |
| Đầu ra | Các bảng Lakehouse, truy vấn, dashboard, mô hình/dự báo PM2.5 trước một giờ và báo cáo đánh giá |
| Ngoài phạm vi | Nhiệt độ, độ ẩm; tính AQI; khuyến cáo sức khỏe |

Kết quả phản ánh các điểm quan trắc được chọn, không được diễn giải thành mức ô nhiễm đại diện cho toàn Hà Nội. Hệ thống được xác định là **gần thời gian thực**, vì độ mới phụ thuộc cả nhà cung cấp số đo và OpenAQ.

## 4. Nguồn dữ liệu và kết quả khảo sát

### 4.1. Cấu trúc dữ liệu OpenAQ

OpenAQ tổ chức dữ liệu theo ba cấp [1][2]:

| Cấp dữ liệu | Nội dung | Ví dụ tại ĐHBK |
|---|---|---|
| Location | Địa điểm quan trắc, tọa độ, nguồn cung cấp và danh sách sensor | Location ID `4946813` |
| Sensor | Kênh đo một chỉ số tại một địa điểm | Sensor PM2.5 có ID `13502154` |
| Measurement | Giá trị do sensor báo cáo cùng thông tin khoảng đo | Nồng độ, đơn vị, thời gian bắt đầu và kết thúc khoảng đo |

Một bản ghi measurement biểu diễn một chỉ số của một sensor; PM2.5 và PM10 cùng trạm là các bản ghi riêng. Dữ liệu dự kiến lưu gồm `location_id`, `sensor_id`, tên chỉ số, giá trị, đơn vị, thời gian bắt đầu/kết thúc khoảng đo và thời điểm thu thập. Metadata trạm được lưu riêng, liên kết qua ID để bổ sung tọa độ và nguồn gốc khi measurement không có các trường này.

### 4.2. Hai trạm và các sensor chính

| Trạm | Location ID | Sensor PM2.5 | Sensor PM10 |
|---|---:|---:|---:|
| ĐHBK – số 1 Giải Phóng | `4946813` | `13502154` | `13502152` |
| Công viên Nhân Chính – Khuất Duy Tiến | `4946812` | `13502151` | `13502153` |

Trong lần kiểm tra khoảng 19:35 ngày 23/10/2026, giờ Việt Nam, hai trạm đều trả về số đo bụi tại mốc 19:20. PM2.5/PM10 tương ứng là 24,91/57,62 µg/m³ tại ĐHBK và 28,48/52,44 µg/m³ tại Nhân Chính. Các giá trị này là ảnh chụp tại thời điểm khảo sát, không phải dữ liệu cập nhật liên tục trong báo cáo.

### 4.3. Kiểm tra khả năng thu thập và độ đầy đủ

Đã truy vấn các trang dữ liệu của bốn sensor trong khoảng từ **19:00 ngày 16/10/2026 đến 19:00 ngày 23/10/2026**, giờ Việt Nam, với điều kiện thời điểm kết thúc khoảng đo lớn hơn đầu kỳ và không vượt cuối kỳ:

| Trạm | Chỉ số | Số bản ghi có timestamp duy nhất | Tỷ lệ số bản ghi so với kỳ vọng 5 phút/bản ghi |
|---|---|---:|---:|
| ĐHBK | PM2.5 | 1.947 | 96,58% |
| ĐHBK | PM10 | 2.014 | 99,90% |
| Nhân Chính | PM2.5 | 2.013 | 99,85% |
| Nhân Chính | PM10 | 2.013 | 99,85% |
| **Tổng** | | **7.987** | |

Các mốc thời gian cách nhau chủ yếu 5 phút. Mẫu PM2.5 tại ĐHBK có khoảng cách giữa hai bản ghi liên tiếp dài nhất là 3 giờ 20 phút. Tỷ lệ trong bảng được tính theo 2.016 bản ghi kỳ vọng trong 7 ngày, nhằm mô tả mức độ đầy đủ theo giả định nhịp cập nhật; đây không phải tỷ lệ chất lượng do nhà cung cấp chứng nhận hay đánh giá độ chính xác cảm biến.

Khả năng truy xuất lịch sử cũng đã được thử với hai sensor bụi tại ĐHBK. Mỗi sensor trả về 203 bản ghi trong ngày 04/07/2025 và 192 bản ghi trong ngày 15/01/2026, tính theo ngày UTC. Kết quả xác nhận có thể lấy dữ liệu quá khứ, nhưng chưa chứng minh toàn bộ khoảng lịch sử 6 tháng là liên tục.

Nếu cả bốn sensor duy trì một bản ghi mỗi 5 phút, lượng dữ liệu ước tính là **1.152 bản ghi/ngày**, tương đương **207.360 bản ghi trong 180 ngày**. Đây là ước lượng quy mô cho phạm vi chính; dữ liệu thực tế phụ thuộc khoảng thiếu và khả năng truy xuất. Quy mô này phù hợp đồ án học phần nhưng chưa phải Big Data về dung lượng.

### 4.4. Hạn chế cần xử lý

- **Ý nghĩa khoảng đo:** mẫu measurement ghi `period.interval = 01:00:00` dù timestamp cách nhau chủ yếu 5 phút. Cần xác minh ý nghĩa khoảng đo với nguồn trước khi tính trung bình theo giờ/ngày; không mặc định các bản ghi là phép đo tức thời độc lập.
- **Độ mới theo sensor:** tại cùng một trạm, các chỉ số có thể có thời điểm cập nhật cuối khác nhau. Các khí mở rộng chỉ được sử dụng khi dữ liệu đáp ứng phạm vi phân tích.
- **Giới hạn API:** tài liệu OpenAQ tại thời điểm khảo sát công bố mức miễn phí 60 request/phút và 2.000 request/giờ theo API key; kết quả có phân trang, tối đa 1.000 bản ghi/trang [4][5]. Quá trình tải lịch sử cần chia nhỏ khoảng thời gian và kiểm soát tốc độ gọi.
- **Dữ liệu đến muộn:** chỉ lấy endpoint `latest` không bảo đảm thu đủ bản ghi, vì số đo có thể được nhập không theo thứ tự thời gian [3]. Cần truy vấn bổ sung measurement theo khoảng thời gian.

## 5. Kiến trúc và phương pháp thực hiện dự kiến

```text
OpenAQ API v3
      ↓
Collector: dữ liệu mới và dữ liệu lịch sử
      ↓
Apache Kafka
      ↓
Spark Structured Streaming / Spark Batch
      ↓
Apache Iceberg trên MinIO
Bronze → Silver → Gold
      ↓
Trino → Apache Superset
```

| Thành phần | Vai trò dự kiến |
|---|---|
| Collector | Lấy metadata và measurement, phân trang, kiểm soát hạn mức, truy vấn bổ sung dữ liệu đến muộn |
| Kafka | Làm lớp đệm giữa thu thập và xử lý; phục vụ đọc lại dữ liệu khi kiểm thử |
| Spark | Làm sạch, chống trùng, xử lý lịch sử và cập nhật dữ liệu mới theo cùng quy tắc |
| Iceberg và MinIO | Lưu dữ liệu dạng bảng trên object storage; hỗ trợ phân vùng, snapshot và bảo trì file |
| Trino | Truy vấn dữ liệu Lakehouse bằng SQL |
| Superset | Hiển thị diễn biến, so sánh trạm, độ mới và mức độ đầy đủ của dữ liệu |

Ba lớp dữ liệu được tổ chức như sau:

- **Bronze:** giữ dữ liệu gốc, metadata và thời điểm thu thập để truy vết, kiểm tra hoặc xử lý lại.
- **Silver:** chuẩn hóa kiểu dữ liệu, thời gian và đơn vị; chống trùng theo sensor và khoảng đo; bảo toàn thông tin nguồn, đánh dấu bản ghi không hợp lệ. Không chuyển dữ liệu thiếu thành giá trị 0.
- **Gold:** tạo bảng phục vụ dashboard về số đo, số bản ghi và độ đầy đủ theo thời gian. Các giá trị trung bình theo giờ/ngày chỉ được xây dựng sau khi xác minh ý nghĩa khoảng đo và chọn cách tổng hợp phù hợp.

Timestamp được chuẩn hóa về UTC để lưu trữ, đồng thời sử dụng múi giờ Việt Nam khi hiển thị và phân tích theo ngày địa phương. Thời điểm đo được phân biệt với thời điểm thu thập.

### 5.1. Phần bổ sung ML dự kiến

Sau khi xác minh ý nghĩa khoảng đo và tạo được chuỗi giờ hợp lệ, huấn luyện Random Forest Regression bằng Spark MLlib, mỗi trạm một model để dự báo PM2.5 trước một giờ. Features gồm PM2.5 hiện tại, lag 1/2/3/24 giờ và giờ trong ngày; lag theo mốc giờ thực, không theo vị trí dòng khi có khoảng thiếu.

Chia train/validation/test 70/15/15 theo thời gian; loại nhãn vượt ranh giới tập, không điền thiếu bằng tương lai hoặc tune trên test. Đánh giá MAE/RMSE trên cùng mẫu với baseline persistence. Ghi số mẫu, khoảng thời gian, snapshot và model version; không cam kết RF thắng baseline. Lưu dự báo vào Iceberg với trạm, issued_at, target_time, value/unit và model version để Superset hiển thị. Phân biệt backtest trên lịch sử tải lại với dự báo vận hành chỉ dùng dữ liệu đã có khi phát hành.

Đây là bổ sung phạm vi theo yêu cầu ML, chưa có model, metrics hay kết quả dự báo được chạy. Pipeline và lưu trữ vẫn là trọng tâm; mục tiêu ML bị chặn nếu chưa đủ chuỗi giờ hoặc chưa rõ interval semantics.

## 6. Mức độ phù hợp với học phần

| Nội dung môn học | Cách áp dụng trong đề tài |
|---|---|
| Kafka và xử lý luồng | Thu nhận dữ liệu, quản lý quá trình đọc và phát lại sự kiện |
| Spark batch/streaming | Kết hợp dữ liệu lịch sử với cập nhật định kỳ; dùng chung quy tắc xử lý |
| Object storage và Lakehouse | Tổ chức Bronze–Silver–Gold trên MinIO và Iceberg |
| Quản lý bảng dữ liệu | Thực nghiệm phân vùng, snapshot, time travel và compaction |
| Truy vấn phân tích | Dùng Trino truy vấn trực tiếp các bảng Iceberg, đánh giá partition pruning |
| Chất lượng dữ liệu | Xử lý trùng, dữ liệu đến muộn, khoảng thiếu và độ mới theo sensor |

So với Topic 1 – Stock Analytics trong tài liệu đề xuất [7], đề tài giữ kiến trúc Streaming Lakehouse và các công nghệ cốt lõi, nhưng thay miền dữ liệu chứng khoán bằng dữ liệu quan trắc môi trường đã khảo sát thực tế. Topic 1 thuận lợi hơn khi tận dụng ví dụ chứng khoán trong lab và thể hiện luồng sự kiện tốc độ cao. Đề tài không khí phù hợp để thể hiện quản lý dữ liệu theo thời gian, chất lượng dữ liệu và lưu trữ lịch sử; không đặt mục tiêu chứng minh thông lượng cao bằng vài trạm quan trắc.

## 7. Sản phẩm và tiêu chí đánh giá dự kiến

### 7.1. Sản phẩm

1. Pipeline thu thập dữ liệu OpenAQ và cập nhật các bảng Bronze–Silver–Gold.
2. Bộ dữ liệu lịch sử kèm mô tả nguồn, schema, phạm vi thời gian và độ đầy đủ thực tế.
3. Dashboard diễn biến PM2.5/PM10, so sánh hai trạm, thời điểm cập nhật cuối và khoảng thiếu dữ liệu.
4. Bộ kịch bản kiểm chứng tính đúng đắn và thực nghiệm đặc tính lưu trữ.
5. Báo cáo thiết kế, kết quả thực nghiệm và các hạn chế còn lại.
6. Model/config, MAE/RMSE so với persistence và bảng dự báo PM2.5 từng trạm; chưa có kết quả thực nghiệm tại giai đoạn đề xuất.

### 7.2. Tiêu chí đánh giá

- Dữ liệu đi được xuyên suốt từ OpenAQ đến bảng truy vấn và dashboard.
- Thu thập lặp cùng dữ liệu không làm tăng số bản ghi duy nhất ở Silver.
- Bản ghi đến muộn được bổ sung và kết quả tổng hợp liên quan được cập nhật khi đủ điều kiện.
- Dữ liệu thiếu được thể hiện rõ; dashboard không nối hoặc điền giá trị theo cách gây hiểu nhầm.
- Kết quả xử lý mẫu được đối chiếu với bản ghi nguồn và quy tắc tổng hợp đã xác minh.
- Có số liệu thực nghiệm về quy mô dữ liệu, số lượng/kích thước file và thời gian truy vấn trước, sau các thao tác tối ưu phù hợp.

Lịch sử có thể được phát lại qua Kafka để kiểm thử hoặc demo. Chế độ replay phải được phân biệt với dữ liệu live và không được mô tả là luồng đo mới từ cảm biến.

## 8. Tính khả thi và kế hoạch dự kiến

Nguồn OpenAQ đã truy cập thành công bằng API key trong khảo sát, cung cấp được PM2.5/PM10 gần thời điểm kiểm tra và các mẫu dữ liệu lịch sử. Các công nghệ đề xuất tương ứng với nội dung và lab hiện có của môn học. Phạm vi hai trạm giúp giới hạn công việc tích hợp, cho phép tập trung vào tính đúng đắn của pipeline và tổ chức lưu trữ.

Rủi ro chính là dữ liệu nguồn gián đoạn, thay đổi độ sẵn có, giới hạn truy cập và metadata khoảng đo cần xác minh. Hướng xử lý là lưu dữ liệu gốc, báo cáo độ phủ, bổ sung truy vấn lịch sử, kiểm soát tốc độ gọi và chuẩn bị dữ liệu replay từ lịch sử đã thu thập. Không cam kết đủ dữ liệu cho mọi chỉ số hoặc mọi ngày trước khi hoàn thành khảo sát toàn bộ khoảng cần tải.

Kế hoạch tham khảo cho nhóm ba thành viên trong sáu tuần:

| Giai đoạn | Công việc | Kết quả dự kiến |
|---|---|---|
| Tuần 1 | Khảo sát toàn bộ khoảng dữ liệu, xác minh khoảng đo, chốt schema và quy tắc chất lượng | Đặc tả dữ liệu và phạm vi tổng hợp có thể thực hiện |
| Tuần 2 | Thiết lập môi trường, Collector và Kafka; bắt đầu tải lịch sử | Luồng thu thập và dữ liệu gốc |
| Tuần 3–4 | Xây dựng Spark và các lớp Iceberg; xử lý trùng, dữ liệu đến muộn và khoảng thiếu | Pipeline xử lý và bảng phục vụ truy vấn |
| Tuần 5 | Kết nối Trino, dashboard, mô hình RF/baseline và thực nghiệm lưu trữ | Dashboard, metrics ML và kết quả đo thực tế |
| Tuần 6 | Kiểm thử tích hợp, đối chiếu dữ liệu, hoàn thiện báo cáo và demo | Sản phẩm và báo cáo đồ án |

Phân công tham khảo: một thành viên phụ trách thu thập/Kafka; một thành viên phụ trách Spark/Iceberg; một thành viên phụ trách Trino/dashboard và tổng hợp thực nghiệm. Quy mô nhóm và thời lượng trên là phương án đề xuất, cần điều chỉnh theo lịch học thực tế.

## 9. Tài liệu tham khảo

[1] OpenAQ, [Sensors](https://docs.openaq.org/resources/sensors).\
[2] OpenAQ, [Measurements](https://docs.openaq.org/resources/measurements).\
[3] OpenAQ, [Latest](https://docs.openaq.org/resources/latest).\
[4] OpenAQ, [Rate limits](https://docs.openaq.org/using-the-api/rate-limits).\
[5] OpenAQ, [Pagination](https://docs.openaq.org/using-the-api/pagination).\
[6] OpenAQ, [Dates, times and timezones](https://docs.openaq.org/using-the-api/dates-datetimes).\
[7] Tài liệu đề xuất đề tài trong workspace: `Topics_Proposal.md`; xem [nguồn gốc tài liệu](README.md).\
[8] Tài liệu lab trong workspace: `git lab/Streaming_Lakehouse_lab/README.md`; xem [nguồn gốc tài liệu](README.md).

Các số liệu khảo sát ở mục 4 là kết quả truy vấn OpenAQ API v3 trong phiên làm việc ngày 23/10/2026. Báo cáo ghi nhận kết quả khảo sát và phương án thực hiện; chưa khẳng định hệ thống đã được triển khai hay các thực nghiệm dự kiến đã hoàn thành.
