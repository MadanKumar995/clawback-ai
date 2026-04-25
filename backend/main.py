from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from engine import engine

app = FastAPI(title="Clawback AI API")

# Setup CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ProviderQuery(BaseModel):
    npi: str
    hcpcs_code: str

@app.get("/")
def read_root():
    return {"status": "ok", "app": "Clawback AI Backend"}

@app.post("/api/analyze")
def analyze_provider(query: ProviderQuery):
    """
    Analyze a specific provider's billing for a given code.
    """
    stats = engine.get_provider_stats(query.npi, query.hcpcs_code)
    
    if not stats:
        raise HTTPException(status_code=404, detail="Provider or code not found in dataset.")
        
    return {"status": "success", "data": stats}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
