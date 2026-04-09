net start postgresql-x64-16
cd E:\Projects\Trend
.\venv\Scripts\Activate.ps1
$env:PYTHONPATH = "E:\Projects\Trend"
uvicorn api.main:app --reload
