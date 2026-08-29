import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function AuthPage() {
  const [mode, setMode] = useState('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login, signup } = useAuth()
  const navigate = useNavigate()

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      if (mode === 'login') await login(email, password)
      else await signup(email, password)
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <h1 style={styles.logo}>DocuQuery</h1>
        <p style={styles.sub}>AI Document Intelligence</p>
        <div style={styles.tabs}>
          <button style={mode === 'login' ? styles.activeTab : styles.tab} onClick={() => setMode('login')}>Login</button>
          <button style={mode === 'signup' ? styles.activeTab : styles.tab} onClick={() => setMode('signup')}>Sign Up</button>
        </div>
        <form onSubmit={submit} style={styles.form}>
          <input style={styles.input} type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} required />
          <input style={styles.input} type="password" placeholder="Password (min 8 chars)" value={password} onChange={e => setPassword(e.target.value)} required minLength={8} />
          {error && <p style={styles.error}>{error}</p>}
          <button style={styles.btn} type="submit" disabled={loading}>
            {loading ? 'Please wait…' : mode === 'login' ? 'Login' : 'Create Account'}
          </button>
        </form>
      </div>
    </div>
  )
}

const styles = {
  page: { minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#0f172a' },
  card: { background: '#1e293b', padding: '2.5rem', borderRadius: '12px', width: '100%', maxWidth: '400px', boxShadow: '0 20px 60px rgba(0,0,0,0.4)' },
  logo: { color: '#6366f1', margin: 0, fontSize: '1.8rem', fontWeight: 700 },
  sub: { color: '#94a3b8', marginTop: '0.25rem', marginBottom: '1.5rem', fontSize: '0.9rem' },
  tabs: { display: 'flex', marginBottom: '1.5rem', borderRadius: '8px', overflow: 'hidden', border: '1px solid #334155' },
  tab: { flex: 1, padding: '0.6rem', background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '0.9rem' },
  activeTab: { flex: 1, padding: '0.6rem', background: '#6366f1', border: 'none', color: '#fff', cursor: 'pointer', fontSize: '0.9rem', fontWeight: 600 },
  form: { display: 'flex', flexDirection: 'column', gap: '0.75rem' },
  input: { padding: '0.75rem', borderRadius: '8px', border: '1px solid #334155', background: '#0f172a', color: '#f1f5f9', fontSize: '0.95rem', outline: 'none' },
  error: { color: '#f87171', fontSize: '0.85rem', margin: 0 },
  btn: { padding: '0.75rem', borderRadius: '8px', background: '#6366f1', color: '#fff', border: 'none', cursor: 'pointer', fontWeight: 600, fontSize: '1rem', marginTop: '0.25rem' },
}
