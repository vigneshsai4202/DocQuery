import { useNavigate } from 'react-router-dom'

const features = [
  {
    icon: '📄',
    title: 'Upload Any PDF',
    desc: 'Drop in research papers, contracts, manuals — any PDF up to 50MB.',
  },
  {
    icon: '🔍',
    title: 'Semantic Search',
    desc: 'Embeddings-powered vector search finds the right passages, not just keywords.',
  },
  {
    icon: '🤖',
    title: 'Grounded Answers',
    desc: 'LLM answers are anchored to your documents — no hallucinations, exact citations.',
  },
  {
    icon: '⚡',
    title: 'Streaming Responses',
    desc: 'Token-by-token streaming via SSE so you see answers as they are generated.',
  },
  {
    icon: '📌',
    title: 'Source Citations',
    desc: 'Every answer links back to the document name, page number, and chunk text.',
  },
  {
    icon: '🗂️',
    title: 'Conversation History',
    desc: 'All your Q&A sessions are saved and browsable at any time.',
  },
]

const steps = [
  { n: '01', title: 'Upload a PDF', desc: 'Drag and drop or browse to upload your document.' },
  { n: '02', title: 'Ask a Question', desc: 'Type any question about the content in plain English.' },
  { n: '03', title: 'Get Cited Answers', desc: 'Receive a streamed answer with exact page references.' },
]

