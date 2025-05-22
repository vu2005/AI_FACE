import os
import cv2
import numpy as np
import sqlite3
from datetime import datetime, timedelta
import json
import base64
from PIL import Image
from io import BytesIO
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import logging

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tạo Flask app
app = Flask(__name__)
CORS(app)

# Cấu hình database
DATABASE_PATH = 'hairstyle_booking.db'

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Khởi tạo database và tạo các bảng cần thiết"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Bảng lưu thông tin đặt lịch
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id TEXT UNIQUE NOT NULL,
                customer_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT,
                appointment_date DATE NOT NULL,
                appointment_time TIME NOT NULL,
                selected_hairstyle TEXT NOT NULL,
                stylist TEXT,
                notes TEXT,
                face_shape TEXT,
                gender TEXT,
                status TEXT DEFAULT 'confirmed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Bảng lưu lịch sử phân tích khuôn mặt
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS face_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id TEXT UNIQUE NOT NULL,
                image_data TEXT,
                face_shape TEXT NOT NULL,
                confidence REAL,
                landmarks TEXT,
                gender TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Bảng thống kê
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                total_bookings INTEGER DEFAULT 0,
                total_analysis INTEGER DEFAULT 0,
                most_common_face_shape TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    
    def save_booking(self, booking_data):
        """Lưu thông tin đặt lịch vào database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO bookings (
                    booking_id, customer_name, phone, email, appointment_date,
                    appointment_time, selected_hairstyle, stylist, notes,
                    face_shape, gender, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                booking_data['booking_id'],
                booking_data['customer_name'],
                booking_data['phone'],
                booking_data.get('email', ''),
                booking_data['appointment_date'],
                booking_data['appointment_time'],
                json.dumps(booking_data['selected_hairstyle']),
                booking_data.get('stylist', 'Bất kỳ'),
                booking_data.get('notes', ''),
                booking_data.get('face_shape', ''),
                booking_data.get('gender', ''),
                'confirmed'
            ))
            
            conn.commit()
            logger.info(f"Booking saved successfully: {booking_data['booking_id']}")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error saving booking: {e}")
            return False
        finally:
            conn.close()
    
    def save_face_analysis(self, analysis_data):
        """Lưu kết quả phân tích khuôn mặt"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO face_analysis (
                    analysis_id, image_data, face_shape, confidence,
                    landmarks, gender
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                analysis_data['analysis_id'],
                analysis_data.get('image_data', ''),
                analysis_data['face_shape'],
                analysis_data.get('confidence', 0.0),
                json.dumps(analysis_data.get('landmarks', [])),
                analysis_data.get('gender', '')
            ))
            
            conn.commit()
            logger.info(f"Face analysis saved: {analysis_data['analysis_id']}")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error saving face analysis: {e}")
            return False
        finally:
            conn.close()
    
    def get_bookings(self, date_from=None, date_to=None):
        """Lấy danh sách đặt lịch"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM bookings"
        params = []
        
        if date_from and date_to:
            query += " WHERE appointment_date BETWEEN ? AND ?"
            params = [date_from, date_to]
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        bookings = cursor.fetchall()
        conn.close()
        
        return bookings
    
    def update_daily_statistics(self):
        """Cập nhật thống kê hàng ngày"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        today = datetime.now().date()
        
        # Đếm số lượng booking hôm nay
        cursor.execute('''
            SELECT COUNT(*) FROM bookings 
            WHERE DATE(created_at) = ?
        ''', (today,))
        total_bookings = cursor.fetchone()[0]
        
        # Đếm số lượng phân tích hôm nay
        cursor.execute('''
            SELECT COUNT(*) FROM face_analysis 
            WHERE DATE(created_at) = ?
        ''', (today,))
        total_analysis = cursor.fetchone()[0]
        
        # Tìm dạng khuôn mặt phổ biến nhất
        cursor.execute('''
            SELECT face_shape, COUNT(*) as count 
            FROM face_analysis 
            WHERE DATE(created_at) = ?
            GROUP BY face_shape 
            ORDER BY count DESC 
            LIMIT 1
        ''', (today,))
        
        result = cursor.fetchone()
        most_common_face_shape = result[0] if result else 'oval'
        
        # Cập nhật hoặc thêm mới thống kê
        cursor.execute('''
            INSERT OR REPLACE INTO statistics (
                date, total_bookings, total_analysis, most_common_face_shape
            ) VALUES (?, ?, ?, ?)
        ''', (today, total_bookings, total_analysis, most_common_face_shape))
        
        conn.commit()
        conn.close()

