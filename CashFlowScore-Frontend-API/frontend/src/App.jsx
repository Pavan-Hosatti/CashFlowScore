import React, { useEffect, useState, useCallback, useRef } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:8002';
const API_KEY  = 'NBFC_TEST_KEY_123';
const authHeaders = { Authorization: `Bearer ${API_KEY}` };

const fmt       = (n) => Number(n).toLocaleString('en-IN');
const fmtRs     = (n) => `₹${fmt(n)}`;
const scoreColor = (s) => s >= 75 ? '#10b981' : s >= 55 ? '#f59e0b' : '#f43f5e';
const scoreLabel = (s) => s >= 75 ? 'Approved' : s >= 55 ? 'Review' : 'Rejected';

/* ─── Utility Components ─────────────────────────────────────────────────── */

function Sep() { return <div style={{width:1,height:28,background:'#1e293b'}} />; }

function Metric({ label, value, color = 'text-white' }) {
  return (
    <div style={{textAlign:'center'}}>
      <div style={{fontSize:15,fontWeight:700,color: color==='text-teal-400'?'#2dd4bf': color==='text-cyan-400'?'#22d3ee':'#f59e0b'}}>{value}</div>
      <div style={{fontSize:10,color:'#64748b',textTransform:'uppercase',letterSpacing:'0.08em'}}>{label}</div>
    </div>
  );
}

function NavLink({ children, href }) {
  return (
    <a href={href} style={{color:'#94a3b8',fontSize:14,textDecoration:'none',transition:'color 0.2s'}}
       onMouseEnter={e=>e.target.style.color='#f1f5f9'}
       onMouseLeave={e=>e.target.style.color='#94a3b8'}>
      {children}
    </a>
  );
}

/* ─── Landing Page Sections ──────────────────────────────────────────────── */

/* ─── Hero Section ───────────────────────────────────────────────────────── */

