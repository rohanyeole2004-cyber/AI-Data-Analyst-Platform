from fastapi import FastAPI,UploadFile,File,HTTPException
from pydantic import BaseModel,Field
from app.analysis.io import load_dataframe
from app.analysis.profiling import profile_dataframe,quality_report
from app.analysis.engine import execute,validate
from app.analysis.charts import chart_for
from app.ai.parser import parse
from app.ai.insights import verified_insight
from app.db import init_db
app=FastAPI(title="AI Data Analyst Platform",version="1.0.0")
init_db()
STATE={"df":None,"filename":None}
class Question(BaseModel): question:str=Field(min_length=3,max_length=500)
@app.get("/health")
def health():return {"status":"ok"}
@app.post("/upload")
async def upload(file:UploadFile=File(...)):
 data=await file.read()
 if len(data)>20*1024*1024:raise HTTPException(413,"File exceeds 20 MB")
 import io
 try:df=load_dataframe(io.BytesIO(data))
 except Exception as e:raise HTTPException(400,str(e))
 STATE.update(df=df,filename=file.filename); return {"filename":file.filename,"profile":profile_dataframe(df),"quality":quality_report(df)}
@app.post("/analyze")
def analyze(q:Question):
 if STATE["df"] is None:raise HTTPException(400,"Upload a dataset first")
 try:
  plan=parse(q.question,STATE["df"]); result=execute(STATE["df"],plan); validation=validate(result); insight=verified_insight(plan,result); chart=chart_for(result,plan)
 except Exception as e:raise HTTPException(400,str(e))
 return {"question":q.question,"plan":plan,"columns":list(result.columns),"result":result.to_dict("records"),"validation":validation,"insight":insight,"chart_json":chart.to_json() if chart else None}
