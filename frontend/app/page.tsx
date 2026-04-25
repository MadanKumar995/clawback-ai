"use client";

import { useState } from 'react';
import axios from 'axios';
import { Upload, AlertCircle, FileText, Activity, ArrowRight, Loader2, Download } from 'lucide-react';

const API_BASE = 'http://localhost:8000/api';

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1);
  const [error, setError] = useState<string | null>(null);
  
  const [entities, setEntities] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);
  const [draft, setDraft] = useState<any>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const processEvidence = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      // 1. Upload and Ingest
      const formData = new FormData();
      formData.append('file', file);
      const ingestRes = await axios.post(`${API_BASE}/ingest`, formData);
      const extracted = ingestRes.data.data;
      setEntities(extracted);
      setStep(2);

      // 2. Query DuckDB (Take first NPI and Code for simplicity)
      if (extracted.npi && extracted.hcpcs_codes && extracted.hcpcs_codes.length > 0) {
        const analyzeRes = await axios.post(`${API_BASE}/analyze`, {
          npi: extracted.npi,
          hcpcs_code: extracted.hcpcs_codes[0]
        });
        setStats(analyzeRes.data.data);
      }
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || "Failed to process evidence. Ensure Backend is running and API keys are set.");
    } finally {
      setLoading(false);
    }
  };

  const generateDraft = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.post(`${API_BASE}/draft`, {
        evidence_summary: entities.summary_of_fraud,
        stats: stats
      });
      setDraft(res.data.data);
      setStep(3);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || "Failed to generate draft.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 p-8">
      <div className="max-w-5xl mx-auto space-y-8">
        {/* Header */}
        <header className="flex items-center justify-between bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <div className="flex items-center space-x-3">
            <Activity className="w-8 h-8 text-blue-600" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Clawback AI</h1>
              <p className="text-sm text-gray-500">Medicaid Fraud Investigator Copilot</p>
            </div>
          </div>
          <div className="flex items-center space-x-2 text-sm text-gray-500 font-mono">
             <span>Status: </span>
             <span className="flex h-3 w-3 relative">
               <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
               <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
             </span>
          </div>
        </header>

        {error && (
          <div className="p-4 bg-red-50 border-l-4 border-red-500 text-red-700 flex items-start space-x-3 rounded-r-md">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <p>{error}</p>
          </div>
        )}

        <div className="grid grid-cols-3 gap-8">
          {/* Left Column: Upload */}
          <div className="col-span-1 space-y-6">
            <div className={`p-6 rounded-xl border-2 transition-all ${step === 1 ? 'border-blue-500 bg-blue-50' : 'border-gray-200 bg-white'}`}>
              <h2 className="font-semibold mb-4 flex items-center"><Upload className="w-5 h-5 mr-2"/> 1. Upload Evidence</h2>
              <p className="text-sm text-gray-600 mb-4">Upload whistleblower tips, emails, or PDFs containing raw allegations.</p>
              
              <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer bg-white hover:bg-gray-50">
                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                  <Upload className="w-6 h-6 mb-2 text-gray-500" />
                  <p className="text-sm text-gray-500 font-semibold">{file ? file.name : "Click to select PDF"}</p>
                </div>
                <input type="file" className="hidden" accept=".pdf" onChange={handleFileChange} />
              </label>

              <button 
                onClick={processEvidence}
                disabled={!file || loading}
                className="w-full mt-4 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 rounded-lg flex items-center justify-center disabled:opacity-50"
              >
                {loading && step === 1 ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : "Extract & Verify"}
                {(!loading || step !== 1) && <ArrowRight className="w-4 h-4 ml-2" />}
              </button>
            </div>
          </div>

          {/* Right Column: Analysis & Output */}
          <div className="col-span-2 space-y-6">
            {/* Step 2: Extraction & Verification */}
            <div className={`p-6 rounded-xl border bg-white shadow-sm ${step >= 2 ? 'opacity-100' : 'opacity-40 pointer-events-none'}`}>
              <h2 className="font-semibold mb-4 flex items-center border-b pb-2"><Activity className="w-5 h-5 mr-2 text-indigo-500"/> 2. AI Extraction & Data Verification</h2>
              
              {entities ? (
                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div className="p-4 bg-gray-50 rounded-lg border">
                    <h3 className="text-xs text-gray-500 uppercase font-bold tracking-wider mb-1">Target Provider</h3>
                    <p className="font-semibold">{entities.provider_name || "Unknown"}</p>
                    <p className="font-mono text-sm text-blue-600">NPI: {entities.npi}</p>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-lg border">
                    <h3 className="text-xs text-gray-500 uppercase font-bold tracking-wider mb-1">Target Codes</h3>
                    <div className="flex flex-wrap gap-2">
                      {entities.hcpcs_codes.map((code: string, i: number) => (
                        <span key={i} className="px-2 py-1 bg-indigo-100 text-indigo-800 text-xs font-mono rounded">{code}</span>
                      ))}
                    </div>
                  </div>
                  <div className="col-span-2 p-4 bg-gray-50 rounded-lg border">
                     <h3 className="text-xs text-gray-500 uppercase font-bold tracking-wider mb-1">Allegation Summary</h3>
                     <p className="text-sm italic text-gray-700">"{entities.summary_of_fraud}"</p>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-gray-500 mb-6">Awaiting document extraction...</p>
              )}

              {/* Stats Section */}
              {stats ? (
                <div className="mb-6 border-l-4 border-red-500 pl-4 py-2 bg-red-50 rounded-r-lg">
                  <h3 className="text-sm font-bold text-red-800 mb-2 flex items-center">
                    <AlertCircle className="w-4 h-4 mr-1"/> Statistical Anomaly Detected (DuckDB)
                  </h3>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-red-600">Provider Total Paid:</p>
                      <p className="font-mono font-bold text-lg">${stats.provider_total_paid.toLocaleString(undefined, {minimumFractionDigits: 2})}</p>
                    </div>
                    <div>
                      <p className="text-gray-600">National Average:</p>
                      <p className="font-mono text-lg">${stats.national_avg_paid.toLocaleString(undefined, {minimumFractionDigits: 2})}</p>
                    </div>
                    <div className="col-span-2">
                      <p className="text-gray-600 mb-1">Z-Score (Standard Deviations above norm):</p>
                      <div className="w-full bg-gray-200 rounded-full h-4 mb-1">
                         <div className="bg-red-500 h-4 rounded-full w-full"></div>
                      </div>
                      <p className="font-mono text-red-700 font-bold text-xl">{stats.z_score_paid.toFixed(2)}</p>
                    </div>
                  </div>
                </div>
              ) : entities ? (
                 <p className="text-sm text-gray-500 mb-6">Provider/Code not found in CMS dataset.</p>
              )}

              {step === 2 && (
                <button 
                  onClick={generateDraft}
                  disabled={loading || !stats}
                  className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 rounded-lg flex items-center justify-center disabled:opacity-50"
                >
                  {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <FileText className="w-4 h-4 mr-2" />}
                  Synthesize Legal Complaint
                </button>
              )}
            </div>

            {/* Step 3: Output */}
            <div className={`p-6 rounded-xl border bg-white shadow-sm ${step >= 3 ? 'opacity-100' : 'opacity-40 pointer-events-none'}`}>
              <div className="flex items-center justify-between border-b pb-4 mb-4">
                <h2 className="font-semibold flex items-center"><FileText className="w-5 h-5 mr-2 text-green-600"/> 3. Draft FCA Complaint</h2>
                {draft && <button className="text-sm text-blue-600 hover:underline flex items-center"><Download className="w-4 h-4 mr-1"/> Export PDF</button>}
              </div>
              
              {draft ? (
                <div className="prose prose-sm max-w-none text-gray-800 whitespace-pre-wrap">
                  <h1 className="text-xl font-bold font-serif mb-4 text-center">{draft.title}</h1>
                  <div dangerouslySetInnerHTML={{ __html: draft.body_markdown.replace(/\n/g, '<br/>') }} />
                </div>
              ) : (
                <p className="text-sm text-gray-500 text-center py-8">Complaint will be generated here.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}