# Kế hoạch phát triển ứng dụng CrewAI Agent Workspace

## 1. Mục tiêu sản phẩm

Xây dựng một ứng dụng multi-agent có giao diện quản trị hoàn chỉnh, cho phép người dùng:

- Tạo, chỉnh sửa, bật/tắt và lưu agent theo cấu hình.
- Giao một task tự nhiên bằng tiếng Việt.
- Hệ thống tự phân tích task, kiểm tra đội hình agent hiện có, đề xuất agent mới nếu thật sự thiếu năng lực.
- Agent quản lý tạo workflow phù hợp, giao việc cho agent chuyên môn, theo dõi quá trình chạy và review kết quả trước khi trả về.
- Agent có thể dùng tool thật để đọc tài liệu, truy vấn database, tạo biểu đồ, xuất file báo cáo.
- Có khả năng kết nối SQL Server thật theo cấu hình an toàn, không còn phụ thuộc `SQL Server` th?t.

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
  tool_groups:
    - sql_readonly
    - data_analysis
  skills:
    - sql_analysis
    - business_metrics
  tools_override: []
  enabled: true
  risk_level: medium
  max_iter: 2
```

### Chuẩn cấu hình agent mở rộng

Agent không nên quản lý tool rời rạc từng cái một trong UI chính. Nên cấu hình theo `tool_groups` và `skills`.

`tool_groups`

Là nhóm công cụ agent được phép dùng. Ví dụ `sql_readonly` tự bung ra thành `sql_schema`, `sql_query`, `sql_sample_rows`.

`skills`

Là bộ hướng dẫn chuyên môn, quy trình suy luận và guardrail riêng cho agent. Skill không nhất thiết là tool. Skill giống “playbook” của agent.

`tools_override`

Chỉ dùng khi cần thêm/bớt tool đặc biệt ngoài nhóm chuẩn.

Ví dụ agent phân tích dữ liệu:

```yaml
sales_data_analyst:
  role: >
    Chuyên viên phân tích dữ liệu bán hàng
  goal: >
    Truy xuất, kiểm tra và phân tích dữ liệu bán hàng để trả lời câu hỏi kinh doanh.
  backstory: >
    Bạn chỉ kết luận từ dữ liệu đã truy xuất. Bạn luôn nêu rõ query, giả định và giới hạn dữ liệu.
  llm: gemini/gemini-3.1-flash-lite-preview
  tool_groups:
    - sql_readonly
    - dataframe_analysis
    - charting
  skills:
    - sql_analysis
    - data_quality_check
    - business_metrics
    - chart_selection
  enabled: true
  risk_level: medium
  max_iter: 3
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

## 4. Chuẩn hóa skill cho agent

Skill là lớp năng lực mềm/chuyên môn của agent. Tool là thứ agent gọi được, còn skill là cách agent phải làm việc.

### Skill schema

```yaml
sql_analysis:
  name: SQL Analysis
  description: >
    Chuyển câu hỏi kinh doanh thành truy vấn SQL read-only an toàn.
  instructions: >
    Luôn đọc schema trước. Chỉ viết SELECT hoặc WITH. Không dùng query ghi dữ liệu.
    Nếu thiếu bảng/cột, hỏi lại hoặc nêu giả định.
  required_tool_groups:
    - sql_readonly
  guardrails:
    - query_must_be_readonly
    - query_must_have_row_limit
  output_contract:
    format: json
    fields:
      - sql
      - explanation
      - assumptions
```

### Nhóm skill chuẩn

