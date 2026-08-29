import { useEffect, useRef, useState } from 'react'
import api from '../api'

function SourceCard({ source }) {
  const [open, setOpen] = useState(false)
  return (
    <div style={styles.source}>
      <div style={styles.sourceHeader} onClick={() => setOpen(o => !o)}>
        <span style={styles.sourceTitle}>📄 {source.document_name} — page {source.page_number}</span>
        <span style={styles.sourceToggle}>{open ? '▲' : '▼'}</span>
      </div>
      {open && <p style={styles.sourceText}>{source.text}</p>}
    </div>
  )
}

function Message({ msg }) {
  const isUser = msg.role === 'user'
  return (
    <div style={{ ...styles.msgWrap, justifyContent: isUser ? 'flex-end' : 'flex-start' }}>
      <div style={{ ...styles.bubble, background: isUser ? '#6366f1' : '#1e293b', maxWidth: '78%' }}>
        <p style={styles.msgText}>
          {msg.content}
          {msg.streaming && <span style={styles.cursor}>▋</span>}
        </p>
        {!msg.streaming && msg.sources && msg.sources.length > 0 && (
          <div style={styles.sources}>
            <p style={styles.sourcesLabel}>Sources ({msg.sources.length})</p>
            {msg.sources.map((s, i) => <SourceCard key={i} source={s} />)}
          </div>
        )}
      </div>
    </div>
  )
}

function ErrorBanner({ message, onDismiss }) {
  return (
    <div style={styles.errorBanner}>
      <span>⚠️ {message}</span>
      <button style={styles.dismissBtn} onClick={onDismiss}>✕</button>
    </div>
  )
}

export default function ChatPage() {
  const [conversationId, setConversationId] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const bottomRef = useRef()
  const abortRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async (e) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const question = input.trim()
    setInput('')
    setError('')
    setLoading(true)

    // Add user message
    setMessages(m => [...m, { role: 'user', content: question, sources: null }])

    // Add empty assistant message that we'll stream into
    const assistantIdx = messages.length + 1
    setMessages(m => [...m, { role: 'assistant', content: '', sources: null, streaming: true }])

    try {
      const token = localStorage.getItem('token')
      const headers = { 'Content-Type': 'application/json' }
      if (token) headers['Authorization'] = `Bearer ${token}`

      const resp = await fetch('/api/v1/query/ask/stream', {
        method: 'POST',
        headers,
        body: JSON.stringify({ question, conversation_id: conversationId }),
        signal: abortRef.current?.signal,
      })

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}))
        throw new Error(err.detail || `Server error ${resp.status}`)
      }

      const reader = resp.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })

        const lines = buffer.split('\n')
        buffer = lines.pop() // keep incomplete line

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const event = JSON.parse(line.slice(6))

          if (event.type === 'sources') {
            setMessages(m => m.map((msg, i) =>
              i === assistantIdx ? { ...msg, sources: event.sources } : msg
            ))
          } else if (event.type === 'token') {
            setMessages(m => m.map((msg, i) =>
              i === assistantIdx ? { ...msg, content: msg.content + event.token } : msg
            ))
          } else if (event.type === 'done') {
            setConversationId(event.conversation_id)
            setMessages(m => m.map((msg, i) =>
              i === assistantIdx ? { ...msg, streaming: false } : msg
            ))
          } else if (event.type === 'error') {
            throw new Error(event.detail)
          }
        }
      }
    } catch (err) {
      if (err.name === 'AbortError') return
      setError(err.message || 'Something went wrong')
      // Remove the empty assistant message on error
      setMessages(m => m.filter((_, i) => i !== assistantIdx))
    } finally {
      setLoading(false)
    }
  }

  const newChat = () => {
    abortRef.current?.abort()
    setConversationId(null)
    setMessages([])
    setError('')
    setLoading(false)
  }

  return (
    <div style={styles.page}>
      <div style={styles.topBar}>
        <h2 style={styles.title}>Ask Your Documents</h2>
        <button style={styles.newBtn} onClick={newChat}>New Chat</button>
      </div>

      {error && <ErrorBanner message={error} onDismiss={() => setError('')} />}

      <div style={styles.feed}>
        {messages.length === 0 && (
          <div style={styles.emptyState}>
            <p style={styles.emptyIcon}>🔍</p>
            <p style={styles.emptyTitle}>Ask anything about your documents</p>
            <p style={styles.emptySub}>Upload PDFs on the Documents page first, then ask questions here.</p>
          </div>
        )}
        {messages.map((m, i) => <Message key={i} msg={m} />)}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={send} style={styles.inputRow}>
        <input
          style={styles.input}
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Ask a question about your documents…"
          disabled={loading}
          autoFocus
        />
        <button style={{ ...styles.sendBtn, opacity: loading || !input.trim() ? 0.5 : 1 }} type="submit" disabled={loading || !input.trim()}>
          {loading ? '⏳' : 'Send'}
        </button>
      </form>
    </div>
  )
}

