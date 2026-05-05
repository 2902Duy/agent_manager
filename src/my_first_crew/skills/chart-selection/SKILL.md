---
name: chart-selection
description: Chọn biểu đồ phù hợp và đảm bảo tạo file output thật.
allowed-tools: create_bar_chart chart_from_dataframe
---

Chọn biểu đồ theo dữ liệu: cột cho so sánh nhóm, đường cho xu hướng thời gian, bảng cho dữ liệu chi tiết.

Khi dùng tool tạo biểu đồ, phải giữ nguyên đường dẫn file thật do tool trả về. Không tự bịa đường dẫn.

Nếu không tạo được file, báo rõ nguyên nhân và không nói rằng biểu đồ đã được tạo.

Với dữ liệu SQL Server hoặc JSON rows bất kỳ, dùng `create_bar_chart`.
