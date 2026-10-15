# Architecture

```text
User
  ↓
Streamlit / future React
  ↓
FastAPI
  ↓
Validation + Authentication
  ↓
Blob Storage (Azure in production)
  ↓
Dataset Processing
  ↓
Azure SQL / SQLite local
  ↓
AI plan generation
  ↓
Safe Pandas/SQL analysis
  ↓
Result validation
  ↓
Plotly
  ↓
Verified AI business explanation
```

The LLM is never the source of numerical truth.
