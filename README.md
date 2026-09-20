# SneakerHub Full Stack - Frontend + Backend

## 1. Cấu trúc

```text
SneakerHub_backend/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   └── seed.py
├── frontend/
│   └── index.html
├── instance/
├── venv/
├── requirements.txt
└── run.py
```

Frontend đã được Flask phục vụ trực tiếp, nên không cần Live Server.

## 2. Chạy project trên Windows

Mở Terminal tại thư mục `SneakerHub_backend`:

```bash
venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Mở trình duyệt:

```text
http://localhost:5000
```

Kiểm tra API:

```text
http://localhost:5000/api/health
http://localhost:5000/api/products
```

## 3. Tài khoản demo

Admin:
- Email: `admin@sneakerhub.vn`
- Password: `admin123`

Customer:
- Email: `customer@sneakerhub.vn`
- Password: `123456`

## 4. Trang quản lý (Admin)

Truy cập:

```text
http://localhost:5000/admin
```

Đăng nhập bằng tài khoản admin (xem mục 3). Trang quản lý gồm:
- Tổng quan: doanh thu, số đơn hàng, tồn kho thấp, số khách hàng
- Sản phẩm: thêm / sửa / xóa
- Đơn hàng: lọc theo trạng thái, cập nhật trạng thái
- Feedback: xem góp ý khách hàng gửi qua form Liên hệ

## 5. Frontend đã kết nối API

- Danh sách sản phẩm lấy từ `/api/products`
- Tìm kiếm và lọc thương hiệu
- Sắp xếp giá
- Đăng ký `/api/auth/register`
- Đăng nhập `/api/auth/login` và lưu JWT vào localStorage
- Giỏ hàng lưu localStorage
- Checkout gửi `/api/orders`
- Xem đơn hàng `/api/orders/my`
- Review `/api/products/<id>/reviews`
- Feedback `/api/contact`
- Admin quản lý sản phẩm và trạng thái đơn hàng

## 6. Lưu ý

Thanh toán hiện là COD/demo, chưa kết nối cổng thanh toán thật.
Google Maps hiện mở trang tìm kiếm Google Maps, chưa dùng Google Maps API.
Ảnh sản phẩm đang dùng URL ảnh mẫu.
