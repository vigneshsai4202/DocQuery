import { useEffect, useRef, useState } from 'react'
import api from '../api'

const STATUS_COLORS = { pending: '#f59e0b', processing: '#3b82f6', ready: '#22c55e', error: '#ef4444' }

export default function DocumentsPage() {
  const [docs, setDocs] = useState([])
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const fileRef = useRef()

  const load = async () => {
    const { data } = await api.get('/documents')
    setDocs(data)
  }

  useEffect(() => { load() }, [])

  // Poll processing documents every 3s
  useEffect(() => {
    const processing = docs.some(d => d.status === 'pending' || d.status === 'processing')
    if (!processing) return
    const id = setTimeout(load, 3000)
    return () => clearTimeout(id)
  }, [docs])

  const upload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setError('')
    setUploading(true)
    const form = new FormData()
    form.append('file', file)
    try {
      await api.post('/documents', form)
      await load()
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed')
    } finally {
      setUploading(false)
      fileRef.current.value = ''
    }
  }

  const remove = async (id) => {
    if (!confirm('Delete this document and all its vectors?')) return
    await api.delete(`/documents/${id}`)
    setDocs(d => d.filter(x => x.id !== id))
  }

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <h2 style={styles.title}>Documents</h2>
        <label style={styles.uploadBtn}>
          {uploading ? 'Uploading…' : '+ Upload PDF'}
          <input ref={fileRef} type="file" accept=".pdf" onChange={upload} style={{ display: 'none' }} disabled={uploading} />
        </label>
      </div>
      {error && <p style={styles.error}>{error}</p>}
      {docs.length === 0 && <p style={styles.empty}>No documents yet. Upload a PDF to get started.</p>}
      <div style={styles.list}>
        {docs.map(doc => (
          <div key={doc.id} style={styles.card}>
            <div style={styles.cardMain}>
              <span style={styles.docName}>{doc.original_name}</span>
              <span style={{ ...styles.badge, background: STATUS_COLORS[doc.status] || '#64748b' }}>{doc.status}</span>
              <button style={styles.deleteBtn} onClick={() => remove(doc.id)}>Delete</button>
            </div>
            <div style={styles.cardMeta}>
              <span>{(doc.file_size / 1024).toFixed(1)} KB</span>
              {doc.page_count > 0 && <span>{doc.page_count} pages</span>}
              <span>{new Date(doc.created_at).toLocaleDateString()}</span>
              {doc.error_message && <span style={styles.errMsg}>{doc.error_message}</span>}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

const styles = {
  page: { padding: '2rem', maxWidth: '800px', margin: '0 auto' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' },
  title: { color: '#f1f5f9', margin: 0, fontSize: '1.4rem' },
  uploadBtn: { padding: '0.6rem 1.2rem', background: '#6366f1', color: '#fff', borderRadius: '8px', cursor: 'pointer', fontWeight: 600, fontSize: '0.9rem' },
  error: { color: '#f87171', marginBottom: '1rem' },
  empty: { color: '#64748b', textAlign: 'center', marginTop: '3rem' },
  list: { display: 'flex', flexDirection: 'column', gap: '0.75rem' },
  card: { background: '#1e293b', borderRadius: '10px', padding: '1rem 1.25rem' },
  cardMain: { display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.4rem' },
  docName: { color: '#f1f5f9', fontWeight: 500, flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  badge: { padding: '0.2rem 0.6rem', borderRadius: '999px', fontSize: '0.75rem', color: '#fff', fontWeight: 600, flexShrink: 0 },
  cardMeta: { display: 'flex', gap: '1rem', color: '#64748b', fontSize: '0.8rem', flexWrap: 'wrap' },
  errMsg: { color: '#f87171' },
  deleteBtn: { background: 'transparent', border: '1px solid #334155', color: '#94a3b8', borderRadius: '6px', padding: '0.25rem 0.6rem', cursor: 'pointer', fontSize: '0.8rem', flexShrink: 0 },
}
