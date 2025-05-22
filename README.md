# 🎨 Hair Style AI - Hệ thống Phân tích Khuôn mặt và Đặt lịch Cắt tóc

## 📖 Tổng quan

Hair Style AI là một ứng dụng web thông minh sử dụng **dữ liệu thật** để:
- 📸 Phân tích khuôn mặt từ camera/ảnh upload
- 🎯 Gợi ý kiểu tóc phù hợp dựa trên dạng khuôn mặt
- 📅 Đặt lịch cắt tóc với thông tin chi tiết
- 📊 Quản lý và thống kê dữ liệu khách hàng

## ✨ Tính năng chính

### 🔍 Phân tích Khuôn mặt Thật
- Sử dụng OpenCV và Computer Vision
- Phát hiện 6 dạng khuôn mặt: Oval, Tròn, Vuông, Tim, Dài, Kim cương
- Tính toán độ tin cậy và đặc trưng khuôn mặt
- Lưu trữ lịch sử phân tích

### 💇 Gợi ý Kiểu tóc Thông minh
- Database kiểu tóc thật với giá cả, thời gian
- Phân loại theo giới tính và dạng khuôn mặt
- Mô tả chi tiết và hình ảnh minh họa
- Tư vấn phù hợp với từng khuôn mặt

### 📅 Hệ thống Đặt lịch Hoàn chỉnh
- Database SQLite lưu trữ thông tin thật
- Validation ngày giờ, giờ làm việc
- Quản lý trạng thái: Confirmed, Completed, Cancelled
- Tìm kiếm và cập nhật đặt lịch

### 📊 Thống kê và Báo cáo
- Thống kê theo ngày, tuần, tháng
- Phân tích xu hướng dạng khuôn mặt
- Export dữ liệu CSV/JSON
- Dashboard admin quản lý

## 🛠️ Công nghệ sử dụng

### Backend
- **Flask** - Web framework Python
- **OpenCV** - Computer vision và phân tích ảnh
- **SQLite** - Database lưu trữ dữ liệu
- **TensorFlow** - Machine learning (tùy chọn)
- **Pillow** - Xử lý ảnh

### Frontend
- **HTML5/CSS3** - Giao diện responsive
- **JavaScript ES6** - Logic frontend
- **WebRTC** - Truy cập camera
- **Canvas API** - Xử lý ảnh client-side

## 📁 Cấu trúc Project

```
hair-style-ai/
├── app.py                 # Main Flask application
├── test_setup.py         # Script setup và test
├── requirements.txt      # Python dependencies
├── Dockerfile           # Docker configuration
├── docker-compose.yml   # Docker compose
├── README.md           # Tài liệu này
├── hairstyle_booking.db # SQLite database
├── static/
│   └── hairstyles/     # Ảnh kiểu tóc
├── uploads/           # Thư mục upload ảnh
└── templates/        # HTML templates (nếu có)
```

## 🚀 Cài đặt và Chạy

### Cách 1: Chạy trực tiếp Python

1. **Clone hoặc tạo project:**
```bash
mkdir hair-style-ai
cd hair-style-ai
```

2. **Tạo virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate     # Windows
```

3. **Cài đặt dependencies:**
```bash
pip install -r requirements.txt
```

4. **Chạy script setup:**
```bash
python test_setup.py
```

5. **Khởi động server:**
```bash
python app.py
```

6. **Mở trình duyệt:**
```
http://localhost:5000
```

### Cách 2: Sử dụng Docker

1. **Build và chạy:**
```bash
docker-compose up --build
```

2. **Truy cập ứng dụng:**
```
http://localhost:5000
```

## 📋 API Documentation

### 🔍 Phân tích Khuôn mặt
```http
POST /api/analyze
Content-Type: application/json

{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQ...",
  "gender": "male"
}
```

**Response:**
```json
{
  "analysis_id": "AN20241101123456",
  "face_shape": "oval",
  "confidence": 0.87,
  "visualization": "data:image/jpeg;base64,...",
  "hairstyles": [...]
}
```

### 📅 Đặt lịch
```http
POST /api/book-appointment
Content-Type: application/json

{
  "customer_name": "Nguyễn Văn A",
  "phone": "0901234567",
  "email": "user@example.com",
  "appointment_date": "2024-11-25",
  "appointment_time": "10:00",
  "selected_hairstyle": {
    "name": "Undercut Classic",
    "price": 150000
  },
  "stylist": "Anh Minh",
  "face_shape": "oval",
  "gender": "male"
}
```

### 📊 Thống kê
```http
GET /api/statistics

