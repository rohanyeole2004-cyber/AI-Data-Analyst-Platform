# Cloud-Based AI-Powered Data Analyst Platform

Portfolio project for Data Analytics + Azure + AI.

## Current implementation
- Streamlit frontend
- FastAPI backend
- CSV/XLSX upload and validation
- Pandas profiling and data-quality checks
- Deterministic natural-language question parser for safe Phase-1 questions
- Structured analysis plans
- Pandas execution on the real uploaded dataset
- Result validation
- Plotly charts
- Verified business insights
- Local SQLite metadata database
- Azure Blob, Key Vault and Application Insights adapters
- Dockerfile
- Automated tests

## Critical anti-hallucination rule
The application never accepts an LLM-generated numerical answer as truth. A question is converted into a structured plan, executed against the real data, validated, and only then explained. The local parser is deterministic. An LLM can be added later as a plan generator behind the provider interface.

## Windows setup
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```
If activation is blocked in PowerShell:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## Run frontend
```powershell
streamlit run app/frontend/app.py
```

## Run API
In another terminal:
```powershell
.\.venv\Scripts\Activate.ps1
uvicorn app.backend.main:app --reload
```
Then open `/docs` on the FastAPI local address.

## Tests
```powershell
pytest -q
```

## Azure roadmap
1. Resource Group
2. Storage Account + Blob Container
3. Azure SQL Database
4. Key Vault + Managed Identity
5. App Service
6. Application Insights
7. Entra ID authentication
8. LLM provider with structured JSON plans

Azure resources are intentionally not created by this package because that requires the user's Azure subscription/credentials and may incur charges.
