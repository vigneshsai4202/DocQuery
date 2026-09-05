import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api'

function ConversationDetail({ id, onBack }) {
  const [conv, setConv] = useState(null)

  useEffect(() => {
    api.get(`/conversations/${id}`).then(r => setConv(r.data))
  }, [id])

  if (!conv) return <p style={styles.loading}>Loading…</p>

  return (
    <div>
      <button style={styles.backBtn} onClick={onBack}>← Back</button>
      <h3 style={styles.convTitle}>{conv.title}</h3>
      <div style={styles.messages}>
        {conv.messages.map(msg => (
          <div key={msg.id} style={{ ...styles.msg, alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
            <div style={{ ...styles.bubble, background: msg.role === 'user' ? '#6366f1' : '#1e293b' }}>
              <p style={styles.msgText}>{msg.content}</p>
              {msg.sources && msg.sources.length > 0 && (
                <div style={styles.sources}>
                  <p style={styles.sourcesLabel}>Sources</p>
                  {msg.sources.map((s, i) => (
                    <div key={i} style={styles.source}>
                      <span style={styles.sourceRef}>{s.document_name} — page {s.page_number}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <span style={styles.time}>{new Date(msg.created_at).toLocaleTimeString()}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function HistoryPage() {
  const [conversations, setConversations] = useState([])
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    api.get('/conversations')
      .then(r => setConversations(r.data))
      .catch(() => setError('Failed to load conversations.'))
  }, [])

  const remove = async (e, id) => {
    e.stopPropagation()
    if (!confirm('Delete this conversation?')) return
    await api.delete(`/conversations/${id}`)
    setConversations(c => c.filter(x => x.id !== id))
  }

  return (
    <div style={styles.page}>
      <h2 style={styles.title}>Conversation History</h2>
      {error && <p style={{ color: '#f87171', marginBottom: '1rem' }}>{error}</p>}
      {!error && conversations.length === 0 && <p style={styles.empty}>No conversations yet.</p>}
      <div style={styles.list}>
        {conversations.map(c => (
          <div key={c.id} style={styles.card} onClick={() => navigate(`/app/chat/${c.id}`)}>
            <div style={styles.cardMain}>
              <span style={styles.cardTitle}>{c.title}</span>
              <button style={styles.deleteBtn} onClick={e => remove(e, c.id)}>Delete</button>
            </div>
            <span style={styles.cardDate}>{new Date(c.created_at).toLocaleString()}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

const styles = {
  page: { padding: '2rem', maxWidth: '800px', margin: '0 auto' },
  title: { color: '#f1f5f9', margin: '0 0 1.5rem', fontSize: '1.4rem' },
  empty: { color: '#64748b', textAlign: 'center', marginTop: '3rem' },
  list: { display: 'flex', flexDirection: 'column', gap: '0.75rem' },
  card: { background: '#1e293b', borderRadius: '10px', padding: '1rem 1.25rem', cursor: 'pointer', transition: 'background 0.15s' },
  cardMain: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  cardTitle: { color: '#f1f5f9', fontWeight: 500, flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  cardDate: { color: '#64748b', fontSize: '0.8rem', marginTop: '0.3rem', display: 'block' },
  deleteBtn: { background: 'transparent', border: '1px solid #334155', color: '#94a3b8', borderRadius: '6px', padding: '0.2rem 0.6rem', cursor: 'pointer', fontSize: '0.8rem', flexShrink: 0 },
  loading: { color: '#64748b' },
  backBtn: { background: 'transparent', border: 'none', color: '#6366f1', cursor: 'pointer', fontSize: '0.95rem', padding: 0, marginBottom: '1rem' },
  convTitle: { color: '#f1f5f9', marginBottom: '1.5rem' },
  messages: { display: 'flex', flexDirection: 'column', gap: '1rem' },
  msg: { display: 'flex', flexDirection: 'column', maxWidth: '75%' },
  bubble: { borderRadius: '12px', padding: '0.85rem 1rem' },
  msgText: { color: '#f1f5f9', margin: 0, lineHeight: 1.6, whiteSpace: 'pre-wrap' },
  time: { color: '#475569', fontSize: '0.75rem', marginTop: '0.25rem' },
  sources: { marginTop: '0.75rem', borderTop: '1px solid #334155', paddingTop: '0.5rem' },
  sourcesLabel: { color: '#94a3b8', fontSize: '0.75rem', margin: '0 0 0.4rem', fontWeight: 600, textTransform: 'uppercase' },
  source: { marginBottom: '0.25rem' },
  sourceRef: { color: '#6366f1', fontSize: '0.8rem' },
}
