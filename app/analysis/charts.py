import pandas as pd
import plotly.express as px
def chart_for(result,plan):
    if result.empty:return None
    if plan["operation"]=="group_by" and len(result.columns)>=2: return px.bar(result,x=result.columns[0],y=result.columns[1],title=f"{result.columns[1]} by {result.columns[0]}")
    if plan["operation"]=="aggregate": return px.bar(result,x="metric",y="value",title="Metric")
    return None
