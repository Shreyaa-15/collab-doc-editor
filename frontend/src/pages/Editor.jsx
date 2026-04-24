import { useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import Quill from 'quill'
import 'quill/dist/quill.snow.css'
import Navbar from '../components/Navbar'
import { getDocument } from '../api'

export default function Editor() {
  const { id: docId }   = useParams()
  const editorRef       = useRef(null)
  const quillRef        = useRef(null)
  const wsRef           = useRef(null)
  const revisionRef     = useRef(0)
  const suppressRef     = useRef(false)

  const [doc, setDoc]       = useState(null)
  const [users, setUsers]   = useState([])
  const [status, setStatus] = useState('connecting...')
  const [cursors, setCursors] = useState({})

  const username = localStorage.getItem('username') || 'anonymous'

  useEffect(() => {
    if (quillRef.current) return

    getDocument(docId).then(r => setDoc(r.data)).catch(() => {})

    const quill = new Quill(editorRef.current, {
      theme: 'snow',
      placeholder: 'Start typing...',
      modules: {
        toolbar: {
          container: [
            ['bold', 'italic', 'underline'],
            [{ header: [1, 2, 3, false] }],
            ['blockquote', 'code-block'],
            [{ list: 'ordered' }, { list: 'bullet' }],
            ['image'],
            ['clean']
          ],
          handlers: {
            image: () => {
              const input = document.createElement('input')
              input.setAttribute('type', 'file')
              input.setAttribute('accept', 'image/*')
              input.click()
              input.onchange = () => {
                const file = input.files[0]
                if (!file) return
                const reader = new FileReader()
                reader.onload = (e) => {
                  const range = quill.getSelection(true)
                  quill.insertEmbed(range.index, 'image', e.target.result, 'user')
                  quill.setSelection(range.index + 1, 'silent')
                }
                reader.readAsDataURL(file)
              }
            }
          }
        }
      }
    })
    quillRef.current = quill

    const ws = new WebSocket(`ws://localhost:8000/ws/${docId}/${username}`)
    wsRef.current = ws

    ws.onopen = () => setStatus('connected')
    ws.onclose = () => setStatus('disconnected')

    ws.onmessage = (e) => {
      const data = JSON.parse(e.data)

      if (data.type === 'init') {
        suppressRef.current = true
        if (data.delta && data.delta.ops) {
          quill.setContents(data.delta, 'silent')
        }
        suppressRef.current = false
        revisionRef.current = data.revision
        setUsers(data.users || [])
      }

      if (data.type === 'operation') {
        if (data.user_id !== username) {
          suppressRef.current = true
          quill.updateContents(data.delta, 'silent')
          suppressRef.current = false
        }
        revisionRef.current = data.revision
      }

      if (data.type === 'ack') {
        revisionRef.current = data.revision
      }

      if (data.type === 'user_joined' || data.type === 'user_left') {
        setUsers(data.users || [])
      }

      if (data.type === 'cursor') {
        setCursors(prev => ({
          ...prev,
          [data.user_id]: { index: data.index, color: data.color }
        }))
      }
    }

    // Send full delta on every change
    quill.on('text-change', (delta, oldDelta, source) => {
      if (source !== 'user' || suppressRef.current) return
      ws.send(JSON.stringify({
        type: 'operation',
        delta: delta,          // send the Quill delta directly
        revision: revisionRef.current
      }))
    })

    quill.on('selection-change', (range) => {
      if (!range || !ws || ws.readyState !== WebSocket.OPEN) return
      ws.send(JSON.stringify({
        type: 'cursor',
        index: range.index
      }))
    })

    return () => {
      ws.close()
    }
  }, [docId])

  return (
    <div style={{ minHeight: '100vh', background: '#1e1e2e', display: 'flex', flexDirection: 'column' }}>
      <Navbar title={doc?.title} users={users} />

      <div style={{
        padding: '0.3rem 1.5rem',
        background: '#181825',
        borderBottom: '1px solid #313244',
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem'
      }}>
        <div style={{
          width: 8, height: 8, borderRadius: '50%',
          background: status === 'connected' ? '#a6e3a1' : '#f38ba8'
        }}/>
        <span style={{ color: '#6c7086', fontSize: '0.8rem' }}>{status}</span>
        <span style={{ color: '#6c7086', fontSize: '0.8rem', marginLeft: '1rem' }}>
          rev {revisionRef.current}
        </span>
        <span style={{ color: '#6c7086', fontSize: '0.8rem', marginLeft: '1rem' }}>
          editing as <strong style={{ color: '#cba6f7' }}>{username}</strong>
        </span>
      </div>

      {Object.keys(cursors).length > 0 && (
        <div style={{ padding: '0.3rem 1.5rem', background: '#181825', display: 'flex', gap: '1rem' }}>
          {Object.entries(cursors).map(([uid, { color }]) => (
            <span key={uid} style={{ fontSize: '0.8rem', color }}>● {uid} is here</span>
          ))}
        </div>
      )}

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '1.5rem' }}>
        <div style={{
          background: '#313244', borderRadius: 10,
          overflow: 'hidden', flex: 1,
          display: 'flex', flexDirection: 'column'
        }}>
          <div ref={editorRef} style={{ flex: 1, fontSize: '1rem' }} />
        </div>
      </div>

      <style>{`
        .ql-toolbar { background: #45475a !important; border: none !important; border-bottom: 1px solid #585b70 !important; }
        .ql-container { background: #313244 !important; border: none !important; color: #cdd6f4 !important; font-size: 1rem !important; min-height: 500px; }
        .ql-editor { color: #cdd6f4 !important; min-height: 500px; }
        .ql-editor.ql-blank::before { color: #6c7086 !important; }
        .ql-stroke { stroke: #cdd6f4 !important; }
        .ql-fill { fill: #cdd6f4 !important; }
        .ql-picker { color: #cdd6f4 !important; }
        .ql-picker-options { background: #313244 !important; border: 1px solid #45475a !important; }
        .ql-editor img { max-width: 100%; border-radius: 6px; margin: 0.5rem 0; }
      `}</style>
    </div>
  )
}