Response:
{
  "total_bookings": 15,
  "total_analysis": 42,
  "face_shape_distribution": {
    "oval": 12,
    "round": 8,
    "square": 6
  },
  "daily_bookings": {...}
}
```

### 🔍 Tìm kiếm đặt lịch
```http
GET /api/search-bookings?phone=0901234567&name=Nguyen
```

## 💾 Database Schema

### Bảng `bookings`
| Cột | Kiểu | Mô tả |
|-----|------|-------|
| id | INTEGER PRIMARY KEY | ID tự tăng |
| booking_id | TEXT UNIQUE | Mã đặt lịch |
| customer_name | TEXT | Tên khách hàng |
| phone | TEXT | Số điện thoại |
| email | TEXT | Email |
| appointment_date | DATE | Ngày hẹn |
| appointment_time | TIME | Giờ hẹn |
| selected_hairstyle | TEXT | Kiểu tóc (JSON) |
| stylist | TEXT | Thợ cắt tóc |
| face_shape | TEXT | Dạng khuôn mặt |
| gender | TEXT | Giới tính |
| status | TEXT | Trạng thái |
| created_at | TIMESTAMP | Ngày tạo |

### Bảng `face_analysis`
| Cột | Kiểu | Mô tả |
|-----|------|-------|
| id | INTEGER PRIMARY KEY | ID tự tăng |
| analysis_id | TEXT UNIQUE | Mã phân tích |
| face_shape | TEXT | Dạng khuôn mặt |
| confidence | REAL | Độ tin cậy |
| gender | TEXT | Giới tính |
| created_at | TIMESTAMP | Ngày phân tích |

## 🎯 Dữ liệu Thật vs Giả định

### ✅ Sử dụng Dữ liệu Thật:
- **Camera thật:** WebRTC API truy cập camera device
- **Phân tích ảnh thật:** OpenCV xử lý ảnh thực tế
- **Database thật:** SQLite lưu trữ persistent
- **Validation thật:** Kiểm tra ngày giờ, format dữ liệu
- **Tính toán thật:** Thuật toán phân tích khuôn mặt

### ❌ Tránh Dữ liệu Giả:
- Không dùng ảnh placeholder cố định
- Không dùng dữ liệu hardcode
- Không dùng random fake data
- Không dùng mock API responses

## 🧪 Testing

### Test tự động:
```bash
python test_setup.py --test-api
```

### Test thủ công:
1. **Test Camera:** Bật camera và chụp ảnh
2. **Test Phân tích:** Upload ảnh thật và xem kết quả
3. **Test Đặt lịch:** Điền form với dữ liệu thật
4. **Test Database:** Kiểm tra SQLite browser

## 📊 Monitoring và Logs

### Logs ứng dụng:
```bash
tail -f app.log
```

### Database queries:
```bash
sqlite3 hairstyle_booking.db
.tables
SELECT * FROM bookings LIMIT 5;
```

### System monitoring:
- CPU/Memory usage
- Database size growth  
- API response times
- Error rates

## 🔒 Bảo mật

### Đã implement:
- Input validation và sanitization
- SQL injection prevention
- File upload restrictions
- API rate limiting (có thể thêm)

### Cần bổ sung:
- User authentication
- HTTPS/SSL certificates
- Data encryption
- Backup strategy

## 🚀 Deployment

### Development:
```bash
python app.py
```

### Production với Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Production với Docker:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## 🔧 Customization

### Thêm dạng khuôn mặt mới:
1. Cập nhật `REAL_HAIRSTYLE_DATA` trong `app.py`
2. Thêm logic phân loại trong `classify_face_shape()`
3. Thêm ảnh mẫu vào `static/hairstyles/`

### Thêm kiểu tóc mới:
1. Cập nhật database structure nếu cần
2. Thêm ảnh và metadata
3. Update recommendation algorithm

### Tích hợp SMS/Email:
1. Thêm API keys vào environment variables
2. Implement `send_confirmation_sms()` và `send_confirmation_email()`
3. Cấu hình SMTP/SMS gateway

## 🐛 Troubleshooting

### Lỗi Camera không hoạt động:
- Kiểm tra browser permissions
- Thử HTTPS thay vì HTTP
- Kiểm tra camera drivers

### Lỗi Database:
```bash
# Tái tạo database
rm hairstyle_booking.db
python test_setup.py
```

### Lỗi OpenCV:
```bash
# Cài đặt lại OpenCV
pip uninstall opencv-python
pip install opencv-python-headless
```

## 📈 Roadmap

### Phase 1 (Hiện tại):
- ✅ Phân tích khuôn mặt cơ bản
- ✅ Đặt lịch và quản lý
- ✅ API và database

### Phase 2 (Tương lai):
- 🔄 Machine learning model training
- 🔄 Advanced face analysis
- 🔄 Mobile app
- 🔄 Payment integration

### Phase 3 (Mở rộng):
- 🔄 Multi-language support
- 🔄 AI stylist chatbot  
- 🔄 Augmented reality try-on
- 🔄 Social media integration

## 👥 Đóng góp

1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Push và tạo Pull Request

## 📞 Hỗ trợ

- **Email:** support@hairstyle-ai.com
- **Issue tracker:** GitHub Issues
- **Documentation:** Wiki pages

## 📄 License

MIT License - Xem file LICENSE để biết thêm chi tiết.

---

**🎉 Chúc bạn sử dụng Hair Style AI thành công!**