export default function LandingPage() {
  const navigate = useNavigate()

  return (
    <div style={s.page}>
      {/* NAV */}
      <nav style={s.nav}>
        <span style={s.logo}>DocuQuery</span>
        <button style={s.navBtn} onClick={() => navigate('/login')}>Sign in →</button>
      </nav>

      {/* HERO */}
      <section style={s.hero}>
        <div style={s.badge}>RAG · FAISS · Groq · SSE Streaming</div>
        <h1 style={s.h1}>
          Ask questions.<br />
          <span style={s.accent}>Get cited answers.</span>
        </h1>
        <p style={s.sub}>
          Upload PDFs, ask anything, and get grounded answers with exact source citations —
          document name, page number, and the relevant passage.
        </p>
        <div style={s.heroActions}>
          <button style={s.primaryBtn} onClick={() => navigate('/login')}>
            Try it now →
          </button>
          <a
            style={s.ghostBtn}
            href="https://github.com/vigneshsai4202/DocQuery"
            target="_blank"
            rel="noreferrer"
          >
            View on GitHub
          </a>
        </div>

        {/* mock terminal */}
        <div style={s.terminal}>
          <div style={s.termBar}>
            <span style={{...s.dot, background:'#ff5f57'}} />
            <span style={{...s.dot, background:'#febc2e'}} />
            <span style={{...s.dot, background:'#28c840'}} />
          </div>
          <div style={s.termBody}>
            <p style={s.termLine}><span style={s.prompt}>user › </span>What are the key findings in section 3?</p>
            <p style={s.termLine}><span style={s.prompt}>ai   › </span><span style={s.streaming}>Section 3 highlights three core findings: ...</span></p>
            <p style={{...s.termLine, color:'#64748b', fontSize:12, marginTop:8}}>
              📄 research-paper.pdf · page 7 · "The results demonstrate a 34% improvement..."
            </p>
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section style={s.section}>
        <h2 style={s.h2}>How it works</h2>
        <div style={s.steps}>
          {steps.map(step => (
            <div key={step.n} style={s.stepCard}>
              <div style={s.stepNum}>{step.n}</div>
              <h3 style={s.stepTitle}>{step.title}</h3>
              <p style={s.stepDesc}>{step.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* FEATURES */}
      <section style={{...s.section, background:'#0f172a'}}>
        <h2 style={s.h2}>What's inside</h2>
        <div style={s.grid}>
          {features.map(f => (
            <div key={f.title} style={s.card}>
              <div style={s.cardIcon}>{f.icon}</div>
              <h3 style={s.cardTitle}>{f.title}</h3>
              <p style={s.cardDesc}>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* STACK */}
      <section style={s.section}>
        <h2 style={s.h2}>Tech stack</h2>
        <div style={s.pills}>
          {['FastAPI','React 18','FAISS','pgvector','Groq LLM','sentence-transformers','Neon Postgres','SSE Streaming','Alembic','Vite'].map(t => (
            <span key={t} style={s.pill}>{t}</span>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section style={s.cta}>
        <h2 style={{...s.h2, marginBottom:12}}>Ready to query your documents?</h2>
        <p style={{color:'#94a3b8', marginBottom:28}}>No login required. Upload a PDF and start asking.</p>
        <button style={s.primaryBtn} onClick={() => navigate('/login')}>Open DocuQuery →</button>
      </section>

      {/* FOOTER */}
      <footer style={s.footer}>
        <span>DocuQuery — built with FastAPI + React</span>
        <a style={s.footerLink} href="https://github.com/vigneshsai4202/DocQuery" target="_blank" rel="noreferrer">GitHub</a>
      </footer>
    </div>
  )
}

const s = {
  page:       { minHeight:'100vh', background:'#0f172a', color:'#f1f5f9', fontFamily:'system-ui,-apple-system,sans-serif' },
  nav:        { display:'flex', justifyContent:'space-between', alignItems:'center', padding:'18px 48px', borderBottom:'1px solid #1e293b', position:'sticky', top:0, background:'rgba(15,23,42,0.9)', backdropFilter:'blur(12px)', zIndex:10 },
  logo:       { fontSize:20, fontWeight:700, letterSpacing:'-0.5px', color:'#f1f5f9' },
  navBtn:     { background:'transparent', border:'1px solid #334155', color:'#94a3b8', padding:'8px 18px', borderRadius:8, cursor:'pointer', fontSize:14, transition:'all .2s' },
  hero:       { maxWidth:760, margin:'0 auto', padding:'96px 24px 80px', textAlign:'center' },
  badge:      { display:'inline-block', background:'#1e293b', border:'1px solid #334155', color:'#94a3b8', fontSize:12, padding:'4px 14px', borderRadius:20, marginBottom:24, letterSpacing:'0.5px' },
  h1:         { fontSize:'clamp(2.2rem,5vw,3.4rem)', fontWeight:800, lineHeight:1.15, letterSpacing:'-1px', marginBottom:20 },
  accent:     { background:'linear-gradient(135deg,#6366f1,#8b5cf6)', WebkitBackgroundClip:'text', WebkitTextFillColor:'transparent' },
  sub:        { fontSize:18, color:'#94a3b8', lineHeight:1.7, maxWidth:580, margin:'0 auto 36px' },
  heroActions:{ display:'flex', gap:14, justifyContent:'center', flexWrap:'wrap', marginBottom:56 },
  primaryBtn: { background:'linear-gradient(135deg,#6366f1,#8b5cf6)', color:'#fff', border:'none', padding:'13px 28px', borderRadius:10, fontSize:16, fontWeight:600, cursor:'pointer' },
  ghostBtn:   { background:'transparent', border:'1px solid #334155', color:'#94a3b8', padding:'13px 28px', borderRadius:10, fontSize:16, textDecoration:'none', display:'inline-flex', alignItems:'center' },
  terminal:   { background:'#0d1117', border:'1px solid #1e293b', borderRadius:12, textAlign:'left', overflow:'hidden', maxWidth:600, margin:'0 auto' },
  termBar:    { background:'#161b22', padding:'10px 16px', display:'flex', gap:6 },
  dot:        { width:12, height:12, borderRadius:'50%', display:'inline-block' },
  termBody:   { padding:'20px 24px' },
  termLine:   { fontFamily:'monospace', fontSize:14, lineHeight:1.8, color:'#e2e8f0' },
  prompt:     { color:'#6366f1', fontWeight:700 },
  streaming:  { color:'#a5f3fc' },
  section:    { padding:'80px 24px', background:'#0a0f1e' },
  h2:         { textAlign:'center', fontSize:'clamp(1.5rem,3vw,2rem)', fontWeight:700, marginBottom:48, letterSpacing:'-0.5px' },
  steps:      { display:'flex', gap:24, justifyContent:'center', flexWrap:'wrap', maxWidth:900, margin:'0 auto' },
  stepCard:   { flex:'1 1 220px', maxWidth:260, background:'#0f172a', border:'1px solid #1e293b', borderRadius:14, padding:'28px 24px' },
  stepNum:    { fontSize:13, fontWeight:700, color:'#6366f1', marginBottom:12, letterSpacing:'1px' },
  stepTitle:  { fontSize:17, fontWeight:600, marginBottom:8 },
  stepDesc:   { fontSize:14, color:'#94a3b8', lineHeight:1.6 },
  grid:       { display:'grid', gridTemplateColumns:'repeat(auto-fit,minmax(240px,1fr))', gap:20, maxWidth:1000, margin:'0 auto' },
  card:       { background:'#0a0f1e', border:'1px solid #1e293b', borderRadius:14, padding:'28px 24px', transition:'border-color .2s' },
  cardIcon:   { fontSize:28, marginBottom:14 },
  cardTitle:  { fontSize:16, fontWeight:600, marginBottom:8 },
  cardDesc:   { fontSize:14, color:'#94a3b8', lineHeight:1.6 },
  pills:      { display:'flex', flexWrap:'wrap', gap:10, justifyContent:'center', maxWidth:700, margin:'0 auto' },
  pill:       { background:'#1e293b', border:'1px solid #334155', color:'#94a3b8', padding:'7px 16px', borderRadius:20, fontSize:13 },
  cta:        { padding:'80px 24px', textAlign:'center', background:'#0f172a' },
  footer:     { borderTop:'1px solid #1e293b', padding:'24px 48px', display:'flex', justifyContent:'space-between', alignItems:'center', color:'#475569', fontSize:13 },
  footerLink: { color:'#6366f1', textDecoration:'none' },
}
