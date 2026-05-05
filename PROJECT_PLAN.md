# Kế hoạch phát triển ứng dụng CrewAI Agent Workspace

## 1. Mục tiêu sản phẩm

Xây dựng một ứng dụng multi-agent có giao diện quản trị hoàn chỉnh, cho phép người dùng:

- Tạo, chỉnh sửa, bật/tắt và lưu agent theo cấu hình.
- Giao một task tự nhiên bằng tiếng Việt.
- Hệ thống tự phân tích task, kiểm tra đội hình agent hiện có, đề xuất agent mới nếu thật sự thiếu năng lực.
- Agent quản lý tạo workflow phù hợp, giao việc cho agent chuyên môn, theo dõi quá trình chạy và review kết quả trước khi trả về.
- Agent có thể dùng tool thật để đọc tài liệu, truy vấn database, tạo biểu đồ, xuất file báo cáo.
- Có khả năng kết nối SQL Server thật theo cấu hình an toàn, không còn phụ thuộc `sample.db` demo.

Ứng dụng mục tiêu không chỉ là demo CrewAI, mà là một workspace để vận hành agent nội bộ cho dữ liệu doanh nghiệp.

## 2. Kiến trúc tổng thể

```text
User
-> Streamlit UI
-> Task Analyzer
-> Agent Designer
-> Agent Registry
-> Workflow Planner
-> CrewAI Manager Agent
-> Worker Agents
-> Tool Layer
-> Output Manager
-> Execution Monitor
-> User Review
```

### Vai trò từng khối

`Streamlit UI`

Giao diện chính để nhập task, quản lý agent, cấu hình model, cấu hình database, chạy workflow, xem trace và xem output.

`Task Analyzer`

Phân tích task trước khi chạy. Xác định task cần RAG, SQL, biểu đồ, file export, phân tích dữ liệu, dự báo hay thao tác hệ thống.

`Agent Designer`

Chỉ đề xuất agent mới khi đội hình hiện tại thiếu năng lực thật sự. Không tự tạo agent chỉ vì gặp từ khóa.

`Agent Registry`

Nguồn cấu hình bền vững cho agent. Hiện dùng `agents.yaml`, về sau nên nâng cấp sang SQLite/PostgreSQL để quản lý version, trạng thái bật/tắt, lịch sử chỉnh sửa.

`Workflow Planner`

Tạo kế hoạch chạy trước khi CrewAI kickoff. Kế hoạch gồm agent nào làm bước nào, tool nào được phép dùng, output mong đợi là gì.

`CrewAI Manager Agent`

Agent quản lý trong CrewAI hierarchical process. Nhận workflow plan, giao việc, tổng hợp kết quả và phối hợp reviewer.

`Worker Agents`

Agent chuyên môn như SQL analyst, RAG researcher, chart builder, report writer, data quality checker.

`Tool Layer`

Tầng gọi công cụ thật. Mọi tool phải có input schema, giới hạn quyền, timeout, logging và output có cấu trúc.

`Execution Monitor`

Ghi lại agent đang chạy, task hiện tại, tool call, input rút gọn, output rút gọn, lỗi và thời gian.

`Output Manager`

Quản lý file sinh ra: ảnh, CSV, Excel, Markdown, PDF. UI chỉ hiển thị file thật đã tồn tại.

## 3. Chuẩn hóa agent

Mỗi agent nên có cấu hình như sau:

```yaml
agent_key:
  role: >
    Vai trò bằng tiếng Việt
  goal: >
    Mục tiêu rõ ràng, đo được
  backstory: >
    Phạm vi chuyên môn, giới hạn hành vi, nguyên tắc không bịa dữ liệu
  llm: gemini/gemini-3.1-flash-lite-preview
  tools:
    - sql_query
    - sql_schema
  enabled: true
  risk_level: medium
  max_iter: 2
```

### Nhóm agent cần có

`Agent quản lý`

Điều phối tổng, chọn agent, giao việc, yêu cầu làm lại nếu thiếu.

`Agent thiết kế agent`

Phân tích thiếu năng lực và đề xuất agent mới. Không tự lưu agent nếu user chưa xác nhận.

`Agent tạo SQL`

Đọc schema, viết SQL read-only, giải thích logic truy vấn.

`Agent truy xuất dữ liệu`

Chạy SQL an toàn, trả dữ liệu nguồn dạng JSON/table.

