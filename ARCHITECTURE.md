# Kiến trúc chuẩn hóa

App được tách thành các khối rõ trách nhiệm:

```text
Streamlit UI
-> Agent Designer
-> Agent Registry
-> Crew Builder
-> Tool Layer
-> Execution Monitor
-> Output Manager
```

## Luồng chạy

```text
1. User nhập task.
2. App load agent từ config/agents.yaml.
3. Agent Designer kiểm tra có cần agent mới không.
4. Nếu cần, agent mới được thêm tạm thời vào lần chạy.
5. Crew Builder tạo CrewAI hierarchical crew.
6. Agent quản lý chọn agent phù hợp và giao việc.
7. Worker agent gọi tool nếu cần.
8. Agent duyệt kết quả review.
9. Output Manager hiển thị file/ảnh sinh ra trong output/.
```

## Module

```text
models.py
```
Định nghĩa `AgentBlueprint`, schema kết quả Agent Designer và hằng số model mặc định.

```text
agent_registry.py
```
Đọc/ghi `src/my_first_crew/config/agents.yaml`. Đây là nguồn cấu hình agent bền vững.

```text
agent_designer.py
```
Dùng LLM để phân tích task và đề xuất agent mới nếu đội hình hiện tại còn thiếu chuyên môn.

```text
crew_builder.py
```
Tạo LLM, agent, manager, reviewer, task và CrewAI crew.

```text
output_manager.py
```
Quản lý file output, hiện tại tập trung vào ảnh PNG trong thư mục `output/`.

```text
execution_monitor.py
```
Lắng nghe CrewAI events để ghi trace agent/task/tool.

```text
dynamic_crew.py
```
Facade tương thích ngược. Code mới nên import từ các module chuẩn ở trên.

## Tool hiện có

```text
rag_search
sqlserver_test_connection
sqlserver_schema
sqlserver_query
sqlserver_sample_rows
create_bar_chart
```