| Skill | Dùng cho agent | Mục tiêu |
| --- | --- | --- |
| `task_decomposition` | Manager, Planner | Chia task thành các bước rõ ràng. |
| `agent_routing` | Manager | Chọn agent theo năng lực, không chọn theo từ khóa đơn giản. |
| `agent_design` | Agent Designer | Đề xuất agent mới khi thiếu năng lực thật sự. |
| `rag_research` | RAG Agent | Truy xuất tài liệu, trích nguồn, tránh bịa. |
| `sql_analysis` | SQL Agent | Viết SQL read-only an toàn. |
| `sqlserver_operations` | SQL Server Agent | Làm việc với SQL Server thật qua connection profile. |
| `data_quality_check` | Data QA Agent | Kiểm tra null, outlier, mismatch, thiếu dữ liệu. |
| `business_metrics` | Data Analyst | Tính KPI, doanh thu, tăng trưởng, phân nhóm. |
| `chart_selection` | Chart Agent | Chọn loại biểu đồ phù hợp với dữ liệu. |
| `report_writing` | Report Agent | Viết báo cáo rõ ràng, có cấu trúc. |
| `result_review` | Reviewer | Kiểm tra kết quả cuối, file thật, dữ liệu thật, thiếu sót. |
| `security_review` | Security Agent | Kiểm tra quyền, secret, query nguy hiểm, data leakage. |
| `export_packaging` | Export Agent | Đóng gói output Markdown/Excel/PDF. |

### Skill khác tool ở điểm nào

| Thành phần | Vai trò |
| --- | --- |
| Tool | Hành động cụ thể agent có thể gọi. Ví dụ `sql_query`. |
| Tool group | Bộ tool được đóng gói theo một năng lực. Ví dụ `sql_readonly`. |
| Skill | Quy trình, luật, tiêu chuẩn đầu ra. Ví dụ `sql_analysis`. |
| Agent | Vai trò dùng nhiều skill và nhiều tool group để hoàn thành task. |

### Cách inject skill vào CrewAI agent

Ở MVP, skill có thể được render vào `backstory` hoặc prompt task:

```text
Skill: sql_analysis
- Luôn đọc schema trước.
- Chỉ viết SELECT/WITH.
- Không dùng câu lệnh ghi dữ liệu.
- Trả về SQL, giải thích, giả định.
```

Ở bản production, nên có `skill_registry.py`:

```text
AgentBlueprint
-> skills: list[str]
-> SkillRegistry.load(skills)
-> CrewBuilder render instructions vào agent/task prompt
```

## 5. Chuẩn hóa tool

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

Chạy `SELECT` read-only trên SQL Server th?t.

`create_bar_chart`

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

## 6. Chuẩn hóa tool group

Tool group là cách đóng gói nhiều tool thành một capability. Một agent có thể có nhiều tool group, nhưng nên giới hạn theo nhiệm vụ.

### Tool group schema

```yaml
sql_readonly:
  description: >
    Đọc schema và chạy truy vấn SELECT read-only.
  risk_level: medium
  tools:
    - sql_schema
    - sql_query
    - sql_sample_rows
  required_skills:
    - sql_analysis
  policies:
    - readonly_only
    - max_rows_500
    - redact_secrets
```

### Tool group chuẩn cho sản phẩm

| Tool group | Tools | Agent nên dùng |
| --- | --- | --- |
| `local_rag` | `rag_search`, `FileReadTool`, `TXTSearchTool`, `PDFSearchTool` | Agent RAG, Researcher |
| `sql_readonly` | `sql_schema`, `sql_query`, `sql_sample_rows` | SQL Agent, Data Analyst |
| `sqlserver_readonly` | `sqlserver_test_connection`, `sqlserver_schema`, `sqlserver_query`, `sqlserver_sample_rows` | SQL Server Agent, Data Analyst |
| `dataframe_analysis` | `dataframe_profile`, `dataframe_transform`, `dataframe_summary` | Data Analyst, Data QA |
| `charting` | `chart_from_dataframe`, `create_bar_chart` | Chart Agent, Data Analyst |
| `report_export` | `export_markdown`, `export_excel`, `export_pdf` | Report Agent |
| `web_research` | `SerperDevTool` hoặc `TavilySearchTool`, `ScrapeWebsiteTool` | Web Research Agent |
| `code_sandbox` | `CodeInterpreterTool`, `E2BPythonTool` | Technical Agent, chỉ dùng khi có approval |
| `cloud_storage_read` | `S3ReaderTool` | Data Integration Agent |
| `cloud_storage_write` | `S3WriterTool` | Export Agent, cần approval |
| `automation_actions` | `ZapierActionTool`, `ComposioTool` | Automation Agent, cần approval |
| `evaluation` | `PatronusLocalEvaluatorTool`, custom guardrail | Reviewer, QA Agent |

### Matrix agent và tool group

