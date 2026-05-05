---
name: sqlserver-operations
description: Làm việc với SQL Server thật qua connection profile read-only.
allowed-tools: sqlserver_test_connection sqlserver_schema sqlserver_query sqlserver_sample_rows
---

Chỉ dùng connection profile đã được user cấu hình.

Không in password, token hoặc connection string đầy đủ trong câu trả lời, trace hoặc file output.

Luôn đọc schema và kiểm tra allowlist bảng/cột trước khi query. Nếu thiếu quyền hoặc thiếu bảng, dừng và báo rõ.
