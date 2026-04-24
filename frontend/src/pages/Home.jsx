import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { listDocuments, createDocument } from '../api'

export default function Home() {
  const [docs, setDocs]       = useState([])
  const [title, setTitle]     = useState('')
  const [username, setUsername] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    listDocuments().then(r => setDocs(r.data)).catch(() => {})
  }, [])

  const handleCreate = async () => {
    if (!title.trim() || !username.trim()) return
    setLoading(true)
    try {
      const r = await createDocument({ title, owner: username })
      localStorage.setItem('username', username)
      navigate(`/doc/${r.data.id}`)
    } finally {
      setLoading(false)
    }
  }

  const handleOpen = (docId) => {
    const user = localStorage.getItem('username') || prompt('Enter your name:')
    if (!user) return
    localStorage.setItem('username', user)
    navigate(`/doc/${docId}`)
  }

  return (
    <div style={{ minHeight: '100vh', background: '#1e1e2e', color: '#cdd6f4' }}>
      <nav style={{ padding: '1rem 2rem', borderBottom: '1px solid #313244' }}>
        <span style={{ color: '#cba6f7', fontWeight: 700, fontSize: '1.2rem' }}>CollabDocs</span>
      </nav>

      <div style={{ maxWidth: 700, margin: '3rem auto', padding: '0 1rem' }}>
        <h1 style={{ color: '#cba6f7', marginBottom: '0.5rem' }}>Real-time Document Editor</h1>
        <p style={{ color: '#a6adc8', marginBottom: '2.5rem' }}>
          Create or open a document. Share the URL with others to collaborate live.
        </p>

        {/* Create new doc */}
        <div style={cardStyle}>
          <h2 style={{ color: '#cdd6f4', marginTop: 0, marginBottom: '1.2rem' }}>New document</h2>
          <input
            placeholder="Your name"
            value={username}
            onChange={e => setUsername(e.target.value)}
            style={{ ...inputStyle, marginBottom: '0.8rem' }}
          />
          <input
            placeholder="Document title"
            value={title}
            onChange={e => setTitle(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleCreate()}
            style={{ ...inputStyle, marginBottom: '1rem' }}
          />
          <button onClick={handleCreate} disabled={loading} style={btnStyle}>
            {loading ? 'Creating...' : 'Create document →'}
          </button>
        </div>

        {/* Existing docs */}
        {docs.length > 0 && (
          <div style={{ marginTop: '2rem' }}>
            <h2 style={{ color: '#cdd6f4', marginBottom: '1rem' }}>Recent documents</h2>
            {docs.map(doc => (
              <div
                key={doc.id}
                onClick={() => handleOpen(doc.id)}
                style={{ ...cardStyle, cursor: 'pointer', marginBottom: '0.8rem' }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontWeight: 600, color: '#cdd6f4' }}>{doc.title}</div>
                    <div style={{ color: '#6c7086', fontSize: '0.85rem', marginTop: '0.2rem' }}>
                      by {doc.owner} · rev {doc.revision}
                    </div>
                  </div>
                  <span style={{ color: '#cba6f7', fontSize: '0.85rem' }}>Open →</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

const cardStyle = {
  background: '#313244', border: '1px solid #45475a',
  borderRadius: 10, padding: '1.5rem'
}
const inputStyle = {
  width: '100%', padding: '0.7rem 1rem',
  background: '#1e1e2e', border: '1px solid #45475a',
  borderRadius: 8, color: '#cdd6f4', fontSize: '1rem',
  boxSizing: 'border-box', display: 'block'
}
const btnStyle = {
  background: '#cba6f7', color: '#1e1e2e',
  border: 'none', borderRadius: 8,
  padding: '0.7rem 1.8rem', fontWeight: 700,
  cursor: 'pointer', fontSize: '1rem'
}