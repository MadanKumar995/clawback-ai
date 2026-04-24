# Clawback AI: Fraud Investigator Copilot

## 1. Background & Motivation
The False Claims Act allows private citizens to sue entities defrauding the government. Investigators receive unstructured tips (messy PDFs, emails) but need hard data to prove fraud. Our system bridges this gap. It ingests whistleblower documents, extracts key entities using AI, and automatically cross-references them against massive federal datasets (CMS Medicaid Spending) to mathematically verify the fraud.

## 2. Scope & Impact
**Scope:** A web workspace where investigators upload whistleblower evidence. The system parses the documents to extract target providers and medical codes, queries a 3GB Medicaid billing dataset to find statistical anomalies for those targets, and synthesizes the findings into a draft False Claims Act complaint.
**Impact:** Combines unstructured evidence with structured government data. Reduces investigation time from months to minutes.

## 3. Architecture & Tech Stack
- **Frontend:** Next.js + Tailwind CSS.
- **Backend:** Python FastAPI.
- **Document Parsing & AI:** Nvidia NIM (Llama 3) for OCR extraction and report drafting.
- **Data Engine:** DuckDB (Reads the CMS Medicaid Parquet dataset directly for fast analytical queries).
- **Storage:** Supabase (for PDFs and user sessions).

## 4. User Workflow (Hybrid)
1. **Drop (Ingest):** Whistleblower uploads "Evidence" (PDFs).
2. **Scan (Extract):** AI parses docs. Extracts Provider NPIs, names, and suspicious medical codes (HCPCS).
3. **Link & Verify (Analyze):** Backend queries the Medicaid Parquet data via DuckDB. Checks if the extracted provider is a statistical outlier compared to national averages for those codes.
4. **File (Draft):** One-click generation of a draft FCA legal complaint, citing both the PDF evidence and the mathematical anomaly found in the CMS data.

## 5. Implementation Epics
### Epic 1: Repo Setup & Data Prep
- Init Next.js and FastAPI.
- Place Parquet file in `data/`.

### Epic 2: Document Ingestion
- Upload UI in Next.js.
- FastAPI endpoint to receive and parse PDFs (using `PyMuPDF` + Nvidia NIM).

### Epic 3: The Data Engine
- Implement DuckDB to query the Parquet dataset.
- Function to take extracted NPI/Codes and return anomaly stats (Z-scores, comparison to averages).

### Epic 4: Synthesis & Output
- Prompt Nvidia NIM with both PDF facts and DuckDB stats to write the final draft complaint.
- Build results dashboard UI.