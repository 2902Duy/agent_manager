@echo off
cd /d D:\Project\1\agent_manager
set STREAMLIT_EMAIL=
uv run streamlit run src/my_first_crew/app.py --server.headless true
