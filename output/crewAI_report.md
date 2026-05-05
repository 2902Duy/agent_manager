# Báo cáo Phát triển Ứng dụng CrewAI Agent Workspace

## 1. Mục tiêu Sản phẩm

Ứng dụng CrewAI Agent Workspace được thiết kế để:
- Tạo, chỉnh sửa, bật/tắt và lưu cấu hình agent.
- Phân tích và xử lý các task tự nhiên bằng tiếng Việt.
- Đề xuất agent mới khi cần thiết.
- Quản lý workflow, theo dõi quá trình thực thi và kiểm tra kết quả.
- Kết nối với SQL Server thật để truy vấn dữ liệu an toàn.
- Tạo biểu đồ, xuất báo cáo và quản lý output.

Ứng dụng không chỉ là một demo mà còn là một công cụ vận hành nội bộ cho doanh nghiệp.

---

## 2. Kiến trúc Tổng thể

### Các Thành phần Chính

1. **Streamlit UI**: Giao diện chính để nhập task, quản lý agent, cấu hình model và database.
2. **Task Analyzer**: Phân tích task, xác định yêu cầu và phân loại công việc.
3. **Agent Designer**: Đề xuất agent mới khi cần thiết.
4. **Agent Registry**: Quản lý cấu hình agent bền vững.
5. **Workflow Planner**: Lập kế hoạch workflow trước khi thực thi.
6. **CrewAI Manager Agent**: Điều phối workflow và tổng hợp kết quả.
7. **Worker Agents**: Các agent chuyên môn như SQL analyst, chart builder, report writer.
8. **Tool Layer**: Tầng công cụ với input schema rõ ràng và output có cấu trúc.
9. **Execution Monitor**: Theo dõi quá trình thực thi, ghi lại log và lỗi.
10. **Output Manager**: Quản lý file output như CSV, Excel, Markdown, PDF.

---

## 3. Chuẩn hóa Agent

### Cấu hình Agent

Mỗi agent cần có cấu hình YAML như sau:
```yaml
agent_key:
  role: Vai trò của agent
  goal: Mục tiêu cụ thể
  backstory: Phạm vi chuyên môn và nguyên tắc
  llm: gemini/gemini-3.1-flash-lite-preview
  tools:
    - sql_query
    - sql_schema
  enabled: true
  risk_level: medium
  max_iter: 2
```

### Nhóm Agent Chính

- **Agent quản lý**: Điều phối tổng thể.
- **Agent thiết kế agent**: Đề xuất agent mới.
- **Agent tạo SQL**: Viết truy vấn SQL read-only.
- **Agent truy xuất dữ liệu**: Chạy SQL an toàn.
- **Agent phân tích dữ liệu**: Tính toán KPI, phát hiện bất thường.
- **Agent tạo biểu đồ**: Tạo biểu đồ từ dữ liệu thật.
- **Agent viết báo cáo**: Tổng hợp kết quả thành Markdown/PDF/Excel.
- **Agent kiểm định dữ liệu**: Kiểm tra chất lượng dữ liệu.
- **Agent RAG**: Truy xuất tài liệu nội bộ.

---

## 4. Chuẩn hóa Tool

### Tiêu chuẩn Tool

- Input schema rõ ràng (Pydantic).
- Output JSON có cấu trúc.
- Timeout và giới hạn số dòng.
- Log tool call và phân quyền theo agent.

### Tool Hiện tại

- `rag_search`: Đọc tài liệu demo.
- `sql_schema`: Đọc cấu trúc bảng an toàn.
- `sql_query`: Chạy truy vấn SQL read-only.
- `create_revenue_chart`: Tạo biểu đồ doanh thu.

### Tool Cần Bổ sung

- `sqlserver_test_connection`: Kiểm tra kết nối SQL Server.
- `sqlserver_schema`: Đọc schema từ SQL Server.
- `sqlserver_query`: Chạy truy vấn SQL read-only.
- `dataframe_profile`: Phân tích nhanh dữ liệu.
- `chart_from_dataframe`: Tạo biểu đồ từ DataFrame.
- `export_excel`: Xuất dữ liệu sang Excel.
- `export_pdf`: Xuất báo cáo sang PDF.

---

## 5. Lộ trình Triển khai

### Phase 1: Ổn định Demo
- Chuẩn hóa encoding UTF-8.
- Hoàn thiện UI hiện tại.
- Lưu trace ra file hoặc SQLite.
- Tách chart tool khỏi logic hard-code doanh thu.

### Phase 2: Agent Registry
- Thêm form tạo/sửa/xóa agent.
- Lưu lịch sử thay đổi agent.
- Quản lý agent như một workspace thật.

### Phase 3: SQL Server Connector
- Thêm dependency `pyodbc`, `sqlalchemy`, `pandas`.
- Thêm test connection và schema browser.
- Thêm validator query.
- Thêm table/column allowlist.

### Phase 4: Data Analysis và Chart Engine
- Chuẩn hóa dữ liệu query thành DataFrame.
- Tạo chart bất kỳ: bar, line, pie, table.
- Hiển thị chart trong UI.

### Phase 5: Report Export
- Xuất Markdown, Excel, PDF.
- Gắn biểu đồ và bảng dữ liệu vào báo cáo.

### Phase 6: Production Hardening
- Auth user và role-based access control.
- Audit log và secret management.
- Docker deployment và CI test.

---

## 6. Tiêu chí Hoàn thành

- User có thể tạo/sửa/lưu agent từ UI.
- Agent đọc schema và tạo query SQL an toàn.
- Workflow hiển thị rõ ràng.
- Output file thật được hiển thị đúng.
- Trace đầy đủ để debug.
- Không có secret xuất hiện trong log.
- Test tối thiểu cho query validator, SQL Server tool, output manager và agent registry.

---

## 7. Ưu tiên Tiếp theo

1. Thêm `workflow_planner.py` để tạo plan JSON trước khi CrewAI chạy.
2. Thêm `security/query_validator.py` dùng chung cho SQLite và SQL Server.
3. Thêm `data_connections/sqlserver_connection.py`.
4. Thêm `tools/sqlserver_tool.py`.
5. Thêm tab `Kết nối dữ liệu` trong UI.
6. Thêm chart tool tổng quát từ DataFrame.
7. Lưu trace và output metadata vào SQLite audit DB.