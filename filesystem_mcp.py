"""File System MCP Server"""
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/files/{path}")
def read_file(path: str):
    """Read file via MCP"""
    return {"content": "file content"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8100)
