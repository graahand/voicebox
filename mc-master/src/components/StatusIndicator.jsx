import React from 'react'

export function StatusIndicator({ state, theme }) {
  const getStateConfig = () => {
    switch (state) {
      case 'speaking':
        return {
          label: 'SPEAKING',
          color: theme.mouthColor,
          icon: '🎙️',
          pulseSpeed: '0.5s',
        }
      case 'listening':
        return {
          label: 'LISTENING',
          color: theme.eyeColor,
          icon: '👂',
          pulseSpeed: '1s',
        }
      default:
        return {
          label: 'IDLE',
          color: '#9CA3AF',
          icon: '💤',
          pulseSpeed: '2s',
        }
    }
  }
  
  const config = getStateConfig()
  
  return (
    <div style={styles.container}>
      <div 
        style={{
          ...styles.indicator,
          borderColor: config.color,
        }}
      >
        <div 
          style={{
            ...styles.pulse,
            backgroundColor: config.color,
            animation: `pulse ${config.pulseSpeed} ease-in-out infinite`,
          }}
        />
        <span style={styles.icon}>{config.icon}</span>
        <span 
          style={{
            ...styles.label,
            color: config.color,
          }}
        >
          {config.label}
        </span>
      </div>
      
      {/* Decorative lines */}
      <div style={styles.lines}>
        <div 
          style={{
            ...styles.line,
            backgroundColor: config.color,
            opacity: state !== 'idle' ? 0.6 : 0.2,
          }}
        />
        <div 
          style={{
            ...styles.line,
            ...styles.lineShort,
            backgroundColor: config.color,
            opacity: state !== 'idle' ? 0.4 : 0.1,
          }}
        />
      </div>
    </div>
  )
}

const styles = {
  container: {
    position: 'absolute',
    top: '100px',
    left: '40px',
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
    zIndex: 50,
  },
  indicator: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: '10px 16px',
    background: 'rgba(250, 249, 246, 0.9)',
    backdropFilter: 'blur(10px)',
    borderRadius: '8px',
    border: '1px solid',
    boxShadow: '0 2px 10px rgba(0, 0, 0, 0.05)',
  },
  pulse: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
  },
  icon: {
    fontSize: '16px',
  },
  label: {
    fontFamily: "'Orbitron', sans-serif",
    fontSize: '11px',
    fontWeight: '600',
    letterSpacing: '2px',
  },
  lines: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
    paddingLeft: '8px',
  },
  line: {
    height: '2px',
    width: '60px',
    borderRadius: '1px',
    transition: 'all 0.3s ease',
  },
  lineShort: {
    width: '40px',
  },
}
