import React, { useState } from "react";
import { Routes, Route, NavLink, useNavigate } from "react-router-dom";
import { ShieldCheck, LayoutDashboard, ScanSearch, FileSearch, Network, FileText, Menu, X, Sparkles, Heart, ArrowUpRight, Upload, ShieldAlert, CheckCircle2, LockKeyhole } from "lucide-react";
import api from "./api";

function Shell({ children }) {
  const [open, setOpen] = useState(false);
  const links = [
    ["/", "Overview", LayoutDashboard],
    ["/footprint", "Footprint scan", ScanSearch],
    ["/files", "File privacy scan", FileSearch],
    ["/exposure", "Exposure insights", Network],
    ["/report", "Privacy report", FileText],
  ];
  return <div className="app-shell">
    <aside className={open ? "sidebar show" : "sidebar"}>
      <div className="brand"><div className="brand-mark"><img src="/vajra-logo.png" alt="VAJRA logo"/></div><div><b>VAJRA</b><small>YOUR DIGITAL SAFETY COMPANION</small></div></div>
      <div className="side-label">WORKSPACE</div>
      <nav>{links.map(([to, label, Icon]) => <NavLink end={to === "/"} to={to} key={to} onClick={() => setOpen(false)}><Icon size={18}/>{label}</NavLink>)}</nav>
      <div className="sidebar-note"><Heart size={18}/><b>Your privacy matters.</b><p>Built with a women-first safety mindset. Your data should stay yours.</p></div>
      <div className="side-foot"><LockKeyhole size={14}/> Privacy-first • No password collection</div>
    </aside>
    <main className="main-area">
      <header className="topbar"><button className="mobile-menu" onClick={() => setOpen(!open)}>{open ? <X/> : <Menu/>}</button><div><span className="eyebrow">PERSONAL DIGITAL SECURITY</span><b>VAJRA <span className="dot">●</span></b></div><div className="top-right"><span className="status"><i/> Local workspace</span><div className="avatar">V</div></div></header>
      <div className="page-wrap">{children}</div>
      <footer>VAJRA · Know what the internet knows about you. Protect what you share next. <span>Stay aware. Stay in control. ✦</span></footer>
    </main>
  </div>;
}
function PageHead({ eyebrow, title, desc, children }) {
  return <div className="page-head"><div><span className="eyebrow">{eyebrow}</span><h1>{title}</h1><p>{desc}</p></div>{children}</div>;
}
function EmptyCard({ icon: Icon, title, text }) {
  return <div className="empty-card"><div className="empty-icon"><Icon size={22}/></div><h3>{title}</h3><p>{text}</p></div>;
}
function RiskPill({ risk }) { return <span className={`risk-pill ${(risk?.level || "low").toLowerCase()}`}>{risk?.level || "Not assessed"} · {risk?.score ?? 0}/100</span>; }
function FindingList({ findings=[] }) {
  if (!findings.length) return <EmptyCard icon={CheckCircle2} title="No findings in this scan" text="No supported privacy indicators were detected. This does not guarantee that the file or account contains no sensitive information."/>;
  return <div className="finding-list">{findings.map((f,i)=><div className="finding" key={i}><div className="finding-symbol"><ShieldAlert size={18}/></div><div className="finding-copy"><b>{f.title}</b><p>{f.evidence}</p><small>Suggested action: {f.recommendation}</small></div><span className="severity">{f.severity}</span></div>)}</div>;
}
function AIAnalysis({ result }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [analysis, setAnalysis] = useState("");

  async function generateAnalysis() {
    setBusy(true);
    setError("");
    setAnalysis("");

    try {
      const { data } = await api.post("/api/ai/analyze", {
        findings: result.findings || [],
        risk: result.risk || {}
      });

      setAnalysis(data.ai_analysis);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "AI analysis failed. Please check whether the backend and Gemini API are running."
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="panel" style={{ marginTop: "20px" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
        <Sparkles size={22} />
        <div>
          <h2 style={{ margin: 0 }}>AI Privacy Assessment</h2>
          <p className="muted">Powered by VAJRA AI</p>
        </div>
      </div>

      <p>
        Get an AI-generated explanation of your scan results,
        understand potential risks, and discover practical ways
        to improve your digital privacy.
      </p>

      <button
        className="btn-primary"
        onClick={generateAnalysis}
        disabled={busy}
      >
        {busy ? "Analyzing your results..." : "Generate AI Assessment"}
        <Sparkles size={16} />
      </button>

      {error && (
        <div className="error" style={{ marginTop: "15px" }}>
          {error}
        </div>
      )}

      {analysis && (
        <div
          style={{
            marginTop: "20px",
            padding: "18px",
            borderRadius: "12px",
            background: "rgba(219, 112, 147, 0.08)",
            lineHeight: "1.7",
            whiteSpace: "pre-wrap"
          }}
        >
          <h3>VAJRA AI Analysis</h3>
          {analysis}
        </div>
      )}
    </div>
  );
}
function Dashboard({ latestFile, latestFootprint }) {
  const navigate = useNavigate();
  const has = latestFile || latestFootprint;
  const findings = [...(latestFile?.findings || []), ...(latestFootprint?.findings || [])];
  const risk = latestFile?.risk || latestFootprint?.risk;
  return <>
    <section className="hero">
      <div className="hero-copy"><span className="hero-kicker"><Sparkles size={14}/> YOUR PRIVACY, YOUR POWER</span><h1>Take control of your<br/><em>digital footprint.</em></h1><p>Discover what may be exposed, understand the risks, and make safer choices before you share.</p><div className="hero-actions"><button className="btn-primary" onClick={()=>navigate("/files")}>Scan a file <ArrowUpRight size={17}/></button><button className="btn-ghost" onClick={()=>navigate("/footprint")}>Check my footprint</button></div></div>
      <div className="hero-art"><div className="orbit orbit-one"></div><div className="orbit orbit-two"></div><div className="hero-shield"><ShieldCheck size={88} strokeWidth={1.2}/></div><div className="spark s1">✦</div><div className="spark s2">✧</div><div className="art-caption">A LITTLE MORE<br/>PRIVACY. A LOT MORE<br/><b>POWER.</b></div></div>
    </section>
    <div className="section-title"><div><span className="eyebrow">YOUR OVERVIEW</span><h2>Privacy at a glance</h2></div><span className="muted">Results from this browser session</span></div>
    <div className="stats-grid"><div className="stat-card"><span>Latest risk score</span><strong>{risk ? risk.score : "—"}<small>/100</small></strong><RiskPill risk={risk}/></div><div className="stat-card"><span>Findings detected</span><strong>{findings.length}</strong><small className="stat-sub">Across completed scans</small></div><div className="stat-card"><span>Scans completed</span><strong>{Number(!!latestFile)+Number(!!latestFootprint)}</strong><small className="stat-sub">File + footprint scans</small></div></div>
    <div className="section-title"><div><span className="eyebrow">GET STARTED</span><h2>Your safety toolkit</h2></div></div>
    <div className="tool-grid"><button className="tool-card" onClick={()=>navigate("/footprint")}><div className="tool-icon pink"><ScanSearch/></div><h3>Digital footprint scan</h3><p>Check your own email, username and public profile references with supported sources.</p><span>Start scan <ArrowUpRight size={15}/></span></button><button className="tool-card" onClick={()=>navigate("/files")}><div className="tool-icon gold"><FileSearch/></div><h3>File privacy scan</h3><p>Inspect images and documents for metadata and common sensitive-data patterns.</p><span>Inspect a file <ArrowUpRight size={15}/></span></button><button className="tool-card" onClick={()=>navigate("/report")}><div className="tool-icon lilac"><FileText/></div><h3>Privacy report</h3><p>Review scan findings, risk explanations and practical next steps.</p><span>View report <ArrowUpRight size={15}/></span></button></div>
    <div className="privacy-banner"><div className="privacy-icon"><LockKeyhole/></div><div><b>Designed around your privacy</b><p>VAJRA never asks for account passwords. This local MVP processes uploaded files temporarily and does not keep scan history on a server.</p></div></div>
  </>;
}
function Footprint({ setResult }) {
  const [form,setForm]=useState({email:"",username:"",profile_url:""});
  const [busy,setBusy]=useState(false), [error,setError]=useState(""), [result,setLocalResult]=useState(null);
  async function submit(e){e.preventDefault();setBusy(true);setError("");try{const {data}=await api.post("/api/footprint/scan",form);setResult(data);setLocalResult(data);}catch(err){setError(err.response?.data?.detail || "Could not connect to VAJRA backend. Is it running?");}finally{setBusy(false);}}
  return <><PageHead eyebrow="MODULE 01 · PUBLIC EXPOSURE" title="Digital footprint scan" desc="Check identifiers that belong to you. VAJRA uses supported, authorized sources and tells you clearly what it could—and could not—verify."/>
    <div className="content-grid"><form className="panel scan-form" onSubmit={submit}><h2>What would you like to check?</h2><p className="muted">Enter at least one of your own identifiers. Do not enter passwords.</p><label>Email address<input type="email" placeholder="you@example.com" value={form.email} onChange={e=>setForm({...form,email:e.target.value})}/></label><label>Username<input placeholder="Your public username" value={form.username} onChange={e=>setForm({...form,username:e.target.value})}/></label><label>Public profile URL<input type="url" placeholder="https://example.com/your-profile" value={form.profile_url} onChange={e=>setForm({...form,profile_url:e.target.value})}/></label><label className="consent"><input type="checkbox" required/> I confirm these identifiers are mine or I have permission to check them.</label>{error&&<div className="error">{error}</div>}<button className="btn-primary full" disabled={busy}>{busy?"Checking…":"Run footprint check"} <ArrowUpRight size={16}/></button></form><div className="panel info-panel"><div className="tool-icon pink"><ShieldCheck/></div><h3>What this MVP checks</h3><ul><li>Input format and supported identifiers</li><li>Optional breach lookup through the official HIBP API when configured</li><li>Clear status messages when a source is unavailable</li></ul><div className="notice"><b>Honest coverage matters</b><p>This version does not crawl social platforms, access private accounts, or guarantee discovery of every public mention or impersonation account.</p></div></div></div>
    <FootprintResult result={result}/>
  </>;
}
function FootprintResult({result}) {
  if(!result)return null;
  return <div className="panel results-panel"><div className="result-head"><div><span className="eyebrow">SCAN COMPLETE</span><h2>Footprint findings</h2></div><RiskPill risk={result.risk}/></div>{result.messages?.map((m,i)=><p className="message-line" key={i}>• {m}</p>)}<FindingList findings={result.findings}/><AIAnalysis key={result.scan_id} result={result}/><p className="fine-print">{result.notice}</p></div>;
}
function FilesPage({setResult,result}) {
 const [file,setFile]=useState(null),[busy,setBusy]=useState(false),[error,setError]=useState("");
 async function submit(e){e.preventDefault();if(!file)return;setBusy(true);setError("");const fd=new FormData();fd.append("file",file);try{const {data}=await api.post("/api/files/scan",fd,{headers:{"Content-Type":"multipart/form-data"}});setResult(data);}catch(err){setError(err.response?.data?.detail||"File scan failed. Check backend.");}finally{setBusy(false);}}
 async function clean(){if(!file)return;const fd=new FormData();fd.append("file",file);try{const res=await api.post("/api/files/clean-image",fd,{responseType:"blob",headers:{"Content-Type":"multipart/form-data"}});const url=URL.createObjectURL(res.data);const a=document.createElement("a");a.href=url;a.download="vajra_cleaned"+(file.name.toLowerCase().endsWith(".png")?".png":".jpg");a.click();URL.revokeObjectURL(url);}catch(err){setError(err.response?.data?.detail||"Cleaning failed. Image files only.");}}
 return <><PageHead eyebrow="MODULE 02 · BEFORE YOU SHARE" title="File privacy scanner" desc="Check photos and documents for hidden metadata and common personal-information patterns before sharing them."/><div className="content-grid"><form className="panel upload-panel" onSubmit={submit}><div className="upload-zone"><div className="upload-icon"><Upload size={28}/></div><h2>Drop your file into the safe zone</h2><p>Or choose a file from your device</p><input type="file" accept=".png,.jpg,.jpeg,.pdf,.docx" onChange={e=>setFile(e.target.files[0])}/><small>PNG, JPG, JPEG, PDF, DOCX · Max 10 MB</small></div>{file&&<div className="selected-file"><FileText size={18}/><span>{file.name}</span><b>{(file.size/1024).toFixed(0)} KB</b></div>}{error&&<div className="error">{error}</div>}<button className="btn-primary full" disabled={!file||busy}>{busy?"Scanning…":"Scan file for privacy leaks"} <ArrowUpRight size={16}/></button></form><div className="panel info-panel"><div className="tool-icon gold"><FileSearch/></div><h3>What VAJRA looks for</h3><ul><li>Image EXIF metadata and possible GPS metadata block</li><li>PDF text and document properties</li><li>DOCX text and author properties</li><li>Email, phone and ID-like patterns</li></ul><div className="notice"><b>Keep control of your original</b><p>VAJRA creates a separate cleaned image copy when you choose to remove EXIF metadata. Your original file is not overwritten.</p></div></div></div>{result&&<div className="panel results-panel"><div className="result-head"><div><span className="eyebrow">FILE SCAN COMPLETE</span><h2>{result.filename}</h2><p className="muted">{result.file_type} · {result.scan_id}</p></div><RiskPill risk={result.risk}/></div><FindingList findings={result.findings}/><AIAnalysis key={result.scan_id} result={result}/><div className="details-box"><b>Technical details</b><pre>{JSON.stringify(result.details,null,2)}</pre></div>{["PNG","JPG","JPEG"].includes(result.file_type)&&<button className="btn-secondary" onClick={clean}>Download separate EXIF-cleaned image</button>}<p className="fine-print">{result.notice}</p></div>}</>;
}
function Exposure({latestFile,latestFootprint}) {
 const items=[...(latestFile?.findings||[]),...(latestFootprint?.findings||[])];
 return <><PageHead eyebrow="MODULE 03 · UNDERSTAND THE CONNECTIONS" title="Exposure insights" desc="A clear view of the privacy indicators found by your completed scans. Connections are only shown when supported by evidence."/>{items.length?<div className="panel"><div className="section-title"><div><h2>Detected exposure indicators</h2><p className="muted">This MVP lists findings; relationship mapping is a future phase.</p></div></div><FindingList findings={items}/></div>:<EmptyCard icon={Network} title="Your exposure view is waiting" text="Complete a footprint or file scan to see the privacy indicators detected by VAJRA here."/>}</>;
}
function Report({latestFile,latestFootprint}) {
 const findings=[...(latestFile?.findings||[]),...(latestFootprint?.findings||[])];
 const risk=latestFile?.risk||latestFootprint?.risk;
 return <><PageHead eyebrow="MODULE 04 · YOUR ACTION PLAN" title="Privacy report" desc="A readable summary of the results available in this browser session."/>{!risk?<EmptyCard icon={FileText} title="No report yet" text="Run a file scan or footprint check first. Your report will be built from actual scan results, not sample data."/>:<><div className="report-score panel"><div><span className="eyebrow">CURRENT ASSESSMENT</span><h2>{risk.level} exposure</h2><p className="muted">{risk.method}</p></div><div className="score-circle"><strong>{risk.score}</strong><small>/100</small></div></div><div className="panel"><h2>Findings and recommended actions</h2><FindingList findings={findings}/></div><div className="notice report-note"><b>Assessment limitations</b><p>This score is a transparent prototype heuristic, not a validated security rating. It only reflects supported findings from scans run in this session. A low score is not proof of safety.</p></div></>}</>;
}
export default function App(){
 const [latestFile,setLatestFile]=useState(null),[latestFootprint,setLatestFootprint]=useState(null);
 return <Shell><Routes>
  <Route path="/" element={<Dashboard latestFile={latestFile} latestFootprint={latestFootprint}/>}/>
  <Route path="/footprint" element={<Footprint setResult={setLatestFootprint}/>}/>
  <Route path="/files" element={<FilesPage setResult={setLatestFile} result={latestFile}/>}/>
  <Route path="/exposure" element={<Exposure latestFile={latestFile} latestFootprint={latestFootprint}/>}/>
  <Route path="/report" element={<Report latestFile={latestFile} latestFootprint={latestFootprint}/>}/>
  <Route path="*" element={<Dashboard latestFile={latestFile} latestFootprint={latestFootprint}/>}/>
 </Routes></Shell>;
}
