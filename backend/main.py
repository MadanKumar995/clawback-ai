from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import shutil
import os
from engine import engine
from ai_agent import ai_pipeline

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

class ComplaintRequest(BaseModel):
    evidence_summary: str
    stats: dict

@app.get("/")
def read_root():
    return {"status": "ok", "app": "Clawback AI Backend"}

@app.post("/api/analyze")
def analyze_provider(query: ProviderQuery):
    """Analyze a specific provider's billing for a given code."""
    stats = engine.get_provider_stats(query.npi, query.hcpcs_code)
    
    if not stats:
        raise HTTPException(status_code=404, detail="Provider or code not found in dataset.")
        
    return {"status": "success", "data": stats}

@app.post("/api/ingest")
async def ingest_evidence(file: UploadFile = File(...)):
    """Upload a PDF tip, extract text, and find entities using LLM."""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # Extract raw text
        raw_text = ai_pipeline.extract_text_from_pdf(temp_path)
        if not raw_text:
            raise HTTPException(status_code=500, detail="Could not extract text from PDF.")
            
        # Parse entities with LLM
        entities = ai_pipeline.analyze_evidence(raw_text)
        if not entities:
            raise HTTPException(status_code=500, detail="LLM extraction failed. Check API key.")
            
        return {"status": "success", "data": entities.dict()}
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/api/draft")
def generate_draft(req: ComplaintRequest):
    """Generate a draft FCA complaint from evidence and DB stats."""
    draft = ai_pipeline.draft_fca_complaint(req.evidence_summary, req.stats)
    if not draft:
        raise HTTPException(status_code=500, detail="Failed to generate draft.")
        
    return {"status": "success", "data": draft.dict()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