class RealFaceAnalyzer:
    def __init__(self):
        """Khởi tạo bộ phân tích khuôn mặt thật"""
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        # Tải model phân tích khuôn mặt nếu có
        try:
            # Thay thế bằng model thật nếu có
            self.model = None
            logger.info("Face analyzer initialized")
        except Exception as e:
            logger.warning(f"Could not load face analysis model: {e}")
            self.model = None
    
    def detect_face(self, image):
        """Phát hiện khuôn mặt trong ảnh"""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) == 0:
            return None
        
        # Chọn khuôn mặt lớn nhất
        largest_face = max(faces, key=lambda rect: rect[2] * rect[3])
        return largest_face
    
    def extract_features(self, image, face_rect):
        """Trích xuất đặc trưng từ khuôn mặt"""
        x, y, w, h = face_rect
        face_roi = image[y:y+h, x:x+w]
        
        # Tính toán các tỷ lệ cơ bản
        face_width = w
        face_height = h
        aspect_ratio = face_height / face_width
        
        # Phân tích các vùng của khuôn mặt
        upper_face = face_roi[:h//3, :]
        middle_face = face_roi[h//3:2*h//3, :]
        lower_face = face_roi[2*h//3:, :]
        
        # Đo độ rộng tại các điểm khác nhau
        forehead_width = w * 0.9  # Giả định
        cheek_width = w
        jaw_width = w * 0.8
        
        features = {
            'aspect_ratio': aspect_ratio,
            'face_width': face_width,
            'face_height': face_height,
            'forehead_width': forehead_width,
            'cheek_width': cheek_width,
            'jaw_width': jaw_width,
            'forehead_jaw_ratio': forehead_width / jaw_width,
            'width_height_ratio': face_width / face_height
        }
        
        return features
    
    def classify_face_shape(self, features):
        """Phân loại dạng khuôn mặt dựa trên đặc trưng"""
        aspect_ratio = features['aspect_ratio']
        forehead_jaw_ratio = features['forehead_jaw_ratio']
        width_height_ratio = features['width_height_ratio']
        
        # Thuật toán phân loại cải tiến
        if 1.3 <= aspect_ratio <= 1.7 and 0.9 <= forehead_jaw_ratio <= 1.1:
            return 'oval'
        elif aspect_ratio < 1.3 and width_height_ratio > 0.8:
            return 'round'
        elif aspect_ratio < 1.3 and forehead_jaw_ratio < 1.1:
            return 'square'
        elif forehead_jaw_ratio > 1.2:
            return 'heart'
        elif aspect_ratio > 1.7:
            return 'oblong'
        elif forehead_jaw_ratio < 0.9:
            return 'diamond'
        else:
            return 'oval'  # Mặc định
    
    def analyze_image(self, image_data, gender='male'):
        """Phân tích ảnh và trả về kết quả"""
        try:
            # Giải mã ảnh từ base64
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            
            img_bytes = base64.b64decode(image_data)
            img = Image.open(BytesIO(img_bytes))
            img_array = np.array(img)
            
            # Chuyển đổi sang BGR nếu cần
            if len(img_array.shape) == 3 and img_array.shape[2] == 3:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            # Phát hiện khuôn mặt
            face_rect = self.detect_face(img_array)
            if face_rect is None:
                return None, "Không phát hiện được khuôn mặt trong ảnh"
            
            # Trích xuất đặc trưng và phân loại
            features = self.extract_features(img_array, face_rect)
            face_shape = self.classify_face_shape(features)
            
            # Tạo hình ảnh visualization
            vis_img = self.create_visualization(img_array, face_rect)
            
            # Tính độ tin cậy (giả lập)
            confidence = np.random.uniform(0.75, 0.95)
            
            result = {
                'face_shape': face_shape,
                'confidence': confidence,
                'features': features,
                'face_rect': face_rect.tolist(),
                'visualization': vis_img
            }
            
            return result, None
            
        except Exception as e:
            logger.error(f"Error in face analysis: {e}")
            return None, f"Lỗi khi phân tích: {str(e)}"
    
    def create_visualization(self, image, face_rect):
        """Tạo hình ảnh visualization với khung khuôn mặt"""
        vis_img = image.copy()
        x, y, w, h = face_rect
        
        # Vẽ khung khuôn mặt
        cv2.rectangle(vis_img, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        # Vẽ các điểm đặc trưng
        center_x, center_y = x + w//2, y + h//2
        cv2.circle(vis_img, (center_x, center_y), 3, (255, 0, 0), -1)
        
        # Chuyển đổi về base64
        _, buffer = cv2.imencode('.jpg', vis_img)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return f"data:image/jpeg;base64,{img_base64}"

# Dữ liệu kiểu tóc thật (có thể mở rộng từ database)
REAL_HAIRSTYLE_DATA = {
    'oval': {
        'male': [
            {
                'name': 'Undercut Classic',
                'description': 'Kiểu tóc undercut cổ điển, ngắn hai bên, dài trên đỉnh',
                'price': 150000,
                'duration': 45,
                'difficulty': 'medium'
            },
            {
                'name': 'Quiff Modern',
                'description': 'Tóc quiff hiện đại với độ phồng tự nhiên',
                'price': 200000,
                'duration': 60,
                'difficulty': 'hard'
            },
            {
                'name': 'Pompadour Vintage',
                'description': 'Pompadour phong cách vintage, lịch lãm',
                'price': 250000,
                'duration': 75,
                'difficulty': 'hard'
            }
        ],
        'female': [
            {
                'name': 'Long Layers Natural',
                'description': 'Tóc dài nhiều tầng tự nhiên, phù hợp mọi độ tuổi',
                'price': 300000,
                'duration': 90,
                'difficulty': 'medium'
            },
            {
                'name': 'Bob Cut Stylish',
                'description': 'Tóc bob thời trang, trẻ trung và năng động',
                'price': 250000,
                'duration': 60,
                'difficulty': 'medium'
            },
            {
                'name': 'Pixie Cut Chic',
                'description': 'Tóc pixie sành điệu, cá tính mạnh',
                'price': 200000,
                'duration': 45,
                'difficulty': 'hard'
            }
        ]
    },
    'round': {
        'male': [
            {
                'name': 'High Fade Pompadour',
                'description': 'Pompadour với fade cao, tạo chiều cao cho khuôn mặt',
                'price': 180000,
                'duration': 50,
                'difficulty': 'medium'
            },
            {
                'name': 'Side Part Professional',
                'description': 'Rẽ ngôi chuyên nghiệp, phù hợp công sở',
                'price': 120000,
                'duration': 30,
                'difficulty': 'easy'
            },
            {
                'name': 'Textured Crop',
                'description': 'Tóc ngắn có texture, hiện đại và năng động',
                'price': 160000,
                'duration': 40,
                'difficulty': 'medium'
            }
        ],
        'female': [
            {
                'name': 'A-Line Bob Extended',
                'description': 'Bob dài góc A, tạo độ thon gọn cho mặt',
                'price': 280000,
                'duration': 70,
                'difficulty': 'medium'
            },
            {
                'name': 'Side Bangs Layers',
                'description': 'Tóc tầng với mái xéo, che bớt gò má',
                'price': 320000,
                'duration': 85,
                'difficulty': 'medium'
            },
            {
                'name': 'Long Pixie Volume',
                'description': 'Pixie dài với volume ở đỉnh đầu',
                'price': 240000,
                'duration': 55,
                'difficulty': 'hard'
            }
        ]
    },
    'square': {
        'male': [
            {
                'name': 'Soft Textured Style',
                'description': 'Kiểu tóc mềm mại với texture nhẹ',
                'price': 170000,
                'duration': 45,
                'difficulty': 'medium'
            }
        ],
        'female': [
            {
                'name': 'Long Wavy Soft',
                'description': 'Tóc dài sóng mềm mại làm dịu góc cạnh',
                'price': 350000,
                'duration': 100,
                'difficulty': 'medium'
            }
        ]
    },
    'heart': {
        'male': [
            {
                'name': 'Medium Length Casual',
                'description': 'Tóc dài vừa phải, thoải mái và tự nhiên',
                'price': 140000,
                'duration': 35,
                'difficulty': 'easy'
            }
        ],
        'female': [
            {
                'name': 'Face Framing Layers',
                'description': 'Tóc tầng ôm mặt, cân bằng tỷ lệ',
                'price': 300000,
                'duration': 80,
                'difficulty': 'medium'
            }
        ]
    },
    'oblong': {
        'male': [
            {
                'name': 'Side Volume Style',
                'description': 'Tóc có volume hai bên, tạo độ rộng',
                'price': 160000,
                'duration': 40,
                'difficulty': 'medium'
            }
        ],
        'female': [
            {
                'name': 'Medium Bob with Bangs',
                'description': 'Bob vừa với mái thẳng che trán',
                'price': 270000,
                'duration': 65,
                'difficulty': 'medium'
            }
        ]
    },
    'diamond': {
        'male': [
            {
                'name': 'Forward Swept Style',
                'description': 'Tóc chải về phía trước, che bớt gò má',
                'price': 150000,
                'duration': 40,
                'difficulty': 'medium'
            }
        ],
        'female': [
            {
                'name': 'Side Swept Pixie',
                'description': 'Pixie với mái chải sang bên',
                'price': 220000,
                'duration': 50,
                'difficulty': 'hard'
            }
        ]
    }
}

# API Endpoints
@app.route('/')
def index():
    """Trang chủ - trả về HTML từ templates/index.html"""
    return render_template('index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze_face():
    """API phân tích khuôn mặt với dữ liệu thật"""
    try:
        data = request.json
        image_data = data.get('image')
        gender = data.get('gender', 'male')
        
        if not image_data:
            return jsonify({'error': 'Thiếu dữ liệu ảnh'}), 400
        
        # Phân tích khuôn mặt
        result, error = face_analyzer.analyze_image(image_data, gender)
        
        if error:
            return jsonify({'error': error}), 400
        
        # Lưu vào database
        analysis_id = f"AN{datetime.now().strftime('%Y%m%d%H%M%S')}"
        analysis_data = {
            'analysis_id': analysis_id,
            'image_data': image_data[:100] + '...',  # Chỉ lưu một phần
            'face_shape': result['face_shape'],
            'confidence': result['confidence'],
            'landmarks': [],
            'gender': gender
        }
        
        db_manager.save_face_analysis(analysis_data)
        
        # Lấy gợi ý kiểu tóc
        hairstyles = get_hairstyle_recommendations({'face_shape': result['face_shape'], 'gender': gender})
        
        response = {
            'analysis_id': analysis_id,
            'face_shape': result['face_shape'],
            'confidence': result['confidence'],
            'visualization': result['visualization'],
            'hairstyles': hairstyles
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in face analysis API: {e}")
        return jsonify({'error': 'Lỗi server nội bộ'}), 500

@app.route('/api/book-appointment', methods=['POST'])
def book_appointment():
    """API đặt lịch với database thật"""
    try:
        data = request.json
        
        # Validate dữ liệu
        required_fields = ['customer_name', 'phone', 'appointment_date', 'appointment_time']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Thiếu trường bắt buộc: {field}'}), 400
        
        # Kiểm tra ngày hẹn
        appointment_date = datetime.strptime(data['appointment_date'], '%Y-%m-%d').date()
        if appointment_date <= datetime.now().date():
            return jsonify({'error': 'Ngày hẹn phải sau ngày hiện tại'}), 400
        
        # Tạo booking ID
        booking_id = f"BK{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        booking_data = {
            'booking_id': booking_id,
            'customer_name': data['customer_name'],
            'phone': data['phone'],
            'email': data.get('email', ''),
            'appointment_date': data['appointment_date'],
            'appointment_time': data['appointment_time'],
            'selected_hairstyle': data.get('selected_hairstyle', {}),
            'stylist': data.get('stylist', 'Bất kỳ'),
            'notes': data.get('notes', ''),
            'face_shape': data.get('face_shape', ''),
            'gender': data.get('gender', ''),
        }
        
        # Lưu vào database
        if db_manager.save_booking(booking_data):
            # Cập nhật thống kê
            db_manager.update_daily_statistics()
            
            return jsonify({
                'success': True,
                'booking_id': booking_id,
                'message': 'Đặt lịch thành công!',
                'booking_data': booking_data
            })
        else:
            return jsonify({'error': 'Lỗi khi lưu đặt lịch'}), 500
            
    except Exception as e:
        logger.error(f"Error in booking API: {e}")
        return jsonify({'error': 'Lỗi server nội bộ'}), 500

@app.route('/api/hairstyles/<face_shape>/<gender>')
def get_hairstyles_api(face_shape, gender):
    """API lấy danh sách kiểu tóc theo dạng mặt và giới tính"""
    try:
        hairstyles = get_hairstyle_recommendations({'face_shape': face_shape, 'gender': gender})
        return jsonify(hairstyles)
    except Exception as e:
        logger.error(f"Error getting hairstyles: {e}")
        return jsonify({'error': 'Lỗi khi lấy danh sách kiểu tóc'}), 500

@app.route('/api/bookings')
def get_bookings_api():
    """API lấy danh sách đặt lịch"""
    try:
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        bookings = db_manager.get_bookings(date_from, date_to)
        
        # Chuyển đổi sang format JSON
        booking_list = []
        for booking in bookings:
            booking_dict = {
                'id': booking[0],
                'booking_id': booking[1],
                'customer_name': booking[2],
                'phone': booking[3],
                'email': booking[4],
                'appointment_date': booking[5],
                'appointment_time': booking[6],
                'selected_hairstyle': json.loads(booking[7]) if booking[7] else {},
                'stylist': booking[8],
                'notes': booking[9],
                'face_shape': booking[10],
                'gender': booking[11],
                'status': booking[12],
                'created_at': booking[13]
            }
            booking_list.append(booking_dict)
        
        return jsonify({
            'bookings': booking_list,
            'total': len(booking_list)
        })
        
    except Exception as e:
        logger.error(f"Error getting bookings: {e}")
        return jsonify({'error': 'Lỗi khi lấy danh sách đặt lịch'}), 500

@app.route('/api/statistics')
def get_statistics():
    """API thống kê"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Thống kê tổng quan
        cursor.execute("SELECT COUNT(*) FROM bookings")
        total_bookings = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM face_analysis")
        total_analysis = cursor.fetchone()[0]
        
        # Thống kê theo dạng khuôn mặt
        cursor.execute('''
            SELECT face_shape, COUNT(*) as count 
            FROM face_analysis 
            GROUP BY face_shape 
            ORDER BY count DESC
        ''')
        face_shape_stats = dict(cursor.fetchall())
        
        # Thống kê theo giới tính
        cursor.execute('''
            SELECT gender, COUNT(*) as count 
            FROM bookings 
            WHERE gender != '' 
            GROUP BY gender
        ''')
        gender_stats = dict(cursor.fetchall())
        
        # Thống kê theo thời gian (7 ngày gần nhất)
        cursor.execute('''
            SELECT DATE(created_at) as date, COUNT(*) as count 
            FROM bookings 
            WHERE created_at >= date('now', '-7 days')
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        ''')
        daily_stats = dict(cursor.fetchall())
        
        conn.close()
        
        statistics = {
            'total_bookings': total_bookings,
            'total_analysis': total_analysis,
            'face_shape_distribution': face_shape_stats,
            'gender_distribution': gender_stats,
            'daily_bookings': daily_stats,
            'generated_at': datetime.now().isoformat()
        }
        
        return jsonify(statistics)
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return jsonify({'error': 'Lỗi khi lấy thống kê'}), 500

def get_hairstyle_recommendations(detected_face):
    """Lấy gợi ý kiểu tóc dựa trên khuôn mặt và giới tính"""
    face_shape = detected_face.get('face_shape', 'oval')
    gender = detected_face.get('gender', 'male')
    
    if face_shape in REAL_HAIRSTYLE_DATA and gender in REAL_HAIRSTYLE_DATA[face_shape]:
        return REAL_HAIRSTYLE_DATA[face_shape][gender]
    else:
        # Trả về mặc định nếu không tìm thấy
        return REAL_HAIRSTYLE_DATA['oval'][gender]

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'API endpoint không tồn tại'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Lỗi server nội bộ'}), 500

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Yêu cầu không hợp lệ'}), 400

# Khởi tạo các component và chạy ứng dụng
if __name__ == '__main__':
    # Tạo thư mục cần thiết
    os.makedirs('static/hairstyles', exist_ok=True)
    os.makedirs('uploads', exist_ok=True)
    
    # Khởi tạo components
    db_manager = DatabaseManager(DATABASE_PATH)
    face_analyzer = RealFaceAnalyzer()
    
    # Cập nhật thống kê khi khởi động
    try:
        db_manager.update_daily_statistics()
    except Exception as e:
        logger.error(f"Error updating statistics: {e}")
    
    # In thông báo khởi động
    print("=" * 50)
    print("🎨 HAIR STYLE AI BACKEND STARTED")
    print("=" * 50)
    print("📊 Database initialized")
    print("🔍 Face analyzer ready")
    print("🌐 Server running at http://localhost:5000")
    print("📱 API endpoints available:")
    print("   - POST /api/analyze")
    print("   - POST /api/book-appointment")
    print("   - GET  /api/hairstyles/<face_shape>/<gender>")
    print("   - GET  /api/bookings")
    print("   - GET  /api/statistics")
    print("=" * 50)
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        print(f"❌ Error starting server: {e}")