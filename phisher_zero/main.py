from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import uvicorn
import logging

from nlp_agent.agent import NLPAgent
from url_agent.agent import URLAgent
from ensemble_agent.agent import EnsembleAgent
from explainer_agent.agent import ExplainerAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Phisher Zero API",
    description="Multi-agent phishing detection system.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev frontend (e.g. localhost:5173). In production lock this down.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agents
nlp_agent = NLPAgent()
url_agent = URLAgent()
ensemble_agent = EnsembleAgent()
explainer_agent = ExplainerAgent()

class AnalyzeRequest(BaseModel):
    email_text: str = Field(..., description="The content of the email to analyze")
    url: Optional[str] = Field(default=None, description="The URL extracted from the email or to analyze independently")

class AnalyzeResponse(BaseModel):
    analysis: dict
    explanation: dict

@app.get("/")
def read_root():
    return {"message": "Phisher Zero API is running."}

@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    try:
        # 1. NLP Agent Analysis
        nlp_score = nlp_agent.get_score(req.email_text)
        nlp_analysis = {"nlp_score": nlp_score}
        
        # 2 + 3. URL Agent & VirusTotal Analysis combined
        if req.url:
            url_analysis = url_agent.analyze(req.url)
            virustotal_confidence = url_analysis["virustotal"]["confidence"]
            url_risk_score = url_analysis["url_risk_score"]
        else:
            url_analysis = None
            url_risk_score = None
            virustotal_confidence = None
        
        # 4. Ensemble Agent Analysis
        ensemble_analysis = ensemble_agent.aggregate(
            nlp_score=nlp_score,
            url_score=url_risk_score,
            virustotal_confidence=virustotal_confidence if virustotal_confidence else 0.0
        )
        
        # Consolidate raw data for the explainer
        full_analysis_data = {
            "final_score": ensemble_analysis["final_score"],
            "verdict": ensemble_analysis["verdict"],
            "url_agent": url_analysis,
            "nlp_agent": nlp_analysis,
            "virustotal": url_analysis["virustotal"] if url_analysis else None
        }
        
        # 5. Explainer Agent Analysis
        explanation = explainer_agent.explain(full_analysis_data)
        
        # Build structure for response
        response = {
            "analysis": {
                "nlp": nlp_analysis,
                "url": url_analysis,
                "ensemble": ensemble_analysis
            },
            "explanation": explanation
        }
        
        return response

    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
