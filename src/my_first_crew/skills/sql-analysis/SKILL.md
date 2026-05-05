---
name: sql-analysis
description: Viết và kiểm tra SQL Server read-only an toàn cho tác vụ phân tích dữ liệu.
allowed-tools: sqlserver_schema sqlserver_query
---

Luôn đọc schema trước khi viết truy vấn.

Chỉ dùng `SELECT` hoặc `WITH`. Không dùng câu lệnh ghi dữ liệu, thay đổi cấu trúc, stored procedure hoặc nhiều statement trong một lần gọi.

Khi trả lời, nêu rõ SQL đã dùng, giả định dữ liệu và giới hạn của kết quả.

SQL Server là nguồn dữ liệu chính. Không dùng dữ liệu demo hoặc file seed để suy luận.
