@echo off
cd %~dp0\..
set USE_REAL_LLM=0
.venv\Scripts\python.exe -m uvicorn api.server:app --host 0.0.0.0 --port 8000 --reload
