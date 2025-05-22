#!/usr/bin/env python3
"""
Script khởi tạo dữ liệu test và chạy hệ thống Hair Style AI
"""

import os
import sys
import json
import sqlite3
import requests
import base64
from datetime import datetime, timedelta
from PIL import Image, ImageDraw
import io
import random

# Thêm thư mục hiện tại vào Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_sample_face_image(face_shape='oval', gender='male'):
    """Tạo ảnh khuôn mặt mẫu để test"""
    # Tạo ảnh 300x300 với background trắng
    img = Image.new('RGB', (300, 300), 'white')
    draw = ImageDraw.Draw(img)
    
    # Vẽ khuôn mặt tùy theo dạng
    center_x, center_y = 150, 150
    
    if face_shape == 'oval':
        # Khuôn mặt oval
        draw.ellipse([75, 60, 225, 240], fill='#FFDBAC', outline='#D4AF37')
    elif face_shape == 'round':
        # Khuôn mặt tròn
        draw.ellipse([70, 70, 230, 230], fill='#FFDBAC', outline='#D4AF37')
    elif face_shape == 'square':
        # Khuôn mặt vuông
        draw.rectangle([75, 75, 225, 225], fill='#FFDBAC', outline='#D4AF37')
    elif face_shape == 'heart':
        # Khuôn mặt tim (tam giác ngược)
        points = [(150, 240), (75, 75), (225, 75)]
        draw.polygon(points, fill='#FFDBAC', outline='#D4AF37')
    
    # Vẽ mắt
    draw.ellipse([100, 120, 120, 140], fill='black')
    draw.ellipse([180, 120, 200, 140], fill='black')
    
    # Vẽ mũi
    draw.ellipse([145, 150, 155, 165], fill='#F4A460')
    
    # Vẽ miệng
    draw.arc([130, 170, 170, 190], 0, 180, fill='red', width=3)
    
    # Lưu ảnh tạm thời
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    buffer.seek(0)
    
    # Chuyển sang base64
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return f"data:image/jpeg;base64,{img_base64}"