| Agent | Tool groups | Skills |
| --- | --- | --- |
| Agent quản lý | Không cần tool dữ liệu trực tiếp | `task_decomposition`, `agent_routing`, `result_review` |
| Agent thiết kế agent | Không cần tool dữ liệu trực tiếp | `agent_design`, `security_review` |
| Agent RAG | `local_rag` | `rag_research`, `report_writing` |
| Agent tạo SQL | `sql_readonly`, `sqlserver_readonly` | `sql_analysis`, `sqlserver_operations` |
| Agent truy xuất dữ liệu | `sql_readonly`, `sqlserver_readonly` | `sql_analysis`, `data_quality_check` |
| Agent phân tích dữ liệu | `sql_readonly`, `dataframe_analysis`, `charting` | `business_metrics`, `data_quality_check`, `chart_selection` |
| Agent tạo biểu đồ | `charting`, `dataframe_analysis` | `chart_selection`, `business_metrics` |
| Agent viết báo cáo | `report_export`, `local_rag` | `report_writing`, `export_packaging` |
| Agent kiểm định dữ liệu | `dataframe_analysis`, `evaluation` | `data_quality_check`, `result_review` |
| Agent bảo mật | `evaluation` | `security_review`, `result_review` |

### Nguyên tắc gán nhiều tool cho một agent

- Một agent có thể có nhiều tool, nhưng chỉ thông qua tool group đã định nghĩa.
- Một agent production nên có tối đa 2-3 tool group.
- Agent có tool ghi file/cloud/action phải có `risk_level=high` và cần approval.
- Manager không nên có tool dữ liệu trực tiếp; manager chỉ điều phối.
- Agent Designer không nên có tool ghi cấu hình trực tiếp; user phải nhấn lưu.
- Tool group phải đi kèm skill phù hợp. Ví dụ có `sqlserver_readonly` thì phải có `sql_analysis` hoặc `sqlserver_operations`.

### Cấu hình mục tiêu

`config/tool_groups.yaml`

```yaml
sqlserver_readonly:
  description: Đọc SQL Server thật bằng quyền read-only.
  risk_level: medium
  tools:
    - sqlserver_test_connection
    - sqlserver_schema
    - sqlserver_query
    - sqlserver_sample_rows
  required_skills:
    - sqlserver_operations
    - sql_analysis
  policies:
    - readonly_only
    - allowlisted_tables_only
    - max_rows_500
```

`config/skills.yaml`

```yaml
sqlserver_operations:
  description: Làm việc an toàn với SQL Server thật.
  instructions: >
    Chỉ dùng connection profile đã được user cấu hình.
    Không in password hoặc connection string.
    Luôn đọc schema trước khi query.
    Không query bảng ngoài allowlist.
```

`config/agents.yaml`

```yaml
sqlserver_data_analyst:
  role: >
    Chuyên viên phân tích dữ liệu SQL Server
  goal: >
    Truy xuất và phân tích dữ liệu từ SQL Server thật bằng quyền read-only.
  backstory: >
    Bạn làm việc với dữ liệu doanh nghiệp, luôn ưu tiên an toàn, chính xác và có audit.
  tool_groups:
    - sqlserver_readonly
    - dataframe_analysis
    - charting
  skills:
    - sqlserver_operations
    - sql_analysis
    - data_quality_check
    - business_metrics
  enabled: true
  risk_level: medium
```

## 7. Catalog tool CrewAI hiện có

Catalog này dựa trên `crewai_tools` đang cài trong project, phiên bản `1.14.4`. Không nên gắn toàn bộ tool cho mọi agent. Mỗi agent chỉ nên có 1-4 tool đúng phạm vi để giảm hallucination, giảm rủi ro và dễ audit.

### File, tài liệu và RAG

