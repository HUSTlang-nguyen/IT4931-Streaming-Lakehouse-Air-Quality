# Fixtures nhỏ

**Đã có:** openaq-hourly-sample.json, một hàng giờ thực từ mỗi sensor cùng thời điểm truy xuất, source URL, provider và license metadata.

Chỉ lưu mẫu nhỏ đã làm sạch, không API key/header auth. Mẫu JSON được cố định để đọc schema offline; không khẳng định freshness hiện tại. Synthetic fixtures trong unit test tạo riêng duplicate/correction/gap/invalid; source và synthetic phải phân biệt. ML leakage/late Spark fixtures còn chờ implementation.
