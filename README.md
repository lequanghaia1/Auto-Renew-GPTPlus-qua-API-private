# Auto Renew GPTPlus qua API Private 

Giao diện Web tự động nâng cấp và gia hạn (Auto-Renew) tài khoản ChatGPT Plus bằng cách sử dụng các Key ủy quyền thông qua Private API. 

Phần mềm được thiết kế với tiêu chí: Bảo mật, Gọn nhẹ và Tự động hóa. Cho phép người dùng trực tiếp nhập mã, pass AuthSession để đẩy Session của OpenAI một cách dễ dàng.

## Tính năng chính (Key Features) 
- **Hệ thống nạp AuthSession tự động**: Nhấn liên kết lấy Session, paste vào ô dán JSON và tool xử lý tự động trong vòng 15 giây.
- **Key Checker (Trình kiểm tra mã)**: Kiểm tra trạng thái Key số lượng lớn nhanh chóng (chưa dùng, đã dùng, lỗi).
- **Thiết kế UI/UX tối giản**: Giao diện tập trung luồng người dùng với CSS tùy chỉnh cực nhẹ.
- **Hỗ trợ đa ngôn ngữ**: Tiếng Việt (VI), English (EN).
- **Bảo mật tuyệt đối**: Không lưu trữ cấu hình nhạy cảm dưới frontend, tất cả API Keys được mã hóa bằng `st.secrets` bảo mật trên Cloud.

## Môi trường hoạt động & Cài đặt 
Dự án được viết bằng Python và giao diện xây dựng thông qua Framework [Streamlit](https://streamlit.io/).
- **Yêu cầu**: Python 3.9+
- **Thư viện chính**: `streamlit`, `requests`

### Khởi động dự án:
1. Clone mã nguồn về máy:
`git clone https://github.com/lequanghaia1/Auto-Renew-GPTPlus-qua-API-private.git`

2. Thiết lập cấu hình Secret:
Vào thư mục `.streamlit`, tạo file `secrets.toml`:
`API_CHECK_KEY = "https://.../api/c"`
`API_CHECKER = "https://.../api/cdks"`
`API_CHECK_USER = "https://.../api/check-user"`
`API_UPGRADE = "https://.../api/r"`

3. Chạy Code thực thi:
`streamlit run hi.py`

## Developer 👨‍💻
Được lập trình và tối ưu hóa bởi **Le Hai**.
Telegram: **https://t.me/arjso1612**

Web đang dùng có nhiều chức năng hơn:
https://renewgpt.streamlit.app/
