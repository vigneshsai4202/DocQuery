import { useEffect, useRef, useState } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import 'react-pdf/dist/Page/AnnotationLayer.css'
import 'react-pdf/dist/Page/TextLayer.css'

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString()

export default function PdfViewerModal({ documentId, documentName, initialPage, onClose }) {
  const [numPages, setNumPages] = useState(null)
  const [page, setPage] = useState(initialPage || 1)
  const [inputVal, setInputVal] = useState(String(initialPage || 1))
  const [width, setWidth] = useState(700)
  const containerRef = useRef()

  useEffect(() => {
    setPage(initialPage || 1)
    setInputVal(String(initialPage || 1))
  }, [initialPage])

  useEffect(() => {
    const obs = new ResizeObserver(entries => {
      const w = entries[0]?.contentRect.width
      if (w) setWidth(Math.min(w - 48, 800))
    })
    if (containerRef.current) obs.observe(containerRef.current)
    return () => obs.disconnect()
  }, [])

  // close on Escape
  useEffect(() => {
    const handler = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  const url = `/api/v1/documents/${documentId}/file`

  return (
    <div style={s.overlay} onClick={e => { if (e.target === e.currentTarget) onClose() }}>
      <div style={s.modal} ref={containerRef}>
        {/* Header */}
        <div style={s.header}>
          <div style={s.headerLeft}>
            <span style={s.docName}>📄 {documentName}</span>
            <span style={s.pageInfo}>{numPages ? `Page ${page} of ${numPages}` : '…'}</span>
          </div>
          <div style={s.headerRight}>
            <button style={s.navBtn} disabled={page <= 1} onClick={() => setPage(p => p - 1)}>‹</button>
            <button style={s.navBtn} disabled={page >= numPages} onClick={() => setPage(p => p + 1)}>›</button>
            <button style={s.closeBtn} onClick={onClose}>✕</button>
          </div>
        </div>

        {/* PDF */}
        <div style={s.viewer}>
          <Document
            file={url}
            onLoadSuccess={({ numPages }) => setNumPages(numPages)}
            loading={<div style={s.loading}>Loading PDF…</div>}
            error={<div style={s.errMsg}>Failed to load PDF.</div>}
          >
            <Page
              pageNumber={page}
              width={width}
              renderTextLayer={true}
              renderAnnotationLayer={true}
            />
          </Document>
        </div>

        {/* Page jump */}
        {numPages && (
          <div style={s.footer}>
            <span style={s.footerLabel}>Go to page</span>
            <input
              style={s.pageInput}
              type="number"
              min={1}
              max={numPages}
              value={inputVal}
              onChange={e => setInputVal(e.target.value)}
              onBlur={() => {
                const v = parseInt(inputVal)
                if (v >= 1 && v <= numPages) setPage(v)
                else setInputVal(String(page))
              }}
              onKeyDown={e => {
                if (e.key === 'Enter') {
                  const v = parseInt(inputVal)
                  if (v >= 1 && v <= numPages) setPage(v)
                  else setInputVal(String(page))
                }
              }}
            />
            <span style={s.footerLabel}>of {numPages}</span>
          </div>
        )}
      </div>
    </div>
  )
}

const s = {
  overlay:    { position:'fixed', inset:0, background:'rgba(0,0,0,0.75)', zIndex:1000, display:'flex', alignItems:'center', justifyContent:'center', padding:16 },
  modal:      { background:'#0f172a', border:'1px solid #1e293b', borderRadius:14, display:'flex', flexDirection:'column', width:'100%', maxWidth:880, maxHeight:'92vh', overflow:'hidden' },
  header:     { display:'flex', justifyContent:'space-between', alignItems:'center', padding:'12px 20px', borderBottom:'1px solid #1e293b', flexShrink:0 },
  headerLeft: { display:'flex', alignItems:'center', gap:12, minWidth:0 },
  headerRight:{ display:'flex', alignItems:'center', gap:8, flexShrink:0 },
  docName:    { color:'#f1f5f9', fontWeight:600, fontSize:14, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap', maxWidth:320 },
  pageInfo:   { color:'#64748b', fontSize:13, flexShrink:0 },
  navBtn:     { background:'#1e293b', border:'1px solid #334155', color:'#94a3b8', borderRadius:6, width:32, height:32, cursor:'pointer', fontSize:18, lineHeight:1, display:'flex', alignItems:'center', justifyContent:'center' },
  closeBtn:   { background:'transparent', border:'1px solid #334155', color:'#94a3b8', borderRadius:6, width:32, height:32, cursor:'pointer', fontSize:16 },
  viewer:     { overflowY:'auto', flex:1, display:'flex', justifyContent:'center', padding:'20px 24px', background:'#0a0f1e' },
  loading:    { color:'#64748b', padding:40, textAlign:'center' },
  errMsg:     { color:'#f87171', padding:40, textAlign:'center' },
  footer:     { display:'flex', alignItems:'center', gap:8, padding:'10px 20px', borderTop:'1px solid #1e293b', flexShrink:0, justifyContent:'center' },
  footerLabel:{ color:'#64748b', fontSize:13 },
  pageInput:  { width:56, padding:'4px 8px', background:'#1e293b', border:'1px solid #334155', borderRadius:6, color:'#f1f5f9', fontSize:13, textAlign:'center' },
}