| Tool | Công dụng |
| --- | --- |
| `FileReadTool` | Đọc nội dung file. |
| `FileWriterTool` | Ghi file ra filesystem, cần kiểm soát path và approval. |
| `DirectoryReadTool` | Đọc danh sách/nội dung thư mục. |
| `DirectorySearchTool` | Tìm kiếm trong thư mục bằng RAG. |
| `TXTSearchTool` | Tìm kiếm trong file `.txt`. |
| `PDFSearchTool` | Tìm kiếm trong PDF. |
| `DOCXSearchTool` | Tìm kiếm trong DOCX. |
| `CSVSearchTool` | Tìm kiếm trong CSV. |
| `JSONSearchTool` | Tìm kiếm trong JSON. |
| `XMLSearchTool` | Tìm kiếm trong XML. |
| `MDXSearchTool` | Tìm kiếm trong tài liệu MDX/Markdown. |
| `RagTool` | RAG tổng quát. |
| `CodeDocsSearchTool` | Tìm kiếm tài liệu code/API. |
| `GithubSearchTool` | Tìm kiếm trong GitHub repository. |
| `OCRTool` | OCR ảnh/tài liệu scan. |
| `FileCompressorTool` | Nén file. |

### Web search, research và scraping

| Tool | Công dụng |
| --- | --- |
| `SerperDevTool` | Google Search qua Serper. |
| `SerperScrapeWebsiteTool` | Scrape website qua Serper. |
| `SerpApiGoogleSearchTool` | Google Search qua SerpAPI. |
| `SerpApiGoogleShoppingTool` | Google Shopping qua SerpAPI. |
| `EXASearchTool` | Search bằng Exa. |
| `FirecrawlSearchTool` | Search qua Firecrawl. |
| `FirecrawlScrapeWebsiteTool` | Scrape một trang qua Firecrawl. |
| `FirecrawlCrawlWebsiteTool` | Crawl nhiều trang qua Firecrawl. |
| `ScrapeWebsiteTool` | Scrape website cơ bản. |
| `ScrapeElementFromWebsiteTool` | Scrape phần tử cụ thể trên website. |
| `WebsiteSearchTool` | RAG/search nội dung website. |
| `JinaScrapeWebsiteTool` | Scrape website bằng Jina. |
| `ScrapegraphScrapeTool` | Scrape có cấu trúc bằng Scrapegraph. |
| `ScrapflyScrapeWebsiteTool` | Scrape bằng Scrapfly. |
| `SpiderTool` | Crawl/scrape bằng Spider. |
| `SeleniumScrapingTool` | Scrape bằng Selenium, phù hợp trang động. |
| `BrowserbaseLoadTool` | Load/trích xuất dữ liệu bằng Browserbase. |
| `HyperbrowserLoadTool` | Load web bằng Hyperbrowser. |
| `LinkupSearchTool` | Search qua Linkup. |
| `ParallelSearchTool` | Chạy nhiều nguồn search song song. |
| `TavilySearchTool` | Search qua Tavily. |
| `TavilyExtractorTool` | Trích xuất nội dung qua Tavily. |
| `TavilyResearchTool` | Research qua Tavily. |
| `TavilyGetResearchTool` | Lấy kết quả research Tavily. |
| `ArxivPaperTool` | Tìm/đọc paper từ arXiv. |

### Brave search

| Tool | Công dụng |
| --- | --- |
| `BraveSearchTool` | Search tổng quát bằng Brave. |
| `BraveWebSearchTool` | Web search Brave. |
| `BraveNewsSearchTool` | Search tin tức Brave. |
| `BraveImageSearchTool` | Search ảnh Brave. |
| `BraveVideoSearchTool` | Search video Brave. |
| `BraveLocalPOIsTool` | Tìm địa điểm địa phương. |
| `BraveLocalPOIsDescriptionTool` | Mô tả địa điểm địa phương. |
| `BraveLLMContextTool` | Lấy context tối ưu cho LLM từ Brave. |

### Serply

| Tool | Công dụng |
| --- | --- |
| `SerplyWebSearchTool` | Web search qua Serply. |
| `SerplyNewsSearchTool` | Search tin tức qua Serply. |
| `SerplyScholarSearchTool` | Search học thuật qua Serply. |
| `SerplyJobSearchTool` | Search việc làm qua Serply. |
| `SerplyWebpageToMarkdownTool` | Chuyển webpage sang Markdown. |

### Database, warehouse và vector store