function HeroSection({ onScrollToDemo }) {
  const [stats, setStats] = React.useState(null);
  const [tick,  setTick]  = React.useState(0);

  React.useEffect(() => {
    const poll = async () => {
      try {
        const r = await axios.get(`${API_BASE}/pipeline-stats`);
        setStats(r.data);
        setTick(t => t + 1);
      } catch {}
    };
    poll();
    const t = setInterval(poll, 2500);
    return () => clearInterval(t);
  }, []);

  const live  = (stats?.events_processed ?? 0) > 0;
  const tsdb  = stats?.timescaledb_rows   ?? null;
  const rkeys = stats?.redis_keys         ?? null;

  return (
    <section id="hero" style={{
      minHeight: '100vh',
      background: '#020817',
      position: 'relative',
      overflow: 'hidden',
      display: 'flex',
      flexDirection: 'column',
    }}>
      {/* fine grid */}
      <div style={{
        position:'absolute', inset:0, pointerEvents:'none',
        backgroundImage: 'linear-gradient(rgba(30,41,59,0.35) 1px,transparent 1px),linear-gradient(90deg,rgba(30,41,59,0.35) 1px,transparent 1px)',
        backgroundSize: '48px 48px',
      }}/>
      {/* teal accent glow */}
      <div style={{
        position:'absolute', bottom:'-80px', left:'-120px',
        width:700, height:500, pointerEvents:'none',
        background:'radial-gradient(ellipse at center,rgba(13,148,136,0.07) 0%,transparent 65%)',
      }}/>
      {/* blue accent glow */}
      <div style={{
        position:'absolute', top:'10%', right:'-80px',
        width:500, height:500, pointerEvents:'none',
        background:'radial-gradient(ellipse at center,rgba(59,130,246,0.05) 0%,transparent 65%)',
      }}/>

      {/* ── main content ── */}
      <div style={{
        position:'relative', flex:1,
        maxWidth:1260, margin:'0 auto', width:'100%',
        padding:'120px 48px 80px',
        display:'grid',
        gridTemplateColumns:'1fr 400px',
        gap:56, alignItems:'center',
      }}>

        {/* ── LEFT ── */}
        <div>
          {/* live pill */}
          <div style={{
            display:'inline-flex', alignItems:'center', gap:8,
            borderRadius:100, padding:'5px 16px', marginBottom:32,
            border:'1px solid',
            borderColor: live ? 'rgba(16,185,129,0.3)' : 'rgba(71,85,105,0.4)',
            background:  live ? 'rgba(16,185,129,0.06)' : 'rgba(15,23,42,0.6)',
          }}>
            <div style={{
              width:7, height:7, borderRadius:'50%',
              background: live ? '#10b981' : '#475569',
              boxShadow: live ? '0 0 7px #10b981' : 'none',
              flexShrink:0,
            }}/>
            <span style={{
              fontSize:10, fontWeight:700, letterSpacing:'0.12em',
              textTransform:'uppercase',
              color: live ? '#10b981' : '#475569',
            }}>
              {live
                ? `${Number(stats.events_processed).toLocaleString('en-IN')} events in pipeline`
                : 'MSME Credit Infrastructure'}
            </span>
          </div>

          {/* headline */}
          <h1 style={{
            fontSize:'clamp(38px,4.8vw,66px)',
            fontWeight:800, lineHeight:1.1,
            letterSpacing:'-0.035em',
            color:'#f1f5f9',
            marginBottom:0,
          }}>
            Credit decisions<br/>
            <span style={{color:'#2dd4bf'}}>from cash flow.</span>
          </h1>
          <p style={{
            fontSize:'clamp(16px,1.6vw,20px)',
            fontWeight:500, color:'#94a3b8',
            letterSpacing:'-0.01em',
            marginTop:10, marginBottom:28,
          }}>Not collateral. Not bureau scores.</p>

          {/* sub-copy */}
          <p style={{
            fontSize:15, color:'#64748b', lineHeight:1.85,
            maxWidth:500, marginBottom:40,
          }}>
            End-to-end credit infrastructure for Indian NBFCs and Small Finance Banks.
            Live UPI, bank and GST event ingestion &rarr; real-time feature engineering
            &rarr; XGBoost + SHAP scoring &rarr; loan officer dashboard.
            Scores 1,000 businesses in under 2 seconds.
          </p>

          {/* CTAs */}
          <div style={{display:'flex', gap:12, flexWrap:'wrap', marginBottom:52}}>
            <button onClick={onScrollToDemo} style={{
              background:'#0d9488', color:'#fff', border:'none',
              borderRadius:8, padding:'14px 32px',
              fontSize:14, fontWeight:700, cursor:'pointer',
              letterSpacing:'-0.01em', transition:'background .15s',
            }}
            onMouseEnter={e=>e.currentTarget.style.background='#0f766e'}
            onMouseLeave={e=>e.currentTarget.style.background='#0d9488'}>
              Open Loan Ops Console
            </button>
            <a href="#who-we-are" style={{
              display:'flex', alignItems:'center', gap:6,
              border:'1px solid #1e293b', borderRadius:8,
              padding:'14px 24px', fontSize:14, fontWeight:600,
              color:'#64748b', textDecoration:'none',
              transition:'all .15s',
            }}
            onMouseEnter={e=>{e.currentTarget.style.borderColor='#334155';e.currentTarget.style.color='#94a3b8';}}
            onMouseLeave={e=>{e.currentTarget.style.borderColor='#1e293b';e.currentTarget.style.color='#64748b';}}>
              The problem we solve ↓
            </a>
          </div>

          {/* live stat strip */}
          <div style={{
            display:'grid', gridTemplateColumns:'repeat(4,1fr)',
            borderTop:'1px solid #0f172a', paddingTop:32, gap:0,
          }}>
            {[
              { v: stats ? Number(stats.events_processed||0).toLocaleString('en-IN')       : '--', l:'Events processed',   color:'#2dd4bf' },
              { v: stats ? Number(stats.business_count||0).toLocaleString('en-IN')         : '--', l:'Businesses tracked', color:'#3b82f6' },
              { v: tsdb  ? Number(tsdb).toLocaleString('en-IN')                            : '--', l:'TimescaleDB rows',   color:'#8b5cf6' },
              { v: rkeys ? Number(rkeys).toLocaleString('en-IN')                           : '--', l:'Redis keys',         color:'#f59e0b' },
            ].map((s,i) => (
              <div key={i} style={{
                padding: i===0 ? '0 24px 0 0' : '0 24px',
                borderLeft: i===0 ? 'none' : '1px solid #0f172a',
              }}>
                <div style={{
                  fontSize:28, fontWeight:800, color:s.color,
                  letterSpacing:'-0.025em', fontVariantNumeric:'tabular-nums',
                  marginBottom:5, lineHeight:1,
                  transition:'color .4s',
                }}>{s.v}</div>
                <div style={{fontSize:10,color:'#334155',textTransform:'uppercase',letterSpacing:'0.1em'}}>{s.l}</div>
              </div>
            ))}
          </div>
        </div>

        {/* ── RIGHT — system card ── */}
        <div style={{
          background:'#040d1a',
          border:'1px solid #1e293b',
          borderRadius:16, padding:0,
          overflow:'hidden',
          boxShadow:'0 24px 60px rgba(0,0,0,0.4)',
        }}>
          {/* card header */}
          <div style={{
            padding:'16px 22px',
            borderBottom:'1px solid #1e293b',
            background:'#061120',
            display:'flex', alignItems:'center', justifyContent:'space-between',
          }}>
            <span style={{fontSize:11,fontWeight:700,color:'#475569',textTransform:'uppercase',letterSpacing:'0.1em'}}>
              System Status
            </span>
            <div style={{display:'flex',alignItems:'center',gap:6}}>
              <div style={{
                width:6,height:6,borderRadius:'50%',
                background:live?'#10b981':'#f59e0b',
                boxShadow:live?'0 0 6px #10b981':'none',
              }}/>
              <span style={{fontSize:11,fontWeight:600,color:live?'#10b981':'#f59e0b'}}>
                {live ? 'Live' : 'Idle'}
              </span>
            </div>
          </div>

          {/* services */}
          <div style={{padding:'16px 22px',display:'flex',flexDirection:'column',gap:8}}>
            {[
              { name:'Redpanda',    sub:'Kafka-API event bus · port 9092',       up:stats?.redpanda_up,  accent:'#3b82f6' },
              { name:'TimescaleDB', sub:'Hypertable · time-partitioned storage',  up:stats?.postgres_up,  accent:'#8b5cf6' },
              { name:'Redis',       sub:'SETNX dedup + feature cache · 15m TTL', up:stats?.redis_up,     accent:'#f59e0b' },
            ].map((s,i) => (
              <div key={i} style={{
                display:'flex', alignItems:'center', gap:12,
                background:'#020817', borderRadius:8,
                padding:'10px 14px',
                border:'1px solid',
                borderColor: s.up ? `${s.accent}22` : '#1e293b',
                transition:'border-color .4s',
              }}>
                <div style={{
                  width:8, height:8, borderRadius:'50%', flexShrink:0,
                  background: s.up ? s.accent : '#1e293b',
                  boxShadow: s.up ? `0 0 7px ${s.accent}` : 'none',
                  transition:'all .4s',
                }}/>
                <div style={{flex:1,minWidth:0}}>
                  <div style={{fontSize:13,fontWeight:600,color:s.up?'#e2e8f0':'#475569'}}>{s.name}</div>
                  <div style={{fontSize:10,color:'#334155',marginTop:1}}>{s.sub}</div>
                </div>
                <span style={{
                  fontSize:10, fontWeight:700, textTransform:'uppercase',
                  borderRadius:100, padding:'2px 9px', flexShrink:0,
                  color: s.up?s.accent:'#334155',
                  background: s.up?`${s.accent}18`:'#0f172a',
                }}>
                  {s.up == null ? '...' : s.up ? 'UP' : 'DOWN'}
                </span>
              </div>
            ))}
          </div>

          {/* metrics grid */}
          <div style={{
            display:'grid', gridTemplateColumns:'1fr 1fr',
            gap:1, background:'#0f172a',
            borderTop:'1px solid #0f172a',
          }}>
            {[
              { l:'Queue depth',     v:stats ? String(stats.queue_depth??0)  : '--', c:'#f59e0b' },
              { l:'Dedup backend',   v:stats?.dedup_backend || '--',                c:'#10b981' },
              { l:'Cache hit rate',  v:stats ? (((stats.cache_hit_rate||0)*100).toFixed(0)+'%') : '--', c:'#a78bfa' },
              { l:'Stress flags',    v:stats ? String(stats.stress_flag_count??0) : '--',         c:'#f43f5e' },
            ].map((s,i) => (
              <div key={i} style={{
                background:'#040d1a', padding:'14px 18px',
              }}>
                <div style={{
                  fontSize:20, fontWeight:800, color:s.c,
                  fontVariantNumeric:'tabular-nums', letterSpacing:'-0.02em',
                  marginBottom:4,
                }}>{s.v}</div>
                <div style={{fontSize:9,color:'#334155',textTransform:'uppercase',letterSpacing:'0.08em'}}>{s.l}</div>
              </div>
            ))}
          </div>

          {/* CTA */}
          <div style={{padding:'16px 22px', background:'#061120', borderTop:'1px solid #1e293b'}}>
            <button onClick={onScrollToDemo} style={{
              width:'100%', background:'#0d9488',
              color:'#fff', border:'none', borderRadius:8,
              padding:'12px', fontSize:13, fontWeight:700,
              cursor:'pointer', letterSpacing:'-0.01em',
              transition:'background .15s',
            }}
            onMouseEnter={e=>e.currentTarget.style.background='#0f766e'}
            onMouseLeave={e=>e.currentTarget.style.background='#0d9488'}>
              Open Console →
            </button>
          </div>
        </div>

      </div>
    </section>
  );
}
function ProblemSection() {
  return (
    <section id="who-we-are" style={{padding:'100px 24px',background:'#020617'}}>
      <div style={{maxWidth:1100,margin:'0 auto'}}>
        <SectionLabel>The Problem</SectionLabel>
        <h2 style={{fontSize:'clamp(28px,4vw,48px)',fontWeight:800,color:'#f1f5f9',marginBottom:20,lineHeight:1.2}}>
          India's Credit Gap Is<br/><span style={{color:'#f43f5e'}}>₹25 Lakh Crore</span>
        </h2>
        <p style={{fontSize:17,color:'#94a3b8',maxWidth:700,lineHeight:1.7,marginBottom:60}}>
          63 million micro and small businesses have no credit history, no collateral, and no CIBIL score. Traditional lenders reject them outright. They are forced into predatory informal lending at 36–60% APR. We fix that.
        </p>

        <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(280px,1fr))',gap:24}}>
          {[
            {icon:'🏦',title:'Traditional Banks Fail MSMEs',body:'Require 3 years of ITR, collateral, and a CIBIL score above 750. 80% of MSMEs qualify for none of these.', tag:'Legacy Problem'},
            {icon:'📱',title:'Digital Transactions Go Unused',body:'MSMEs process millions of UPI and GST transactions daily — rich behavioral signals that traditional scorecards completely ignore.', tag:'Our Insight'},
            {icon:'⚡',title:'Manual Underwriting is Slow',body:'NBFC underwriters manually review files for 3–5 days per applicant. The process doesn\'t scale. We score 1,000 businesses in 120ms.', tag:'Our Solution'},
          ].map((c,i) => (
            <div key={i} style={{background:'#0f172a',border:'1px solid #1e293b',borderRadius:16,padding:28,transition:'border-color 0.2s,transform 0.2s'}}
                 onMouseEnter={e=>{e.currentTarget.style.borderColor='#2dd4bf';e.currentTarget.style.transform='translateY(-4px)'}}
                 onMouseLeave={e=>{e.currentTarget.style.borderColor='#1e293b';e.currentTarget.style.transform='translateY(0)'}}>
              <div style={{fontSize:32,marginBottom:12}}>{c.icon}</div>
              <div style={{display:'inline-block',fontSize:10,fontWeight:700,color:'#2dd4bf',background:'rgba(45,212,191,0.1)',borderRadius:100,padding:'3px 10px',marginBottom:12,textTransform:'uppercase',letterSpacing:'0.1em'}}>{c.tag}</div>
              <h3 style={{fontSize:16,fontWeight:700,color:'#e2e8f0',marginBottom:8}}>{c.title}</h3>
              <p style={{fontSize:14,color:'#64748b',lineHeight:1.6}}>{c.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function DifferentiatorSection() {
  return (
    <section id="differentiator" style={{padding:'100px 24px',background:'#040d1f'}}>
      <div style={{maxWidth:1100,margin:'0 auto'}}>
        <SectionLabel>Our Edge</SectionLabel>
        <h2 style={{fontSize:'clamp(28px,4vw,48px)',fontWeight:800,color:'#f1f5f9',marginBottom:16,lineHeight:1.2}}>
          Alternative Data Beats<br/><span style={{background:'linear-gradient(90deg,#2dd4bf,#3b82f6)',WebkitBackgroundClip:'text',WebkitTextFillColor:'transparent'}}>Traditional Scorecards</span>
        </h2>
        <p style={{fontSize:17,color:'#94a3b8',maxWidth:600,lineHeight:1.7,marginBottom:60}}>
          We score creditworthiness from live behavioral data — not from historical debt records that most MSMEs simply don't have.
        </p>

        <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:3,borderRadius:16,overflow:'hidden',maxWidth:900}}>
          {/* Header */}
          <div style={{background:'#0f172a',padding:'16px 24px',fontWeight:700,color:'#64748b',fontSize:12,textTransform:'uppercase',letterSpacing:'0.1em'}}>Signal</div>
          <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',background:'#0f172a',padding:'16px 24px',gap:8}}>
            <div style={{fontWeight:700,color:'#64748b',fontSize:12,textTransform:'uppercase',letterSpacing:'0.1em'}}>CIBIL / Banks</div>
            <div style={{fontWeight:700,color:'#2dd4bf',fontSize:12,textTransform:'uppercase',letterSpacing:'0.1em'}}>CashFlowScore</div>
          </div>

          {[
            {signal:'UPI Cash Flow Volume', bank:'❌ Not tracked', us:'✅ Primary signal'},
            {signal:'GST Filing Regularity', bank:'❌ Ignored', us:'✅ Compliance score'},
            {signal:'Cheque Bounce History', bank:'⚠️ Partial', us:'✅ Real-time stream'},
            {signal:'Credit History (CIBIL)', bank:'✅ Required', us:'⚠️ Optional context'},
            {signal:'Collateral Requirement', bank:'✅ Mandatory', us:'❌ Not needed'},
            {signal:'Scoring Time', bank:'3–5 days', us:'<120ms'},
          ].map((row,i) => (
            <React.Fragment key={`diff-row-${i}`}>
              <div style={{background: i%2===0?'#0c1525':'#0f1b30',padding:'14px 24px',color:'#cbd5e1',fontSize:14,borderTop:'1px solid #1e293b'}}>{row.signal}</div>
              <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',background: i%2===0?'#0c1525':'#0f1b30',padding:'14px 24px',gap:8,borderTop:'1px solid #1e293b'}}>
                <div style={{fontSize:13,color:'#94a3b8'}}>{row.bank}</div>
                <div style={{fontSize:13,color:'#5eead4',fontWeight:600}}>{row.us}</div>
              </div>
            </React.Fragment>
          ))}
        </div>
      </div>
    </section>
  );
}

function NoveltiesSection() {
  return (
    <section id="novelties" style={{padding:'100px 24px',background:'#020617'}}>
      <div style={{maxWidth:1100,margin:'0 auto'}}>
        <SectionLabel>What Makes Us Novel</SectionLabel>
        <h2 style={{fontSize:'clamp(28px,4vw,48px)',fontWeight:800,color:'#f1f5f9',marginBottom:60,lineHeight:1.2}}>
          Built for Speed, Scale,<br/>and <span style={{color:'#a78bfa'}}>Explainability</span>
        </h2>

        <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(240px,1fr))',gap:20}}>
          {[
            {icon:'🤖',title:'XGBoost ML Engine',body:'Gradient-boosted decision trees trained on 10+ MSME-specific features. Sub-100ms inference on 1,000 applications in a single batch.',color:'#2dd4bf'},
            {icon:'📡',title:'Redpanda Event Streaming',body:'Kafka-compatible distributed log. Every Excel upload becomes a real-time event stream. Zero data loss, fully durable.',color:'#3b82f6'},
            {icon:'🗄️',title:'TimescaleDB Hypertables',body:'Time-series database built for financial event data. Auto-partitioned by time. Query 1M rows in milliseconds.',color:'#8b5cf6'},
            {icon:'⚡',title:'Redis Feature Cache',body:'Feature vectors cached in-memory between requests. Cache-hits serve scores 10× faster than recomputing from scratch.',color:'#f59e0b'},
            {icon:'🔍',title:'SHAP Explainability',body:'Every credit decision comes with top-3 reason codes in plain English. Regulatorily compliant and auditable.',color:'#f43f5e'},
            {icon:'📊',title:'One-Click NBFC Reports',body:'Upload a portfolio Excel, get a fully-scored, downloadable report back in 2 seconds. Production-ready API.',color:'#10b981'},
          ].map((n,i) => (
            <div key={i} style={{background:'#0f172a',border:`1px solid ${n.color}22`,borderRadius:16,padding:24,transition:'all 0.2s'}}
                 onMouseEnter={e=>{e.currentTarget.style.borderColor=n.color+'66';e.currentTarget.style.transform='translateY(-4px)';e.currentTarget.style.background='#111827'}}
                 onMouseLeave={e=>{e.currentTarget.style.borderColor=n.color+'22';e.currentTarget.style.transform='translateY(0)';e.currentTarget.style.background='#0f172a'}}>
              <div style={{fontSize:28,marginBottom:12}}>{n.icon}</div>
              <h3 style={{fontSize:15,fontWeight:700,color:'#e2e8f0',marginBottom:8}}>{n.title}</h3>
              <p style={{fontSize:13,color:'#64748b',lineHeight:1.6}}>{n.body}</p>
              <div style={{marginTop:14,height:2,width:'40%',borderRadius:2,background:`linear-gradient(90deg,${n.color},transparent)`}} />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function HowItWorksSection() {
  const steps = [
    {num:'01',title:'NBFC Uploads Portfolio',body:'Drag-and-drop an Excel CSV with 1,000 MSME applicants. The file is streamed as events into Redpanda.',icon:'📁'},
    {num:'02',title:'Redpanda Event Ingestion',body:'Each row is published as a message to the `loan_applications` Kafka topic. Fully durable, replicated, and auditable.',icon:'📡'},
    {num:'03',title:'TimescaleDB Persistence',body:'Events land in a hypertable, partitioned by time. Data is queryable instantly for analytics and compliance.',icon:'🗄️'},
    {num:'04',title:'ML Engine Scoring',body:'XGBoost inference runs on 11 features per applicant. Vectorized batch inference scores 1,000 businesses in < 120ms.',icon:'🤖'},
    {num:'05',title:'Redis Feature Caching',body:'Score vectors are cached in Redis. The NBFC can re-score an applicant with a slider change — served from cache in microseconds.',icon:'⚡'},
    {num:'06',title:'Report Generation',body:'A fully-scored Excel report is generated and made available for download. Each decision includes 3 plain-English reason codes.',icon:'📊'},
  ];

  return (
    <section id="how-it-works" style={{padding:'100px 24px',background:'#040d1f'}}>
      <div style={{maxWidth:1100,margin:'0 auto'}}>
        <SectionLabel>The Pipeline</SectionLabel>
        <h2 style={{fontSize:'clamp(28px,4vw,48px)',fontWeight:800,color:'#f1f5f9',marginBottom:60,lineHeight:1.2}}>
          From Excel Upload to<br/><span style={{color:'#2dd4bf'}}>Credit Decision in 2s</span>
        </h2>

        <div style={{position:'relative'}}>
          {/* Connecting line */}
          <div style={{position:'absolute',top:40,left:'calc(5% + 28px)',right:'5%',height:2,background:'linear-gradient(90deg,#2dd4bf22,#3b82f622,#8b5cf622)',zIndex:0,display:'none'}} />

          <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(300px,1fr))',gap:20}}>
            {steps.map((s,i) => (
              <div key={i} style={{background:'#0c1525',border:'1px solid #1e293b',borderRadius:16,padding:24,position:'relative',transition:'all 0.2s'}}
                   onMouseEnter={e=>{e.currentTarget.style.borderColor='#2dd4bf44';e.currentTarget.style.transform='translateY(-4px)'}}
                   onMouseLeave={e=>{e.currentTarget.style.borderColor='#1e293b';e.currentTarget.style.transform='translateY(0)'}}>
                <div style={{display:'flex',alignItems:'center',gap:12,marginBottom:14}}>
                  <div style={{fontSize:22}}>{s.icon}</div>
                  <div style={{fontSize:11,fontWeight:800,color:'#2dd4bf',fontFamily:'monospace'}}>{s.num}</div>
                </div>
                <h3 style={{fontSize:16,fontWeight:700,color:'#e2e8f0',marginBottom:8}}>{s.title}</h3>
                <p style={{fontSize:13,color:'#64748b',lineHeight:1.6}}>{s.body}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

/* ─── Data Cleaning Section ──────────────────────────────────────────────── */

function DataCleaningSection() {
  const [rawData,     setRawData]     = React.useState(null);
  const [cleanedData, setCleanedData] = React.useState(null);
  const [loading,     setLoading]     = React.useState(false);
  const [phase,       setPhase]       = React.useState('idle'); // idle | raw | cleaning | done

  const loadRaw = async () => {
    setPhase('raw'); setCleanedData(null);
    try {
      const r = await axios.get(`${API_BASE}/data-cleaning/raw`);
      setRawData(r.data);
    } catch { setPhase('idle'); }
  };

  const runClean = async () => {
    setPhase('cleaning'); setLoading(true);
    try {
      const r = await axios.post(`${API_BASE}/data-cleaning/clean`, {});
      setCleanedData(r.data);
      setPhase('done');
    } catch { setPhase('raw'); }
    finally { setLoading(false); }
  };

  const reset = () => { setRawData(null); setCleanedData(null); setPhase('idle'); };

  const displayRows = phase === 'done' ? cleanedData?.cleaned_rows : rawData?.rows;
  const cols = ['txn_id','business','type','amount','timestamp'];

  const cellColor = (col, val, row) => {
    if (val === null || val === '' || val === undefined) return '#f43f5e';
    if (phase === 'done' && row?.fixes?.length > 0) {
      const fixedCols = {
        business: row.fixes.some(f => f.includes('business')),
        type:     row.fixes.some(f => f.includes('type')),
        amount:   row.fixes.some(f => f.includes('amount')),
        timestamp:row.fixes.some(f => f.includes('timestamp')),
      };
      if (fixedCols[col]) return '#f59e0b';
    }
    return '#e2e8f0';
  };

  const fmtCell = (col, val) => {
    if (val === null || val === '' || val === undefined) return 'Missing';
    if (col === 'amount' && phase === 'done') {
      const n = parseFloat(val);
      return isNaN(n) ? String(val) : `₹${n.toLocaleString('en-IN', {maximumFractionDigits:0})}`;
    }
    return String(val);
  };

  return (
    <section id="data-cleaning" style={{padding:'80px 24px',background:'#020617'}}>
      <div style={{maxWidth:1100,margin:'0 auto'}}>
        <SectionLabel>Data Cleaning Pipeline</SectionLabel>
        <h2 style={{fontSize:'clamp(24px,3.5vw,42px)',fontWeight:800,color:'#f1f5f9',
          marginBottom:12,lineHeight:1.2}}>
          Raw transaction data arrives <span style={{color:'#f43f5e'}}>dirty.</span><br/>
          We clean it before it enters the pipeline.
        </h2>
        <p style={{fontSize:16,color:'#64748b',maxWidth:640,lineHeight:1.75,marginBottom:36}}>
          Missing amounts, null business names, unparseable timestamps — real MSME data has all of these.
          The cleaning layer strips symbols, fills missing values with statistical medians, then publishes
          the clean rows as real events into the pipeline.
        </p>

        {/* Controls */}
        <div style={{display:'flex',gap:10,marginBottom:28,flexWrap:'wrap',alignItems:'center'}}>
          <button onClick={loadRaw} disabled={phase==='raw'||phase==='cleaning'} style={{
            background: phase==='raw'?'#1e293b':'#0d9488',color:'#fff',border:'none',
            borderRadius:8,padding:'10px 22px',fontSize:13,fontWeight:700,cursor:'pointer',
            opacity: phase==='cleaning'?0.5:1}}>
            {phase==='raw'||phase==='done' ? '↺ Reload Raw Data' : '① Load Raw Dirty Data'}
          </button>
          {(phase==='raw'||phase==='done') && (
            <button onClick={runClean} disabled={loading} style={{
              background:'linear-gradient(135deg,#7c3aed,#4f46e5)',color:'#fff',border:'none',
              borderRadius:8,padding:'10px 22px',fontSize:13,fontWeight:700,cursor:'pointer',
              opacity:loading?0.6:1}}>
              {loading ? '⟳ Cleaning...' : '② Run Cleaning Pipeline'}
            </button>
          )}
          {phase==='done' && (
            <button onClick={reset} style={{
              background:'transparent',color:'#64748b',border:'1px solid #1e293b',
              borderRadius:8,padding:'10px 18px',fontSize:13,fontWeight:600,cursor:'pointer'}}>
              Reset
            </button>
          )}
          {phase==='done' && cleanedData && (
            <span style={{fontSize:12,color:'#10b981',background:'rgba(16,185,129,0.1)',
              border:'1px solid rgba(16,185,129,0.2)',borderRadius:100,padding:'6px 14px',fontWeight:600}}>
              ✓ {cleanedData.total_fixes} fixes applied · {cleanedData.events_published} events published to pipeline
            </span>
          )}
        </div>

        {/* Legend */}
        {displayRows && (
          <div style={{display:'flex',gap:16,marginBottom:14,flexWrap:'wrap'}}>
            <div style={{display:'flex',alignItems:'center',gap:6,fontSize:11,color:'#94a3b8'}}>
              <div style={{width:10,height:10,borderRadius:2,background:'#f43f5e'}}/>Missing value
            </div>
            {phase==='done' && (
              <div style={{display:'flex',alignItems:'center',gap:6,fontSize:11,color:'#94a3b8'}}>
                <div style={{width:10,height:10,borderRadius:2,background:'#f59e0b'}}/>Filled by cleaning
              </div>
            )}
            <div style={{display:'flex',alignItems:'center',gap:6,fontSize:11,color:'#94a3b8'}}>
              <div style={{width:10,height:10,borderRadius:2,background:'#e2e8f0'}}/>Valid value
            </div>
          </div>
        )}

        {/* Table */}
        {displayRows ? (
          <div style={{background:'#061120',border:'1px solid #1e293b',borderRadius:14,overflow:'hidden'}}>
            {/* Phase header */}
            <div style={{padding:'12px 20px',borderBottom:'1px solid #1e293b',
              display:'flex',alignItems:'center',justifyContent:'space-between',
              background: phase==='done' ? 'rgba(16,185,129,0.06)' : 'rgba(244,63,94,0.05)'}}>
              <span style={{fontSize:12,fontWeight:700,
                color: phase==='done' ? '#10b981' : '#f43f5e'}}>
                {phase==='done' ? `✓ Cleaned — ${cleanedData?.total_rows} rows` : `⚠ Raw dirty data — ${rawData?.missing_count} missing values`}
              </span>
              <span style={{fontSize:11,color:'#475569'}}>
                {phase==='done' ? `Median fill: ₹${(cleanedData?.median_amount_used||0).toLocaleString('en-IN',{maximumFractionDigits:0})}` : `${rawData?.total_rows} rows loaded`}
              </span>
            </div>

            <div style={{overflowX:'auto'}}>
              <table style={{width:'100%',borderCollapse:'collapse',fontSize:13}}>
                <thead>
                  <tr style={{background:'#040d1a'}}>
                    {cols.map(c => (
                      <th key={c} style={{padding:'10px 16px',textAlign:'left',
                        fontSize:10,fontWeight:700,color:'#475569',
                        textTransform:'uppercase',letterSpacing:'0.08em',
                        borderBottom:'1px solid #1e293b'}}>{c}</th>
                    ))}
                    {phase==='done' && (
                      <th style={{padding:'10px 16px',fontSize:10,fontWeight:700,
                        color:'#475569',textTransform:'uppercase',letterSpacing:'0.08em',
                        borderBottom:'1px solid #1e293b'}}>Fixes</th>
                    )}
                  </tr>
                </thead>
                <tbody>
                  {displayRows.map((row, ri) => (
                    <tr key={ri} style={{borderBottom:'1px solid #0f172a',
                      transition:'background .1s'}}
                      onMouseEnter={e=>e.currentTarget.style.background='rgba(255,255,255,0.02)'}
                      onMouseLeave={e=>e.currentTarget.style.background='transparent'}>
                      {cols.map(col => {
                        const val = row[col];
                        const color = cellColor(col, val, row);
                        const isMissing = val === null || val === '' || val === undefined;
                        return (
                          <td key={col} style={{padding:'10px 16px'}}>
                            <span style={{
                              color,
                              fontWeight: isMissing || color==='#f59e0b' ? 600 : 400,
                              fontStyle: isMissing ? 'italic' : 'normal',
                              fontSize: 12,
                              background: isMissing ? 'rgba(244,63,94,0.08)' : color==='#f59e0b' ? 'rgba(245,158,11,0.08)' : 'transparent',
                              borderRadius: 4,
                              padding: isMissing || color==='#f59e0b' ? '1px 6px' : 0,
                            }}>
                              {fmtCell(col, val)}
                            </span>
                          </td>
                        );
                      })}
                      {phase==='done' && (
                        <td style={{padding:'10px 16px',fontSize:11,color:'#64748b'}}>
                          {row.fixes?.length > 0
                            ? row.fixes.map((f,fi) => (
                                <span key={fi} style={{display:'inline-block',
                                  background:'rgba(245,158,11,0.1)',color:'#f59e0b',
                                  borderRadius:100,padding:'1px 8px',fontSize:10,
                                  marginRight:4,marginBottom:2,fontWeight:600}}>
                                  {f}
                                </span>
                              ))
                            : <span style={{color:'#334155'}}>—</span>
                          }
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div style={{background:'#061120',border:'1px dashed #1e293b',borderRadius:14,
            padding:'48px 24px',textAlign:'center'}}>
            <div style={{fontSize:32,marginBottom:12}}>🧹</div>
            <div style={{fontSize:15,fontWeight:600,color:'#475569',marginBottom:6}}>
              Click "Load Raw Dirty Data" to begin
            </div>
            <div style={{fontSize:13,color:'#334155'}}>
              Shows missing values, then cleans and publishes to the live pipeline
            </div>
          </div>
        )}

        {/* Missing value heatmap */}
        {rawData && phase !== 'done' && (
          <div style={{marginTop:20,background:'#061120',border:'1px solid #1e293b',
            borderRadius:12,padding:20}}>
            <div style={{fontSize:11,fontWeight:700,color:'#94a3b8',textTransform:'uppercase',
              letterSpacing:'0.1em',marginBottom:14}}>Missing Value Heatmap</div>
            <div style={{display:'flex',gap:6,alignItems:'flex-start',flexWrap:'wrap'}}>
              {rawData.rows.map((row, ri) => (
                <div key={ri} style={{display:'flex',flexDirection:'column',gap:3,alignItems:'center'}}>
                  <div style={{fontSize:9,color:'#334155',marginBottom:2,
                    writingMode:'vertical-lr',transform:'rotate(180deg)',
                    maxHeight:60,overflow:'hidden'}}>{row.txn_id}</div>
                  {cols.map(col => {
                    const v = row[col];
                    const missing = v === null || v === '' || v === undefined;
                    return (
                      <div key={col} title={`${col}: ${missing?'Missing':v}`}
                        style={{width:20,height:20,borderRadius:3,
                          background: missing ? '#f43f5e' : '#10b981',
                          opacity: missing ? 1 : 0.6,
                          cursor:'default',transition:'opacity .15s'}}
                        onMouseEnter={e=>e.currentTarget.style.opacity='1'}
                        onMouseLeave={e=>e.currentTarget.style.opacity= missing?'1':'0.6'}
                      />
                    );
                  })}
                </div>
              ))}
              <div style={{marginLeft:16,display:'flex',flexDirection:'column',gap:8,justifyContent:'flex-end'}}>
                {cols.map(c => (
                  <div key={c} style={{fontSize:9,color:'#475569',height:20,
                    display:'flex',alignItems:'center'}}>{c}</div>
                ))}
              </div>
            </div>
          </div>
        )}

      </div>
    </section>
  );
}

/* ─── Section Label ───────────────────────────────────────────────────────── */

function SectionLabel({ children }) {
  return (
    <div style={{display:'inline-flex',alignItems:'center',gap:8,background:'rgba(45,212,191,0.08)',border:'1px solid rgba(45,212,191,0.2)',borderRadius:100,padding:'5px 14px',marginBottom:20}}>
      <span style={{fontSize:11,color:'#5eead4',fontWeight:700,textTransform:'uppercase',letterSpacing:'0.12em'}}>{children}</span>
    </div>
  );
}

/* ─── Terminal Window Component ─────────────────────────────────────────── */

function TerminalWindow({ title, command, output, loading, onClose }) {
  const endRef = useRef(null);
  useEffect(() => { if(endRef.current) endRef.current.scrollIntoView({behavior:'smooth'}); }, [output]);

  return (
    <div style={{
      position:'fixed',inset:0,zIndex:999,background:'rgba(2,6,23,0.85)',
      display:'flex',alignItems:'center',justifyContent:'center',padding:24,
      backdropFilter:'blur(4px)'
    }}>
      <div style={{background:'#0c1117',border:'1px solid #1e3a2f',borderRadius:16,width:'100%',maxWidth:700,boxShadow:'0 24px 80px rgba(0,0,0,0.6)'}}>
        {/* Window chrome */}
        <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',padding:'12px 16px',borderBottom:'1px solid #1e293b'}}>
          <div style={{display:'flex',alignItems:'center',gap:8}}>
            <div style={{width:12,height:12,borderRadius:'50%',background:'#f43f5e'}} />
            <div style={{width:12,height:12,borderRadius:'50%',background:'#f59e0b'}} />
            <div style={{width:12,height:12,borderRadius:'50%',background:'#10b981'}} />
            <span style={{fontSize:12,color:'#64748b',marginLeft:8,fontFamily:'monospace'}}>bash — {title}</span>
          </div>
          <button onClick={onClose} style={{background:'none',border:'none',color:'#64748b',cursor:'pointer',fontSize:16,padding:'0 4px'}}>✕</button>
        </div>
        {/* Command input line */}
        <div style={{padding:'12px 16px',borderBottom:'1px solid #0f1f18',background:'#080e0b'}}>
          <span style={{color:'#10b981',fontFamily:'monospace',fontSize:12}}>cashflowscore@docker</span>
          <span style={{color:'#64748b',fontFamily:'monospace',fontSize:12}}> ~ $ </span>
          <span style={{color:'#e2e8f0',fontFamily:'monospace',fontSize:12}}>{command}</span>
          {loading && <span style={{animation:'blink 1s infinite',color:'#2dd4bf',fontFamily:'monospace',fontSize:12}}>▌</span>}
        </div>
        {/* Output */}
        <div style={{padding:16,minHeight:160,maxHeight:380,overflowY:'auto',fontFamily:'monospace',fontSize:12,lineHeight:1.8}}>
          {loading ? (
            <div style={{color:'#5eead4'}}>
              <span style={{color:'#64748b'}}>Connecting to Docker container... </span>
              <span style={{animation:'pulse 1s infinite'}}>●</span>
            </div>
          ) : (
            <pre style={{margin:0,whiteSpace:'pre-wrap',wordBreak:'break-word',color:'#a3e635'}}>
              {output || 'No output.'}
            </pre>
          )}
          <div ref={endRef} />
        </div>
        <div style={{padding:'12px 16px',borderTop:'1px solid #1e293b',display:'flex',justifyContent:'flex-end'}}>
          <button onClick={onClose} style={{background:'#0d9488',color:'#fff',border:'none',borderRadius:8,padding:'8px 20px',fontSize:13,fontWeight:600,cursor:'pointer'}}>Close</button>
        </div>
      </div>
    </div>
  );
}

/* ─── System Proof / Terminal Buttons Section ────────────────────────────── */

function ProofSection() {
  const [terminal, setTerminal] = useState(null); // null | {title, command, output, loading}

  const runDiagnostic = async (service, title, command) => {
    setTerminal({ title, command, output: '', loading: true });
    try {
      const r = await axios.post(`${API_BASE}/diagnostics`,
        { service },
        { headers: authHeaders }
      );
      setTerminal({ title, command, output: r.data.output, loading: false });
    } catch (err) {
      setTerminal({ title, command, output: `Error: ${err.message}\n\nMake sure Docker containers are running.`, loading: false });
    }
  };

  const proofs = [
    {
      icon:'📡', service:'redpanda', color:'#3b82f6',
      title:'Ping Redpanda Cluster',
      desc:'Run rpk cluster info inside the Docker container to verify Redpanda is live and healthy.',
      command:'docker exec redpanda rpk cluster info',
      badge:'Kafka-Compatible Streaming',
    },
    {
      icon:'🗄️', service:'postgres', color:'#8b5cf6',
      title:'Count Database Rows',
      desc:'Run a live SQL query inside TimescaleDB to count how many business events are stored on disk.',
      command:'psql -c "SELECT count(*) FROM business_events;"',
      badge:'TimescaleDB Persistence',
    },
    {
      icon:'⚡', service:'redis', color:'#f59e0b',
      title:'Inspect Redis Cache',
      desc:'Connect to the Redis container and inspect the keyspace to prove features are cached in memory.',
      command:'redis-cli info keyspace',
      badge:'In-Memory Feature Store',
    },
  ];

  return (
    <section id="proof" style={{padding:'100px 24px',background:'#020617'}}>
      {terminal && (
        <TerminalWindow
          {...terminal}
          onClose={() => setTerminal(null)}
        />
      )}
      <div style={{maxWidth:1100,margin:'0 auto'}}>
        <SectionLabel>Live System Proof</SectionLabel>
        <h2 style={{fontSize:'clamp(28px,4vw,48px)',fontWeight:800,color:'#f1f5f9',marginBottom:16,lineHeight:1.2}}>
          Not a Mock. Click to<br/><span style={{color:'#2dd4bf'}}>Prove the Infrastructure</span>
        </h2>
        <p style={{fontSize:17,color:'#94a3b8',maxWidth:600,lineHeight:1.7,marginBottom:50}}>
          Every component runs in a real Docker container on this machine. These buttons execute live terminal commands and return the actual output — no simulation.
        </p>

        <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(300px,1fr))',gap:20}}>
          {proofs.map((p,i) => (
            <div key={i} style={{background:'#0f172a',border:`1px solid ${p.color}22`,borderRadius:16,padding:28,display:'flex',flexDirection:'column',gap:16}}>
              <div style={{display:'flex',alignItems:'flex-start',justifyContent:'space-between'}}>
                <div style={{fontSize:32}}>{p.icon}</div>
                <div style={{fontSize:10,fontWeight:700,color:p.color,background:`${p.color}18`,borderRadius:100,padding:'3px 10px',textTransform:'uppercase',letterSpacing:'0.1em'}}>{p.badge}</div>
              </div>
              <div>
                <h3 style={{fontSize:16,fontWeight:700,color:'#e2e8f0',marginBottom:8}}>{p.title}</h3>
                <p style={{fontSize:13,color:'#64748b',lineHeight:1.6}}>{p.desc}</p>
              </div>
              {/* Command preview */}
              <div style={{background:'#080e1a',border:'1px solid #1e293b',borderRadius:8,padding:'8px 12px',fontFamily:'monospace',fontSize:11,color:'#64748b'}}>
                <span style={{color:'#10b981'}}>$ </span>{p.command}
              </div>
              <button onClick={() => runDiagnostic(p.service, p.title, p.command)}
                style={{
                  background:`linear-gradient(135deg,${p.color}dd,${p.color}aa)`,
                  color:'#fff',border:'none',borderRadius:10,padding:'12px 20px',
                  fontSize:14,fontWeight:700,cursor:'pointer',
                  transition:'all 0.2s',boxShadow:`0 4px 20px ${p.color}33`
                }}
                onMouseEnter={e=>{e.currentTarget.style.transform='translateY(-2px)';e.currentTarget.style.boxShadow=`0 8px 30px ${p.color}55`}}
                onMouseLeave={e=>{e.currentTarget.style.transform='translateY(0)';e.currentTarget.style.boxShadow=`0 4px 20px ${p.color}33`}}>
                ▶ Execute in Terminal
              </button>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ─── Dashboard / Demo Section ──────────────────────────────────────────── */

function DashboardSection({ portfolio, uploadSummary, uploadLoading, uploadProgress,
  downloadUrl, downloadFilename, dragOver, fileInputRef,
  handleFileInput, handleDrop, handleDragOver, handleDragLeave,
  selectedRow, formVals, scoreState, scorePending,
  handleSelect, handleScoreChange, eventLog, status, pipeline,
  liveActivity, pipelineStats, queueDepth
}) {
  const [tab, setTab] = useState('upload');
  const totalApproved = portfolio.filter(r=>r.status==='approved').length;
  const totalRejected = portfolio.filter(r=>r.status==='rejected').length;
  const totalCredit   = portfolio.reduce((s,r)=>s+(r.credit_unlocked||0),0);
  const hasResults    = portfolio.length > 0;

  return (
    <section id="demo" style={{padding:'100px 24px',background:'#040d1f'}}>
      <div style={{maxWidth:1400,margin:'0 auto'}}>
        {/* Live Kafka Ticker */}
        {liveActivity.length > 0 && (
          <div style={{background:'#020617',border:'1px solid rgba(20,184,166,0.2)',borderRadius:10,padding:'8px 16px',marginBottom:24,display:'flex',alignItems:'center',gap:12,overflow:'hidden'}}>
            <div style={{flexShrink:0,fontSize:10,fontWeight:700,color:'#0d9488',textTransform:'uppercase',letterSpacing:'0.1em',display:'flex',alignItems:'center',gap:6}}>
              <div style={{width:5,height:5,borderRadius:'50%',background:'#10b981',boxShadow:'0 0 4px #10b981'}} />
              Kafka Live
            </div>
            <div style={{flex:1,overflow:'hidden',position:'relative'}}>
              <div style={{display:'flex',gap:40,fontSize:11,fontFamily:'monospace',color:'#475569',whiteSpace:'nowrap',overflow:'hidden'}}>
                {liveActivity.slice(0,6).map((ev,i) => (
                  <span key={i} style={{color: (ev.category||ev.event_type)==='stress_flagged'?'#f43f5e': (ev.category||ev.event_type)==='event_ingested'?'#10b981':'#5eead4'}}>
                    {(ev.category||ev.event_type)==='stress_flagged'?'⚠️':(ev.category||ev.event_type)==='cache_hit'?'⚡':'▶'} {(ev.business_id||'').slice(0,10)} — {(ev.message||ev.description||'').slice(0,40)}
                  </span>
                ))}
              </div>
            </div>
            <div style={{flexShrink:0,fontSize:10,color:'#334155'}}>{pipelineStats?.events_processed||0} events processed</div>
          </div>
        )}
        <SectionLabel>Interactive Control Portal</SectionLabel>
        <h2 style={{fontSize:'clamp(28px,4vw,48px)',fontWeight:800,color:'#f1f5f9',marginBottom:8,lineHeight:1.2}}>
          Score a Portfolio Right Now
        </h2>
        <p style={{fontSize:17,color:'#94a3b8',maxWidth:600,lineHeight:1.7,marginBottom:40}}>
          Upload the sample CSV file and watch the XGBoost engine score all 1,000 businesses in real-time. Then adjust sliders to see live re-scoring.
        </p>

        {/* Tab bar */}
        <div style={{display:'flex',gap:4,background:'#0c1525',border:'1px solid #1e293b',borderRadius:12,padding:4,marginBottom:28,width:'fit-content'}}>
          {[['upload','📊 Score Portfolio'],['pipeline','⚡ Live Pipeline']].map(([t,label])=>(
            <button key={t} onClick={()=>setTab(t)} style={{
              background: tab===t ? 'linear-gradient(135deg,#0d9488,#0891b2)' : 'transparent',
              color: tab===t ? '#fff' : '#64748b',
              border:'none',borderRadius:8,padding:'10px 20px',fontSize:14,fontWeight:600,
              cursor:'pointer',transition:'all 0.2s'
            }}>{label}</button>
          ))}
        </div>

        {/* Upload Tab */}
        {tab === 'upload' && (
          <div>
            {/* Upload Zone */}
            <div
              onClick={()=>fileInputRef.current?.click()}
              onDrop={handleDrop} onDragOver={handleDragOver} onDragLeave={handleDragLeave}
              style={{
                border: `2px dashed ${dragOver ? '#2dd4bf' : '#1e293b'}`,
                borderRadius:16, padding:'40px 24px', textAlign:'center', cursor:'pointer',
                background: dragOver ? 'rgba(45,212,191,0.05)' : '#0c1525',
                transition:'all 0.2s', marginBottom:24,
              }}>
              <div style={{fontSize:40,marginBottom:12}}>📁</div>
              <div style={{fontSize:16,fontWeight:600,color:'#e2e8f0',marginBottom:6}}>
                {uploadLoading ? 'Processing...' : 'Drop your Portfolio Excel/CSV here'}
              </div>
              <div style={{fontSize:13,color:'#64748b'}}>or click to browse · Supports .xlsx and .csv</div>
              <input ref={fileInputRef} type="file" accept=".csv,.xlsx" style={{display:'none'}} onChange={handleFileInput} />

              {uploadLoading && (
                <div style={{marginTop:20}}>
                  <div style={{background:'#0f172a',borderRadius:100,height:6,overflow:'hidden',maxWidth:400,margin:'0 auto 8px'}}>
                    <div style={{height:'100%',width:`${uploadProgress}%`,background:'linear-gradient(90deg,#0d9488,#3b82f6)',borderRadius:100,transition:'width 0.3s'}} />
                  </div>
                  <div style={{fontSize:12,color:'#64748b'}}>{uploadProgress}% — XGBoost inference running...</div>
                </div>
              )}
            </div>

            {/* Download Report Banner — always visible when ready */}
            {downloadUrl && (
              <div style={{
                display:'flex',alignItems:'center',justifyContent:'space-between',flexWrap:'wrap',gap:16,
                background:'linear-gradient(135deg,rgba(16,185,129,0.15),rgba(5,150,105,0.1))',
                border:'1px solid rgba(16,185,129,0.4)',borderRadius:16,padding:'20px 28px',marginBottom:24,
              }}>
                <div style={{display:'flex',alignItems:'center',gap:16}}>
                  <div style={{width:48,height:48,borderRadius:12,background:'rgba(16,185,129,0.2)',display:'flex',alignItems:'center',justifyContent:'center',fontSize:24}}>📊</div>
                  <div>
                    <div style={{fontWeight:700,color:'#10b981',fontSize:16,marginBottom:2}}>Excel Report Ready</div>
                    <div style={{fontSize:13,color:'#94a3b8'}}>{downloadFilename} · Fully scored with Credit Score, Status &amp; Risk Band</div>
                  </div>
                </div>
                <button onClick={() => {
                  const a = document.createElement('a');
                  a.href = downloadUrl;
                  a.download = downloadFilename || 'CashFlowScore_Report.xlsx';
                  document.body.appendChild(a);
                  a.click();
                  document.body.removeChild(a);
                }} style={{
                  background:'linear-gradient(135deg,#10b981,#059669)',color:'#fff',border:'none',
                  borderRadius:10,padding:'12px 28px',fontSize:15,fontWeight:700,cursor:'pointer',
                  boxShadow:'0 6px 20px rgba(16,185,129,0.35)',display:'flex',alignItems:'center',gap:10,
                  transition:'all 0.2s',
                }}
                onMouseEnter={e=>{e.currentTarget.style.boxShadow='0 8px 28px rgba(16,185,129,0.5)';e.currentTarget.style.transform='translateY(-1px)'}}
                onMouseLeave={e=>{e.currentTarget.style.boxShadow='0 6px 20px rgba(16,185,129,0.35)';e.currentTarget.style.transform='translateY(0)'}}>
                  <span style={{fontSize:18}}>📥</span>
                  Download .xlsx Report
                </button>
              </div>
            )}

            {/* Summary Cards */}
            {uploadSummary && hasResults && (
              <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(160px,1fr))',gap:16,marginBottom:24}}>
                {[
                  {label:'Businesses Scored',val:uploadSummary.rows_processed,color:'#2dd4bf',icon:'📊'},
                  {label:'Approved',val:totalApproved,color:'#10b981',icon:'✅'},
                  {label:'Rejected',val:totalRejected,color:'#f43f5e',icon:'❌'},
                  {label:'Credit Unlocked',val:fmtRs(totalCredit),color:'#f59e0b',icon:'💰'},
                  {label:'Avg Score',val:uploadSummary.average_score,color:'#8b5cf6',icon:'📈'},
                ].map((c,i)=>(
                  <div key={i} style={{background:'#0c1525',border:'1px solid #1e293b',borderRadius:12,padding:16}}>
                    <div style={{fontSize:20,marginBottom:4}}>{c.icon}</div>
                    <div style={{fontSize:20,fontWeight:800,color:c.color}}>{c.val}</div>
                    <div style={{fontSize:11,color:'#64748b',textTransform:'uppercase',letterSpacing:'0.08em'}}>{c.label}</div>
                  </div>
                ))}
              </div>
            )}

            {/* Two-column: Table + Detail */}
            {hasResults && (
              <div style={{display:'grid',gridTemplateColumns:'1fr 380px',gap:20,alignItems:'start'}}>
                {/* Portfolio Table */}
                <div style={{background:'#0c1525',border:'1px solid #1e293b',borderRadius:16,overflow:'hidden'}}>
                  <div style={{padding:'14px 20px',borderBottom:'1px solid #1e293b',display:'flex',alignItems:'center',justifyContent:'space-between'}}>
                    <span style={{fontWeight:700,color:'#e2e8f0'}}>Portfolio Results</span>
                    <span style={{fontSize:12,color:'#64748b'}}>{portfolio.length} businesses · click to rescore</span>
                  </div>
                  <div style={{overflowY:'auto',maxHeight:420}}>
                    <table style={{width:'100%',borderCollapse:'collapse'}}>
                      <thead>
                        <tr style={{background:'#080e1a'}}>
                          {['Business','Score','Status','Risk','Credit'].map(h=>(
                            <th key={h} style={{padding:'10px 14px',fontSize:11,color:'#475569',fontWeight:700,textTransform:'uppercase',letterSpacing:'0.08em',textAlign:'left'}}>{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {portfolio.map((row,i)=>(
                          <tr key={row.id} onClick={()=>handleSelect(row)}
                            style={{borderTop:'1px solid #0f172a',cursor:'pointer',background: selectedRow?.id===row.id ? 'rgba(45,212,191,0.06)' : 'transparent',transition:'background 0.15s'}}
                            onMouseEnter={e=>e.currentTarget.style.background='rgba(255,255,255,0.03)'}
                            onMouseLeave={e=>e.currentTarget.style.background=selectedRow?.id===row.id?'rgba(45,212,191,0.06)':'transparent'}>
                            <td style={{padding:'10px 14px',fontSize:13,color:'#cbd5e1',fontWeight:500,maxWidth:120,overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}>{row.name}</td>
                            <td style={{padding:'10px 14px'}}>
                              <span style={{fontWeight:800,fontSize:16,color:scoreColor(row.score)}}>{row.score}</span>
                            </td>
                            <td style={{padding:'10px 14px'}}>
                              <span style={{fontSize:11,fontWeight:700,color:scoreColor(row.score),background:`${scoreColor(row.score)}18`,borderRadius:100,padding:'3px 10px'}}>{scoreLabel(row.score)}</span>
                            </td>
                            <td style={{padding:'10px 14px',fontSize:12,color:'#94a3b8',textTransform:'capitalize'}}>{row.risk_band}</td>
                            <td style={{padding:'10px 14px',fontSize:12,color: row.credit_unlocked>0?'#10b981':'#64748b'}}>{row.credit_unlocked>0?fmtRs(row.credit_unlocked):'—'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Detail Panel */}
                <div style={{background:'#0c1525',border:'1px solid #1e293b',borderRadius:16,padding:20,position:'sticky',top:80}}>
                  {!selectedRow ? (
                    <div style={{textAlign:'center',padding:'40px 0',color:'#475569'}}>
                      <div style={{fontSize:32,marginBottom:8}}>👆</div>
                      <div style={{fontSize:14}}>Click a row to rescore with live ML</div>
                    </div>
                  ) : (
                    <>
                      <div style={{marginBottom:16}}>
                        <div style={{fontSize:11,color:'#64748b',marginBottom:4,textTransform:'uppercase',letterSpacing:'0.08em'}}>{selectedRow.id}</div>
                        <div style={{fontSize:17,fontWeight:700,color:'#e2e8f0',marginBottom:16}}>{selectedRow.name}</div>
                        {/* Score ring */}
                        <div style={{display:'flex',alignItems:'center',gap:16,marginBottom:20}}>
                          <div style={{width:72,height:72,borderRadius:'50%',display:'flex',alignItems:'center',justifyContent:'center',background:`conic-gradient(${scoreColor(scoreState?.score ?? selectedRow.score)} ${(scoreState?.score??selectedRow.score)*3.6}deg, #1e293b 0deg)`,position:'relative'}}>
                            <div style={{position:'absolute',width:56,height:56,borderRadius:'50%',background:'#0c1525',display:'flex',alignItems:'center',justifyContent:'center'}}>
                              <span style={{fontSize:17,fontWeight:800,color:scoreColor(scoreState?.score??selectedRow.score)}}>{scoreState?.score??selectedRow.score}</span>
                            </div>
                          </div>
                          <div>
                            <div style={{fontSize:15,fontWeight:700,color:scoreColor(scoreState?.score??selectedRow.score)}}>{scoreLabel(scoreState?.score??selectedRow.score)}</div>
                            <div style={{fontSize:11,color:'#475569',marginTop:2}}>source: {scoreState?.source || 'batch'}</div>
                          </div>
                        </div>
                      </div>

                      {/* Editable sliders */}
                      {formVals && [
                        {name:'business_age_years',label:'Business Age (Years)',min:0,max:50,step:1},
                        {name:'monthly_upi_volume',label:'Monthly UPI Vol (₹)',min:0,max:1000000,step:10000},
                        {name:'monthly_bank_volume',label:'Monthly Bank Vol (₹)',min:0,max:2000000,step:10000},
                        {name:'monthly_cash_volume',label:'Monthly Cash Vol (₹)',min:0,max:500000,step:10000},
                        {name:'gst_filing_regularity',label:'GST Filing Regularity (%)',min:0,max:100,step:5},
                        {name:'gst_turnover',label:'Annual GST Turnover (₹)',min:0,max:5000000,step:50000},
                        {name:'bounce_frequency',label:'Cheque Bounces (Count)',min:0,max:10,step:1},
                        {name:'avg_monthly_balance',label:'Avg Monthly Bal (₹)',min:0,max:1000000,step:10000},
                        {name:'income_stability',label:'Income Stability (0-1)',min:0,max:1,step:0.1},
                        {name:'seasonality_score',label:'Seasonality Score (0-1)',min:0,max:1,step:0.1},
                        {name:'loan_default_history',label:'Past Defaults (Count)',min:0,max:5,step:1},
                      ].map(f=>(
                        <div key={f.name} style={{marginBottom:10}}>
                          <div style={{display:'flex',justifyContent:'space-between',marginBottom:4}}>
                            <label style={{fontSize:11,color:'#94a3b8'}}>{f.label}</label>
                            <span style={{fontSize:11,fontWeight:700,color:'#e2e8f0'}}>{f.name.includes('volume')||f.name.includes('turnover')||f.name.includes('balance')?fmtRs(formVals[f.name]):formVals[f.name]}</span>
                          </div>
                          <input type="range" name={f.name} min={f.min} max={f.max} step={f.step}
                            value={formVals[f.name]} onChange={handleScoreChange}
                            style={{width:'100%',accentColor:'#0d9488',height:4}} />
                        </div>
                      ))}

                      {scorePending && <div style={{fontSize:12,color:'#5eead4',marginBottom:10}}>⟳ XGBoost re-scoring...</div>}

                      {/* Reasons */}
                      {(scoreState?.top_reasons||selectedRow.reasons||[]).map((r,i)=>(
                        <div key={i} style={{display:'flex',alignItems:'flex-start',gap:8,marginBottom:6}}>
                          <span style={{color:'#2dd4bf',marginTop:2}}>▸</span>
                          <span style={{fontSize:12,color:'#94a3b8',lineHeight:1.5}}>{r}</span>
                        </div>
                      ))}
                    </>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Pipeline Tab */}
        {tab === 'pipeline' && (
          <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:20}}>
            {/* System Health */}
            <div style={{background:'#0c1525',border:'1px solid #1e293b',borderRadius:16,padding:24}}>
              <div style={{fontWeight:700,color:'#e2e8f0',marginBottom:20,fontSize:16}}>⚙️ System Architecture</div>
              <div style={{display:'flex',flexDirection:'column',gap:14}}>
                {[
                  {label:'Redpanda',sub:'Kafka-compatible event stream',color:'#3b82f6',data: pipeline?.redpanda},
                  {label:'TimescaleDB',sub:'Time-series hypertable',color:'#8b5cf6',data: pipeline?.timescaledb},
                  {label:'Redis Cache',sub:'Feature vector store',color:'#f59e0b',data: pipeline?.redis},
                  {label:'XGBoost ML Engine',sub:'Inference API on port 8001',color:'#10b981',data: pipeline?.ml_engine},
                ].map((s,i)=>{
                  const up = s.data?.status === 'up';
                  return (
                    <div key={i} style={{display:'flex',alignItems:'center',gap:14,background:'#080e1a',borderRadius:12,padding:'14px 16px'}}>
                      <div style={{width:10,height:10,borderRadius:'50%',background: up?s.color:'#475569',boxShadow: up?`0 0 8px ${s.color}`:'none',flexShrink:0}} />
                      <div style={{flex:1}}>
                        <div style={{fontSize:14,fontWeight:600,color: up?'#e2e8f0':'#475569'}}>{s.label}</div>
                        <div style={{fontSize:11,color:'#475569'}}>{s.sub}</div>
                      </div>
                      <div style={{fontSize:10,fontWeight:700,textTransform:'uppercase',letterSpacing:'0.08em',padding:'3px 8px',borderRadius:100,
                        background: up?`${s.color}18`:'#1e293b',color: up?s.color:'#475569'}}>
                        {s.data?.status || 'unknown'}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Real pipeline stats grid */}
              {pipelineStats && (
                <div style={{marginTop:20,background:'#080e1a',borderRadius:12,padding:'14px 16px',display:'grid',gridTemplateColumns:'repeat(3,1fr)',gap:12}}>
                  <StatBox label="Events Processed" val={fmt(pipelineStats.events_processed||0)} color="#10b981" />
                  <StatBox label="Businesses Tracked" val={fmt(pipelineStats.business_count||0)} color="#3b82f6" />
                  <StatBox label="Risk Flags" val={fmt(pipelineStats.stress_flag_count||0)} color="#f43f5e" />
                </div>
              )}
              {/* Queue Depth Gauge */}
              <div style={{marginTop:16,background:'#080e1a',borderRadius:12,padding:'14px 16px'}}>
                <div style={{display:'flex',justifyContent:'space-between',marginBottom:8}}>
                  <span style={{fontSize:12,color:'#94a3b8',fontWeight:600}}>⚡ Redpanda Queue Depth</span>
                  <span style={{fontSize:12,fontWeight:800,color: queueDepth>0?'#f59e0b':'#10b981'}}>{queueDepth} events pending</span>
                </div>
                <div style={{height:8,background:'#1e293b',borderRadius:100,overflow:'hidden'}}>
                  <div style={{height:'100%',width:`${Math.min(100,(queueDepth/50)*100)}%`,background: queueDepth>10?'#f59e0b':'#10b981',borderRadius:100,transition:'width 0.6s ease'}} />
                </div>
                <div style={{fontSize:10,color:'#475569',marginTop:4}}>Cache hit rate: {(((pipelineStats?.cache_hit_rate)||0)*100).toFixed(0)}%</div>
              </div>
              {/* DB stats from pipeline */}
              {pipeline?.timescaledb?.event_rows != null && (
                <div style={{marginTop:12,background:'#080e1a',borderRadius:12,padding:'14px 16px',display:'grid',gridTemplateColumns:'1fr 1fr',gap:12}}>
                  <StatBox label="TimescaleDB Rows" val={fmt(pipeline.timescaledb.event_rows)} color="#8b5cf6" />
                  <StatBox label="Redis Keys" val={fmt(pipeline.redis?.total_keys||0)} color="#f59e0b" />
                </div>
              )}
            </div>

            {/* Live Kafka Event Feed */}
            <div style={{background:'#0c1525',border:'1px solid #1e293b',borderRadius:16,padding:24}}>
              <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:16}}>
                <div style={{fontWeight:700,color:'#e2e8f0',fontSize:16}}>📡 Live Kafka Event Stream</div>
                <div style={{display:'flex',alignItems:'center',gap:6,fontSize:11,color:'#10b981'}}>
                  <div style={{width:6,height:6,borderRadius:'50%',background:'#10b981',boxShadow:'0 0 6px #10b981'}} />
                  {liveActivity.length > 0 ? 'LIVE DATA' : 'WAITING'}
                </div>
              </div>

              {liveActivity.length > 0 ? (
                <div style={{background:'#040a12',borderRadius:12,padding:12,height:260,overflowY:'auto',fontFamily:'monospace',fontSize:11}}>
                  {liveActivity.map((ev,i) => {
                    const cat = ev.category || ev.event_type || '';
                    const msg = ev.message || ev.description || cat;
                    const isFlag = cat === 'stress_flagged';
                    const isIngest = cat === 'event_ingested';
                    const isCacheHit = cat === 'cache_hit';
                    const color = isFlag ? '#f43f5e' : isIngest ? '#10b981' : isCacheHit ? '#f59e0b' : '#5eead4';
                    const ts = (ev.created_at||ev.timestamp||'').slice(11,23);
                    return (
                      <div key={i} style={{marginBottom:5,lineHeight:1.5,display:'flex',gap:8,alignItems:'flex-start',borderBottom:'1px solid #0f172a',paddingBottom:4}}>
                        <span style={{color:'#334155',flexShrink:0,fontSize:10}}>[{ts}]</span>
                        <span style={{color:'#475569',flexShrink:0,fontSize:10}}>{(ev.business_id||'SYSTEM').slice(0,14)}</span>
                        <span style={{color,flex:1}}>{msg}</span>
                        {isFlag && <span style={{background:'#f43f5e18',color:'#f43f5e',fontSize:9,fontWeight:700,padding:'1px 6px',borderRadius:100,flexShrink:0}}>⚠️ RISK</span>}
                        {isCacheHit && <span style={{background:'#f59e0b18',color:'#f59e0b',fontSize:9,fontWeight:700,padding:'1px 6px',borderRadius:100,flexShrink:0}}>CACHE</span>}
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div style={{background:'#040a12',borderRadius:12,padding:16,height:260,overflowY:'auto',fontFamily:'monospace',fontSize:11}}>
                  {eventLog.map((ev,i) => (
                    <div key={i} style={{marginBottom:6,lineHeight:1.5}}>
                      <span style={{color:'#334155'}}>[{ev.ts}] </span>
                      <span style={{color: ev.text.includes('[DECISION]')?'#10b981': ev.text.includes('[ERROR]')?'#f43f5e':'#5eead4'}}>{ev.text}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Risk Alert Panel */}
              {liveActivity.filter(e => (e.category||e.event_type) === 'stress_flagged').length > 0 && (
                <div style={{marginTop:12,background:'rgba(244,63,94,0.05)',border:'1px solid rgba(244,63,94,0.2)',borderRadius:12,padding:12}}>
                  <div style={{fontSize:12,fontWeight:700,color:'#f43f5e',marginBottom:8}}>⚠️ Risk Alerts — Live Stress Flags</div>
                  {liveActivity.filter(e => (e.category||e.event_type) === 'stress_flagged').slice(0,3).map((ev,i) => (
                    <div key={i} style={{fontSize:11,color:'#fca5a5',marginBottom:4,fontFamily:'monospace',display:'flex',gap:8}}>
                      <span style={{color:'#f43f5e'}}>{(ev.business_id||'').slice(0,16)}</span>
                      <span>{ev.message||ev.description}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

function StatBox({ label, val, color }) {
  return (
    <div>
      <div style={{fontSize:20,fontWeight:800,color}}>{val}</div>
      <div style={{fontSize:10,color:'#475569',textTransform:'uppercase',letterSpacing:'0.08em'}}>{label}</div>
    </div>
  );
}

/* ─── Footer ─────────────────────────────────────────────────────────────── */

function Footer() {
  return (
    <footer style={{background:'#020617',borderTop:'1px solid #0f172a',padding:'48px 24px'}}>
      <div style={{maxWidth:1100,margin:'0 auto',display:'flex',flexWrap:'wrap',gap:40,justifyContent:'space-between',alignItems:'flex-start'}}>
        <div>
          <div style={{display:'flex',alignItems:'center',gap:10,marginBottom:12}}>
            <div style={{width:36,height:36,borderRadius:10,background:'linear-gradient(135deg,#0d9488,#0891b2)',display:'flex',alignItems:'center',justifyContent:'center',fontWeight:800,color:'#fff',fontSize:13}}>CS</div>
            <div>
              <div style={{fontWeight:700,color:'#f1f5f9',fontSize:15}}>CashFlowScore</div>
              <div style={{fontSize:10,color:'#475569',textTransform:'uppercase',letterSpacing:'0.1em'}}>MSME Credit Intelligence</div>
            </div>
          </div>
          <p style={{fontSize:13,color:'#475569',maxWidth:300,lineHeight:1.6}}>
            Real-time ML-powered credit scoring for India's underserved micro-businesses. Backed by alternative financial data.
          </p>
        </div>
        <div style={{display:'flex',gap:60,flexWrap:'wrap'}}>
          <div>
            <div style={{fontSize:11,color:'#334155',fontWeight:700,textTransform:'uppercase',letterSpacing:'0.1em',marginBottom:14}}>Product</div>
            {['How It Works','Console Portal','System Architecture'].map(l=>(
              <div key={l} style={{fontSize:13,color:'#475569',marginBottom:8,cursor:'pointer'}}>{l}</div>
            ))}
          </div>
          <div>
            <div style={{fontSize:11,color:'#334155',fontWeight:700,textTransform:'uppercase',letterSpacing:'0.1em',marginBottom:14}}>Tech Stack</div>
            {['XGBoost ML','Redpanda Kafka','TimescaleDB','Redis Cache','FastAPI'].map(l=>(
              <div key={l} style={{fontSize:13,color:'#475569',marginBottom:8}}>{l}</div>
            ))}
          </div>
        </div>
      </div>
      <div style={{maxWidth:1100,margin:'32px auto 0',paddingTop:24,borderTop:'1px solid #0f172a',display:'flex',justifyContent:'space-between',flexWrap:'wrap',gap:8}}>
        <div style={{fontSize:12,color:'#334155'}}>© 2025 CashFlowScore. Built for the NBFC Credit Intelligence Platform.</div>
        <div style={{fontSize:12,color:'#334155'}}>Powered by XGBoost · Redpanda · TimescaleDB · Redis · FastAPI</div>
      </div>
    </footer>
  );
}

/* ─── Main App ───────────────────────────────────────────────────────────── */

export default function App() {
  const [status, setStatus]     = useState(null);
  const [pipeline, setPipeline] = useState(null);

  const [portfolio, setPortfolio]             = useState([]);
  const [uploadSummary, setUploadSummary]     = useState(null);
  const [uploadLoading, setUploadLoading]     = useState(false);
  const [uploadProgress, setUploadProgress]   = useState(0);
  const [downloadUrl, setDownloadUrl]         = useState('');
  const [downloadFilename, setDownloadFilename] = useState('');
  const [dragOver, setDragOver]               = useState(false);
  const [selectedRow, setSelectedRow]         = useState(null);
  const [formVals, setFormVals]               = useState(null);
  const [scoreState, setScoreState]           = useState(null);
  const [scorePending, setScorePending]       = useState(false);
  const [navScrolled, setNavScrolled]         = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen]   = useState(false);
  const fileInputRef = useRef(null);

  const [eventLog, setEventLog] = useState([
    { ts: new Date().toISOString().slice(11,23), text: '[SYSTEM] CashFlowScore API Gateway initialized' },
    { ts: new Date().toISOString().slice(11,23), text: '[SYSTEM] Listening for NBFC portfolio streams on port 8000' }
  ]);

  // Live Kafka activity feed state
  const [liveActivity, setLiveActivity] = useState([]);
  const [pipelineStats, setPipelineStats] = useState(null);
  const [queueDepth, setQueueDepth] = useState(0);
  const [totalCreditUnlocked, setTotalCreditUnlocked] = useState(0);
  const prevQueueDepthRef = useRef(0);

  const addEvent = useCallback((text) => {
    setEventLog(prev => [{ ts: new Date().toISOString().slice(11,23), text }, ...prev.slice(0,49)]);
  }, []);

  // Handle nav scroll
  useEffect(() => {
    const onScroll = () => setNavScrolled(window.scrollY > 60);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  // Poll status + pipeline
  useEffect(() => {
    let lastRp = null, lastTs = null, lastRd = null;
    const pollStatus = async () => {
      try { const r = await axios.get(`${API_BASE}/status`); setStatus(r.data); } catch {}
    };
    const pollPipeline = async () => {
      try {
        const r = await axios.get(`${API_BASE}/pipeline`);
        setPipeline(r.data);
        if (r.data?.redpanda?.status === 'up' && lastRp !== 'up') { addEvent(`[SYSTEM_SYNC] Redpanda cluster verified (${r.data.redpanda.brokers} brokers)`); lastRp='up'; }
        if (r.data?.timescaledb?.status === 'up' && lastTs !== 'up') { addEvent(`[SYSTEM_SYNC] TimescaleDB synced (${r.data.timescaledb.tables} tables)`); lastTs='up'; }
        if (r.data?.redis?.status === 'up' && lastRd !== 'up') { addEvent(`[SYSTEM_SYNC] Redis feature cache connected`); lastRd='up'; }
      } catch {}
    };
    pollStatus(); pollPipeline();
    const t1 = setInterval(pollStatus, 4000);
    const t2 = setInterval(pollPipeline, 8000);
    return () => { clearInterval(t1); clearInterval(t2); };
  }, [addEvent]);

  // Poll live Kafka activity feed from real pipeline (port 8002 via gateway proxy)
  useEffect(() => {
    const pollActivityFeed = async () => {
      try {
        const r = await axios.get(`${API_BASE}/activity-feed?limit=30`);
        if (r.data?.items?.length > 0) {
          setLiveActivity(r.data.items.slice(0, 30));
        }
      } catch {}
    };
    const pollPipelineStats = async () => {
      try {
        const r = await axios.get(`${API_BASE}/pipeline-stats`);
        if (r.data) {
          setPipelineStats(r.data);
          const depth = r.data.queue_depth || 0;
          if (depth !== prevQueueDepthRef.current) {
            setQueueDepth(depth);
            prevQueueDepthRef.current = depth;
          }
        }
      } catch {}
    };
    pollActivityFeed();
    pollPipelineStats();
    const t3 = setInterval(pollActivityFeed, 2000);
    const t4 = setInterval(pollPipelineStats, 1500);
    return () => { clearInterval(t3); clearInterval(t4); };
  }, []);

  const processFile = useCallback(async (file) => {
    if (!file) return;
    const fd = new FormData();
    fd.append('file', file);
    setUploadLoading(true); setUploadProgress(0);
    setUploadSummary(null); setDownloadUrl('');
    setSelectedRow(null); setPortfolio([]);
    addEvent(`[UPLOAD] Batch ingest started for ${file.name}`);
    addEvent(`[REDPANDA] Publishing events to loan_applications topic`);
    let pv = 0;
    const ticker = setInterval(() => {
      pv = Math.min(90, pv+6);
      setUploadProgress(pv);
      if (pv === 30) addEvent(`[ML_ENGINE] XGBoost vectorized inference running...`);
      if (pv === 60) addEvent(`[REDIS] Caching feature vectors...`);
    }, 180);
    try {
      const r = await axios.post(`${API_BASE}/score-batch`, fd, {
        headers: { 'Content-Type': 'multipart/form-data', ...authHeaders },
      });
      await new Promise(res => setTimeout(res, 2000));
      clearInterval(ticker); setUploadProgress(100); setUploadSummary(r.data);
      const count = r.data.rows_processed || r.data.preview?.length || 0;
      addEvent(`[TIMESCALE] Wrote ${count} scored rows to hypertable`);
      addEvent(`[DECISION] Batch scoring complete — download ready`);
      const rows = (r.data.preview || []).map((row, idx) => ({
        id:   `ROW-${idx+1}`,
        name: row.business_name || `Business ${idx+1}`,
        score: Number(row.score ?? row.credit_score ?? 0),
        status: Number(row.score ?? row.credit_score ?? 0) >= 70 ? 'approved' : 'rejected',
        risk_band: Number(row.score ?? row.credit_score ?? 0) >= 80 ? 'low' : Number(row.score ?? row.credit_score ?? 0) >= 60 ? 'medium' : 'high',
        credit_unlocked: Number(row.score ?? row.credit_score ?? 0) >= 70 ? Math.round(Number(row.inflow_amount||0)*1.5) : 0,
        reasons: typeof row.top_reasons === 'string' ? row.top_reasons.split(' | ') : (row.top_reasons||[]),
        editable_inputs: {
          inflow_amount:  Number(row.inflow_amount||0),
          gst_delay_days: Number(row.gst_delay_days||0),
          bounce_count:   Number(row.bounce_count||0),
        },
      }));
      setPortfolio(rows);
      if (r.data.download_content_base64) {
        const type = r.data.download_content_type || 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
        const filename = r.data.download_filename || 'scored_output.xlsx';
        const b64 = r.data.download_content_base64;
        const byteChars = atob(b64);
        const byteArr = new Uint8Array(byteChars.length);
        for (let i = 0; i < byteChars.length; i++) byteArr[i] = byteChars.charCodeAt(i);
        const blob = new Blob([byteArr], { type });
        const objUrl = URL.createObjectURL(blob);
        setDownloadUrl(objUrl);
        setDownloadFilename(filename);
        // Auto-trigger download so user gets the file immediately
        const a = document.createElement('a');
        a.href = objUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        addEvent(`[REPORT] Excel report ready — ${filename} downloaded`);
      }
    } catch (err) { clearInterval(ticker); console.error(err); }
    finally { setUploadLoading(false); }
  }, [addEvent]);

  const handleFileInput = (e) => processFile(e.target.files?.[0]);
  const handleDrop      = (e) => { e.preventDefault(); setDragOver(false); processFile(e.dataTransfer.files?.[0]); };
  const handleDragOver  = (e) => { e.preventDefault(); setDragOver(true); };
  const handleDragLeave = ()  => setDragOver(false);

  const handleSelect = useCallback((row) => {
    setSelectedRow(row); setFormVals({...row.editable_inputs});
    setScoreState({ score: row.score, top_reasons: row.reasons, source: 'batch' });
  }, []);

  const handleScoreChange = useCallback(async (e) => {
    const { name, value } = e.target;
    const next = { ...formVals, [name]: Number(value) };
    setFormVals(next); setScorePending(true);
    addEvent(`[SCORE_UPDATE] Re-scoring ${selectedRow?.id} — ${name} changed`);
    try {
      const r = await axios.post(`${API_BASE}/score`, { business_id: selectedRow?.id, features: next }, { headers: authHeaders });
      setScoreState(r.data);
      addEvent(`[DECISION] ${selectedRow?.id} → new score ${r.data.score} (${scoreLabel(r.data.score)})`);
    } catch {}
    finally { setScorePending(false); }
  }, [formVals, selectedRow, addEvent]);

  const scrollToDemo = () => document.getElementById('demo')?.scrollIntoView({ behavior:'smooth' });

  return (
    <div style={{minHeight:'100vh',background:'#020617',color:'#f1f5f9',fontFamily:"'Inter','Segoe UI',sans-serif"}}>

      {/* Google Font */}
      <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet" />

      {/* Sticky Nav */}
      <nav style={{
        position:'fixed',top:0,left:0,right:0,zIndex:100,
        background: navScrolled ? 'rgba(2,6,23,0.95)' : 'transparent',
        backdropFilter: navScrolled ? 'blur(12px)' : 'none',
        borderBottom: navScrolled ? '1px solid #0f172a' : '1px solid transparent',
        transition:'all 0.3s',
      }}>
        <div style={{maxWidth:1200,margin:'0 auto',padding:'0 24px',height:64,display:'flex',alignItems:'center',justifyContent:'space-between'}}>
          {/* Logo */}
          <div style={{display:'flex',alignItems:'center',gap:10}}>
            <div style={{width:36,height:36,borderRadius:10,background:'linear-gradient(135deg,#0d9488,#0891b2)',display:'flex',alignItems:'center',justifyContent:'center',fontWeight:800,color:'#fff',fontSize:13}}>CS</div>
            <div>
              <div style={{fontWeight:700,color:'#f1f5f9',fontSize:15,lineHeight:1.2}}>CashFlowScore</div>
              <div style={{fontSize:9,color:'#475569',textTransform:'uppercase',letterSpacing:'0.12em'}}>MSME Credit Intelligence</div>
            </div>
          </div>
          {/* Nav Links */}
          <div style={{display:'flex',alignItems:'center',gap:32}}>
            {[['#who-we-are','Problem'],['#differentiator','Our Edge'],['#novelties','Tech'],['#how-it-works','Pipeline'],['#data-cleaning','Data Cleaning'],['#proof','Live Proof'],['#demo','Console']].map(([href,label])=>(
              <NavLink key={href} href={href}>{label}</NavLink>
            ))}
          </div>
          <button onClick={scrollToDemo} style={{
            background:'linear-gradient(135deg,#0d9488,#0891b2)',
            color:'#fff',border:'none',borderRadius:8,padding:'9px 20px',
            fontSize:13,fontWeight:700,cursor:'pointer',
            boxShadow:'0 4px 16px rgba(13,148,136,0.35)',transition:'all 0.2s'
          }}
          onMouseEnter={e=>e.currentTarget.style.boxShadow='0 6px 24px rgba(13,148,136,0.5)'}
          onMouseLeave={e=>e.currentTarget.style.boxShadow='0 4px 16px rgba(13,148,136,0.35)'}>
            Launch Console
          </button>
        </div>
      </nav>

      {/* Sections */}
      <HeroSection onScrollToDemo={scrollToDemo} />
      <ProblemSection />
      <DifferentiatorSection />
      <NoveltiesSection />
      <HowItWorksSection />
      <DataCleaningSection />
      <ProofSection />
      <DashboardSection
        portfolio={portfolio}
        uploadSummary={uploadSummary}
        uploadLoading={uploadLoading}
        uploadProgress={uploadProgress}
        downloadUrl={downloadUrl}
        downloadFilename={downloadFilename}
        dragOver={dragOver}
        fileInputRef={fileInputRef}
        handleFileInput={handleFileInput}
        handleDrop={handleDrop}
        handleDragOver={handleDragOver}
        handleDragLeave={handleDragLeave}
        selectedRow={selectedRow}
        formVals={formVals}
        scoreState={scoreState}
        scorePending={scorePending}
        handleSelect={handleSelect}
        handleScoreChange={handleScoreChange}
        eventLog={eventLog}
        status={status}
        pipeline={pipeline}
        liveActivity={liveActivity}
        pipelineStats={pipelineStats}
        queueDepth={queueDepth}
      />
      <Footer />
    </div>
  );
}