`Agent phân tích dữ liệu`

Tính toán KPI, so sánh, phân nhóm, phát hiện bất thường từ dữ liệu đã truy xuất.

`Agent tạo biểu đồ`

Tạo PNG/HTML chart từ dữ liệu thật, trả về đường dẫn file thật.

`Agent viết báo cáo`

Tổng hợp kết quả thành Markdown/PDF/Excel.

`Agent kiểm định dữ liệu`

Kiểm tra dữ liệu rỗng, sai kiểu, thiếu cột, số âm bất thường, mismatch tổng.

`Agent RAG`

Truy xuất tài liệu nội bộ và trả context có nguồn.

## 4. Chuẩn hóa tool

Mỗi tool cần tuân thủ:

- Có `args_schema` Pydantic rõ ràng.
- Output là JSON nếu có dữ liệu máy cần đọc tiếp.
- Không trả đường dẫn giả.
- Không trả script nguy hiểm trong trace.
- Có timeout.
- Có giới hạn số dòng.
- Có log tool call.
- Có phân quyền theo agent.

### Tool hiện tại

`rag_search`

Đọc `data.txt`, dùng cho tài liệu demo.

`sql_schema`

Đọc cấu trúc bảng đã lọc an toàn.

`sql_query`

Chạy `SELECT` read-only trên `sample.db`.

`create_revenue_chart`

Tạo biểu đồ PNG trong `output/`.

### Tool cần bổ sung cho sản phẩm thật

`sqlserver_test_connection`

Kiểm tra kết nối SQL Server bằng thông tin cấu hình đã lưu.

`sqlserver_schema`

Đọc danh sách schema, table, column, type, khóa chính, khóa ngoại từ SQL Server thật.

`sqlserver_query`

Chạy truy vấn `SELECT` read-only trên SQL Server thật.

`sqlserver_sample_rows`

Lấy vài dòng mẫu của bảng được chọn để agent hiểu dữ liệu.

`sqlserver_saved_queries`

Quản lý query template an toàn cho các báo cáo hay dùng.

`dataframe_profile`

Phân tích nhanh dữ liệu trả về: số dòng, số cột, null, min/max, top values.

`chart_from_dataframe`

Tạo biểu đồ từ dữ liệu bất kỳ, không hard-code doanh thu.

`export_excel`

Xuất dữ liệu và biểu đồ sang `.xlsx`.

`export_pdf`

Xuất báo cáo cuối sang `.pdf`.

## 5. Thiết kế kết nối SQL Server thật

### Driver đề xuất

Ưu tiên dùng `pyodbc` với Microsoft ODBC Driver 18 for SQL Server.

Dependency dự kiến:

```bash
uv add pyodbc sqlalchemy pandas
```

Máy chạy app cần cài ODBC Driver 18 riêng ở hệ điều hành.

### Biến môi trường

Không nhập password trực tiếp vào code hoặc YAML.

```env
SQLSERVER_HOST=localhost
SQLSERVER_PORT=1433
SQLSERVER_DATABASE=SalesDW
SQLSERVER_USER=readonly_user
SQLSERVER_PASSWORD=...
SQLSERVER_DRIVER=ODBC Driver 18 for SQL Server
SQLSERVER_ENCRYPT=yes
SQLSERVER_TRUST_CERTIFICATE=no
SQLSERVER_QUERY_TIMEOUT=30
SQLSERVER_MAX_ROWS=500
```

### Quyền database

Tạo user read-only riêng:

```sql
CREATE USER readonly_user FOR LOGIN readonly_user;
ALTER ROLE db_datareader ADD MEMBER readonly_user;
```

Không dùng tài khoản admin. Không cấp quyền `db_owner`, `db_ddladmin`, `db_datawriter`.

### Luồng an toàn cho query

```text
User task
-> SQL Agent viết SELECT
-> Query Validator kiểm tra
-> sqlserver_query chạy read-only
-> Data Analyst phân tích JSON/table
-> Chart/Report Agent tạo output
-> Manager review
```

### Query Validator bắt buộc

Chặn các câu sau:

- `INSERT`
- `UPDATE`
- `DELETE`
- `DROP`
- `ALTER`
- `CREATE`
- `MERGE`
- `TRUNCATE`
- `EXEC`
- `sp_`
- nhiều statement trong một lần gọi

Chỉ cho phép query bắt đầu bằng `SELECT` hoặc `WITH`.

