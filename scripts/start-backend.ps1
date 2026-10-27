Set-Location "$PSScriptRoot\..\backend"
if (-not (Test-Path .venv)) {
  py -3.12 -m venv .venv
  .\.venv\Scripts\pip install -r requirements.txt
}
.\.venv\Scripts\uvicorn app.main:app --reload --port 8000