| Tool | Công dụng |
| --- | --- |
| `NL2SQLTool` | Chuyển ngôn ngữ tự nhiên sang SQL. Cần guardrail chặt trước production. |
| `MySQLSearchTool` | Search/truy vấn MySQL. |
| `SnowflakeSearchTool` | Search/truy vấn Snowflake. |
| `SingleStoreSearchTool` | Search/truy vấn SingleStore. |
| `DatabricksQueryTool` | Query Databricks. |
| `PGSearchTool` | PostgreSQL search/RAG, tool này có trong docs CrewAI nhưng package hiện tại không export trực tiếp ở root. |
| `QdrantVectorSearchTool` | Vector search Qdrant. |
| `WeaviateVectorSearchTool` | Vector search Weaviate. |
| `MongoDBVectorSearchTool` | Vector search MongoDB. |
| `CouchbaseFTSVectorSearchTool` | Full-text/vector search Couchbase. |

Ghi chú cho dự án này: CrewAI chưa có tool SQL Server root-level phù hợp với yêu cầu read-only/audit của mình. Nên tự viết `sqlserver_schema`, `sqlserver_query`, `sqlserver_test_connection` thay vì dùng `NL2SQLTool` trực tiếp trên database thật.

### Code execution và sandbox

| Tool | Công dụng |
| --- | --- |
| `CodeInterpreterTool` | Chạy code trong môi trường interpreter. Có rủi ro cao, cần sandbox. |
| `E2BExecTool` | Chạy lệnh qua E2B sandbox. |
| `E2BFileTool` | Thao tác file trong E2B sandbox. |
| `E2BPythonTool` | Chạy Python trong E2B sandbox. |
| `DaytonaExecTool` | Chạy lệnh qua Daytona. |
| `DaytonaFileTool` | Thao tác file qua Daytona. |
| `DaytonaPythonTool` | Chạy Python qua Daytona. |

Khuyến nghị: chỉ bật nhóm này cho agent kỹ thuật sau khi có approval và audit log. Không bật cho agent phân tích dữ liệu thông thường.

### Cloud, storage và platform

| Tool | Công dụng |
| --- | --- |
| `S3ReaderTool` | Đọc file từ S3. |
| `S3WriterTool` | Ghi file lên S3, cần kiểm soát quyền. |
| `BedrockInvokeAgentTool` | Gọi AWS Bedrock Agent. |
| `BedrockKBRetrieverTool` | Retrieve từ AWS Bedrock Knowledge Base. |
| `CrewaiPlatformTools` | Tool tích hợp với CrewAI platform. |
| `GenerateCrewaiAutomationTool` | Tạo automation CrewAI. |
| `InvokeCrewAIAutomationTool` | Gọi automation CrewAI. |
| `EnterpriseActionTool` | Action tool cho môi trường enterprise. |

### Automation và integration

| Tool | Công dụng |
| --- | --- |
| `ComposioTool` | Tích hợp action qua Composio. |
| `ZapierActionTool` | Gọi một Zapier action. |
| `ZapierActionTools` | Bộ Zapier actions. |
| `ApifyActorsTool` | Gọi Apify Actor. |
| `MultiOnTool` | Automation qua MultiOn. |
| `StagehandTool` | Browser automation qua Stagehand. |

Khuyến nghị: nhóm này dễ tạo tác động bên ngoài hệ thống, nên cần human approval trước khi chạy.

### AI, vision và generation

| Tool | Công dụng |
| --- | --- |
| `DallETool` | Tạo ảnh bằng DALL-E. |
| `VisionTool` | Xử lý/tạo tác vụ liên quan vision theo CrewAI tools. |
| `AIMindTool` | Tool AI Mind. |
| `LlamaIndexTool` | Bọc LlamaIndex tool để dùng trong CrewAI. |

### Video và media

| Tool | Công dụng |
| --- | --- |
| `YoutubeChannelSearchTool` | Search trong YouTube channel. |
| `YoutubeVideoSearchTool` | Search trong YouTube video. |

### Data extraction thương mại

