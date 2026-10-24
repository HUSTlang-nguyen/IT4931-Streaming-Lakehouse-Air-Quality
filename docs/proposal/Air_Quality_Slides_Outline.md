# Dàn ý slide đề xuất đề tài

**Thiết kế:** Paper & Ink theo `slide-theme.md` được cung cấp. Nền giấy ngà, chữ đen, Be Vietnam Pro và IBM Plex Mono. Canvas 1920 × 1080, cuộn dọc và Tab/Shift+Tab để chuyển slide.

**Độ dài:** 6 slide, dành cho phần đề xuất ngắn khoảng 5–6 phút.

## Slide 01 — Giám sát chất lượng không khí tại Hà Nội

**Vai trò:** Giới thiệu tên đề tài, đối tượng dữ liệu và hướng tiếp cận.

**Nội dung trên slide:**
- Streaming Lakehouse cho dữ liệu PM2.5 và PM10.
- OpenAQ v3, hai trạm tại Hà Nội.
- Dự báo PM2.5 bằng ML là đầu ra dự kiến bổ sung.

**Visualize:** Bìa chữ lớn, một thanh nhấn đen và ba nhãn phạm vi. Không thêm người hướng dẫn, ngày hoặc dòng trạng thái.

**Nguồn và lưu ý:** Báo cáo đề xuất, mục 1–3. Tên đầy đủ và phạm vi nằm trong ghi chú.

> REVIEW: Chưa có góp ý.

## Slide 02 — Bài toán và phạm vi

**Vai trò:** Làm rõ hệ thống dự kiến giải quyết gì và giới hạn ở đâu.

**Nội dung trên slide:**
- Theo dõi diễn biến, so sánh hai điểm quan trắc và dự báo PM2.5 trước một giờ.
- Trạm ĐHBK và Công viên Nhân Chính, PM2.5 và PM10.
- Dự kiến 6 tháng lịch sử và thu thập mới khoảng 5 phút/lần.
- Trọng tâm là pipeline và lưu trữ dữ liệu.

**Visualize:** Bảng hai cột gồm bài toán, địa điểm, chỉ số và thời gian. Thanh nhấn nêu trọng tâm môn học.

**Nguồn và lưu ý:** Báo cáo mục 2–3 và phạm vi ML bổ sung theo yêu cầu. Sáu tháng và chu kỳ gọi là cấu hình dự kiến. Các khí là phần mở rộng. Không gồm AQI và không suy rộng toàn Hà Nội. PM10 vẫn được giám sát, phần dự báo tập trung PM2.5.

> REVIEW: Chưa có góp ý.

## Slide 03 — Dữ liệu đã kiểm tra được

**Vai trò:** Cung cấp bằng chứng khả thi của nguồn OpenAQ.

**Nội dung trên slide:**
- 7.987 bản ghi từ bốn sensor trong bảy ngày.
- Bảng số bản ghi và tỷ lệ theo từng sensor.
- Tỷ lệ tính theo 2.016 bản ghi kỳ vọng/sensor, giả định 5 phút/bản ghi.

**Visualize:** Một số tổng nổi bật phía trên bảng bốn hàng. Số liệu căn phải. Chân slide ghi thời gian khảo sát và giả định mẫu số.

**Nguồn và lưu ý:** Báo cáo mục 4.3. Khảo sát 19:00 ngày 16/10 đến 19:00 ngày 23/10/2026, giờ Việt Nam. Đây là kiểm tra truy xuất và số lượng, không phải chứng nhận độ chính xác cảm biến. Mẫu lịch sử có khoảng thiếu.

> REVIEW: Chưa có góp ý.

## Slide 04 — Kiến trúc Streaming Lakehouse

**Vai trò:** Nối bài toán dữ liệu với các công nghệ trong học phần.

**Nội dung trên slide:**
- OpenAQ/Collector, Kafka, Spark, Iceberg/MinIO, Trino/Superset.
- Bronze lưu gốc, Silver làm sạch, Gold phục vụ phân tích.
- Dữ liệu mới và lịch sử dùng chung quy tắc xử lý.
- Spark MLlib huấn luyện từ lịch sử và ghi kết quả dự báo vào Iceberg.

**Visualize:** Sơ đồ năm bước ngang có mũi tên, nhấn lớp Iceberg/MinIO bằng nền đen. Bên dưới là ba lớp dữ liệu với mô tả ngắn.

**Nguồn và lưu ý:** Báo cáo mục 5–6 và lab Streaming Lakehouse. Toàn bộ sơ đồ là phương án dự kiến, chưa triển khai. Gold chỉ tổng hợp trung bình sau khi xác minh khoảng đo.

> REVIEW: Chưa có góp ý.

## Slide 05 — Dự báo PM2.5 trước 1 giờ

**Vai trò:** Làm rõ mục tiêu dự báo, mô hình và cách đánh giá ML.

**Nội dung trên slide:**
- Đầu vào là PM2.5 hiện tại, các giá trị trễ và giờ trong ngày.
- Random Forest Regression với Spark MLlib.
- So sánh baseline giữ nguyên số đo gần nhất bằng MAE và RMSE.
- Chia train/validation/test theo thời gian.
- Hiển thị dự báo từng trạm, đơn vị µg/m³.

**Visualize:** Bảng hai cột gồm đầu vào, mô hình, baseline, đánh giá và đầu ra. Thanh nhấn nhắc cách chia tập theo thời gian. Không vẽ đường dự báo hoặc sai số giả lập.

**Nguồn và lưu ý:** Thiết kế mới theo yêu cầu bổ sung ML, chưa huấn luyện hoặc đánh giá. Nguồn phương pháp: [Spark Random Forest Regression](https://spark.apache.org/docs/latest/ml-classification-regression.html#random-forest-regression), [RegressionEvaluator](https://spark.apache.org/docs/latest/api/python/reference/api/pyspark.ml.evaluation.RegressionEvaluator.html), [TimeSeriesSplit](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html). Cần xác minh ý nghĩa khoảng đo trước khi tạo chuỗi giờ. Các độ trễ phải bám mốc thời gian thực, chỉ dùng dữ liệu sẵn có khi phát hành dự báo, không dùng thông tin tương lai để điền dữ liệu thiếu. Test là giai đoạn tương lai giữ riêng. Không cam kết mô hình vượt baseline.

> REVIEW: Đã bổ sung phần ML theo yêu cầu.

## Slide 06 — Sản phẩm và kiểm chứng

**Vai trò:** Chốt đầu ra và tiêu chí để đánh giá đề tài.

**Nội dung trên slide:**
- Đầu ra gồm bảng Iceberg, dashboard, mô hình dự báo PM2.5 và báo cáo thực nghiệm.
- Kiểm chứng chống trùng, dữ liệu đến muộn và tối ưu lưu trữ.
- Cần xác minh khoảng đo trước khi tính trung bình.

**Visualize:** Bảng hai cột ghép từng đầu ra với cách kiểm chứng, bổ sung hàng mô hình dự báo và MAE/RMSE so với baseline. Một thanh nhấn thể hiện điều kiện cần giải quyết đầu tiên.

**Nguồn và lưu ý:** Báo cáo mục 4.4 và 7–8. Metadata hiện ghi khoảng đo một giờ dù mốc bản ghi cách nhau chủ yếu năm phút. Quy mô hai trạm còn nhỏ. Replay lịch sử phải phân biệt với dữ liệu live.

> REVIEW: Chưa có góp ý.
