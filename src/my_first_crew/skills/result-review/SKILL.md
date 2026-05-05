---
name: result-review
description: Review kết quả cuối trước khi trả về user.
allowed-tools:
---

Kiểm tra câu trả lời có bám sát task không.

Nếu task yêu cầu dữ liệu, phải có dữ liệu nguồn hoặc query rõ ràng.

Nếu task yêu cầu file, phải có đường dẫn file thật. Nếu thiếu, yêu cầu làm lại hoặc nêu rõ thiếu.

Chỉ công nhận file trong thư mục `output/` của project hoặc đường dẫn tuyệt đối do tool trả về nằm trong project. Không chấp nhận `/tmp/...` hoặc tên file tự đặt.
