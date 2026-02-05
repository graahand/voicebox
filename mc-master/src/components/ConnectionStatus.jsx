import React from 'react'

export function ConnectionStatus({ connected, statusMessage, theme }) {
  return (
    <div style={{
      ...styles.container,
      border: `1px solid ${theme.primary}33`,
    }}>
      <div style={styles.statusRow}>
        <div style={{
          ...styles.indicator,
          backgroundColor: connected ? '#16A34A' : '#DC2626',
          boxShadow: connected 
            ? '0 0 10px #16A34A66, 0 0 20px #16A34A33' 
            : '0 0 10px #DC262666, 0 0 20px #DC262633',
        }} />
        <div style={styles.textContainer}>
          <div style={styles.label}>CONNECTION STATUS</div>
          <div style={{
            ...styles.status,
            color: connected ? '#16A34A' : '#DC2626',
          }}>
            {connected ? 'CONNECTED' : 'DISCONNECTED'}
          </div>
        </div>
      </div>
      {statusMessage && (
        <div style={styles.message}>
          {statusMessage}
        </div>
      )}
    </div>
  )
}

const styles = {
  container: {
    position: 'absolute',
    top: '100px',
    right: '30px',
    padding: '16px 20px',
    background: 'rgba(250, 249, 246, 0.95)',
    backdropFilter: 'blur(10px)',
    borderRadius: '12px',
    border: '1px solid rgba(220, 38, 38, 0.2)',
    boxShadow: '0 4px 20px rgba(0, 0, 0, 0.05)',
    zIndex: 50,
    minWidth: '200px',
  },
  statusRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  indicator: {
    width: '12px',
    height: '12px',
    borderRadius: '50%',
    animation: 'pulse 2s infinite',
  },
  textContainer: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  label: {
    fontFamily: "'Orbitron', sans-serif",
    fontSize: '9px',
    fontWeight: '600',
    color: '#9CA3AF',
    letterSpacing: '1.5px',
  },
  status: {
    fontFamily: "'Orbitron', sans-serif",
    fontSize: '13px',
    fontWeight: '700',
    letterSpacing: '1px',
  },
  message: {
    marginTop: '12px',
    paddingTop: '12px',
    borderTop: '1px solid rgba(220, 38, 38, 0.1)',
    fontFamily: "'Rajdhani', sans-serif",
    fontSize: '12px',
    color: '#6B7280',
    lineHeight: '1.4',
  },
}

// Add CSS animation
const style = document.createElement('style')
style.textContent = `
  @keyframes pulse {
    0%, 100% {
      opacity: 1;
      transform: scale(1);
    }
    50% {
      opacity: 0.7;
      transform: scale(1.1);
    }
  }
`
if (typeof document !== 'undefined' && !document.getElementById('connection-status-animation')) {
  style.id = 'connection-status-animation'
  document.head.appendChild(style)
}