| Tool | Công dụng |
| --- | --- |
| `BrightDataSearchTool` | Search qua Bright Data. |
| `BrightDataDatasetTool` | Dùng dataset Bright Data. |
| `BrightDataWebUnlockerTool` | Web unlock/proxy Bright Data. |
| `OxylabsGoogleSearchScraperTool` | Scrape Google Search qua Oxylabs. |
| `OxylabsAmazonSearchScraperTool` | Scrape Amazon Search qua Oxylabs. |
| `OxylabsAmazonProductScraperTool` | Scrape Amazon product qua Oxylabs. |
| `OxylabsUniversalScraperTool` | Universal scraper Oxylabs. |

### Contextual AI và evaluation

| Tool | Công dụng |
| --- | --- |
| `ContextualAICreateAgentTool` | Tạo agent Contextual AI. |
| `ContextualAIParseTool` | Parse tài liệu bằng Contextual AI. |
| `ContextualAIQueryTool` | Query Contextual AI. |
| `ContextualAIRerankTool` | Rerank kết quả bằng Contextual AI. |
| `PatronusEvalTool` | Đánh giá output qua Patronus. |
| `PatronusLocalEvaluatorTool` | Đánh giá local theo tiêu chí. |
| `PatronusPredefinedCriteriaEvalTool` | Đánh giá theo tiêu chí có sẵn Patronus. |

### Agent orchestration nội bộ

| Tool | Công dụng |
| --- | --- |
| `MergeAgentHandlerTool` | Hỗ trợ merge/xử lý agent handler. |

### Tool nên dùng cho sản phẩm này

MVP nội bộ nên ưu tiên ít tool, rõ quyền:

| Nhóm | Tool nên dùng |
| --- | --- |
| Tài liệu nội bộ | `FileReadTool`, `DirectoryReadTool`, `TXTSearchTool`, `PDFSearchTool`, `RagTool` hoặc custom `rag_search` |
| SQL Server thật | custom `sqlserver_test_connection`, `sqlserver_schema`, `sqlserver_query`, `sqlserver_sample_rows` |
| Biểu đồ/báo cáo | custom `chart_from_dataframe`, `export_excel`, `export_pdf` |
| Web research | `SerperDevTool` hoặc `TavilySearchTool`, chỉ bật nếu task cần internet |
| Audit/evaluation | `PatronusLocalEvaluatorTool` hoặc custom reviewer/guardrail |
| File output | `FileReadTool`, custom output manager; hạn chế `FileWriterTool` cho path đã allowlist |

### Tool nên tránh ở giai đoạn đầu

| Nhóm | Lý do |
| --- | --- |
| Code execution tools | Rủi ro chạy lệnh/code ngoài ý muốn. |
| Browser automation tools | Dễ tạo hành động bên ngoài khó audit. |
| Zapier/Composio/action tools | Có thể gửi email, tạo ticket, sửa dữ liệu nếu cấu hình sai. |
| `NL2SQLTool` trực tiếp trên DB thật | Cần query validator và allowlist trước. |
| Writer/storage cloud tools | Có thể làm lộ dữ liệu nếu chưa có policy. |

## 8. Thiết kế kết nối SQL Server thật

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

## 9. Giao diện cần hoàn thiện

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

## 10. Workflow production đề xuất

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

## 11. Bảo mật và kiểm soát rủi ro

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

## 12. Lộ trình triển khai

### Phase 1: Ổn định demo thành MVP

- Chuẩn hóa encoding UTF-8.
- Chuẩn hóa output JSON cho mọi tool.
- Hoàn thiện UI hiện tại.
- Thêm workflow plan trước khi chạy.
- Lưu trace ra file hoặc SQLite.
- Tách chart tool khỏi logic hard-code doanh thu.

Kết quả: app chạy ổn với SQL Server th?t.

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

## 13. Cấu trúc file mục tiêu

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

## 14. Tiêu chí hoàn thành

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

## 15. Ưu tiên làm tiếp theo

1. Thêm `workflow_planner.py` để tạo plan JSON trước khi CrewAI chạy.
2. Thêm `security/query_validator.py` dùng chung cho SQLite và SQL Server.
3. Thêm `data_connections/sqlserver_connection.py`.
4. Thêm `tools/sqlserver_tool.py`.
5. Thêm tab `Kết nối dữ liệu` trong UI.
6. Thêm chart tool tổng quát từ DataFrame thay vì chart doanh thu hard-code.
7. Lưu trace và output metadata vào SQLite audit DB.
