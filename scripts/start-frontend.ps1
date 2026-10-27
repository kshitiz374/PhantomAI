Set-Location "$PSScriptRoot\..\frontend"
if (-not (Test-Path node_modules)) { npm install }
$env:NEXT_PUBLIC_API_URL = "http://127.0.0.1:8000"
npm run dev
