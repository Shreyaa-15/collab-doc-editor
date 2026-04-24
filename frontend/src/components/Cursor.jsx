export default function Cursor({ user_id, color }) {
  return (
    <span style={{
      display: 'inline-block',
      borderLeft: `2px solid ${color}`,
      marginLeft: '1px',
      position: 'relative',
      height: '1.2em',
      verticalAlign: 'text-bottom'
    }}>
      <span style={{
        position: 'absolute',
        top: '-1.4em',
        left: 0,
        background: color,
        color: '#1e1e2e',
        fontSize: '0.65rem',
        fontWeight: 700,
        padding: '1px 4px',
        borderRadius: '3px',
        whiteSpace: 'nowrap'
      }}>
        {user_id}
      </span>
    </span>
  )
}