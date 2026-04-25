import os
import logging
from typing import List, Optional
import fitz  # PyMuPDF
from pydantic import BaseModel
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class ExtractedEntities(BaseModel):
    npi: Optional[str]
    hcpcs_codes: List[str]
    provider_name: Optional[str]
    summary_of_fraud: Optional[str]

class DraftComplaint(BaseModel):
    title: str
    body_markdown: str

class AIPipeline:
    def __init__(self):
        # Requires NVIDIA_API_KEY in .env
        api_key = os.getenv("NVIDIA_API_KEY")
        if not api_key:
            logger.warning("NVIDIA_API_KEY not found in environment.")
            self.llm = None
        else:
            self.llm = ChatNVIDIA(model="meta/llama-3.1-70b-instruct", api_key=api_key)

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract all text from a PDF file using PyMuPDF."""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            return text
        except Exception as e:
            logger.error(f"Failed to read PDF {pdf_path}: {e}")
            return ""

    def analyze_evidence(self, text: str) -> Optional[ExtractedEntities]:
        """Use LLM to extract NPIs and medical codes from messy text."""
        if not self.llm:
            return None

        parser = PydanticOutputParser(pydantic_object=ExtractedEntities)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert fraud investigator. Extract entities from the following whistleblower evidence. Find any 10-digit NPIs (National Provider Identifiers) and 5-character HCPCS/CPT medical billing codes. Also summarize the core fraud allegation. \n{format_instructions}"),
            ("user", "EVIDENCE TEXT:\n{text}")
        ])
        
        chain = prompt | self.llm | parser
        
        try:
            result = chain.invoke({
                "text": text[:10000], # Limit to avoid context window blowouts
                "format_instructions": parser.get_format_instructions()
            })
            return result
        except Exception as e:
            logger.error(f"LLM Extraction failed: {e}")
            return None

    def draft_fca_complaint(self, evidence_summary: str, stats: dict) -> Optional[DraftComplaint]:
        """Synthesize whistleblower tip and database stats into a legal complaint."""
        if not self.llm:
            return None
            
        parser = PydanticOutputParser(pydantic_object=DraftComplaint)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an elite False Claims Act (qui tam) lawyer. Write a draft legal complaint. Combine the qualitative whistleblower evidence with the quantitative statistical anomaly found in the CMS database. Format the body in professional Markdown. \n{format_instructions}"),
            ("user", "WHISTLEBLOWER EVIDENCE SUMMARY:\n{evidence_summary}\n\nSTATISTICAL ANOMALY FROM CMS DATABASE:\n{stats}")
        ])
        
        chain = prompt | self.llm | parser
        
        try:
            result = chain.invoke({
                "evidence_summary": evidence_summary,
                "stats": str(stats),
                "format_instructions": parser.get_format_instructions()
            })
            return result
        except Exception as e:
            logger.error(f"LLM Drafting failed: {e}")
            return None

ai_pipeline = AIPipeline()