Tự thêm giới hạn dòng nếu thiếu:

```sql
SELECT TOP (500) ...
```

hoặc dùng wrapper phía Python để chỉ fetch tối đa `SQLSERVER_MAX_ROWS`.

## 6. Giao diện cần hoàn thiện

### Trang 1: Chạy task

- Nhập task.
- Chọn model.
- Chọn nguồn dữ liệu.
- Bật/tắt tự đề xuất agent.
- Xem workflow plan trước khi chạy.
- Nút `Chạy workflow`.
- Trạng thái real-time: agent đang chạy, task hiện tại, tool đang gọi, đã giao cho ai.

### Trang 2: Quản lý agent

- Danh sách agent.
- Form tạo agent thủ công.
- Form chỉnh sửa role/goal/backstory/tool.
- Bật/tắt agent.
- Lưu agent đề xuất vào registry.
- Xem agent nào có tool nào.

### Trang 3: Quản lý tool

- Danh sách tool.
- Test tool.
- Xem input schema.
- Xem quyền/risk level.
- Bật/tắt tool theo môi trường.

### Trang 4: Kết nối dữ liệu

- Tạo connection profile.
- Test SQL Server connection.
- Xem database/schema/table.
- Preview dữ liệu mẫu.
- Chọn bảng được phép cho agent dùng.
- Lưu allowlist table/column.

### Trang 5: Output

- Kết quả cuối.
- Biểu đồ.
- File Markdown/Excel/PDF.
- Lịch sử output.
- Tải file.

### Trang 6: Trace và Audit

- Timeline workflow.
- Agent/task/tool event.
- Query đã chạy.
- Thời gian chạy.
- Lỗi.
- Token usage nếu provider trả về.

### Trang 7: Cấu hình hệ thống

- Model provider.
- API key status.
- Rate limit.
- Max rows.
- Output folder.
- Chế độ dev/prod.

## 7. Workflow production đề xuất

### Bước 1: Preflight

- Kiểm tra API key/model.
- Kiểm tra connection profile nếu task cần DB.
- Kiểm tra agent/tool có sẵn.
- Kiểm tra quyền tool.

### Bước 2: Plan

Sinh workflow plan dạng JSON:

```json
{
  "steps": [
    {
      "agent": "Chuyên viên tạo SQL",
      "tool": "sqlserver_schema",
      "goal": "Đọc cấu trúc bảng"
    },
    {
      "agent": "Chuyên viên truy xuất dữ liệu",
      "tool": "sqlserver_query",
      "goal": "Lấy dữ liệu doanh thu"
    },
    {
      "agent": "Chuyên viên tạo biểu đồ",
      "tool": "chart_from_dataframe",
      "goal": "Tạo biểu đồ doanh thu"
    }
  ]
}
```

### Bước 3: Human confirm nếu rủi ro cao

Nếu task dùng database thật, app nên cho user xem:

- agent sẽ chạy;
- tool sẽ dùng;
- bảng sẽ đọc;
- query dự kiến.

Sau đó user nhấn xác nhận mới chạy.

### Bước 4: Execute

CrewAI chạy theo hierarchical process hoặc sequential flow tùy độ kiểm soát cần thiết.

Với production, nên ưu tiên:

- Flow để kiểm soát logic hệ thống.
- CrewAI để xử lý các bước cần suy luận/ngôn ngữ.

### Bước 5: Review

Reviewer kiểm tra:

- Có dùng dữ liệu thật không.
- Có file output thật không.
- Có bịa đường dẫn không.
- Có thiếu yêu cầu nào không.
- Query có đúng phạm vi không.

### Bước 6: Persist

Lưu:

- task input;
- workflow plan;
- agent đã chạy;
- tool calls;
- query;
- output;
- lỗi;
- thời gian.

## 8. Bảo mật và kiểm soát rủi ro

### Nguyên tắc

- Tool database mặc định read-only.
- Secret nằm trong `.env` hoặc secret manager, không lưu vào YAML.
- Không show password trong UI/trace.
- Không cho agent tự tạo connection profile có credential.
- Không cho agent tự chạy query ghi dữ liệu.
- Không cho agent tự quyết định gửi dữ liệu ra ngoài.

### Risk level cho tool

`low`

Đọc file nội bộ không nhạy cảm, tạo biểu đồ local.

`medium`

Đọc database thật read-only.

