"""Postgres MCP Server"""
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/query")
def execute_query(query: str):
    """Execute SQL via MCP"""
    return {"results": []}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8101)
