export default function Navbar({ title, users }) {
  return (
    <nav style={{
      background: '#1e1e2e',
      padding: '0.8rem 1.5rem',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      borderBottom: '1px solid #313244'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <a href="/" style={{ color: '#cba6f7', fontWeight: 700, textDecoration: 'none', fontSize: '1.1rem' }}>
          CollabDocs
        </a>
        {title && (
          <span style={{ color: '#cdd6f4', fontSize: '0.95rem' }}>/ {title}</span>
        )}
      </div>

      {users && users.length > 0 && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ color: '#a6adc8', fontSize: '0.85rem', marginRight: '0.5rem' }}>
            {users.length} online
          </span>
          {users.map(u => (
            <div
              key={u.user_id}
              title={u.user_id}
              style={{
                width: 28, height: 28,
                borderRadius: '50%',
                background: u.color,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '0.75rem', fontWeight: 700,
                color: '#1e1e2e'
              }}
            >
              {u.user_id[0].toUpperCase()}
            </div>
          ))}
        </div>
      )}
    </nav>
  )
}