const styles = {
  page: { display: 'flex', flexDirection: 'column', height: '100%', padding: '1.5rem', maxWidth: '820px', margin: '0 auto' },
  topBar: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexShrink: 0 },
  title: { color: '#f1f5f9', margin: 0, fontSize: '1.4rem', fontWeight: 600 },
  newBtn: { padding: '0.4rem 0.9rem', background: 'transparent', border: '1px solid #334155', color: '#94a3b8', borderRadius: '6px', cursor: 'pointer', fontSize: '0.85rem' },
  errorBanner: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#450a0a', border: '1px solid #7f1d1d', borderRadius: '8px', padding: '0.6rem 1rem', marginBottom: '0.75rem', color: '#fca5a5', fontSize: '0.875rem', flexShrink: 0 },
  dismissBtn: { background: 'none', border: 'none', color: '#fca5a5', cursor: 'pointer', fontSize: '1rem', padding: '0 0.25rem' },
  feed: { flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1rem', paddingBottom: '1rem' },
  emptyState: { display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', flex: 1, gap: '0.5rem', color: '#475569' },
  emptyIcon: { fontSize: '2.5rem', margin: 0 },
  emptyTitle: { fontSize: '1.1rem', color: '#94a3b8', fontWeight: 500, margin: 0 },
  emptySub: { fontSize: '0.875rem', margin: 0, textAlign: 'center' },
  msgWrap: { display: 'flex' },
  bubble: { borderRadius: '12px', padding: '0.85rem 1rem' },
  msgText: { color: '#f1f5f9', margin: 0, lineHeight: 1.7, whiteSpace: 'pre-wrap', wordBreak: 'break-word' },
  cursor: { display: 'inline-block', animation: 'blink 1s step-end infinite', marginLeft: '2px', color: '#6366f1' },
  sources: { marginTop: '0.75rem', borderTop: '1px solid #334155', paddingTop: '0.75rem' },
  sourcesLabel: { color: '#94a3b8', fontSize: '0.78rem', margin: '0 0 0.5rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' },
  source: { background: '#0f172a', borderRadius: '8px', marginBottom: '0.4rem', overflow: 'hidden' },
  sourceHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem 0.75rem', cursor: 'pointer' },
  sourceTitle: { color: '#6366f1', fontSize: '0.82rem', fontWeight: 500 },
  sourceToggle: { color: '#64748b', fontSize: '0.7rem' },
  sourceText: { color: '#94a3b8', fontSize: '0.82rem', padding: '0 0.75rem 0.75rem', margin: 0, lineHeight: 1.6 },
  inputRow: { display: 'flex', gap: '0.75rem', paddingTop: '1rem', borderTop: '1px solid #1e293b', flexShrink: 0 },
  input: { flex: 1, padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid #334155', background: '#1e293b', color: '#f1f5f9', fontSize: '0.95rem', outline: 'none' },
  sendBtn: { padding: '0.75rem 1.5rem', background: '#6366f1', color: '#fff', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 600, fontSize: '0.95rem', transition: 'opacity 0.15s' },
}
