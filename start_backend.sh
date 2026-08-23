#!/bin/bash
cd /workspace/hjrm/migpal/backend
export PYTHONPATH=/workspace/hjrm/migpal/backend
/workspace/hjrm/migpal/backend/.venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000