def create_test_database():
    """Tạo database test với dữ liệu mẫu"""
    print("🗄️  Đang tạo database test...")
    
    db_path = 'hairstyle_booking.db'
    
    # Xóa database cũ nếu có
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Tạo bảng bookings
    cursor.execute('''
        CREATE TABLE bookings (
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
    
    # Tạo bảng face_analysis
    cursor.execute('''
        CREATE TABLE face_analysis (
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
    
    # Tạo bảng statistics
    cursor.execute('''
        CREATE TABLE statistics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            total_bookings INTEGER DEFAULT 0,
            total_analysis INTEGER DEFAULT 0,
            most_common_face_shape TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Thêm dữ liệu mẫu
    sample_bookings = [
        {
            'booking_id': 'BK20241101001',
            'customer_name': 'Nguyễn Văn A',
            'phone': '0901234567',
            'email': 'nguyenvana@email.com',
            'appointment_date': '2024-11-25',
            'appointment_time': '10:00',
            'selected_hairstyle': '{"name": "Undercut Classic", "price": 150000}',
            'stylist': 'Anh Minh',
            'face_shape': 'oval',
            'gender': 'male',
            'status': 'confirmed'
        },
        {
            'booking_id': 'BK20241101002',
            'customer_name': 'Trần Thị B',
            'phone': '0912345678',
            'email': 'tranthib@email.com',
            'appointment_date': '2024-11-26',
            'appointment_time': '14:00',
            'selected_hairstyle': '{"name": "Bob Cut Stylish", "price": 250000}',
            'stylist': 'Chị Lan',
            'face_shape': 'round',
            'gender': 'female',
            'status': 'confirmed'
        },
        {
            'booking_id': 'BK20241101003',
            'customer_name': 'Lê Văn C',
            'phone': '0923456789',
            'email': 'levanc@email.com',
            'appointment_date': '2024-11-27',
            'appointment_time': '16:00',
            'selected_hairstyle': '{"name": "Pompadour Vintage", "price": 250000}',
            'stylist': 'Anh Tuấn',
            'face_shape': 'square',
            'gender': 'male',
            'status': 'completed'
        }
    ]
    
    for booking in sample_bookings:
        cursor.execute('''
            INSERT INTO bookings (
                booking_id, customer_name, phone, email, appointment_date,
                appointment_time, selected_hairstyle, stylist, face_shape, gender, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            booking['booking_id'], booking['customer_name'], booking['phone'],
            booking['email'], booking['appointment_date'], booking['appointment_time'],
            booking['selected_hairstyle'], booking['stylist'], booking['face_shape'],
            booking['gender'], booking['status']
        ))
    
    # Thêm dữ liệu phân tích mẫu
    face_shapes = ['oval', 'round', 'square', 'heart', 'oblong', 'diamond']
    genders = ['male', 'female']
    
    for i in range(20):
        analysis_id = f"AN2024110100{i+1:02d}"
        face_shape = random.choice(face_shapes)
        gender = random.choice(genders)
        confidence = random.uniform(0.75, 0.95)
        
        cursor.execute('''
            INSERT INTO face_analysis (
                analysis_id, face_shape, confidence, gender
            ) VALUES (?, ?, ?, ?)
        ''', (analysis_id, face_shape, confidence, gender))
    
    conn.commit()
    conn.close()
    
    print("✅ Database test đã được tạo thành công!")

def test_api_endpoints():
    """Test các API endpoints"""
    print("🧪 Đang test API endpoints...")
    
    base_url = "http://localhost:5000"
    
    # Test 1: Phân tích khuôn mặt
    print("\n1. Testing face analysis API...")
    try:
        sample_image = create_sample_face_image('oval', 'male')
        
        response = requests.post(f"{base_url}/api/analyze", 
                               json={
                                   'image': sample_image,
                                   'gender': 'male'
                               },
                               timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Face shape detected: {result['face_shape']}")
            print(f"   ✅ Confidence: {result['confidence']:.2f}")
        else:
            print(f"   ❌ Error: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Connection error: {e}")
    
    # Test 2: Đặt lịch
    print("\n2. Testing booking API...")
    try:
        tomorrow = datetime.now() + timedelta(days=1)
        booking_data = {
            'customer_name': 'Test User',
            'phone': '0900000000',
            'email': 'test@example.com',
            'appointment_date': tomorrow.strftime('%Y-%m-%d'),
            'appointment_time': '10:00',
            'selected_hairstyle': {
                'name': 'Test Hairstyle',
                'price': 100000
            },
            'stylist': 'Test Stylist',
            'face_shape': 'oval',
            'gender': 'male'
        }
        
        response = requests.post(f"{base_url}/api/book-appointment",
                                json=booking_data,
                                timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Booking created: {result['booking_id']}")
        else:
            print(f"   ❌ Error: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Connection error: {e}")
    
    # Test 3: Lấy thống kê
    print("\n3. Testing statistics API...")
    try:
        response = requests.get(f"{base_url}/api/statistics", timeout=10)
        
        if response.status_code == 200:
            stats = response.json()
            print(f"   ✅ Total bookings: {stats['total_bookings']}")
            print(f"   ✅ Total analysis: {stats['total_analysis']}")
        else:
            print(f"   ❌ Error: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Connection error: {e}")

def create_sample_hairstyle_images():
    """Tạo ảnh mẫu cho các kiểu tóc"""
    print("🖼️  Đang tạo ảnh mẫu cho kiểu tóc...")
    
    # Tạo thư mục static/hairstyles nếu chưa có
    os.makedirs('static/hairstyles', exist_ok=True)
    
    hairstyles = [
        'undercut.jpg', 'quiff.jpg', 'pompadour.jpg',
        'long_layers.jpg', 'bob.jpg', 'pixie.jpg'
    ]
    
    for hairstyle in hairstyles:
        img = Image.new('RGB', (200, 200), 'lightgray')
        draw = ImageDraw.Draw(img)
        
        # Vẽ text tên kiểu tóc
        text = hairstyle.replace('.jpg', '').replace('_', ' ').title()
        bbox = draw.textbbox((0, 0), text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        draw.text(
            ((200 - text_width) // 2, (200 - text_height) // 2),
            text,
            fill='black'
        )
        
        img.save(f'static/hairstyles/{hairstyle}')
    
    print("✅ Ảnh mẫu kiểu tóc đã được tạo!")

def setup_requirements():
    """Tạo file requirements.txt"""
    requirements = [
        'Flask==2.3.3',
        'Flask-CORS==4.0.0',
        'opencv-python==4.8.1.78',
        'numpy==1.24.3',
        'tensorflow==2.13.0',
        'Pillow==10.0.1',
        'requests==2.31.0',
        'pandas==2.0.3',
        'scikit-learn==1.3.0'
    ]
    
    with open('requirements.txt', 'w') as f:
        f.write('\n'.join(requirements))
    
    print("📦 File requirements.txt đã được tạo!")

def create_docker_setup():
    """Tạo file Docker setup"""
    dockerfile = '''FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p static/hairstyles uploads

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
'''
    
    docker_compose = '''version: '3.8'

services:
  hairstyle-ai:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data
      - ./static:/app/static
    environment:
      - FLASK_ENV=production
      - DATABASE_PATH=/app/data/hairstyle_booking.db
    restart: unless-stopped
'''
    
    with open('Dockerfile', 'w') as f:
        f.write(dockerfile)
    
    with open('docker-compose.yml', 'w') as f:
        f.write(docker_compose)
    
    print("🐳 Docker setup files đã được tạo!")

def main():
    """Hàm chính"""
    print("🎨 HAIR STYLE AI - SETUP & TEST")
    print("=" * 50)
    
    # Tạo các file cần thiết
    setup_requirements()
    create_docker_setup()
    
    # Tạo database test
    create_test_database()
    
    # Tạo ảnh mẫu
    create_sample_hairstyle_images()
    
    print("\n✅ Setup hoàn tất!")
    print("\n📋 Hướng dẫn chạy ứng dụng:")
    print("1. Cài đặt dependencies:")
    print("   pip install -r requirements.txt")
    print("\n2. Chạy server:")
    print("   python app.py")
    print("\n3. Mở trình duyệt:")
    print("   http://localhost:5000")
    print("\n4. Test API:")
    print("   python test_setup.py --test-api")
    print("\n5. Hoặc dùng Docker:")
    print("   docker-compose up --build")
    
    # Nếu có tham số --test-api, chạy test
    if len(sys.argv) > 1 and sys.argv[1] == '--test-api':
        print("\n🧪 Bắt đầu test API...")
        test_api_endpoints()
    
    print("\n" + "=" * 50)
    print("🎉 Sẵn sàng sử dụng Hair Style AI!")

if __name__ == '__main__':
    main()