`high`

Gửi dữ liệu ra API ngoài, export file chứa dữ liệu nhạy cảm.

`blocked`

Ghi database, xóa file, chạy shell, gửi email tự động khi chưa có approval.

## 9. Lộ trình triển khai

### Phase 1: Ổn định demo thành MVP

- Chuẩn hóa encoding UTF-8.
- Chuẩn hóa output JSON cho mọi tool.
- Hoàn thiện UI hiện tại.
- Thêm workflow plan trước khi chạy.
- Lưu trace ra file hoặc SQLite.
- Tách chart tool khỏi logic hard-code doanh thu.

Kết quả: app chạy ổn với `sample.db`.

### Phase 2: Agent registry thật

- Thêm form tạo/sửa/xóa/bật/tắt agent.
- Thêm schema `enabled`, `risk_level`, `tools`, `tags`.
- Lưu lịch sử thay đổi agent.
- Cho phép rollback config.

Kết quả: quản lý agent như một workspace thật.

### Phase 3: SQL Server connector

- Thêm dependency `pyodbc`, `sqlalchemy`, `pandas`.
- Thêm connection profile.
- Thêm test connection.
- Thêm schema browser.
- Thêm read-only query tool.
- Thêm validator query.
- Thêm table/column allowlist.

Kết quả: agent có thể đọc SQL Server thật an toàn.

### Phase 4: Data analysis và chart engine

- Chuẩn hóa dữ liệu query thành DataFrame.
- Thêm chart config JSON.
- Tạo chart bất kỳ: bar, line, pie, table, KPI card.
- Lưu file PNG/HTML.
- Hiển thị chart trong UI.

Kết quả: task phân tích dữ liệu không còn bị giới hạn ở doanh thu demo.

### Phase 5: Report export

- Xuất Markdown.
- Xuất Excel.
- Xuất PDF.
- Gắn biểu đồ và bảng dữ liệu vào báo cáo.

Kết quả: app tạo được báo cáo dùng được trong công việc.

### Phase 6: Production hardening

- Auth user.
- Role-based access control.
- Audit log.
- Secret management.
- Background job queue.
- Retry policy.
- Rate limit.
- Docker deployment.
- CI test.

Kết quả: đủ điều kiện chạy nội bộ nghiêm túc.

## 10. Cấu trúc file mục tiêu

```text
src/my_first_crew/
├── app.py
├── models.py
├── agent_designer.py
├── agent_registry.py
├── workflow_planner.py
├── crew_builder.py
├── execution_monitor.py
├── output_manager.py
├── security/
│   ├── query_validator.py
│   └── secrets.py
├── data_connections/
│   ├── profiles.py
│   ├── sqlite_connection.py
│   └── sqlserver_connection.py
├── tools/
│   ├── rag_tool.py
│   ├── sql_tool.py
│   ├── sqlserver_tool.py
│   ├── chart_tool.py
│   ├── export_tool.py
│   └── dataframe_tool.py
├── config/
│   ├── agents.yaml
│   ├── tools.yaml
│   └── connections.yaml.example
└── storage/
    ├── audit.sqlite
    └── outputs/
```

## 11. Tiêu chí hoàn thành

Một phiên bản được xem là hoàn thiện khi:

- User có thể tạo/sửa/lưu agent từ UI.
- User có thể cấu hình SQL Server read-only từ UI.
- Agent có thể đọc schema thật.
- Agent có thể tạo query `SELECT` an toàn.
- Query nguy hiểm bị chặn trước khi tới database.
- Workflow hiển thị rõ agent nào làm bước nào.
- Output file thật được hiển thị đúng.
- Trace đầy đủ để debug.
- Không có secret xuất hiện trong log.
- Có test tối thiểu cho query validator, SQL Server tool, output manager và agent registry.

## 12. Ưu tiên làm tiếp theo

1. Thêm `workflow_planner.py` để tạo plan JSON trước khi CrewAI chạy.
2. Thêm `security/query_validator.py` dùng chung cho SQLite và SQL Server.
3. Thêm `data_connections/sqlserver_connection.py`.
4. Thêm `tools/sqlserver_tool.py`.
5. Thêm tab `Kết nối dữ liệu` trong UI.
6. Thêm chart tool tổng quát từ DataFrame thay vì chart doanh thu hard-code.
7. Lưu trace và output metadata vào SQLite audit DB.

