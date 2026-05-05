---
name: export-packaging
description: Đóng gói output thành CSV, Markdown, Excel hoặc PDF.
allowed-tools: save_rows_csv export_markdown export_excel export_pdf
---

Chỉ báo file đã tạo khi tool trả về đường dẫn file thật.

Giữ output gọn, có tên file, định dạng và nội dung chính.

Khi user yêu cầu lưu bảng dữ liệu hoặc xuất CSV, dùng `save_rows_csv` với JSON rows đã truy xuất. Không tự đặt đường dẫn `/tmp/...`.
