Để trả lời câu hỏi của user, tôi sẽ chọn agent phù hợp dựa trên năng lực và mục tiêu của task.

**Agent đã chọn:** Nhà nghiên cứu tài liệu
**Lý do chọn:** Vì task cần tìm thông tin liên quan trong tài liệu nội bộ và trả context có nguồn, nên Nhà nghiên cứu tài liệu là lựa chọn phù hợp nhất.

**Giao việc cho agent:**

{"name": "delegate_work_to_coworker", "parameters": {"context": "Task của user: RAG la gi va Ollama dung de lam gi?", "coworker": "Nhà nghiên cứu tài liệu", "task": "Tìm thông tin liên quan trong tài liệu nội bộ và trả context có nguồn."}}

**Tổng hợp kết quả:**

Bản trả lời nháp bằng tiếng Việt:

* Agent đã chọn: Nhà nghiên cứu tài liệu
* Lý do chọn: Vì task cần tìm thông tin liên quan trong tài liệu nội bộ và trả context có nguồn.
* Kết quả thực hiện: Chưa được thực hiện.
* Điểm còn thiếu: Chưa có kết quả.

Nếu có file output, sẽ ghi đúng đường dẫn file.

Để review kết quả cuối cùng trước khi trả về user, tôi sẽ sử dụng skill "result-review".

**Review kết quả cuối cùng:**

Kết quả thực hiện: Chưa được thực hiện.
Điểm còn thiếu: Chưa có kết quả.

Do đó, tôi yêu cầu làm lại task và cung cấp kết quả cụ thể.

**Bước tiếp theo:**

* Làm lại task với thông tin chi tiết hơn về yêu cầu của user.
* Cung cấp kết quả cụ thể và chính xác.
* Kiểm tra lại kết quả để đảm bảo bám sát task.