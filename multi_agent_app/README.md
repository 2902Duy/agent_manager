# Multi-Agent System (LangGraph + Gemini)

Hệ thống Multi-Agent chuyên nghiệp sử dụng **LangGraph** để điều phối và **Google Gemini** làm LLM, theo kiến trúc Clean Architecture.

## Kiến trúc hệ thống

```
User Request
     │
     ▼
┌─────────────┐
│  Supervisor  │ ◄── Traffic Controller
└──────┬──────┘
       │ (routing decision)
       ├──────────► RAG Agent ──────► Vector DB (ChromaDB)
       ├──────────► DB Reader Agent ─► Database (SQLAlchemy)
       ├──────────► DB Writer Agent ─► Database (cần Human Approval)
       ├──────────► Web Agent ──────► Tavily API
       └──────────► Final Agent ────► Tổng hợp câu trả lời
```

## Cài đặt

```bash
# 1. Cài đặt dependencies
pip install -r multi_agent_app/requirements.txt

# 2. Tạo file .env từ template
cp multi_agent_app/.env.example .env

# 3. Thêm API keys vào .env
# GOOGLE_API_KEY=your_key
# TAVILY_API_KEY=your_key

# 4. Tạo sample database
python -m multi_agent_app.sample_data.create_sample_db
```

## Chạy ứng dụng

### FastAPI Server
```bash
python -m multi_agent_app.main
# Server chạy tại http://localhost:8000
# Docs: http://localhost:8000/docs
```

### CLI Mode
```bash
python -m multi_agent_app.main --cli
```

## API Endpoints

| Method | Endpoint                    | Mô tả                              |
|--------|-----------------------------|-------------------------------------|
| GET    | `/health`                   | Kiểm tra trạng thái server         |
| POST   | `/chat`                     | Gửi tin nhắn và nhận phản hồi      |
| POST   | `/approve`                  | Phê duyệt/từ chối SQL action       |
| POST   | `/ingest`                   | Nạp tài liệu vào Vector DB         |
| GET    | `/threads/{id}/state`       | Xem trạng thái conversation thread  |

### Ví dụ sử dụng

```bash
# Chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Cho tôi xem danh sách sản phẩm trong database"}'

# Ingest document
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"file_path": "multi_agent_app/sample_data/sample_report.txt", "file_type": "txt"}'

# Approve SQL action
curl -X POST http://localhost:8000/approve \
  -H "Content-Type: application/json" \
  -d '{"thread_id": "your-thread-id", "approved": true}'
```

## Cấu trúc thư mục

```
multi_agent_app/
├── core/
│   ├── graph.py             # Sơ đồ LangGraph (Nodes, Edges, State)
│   ├── state.py             # Schema của AgentState
│   └── supervisor.py        # Logic điều phối Supervisor Agent
├── agents/
│   ├── rag_agent.py         # Agent đọc file & tìm kiếm nội bộ
│   ├── db_reader_agent.py   # Agent đọc database (SELECT)
│   ├── db_writer_agent.py   # Agent ghi database (INSERT/UPDATE + HITL)
│   ├── web_agent.py         # Agent tìm kiếm Internet (Tavily)
│   └── final_agent.py       # Agent tổng hợp câu trả lời
├── tools/
│   ├── db_tools.py          # SQL tools (SQLAlchemy)
│   ├── rag_tools.py         # RAG tools (ChromaDB + HuggingFace)
│   └── web_tools.py         # Web search tools (Tavily)
├── prompts/
│   ├── supervisor_prompt.py # System prompt cho Supervisor
│   └── agent_prompts.py     # System prompts cho từng Agent
├── db/
│   ├── sample.db            # SQLite database mẫu
│   ├── sqlite_checkpoints.db # LangGraph checkpointing (HITL)
│   └── vector_store/        # ChromaDB index
├── sample_data/
│   ├── create_sample_db.py  # Script tạo DB mẫu
│   ├── sample_report.txt    # Báo cáo doanh thu mẫu
│   └── company_policy.txt   # Quy định nội bộ mẫu
├── main.py                  # Entry point (FastAPI + CLI)
├── requirements.txt
├── .env.example
└── README.md
```

## Human-in-the-Loop (HITL)

Khi `db_writer_agent` đề xuất một câu lệnh SQL ghi dữ liệu:

1. Hệ thống **tạm dừng** (interrupt) trước khi thực thi.
2. API trả về `status: "awaiting_approval"` và `proposed_action` chứa SQL.
3. Người dùng gửi `/approve` với `approved: true/false`.
4. Nếu approved → SQL được thực thi → kết quả trả về.
5. Nếu rejected → quay lại Supervisor để xử lý tiếp.

## Tech Stack

- **LLM**: Google Gemini 2.0 Flash Lite
- **Orchestration**: LangGraph
- **Vector DB**: ChromaDB + HuggingFace Embeddings
- **Web Search**: Tavily API
- **Database**: SQLAlchemy (hỗ trợ SQLite, MySQL, PostgreSQL, SQL Server)
- **API**: FastAPI + Uvicorn
- **Checkpointing**: SQLite (LangGraph built-in)
