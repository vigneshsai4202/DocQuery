import { NavLink, Outlet } from 'react-router-dom'

const NAV = [
  { to: '/', label: '💬 Chat', end: true },
  { to: '/documents', label: '📄 Documents' },
  { to: '/history', label: '🕑 History' },
]

export default function Layout() {
  return (
    <div style={styles.shell}>
      <aside style={styles.sidebar}>
        <div style={styles.brand}>DocuQuery</div>
        <nav style={styles.nav}>
          {NAV.map(n => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.end}
              style={({ isActive }) => ({ ...styles.link, ...(isActive ? styles.activeLink : {}) })}
            >
              {n.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main style={styles.main}>
        <Outlet />
      </main>
    </div>
  )
}

const styles = {
  shell: { display: 'flex', height: '100vh', background: '#0f172a', fontFamily: 'system-ui, sans-serif' },
  sidebar: { width: '220px', background: '#1e293b', display: 'flex', flexDirection: 'column', padding: '1.5rem 1rem', flexShrink: 0 },
  brand: { color: '#6366f1', fontWeight: 700, fontSize: '1.3rem', marginBottom: '2rem', paddingLeft: '0.5rem' },
  nav: { display: 'flex', flexDirection: 'column', gap: '0.25rem', flex: 1 },
  link: { display: 'block', padding: '0.6rem 0.75rem', borderRadius: '8px', color: '#94a3b8', textDecoration: 'none', fontSize: '0.9rem', transition: 'background 0.15s' },
  activeLink: { background: '#334155', color: '#f1f5f9', fontWeight: 500 },
  logoutBtn: { background: 'transparent', border: '1px solid #334155', color: '#64748b', borderRadius: '8px', padding: '0.5rem', cursor: 'pointer', fontSize: '0.85rem' },
  main: { flex: 1, overflowY: 'auto' },
}
