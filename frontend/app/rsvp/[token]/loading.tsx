export default function RsvpLoading() {
  return (
    <div
      style={{
        minHeight: '100vh',
        background: 'linear-gradient(to bottom, #080202, #0f0404)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🪔</div>
        <p style={{ color: '#f0b429', fontFamily: 'Georgia, serif', fontSize: '1.125rem' }}>
          Loading your invitation…
        </p>
      </div>
    </div>
  )
}
