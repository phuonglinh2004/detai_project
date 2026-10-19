# Đề tài 4: Phát hiện tái sử dụng Nonce trong AES-GCM bằng phân tích nhật ký

**Sinh viên thực hiện:** Phương Linh
**Môn học:** An toàn và Bảo mật Hệ thống Thông tin

## 1. Giới thiệu
Đồ án xây dựng một nguyên mẫu phát hiện lỗi tái sử dụng Nonce (Nonce Reuse) trong thuật toán mã hóa AES-GCM. Đồ án bao gồm việc xử lý dữ liệu từ NIST ACVP, sinh log giả lập, cài đặt các bộ phát hiện (Baseline và Biến thể), và đánh giá hiệu năng (Precision, Recall, False Alarm).

## 2. Yêu cầu hệ thống
- Hệ điều hành: Windows 10/11
- Python 3.10 trở lên
- Git (để tải dữ liệu)

## 3. Hướng dẫn chạy (Tái lập)
Mở Terminal (PowerShell) tại thư mục gốc của dự án và chạy lần lượt các lệnh sau:

```powershell
# 1. Tạo môi trường ảo và cài đặt thư viện
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install cryptography pytest matplotlib

# 2. Tải dữ liệu NIST ACVP (nếu chưa có)
python scripts/download_acvp.py

# 3. Xử lý dữ liệu (tạo file CSV)
python src/prepare_data.py

# 4. Chạy kiểm thử tự động (phải pass hết)
python -m pytest -v tests

# 5. Chạy demo hậu quả Nonce Reuse
python src/demo_consequence.py

# 6. Chạy ma trận thực nghiệm (3 seed, 3 tỉ lệ)
python src/run_experiments.py

# 7. Vẽ biểu đồ kết quả
python src/plot.py
