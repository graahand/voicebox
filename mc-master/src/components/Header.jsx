import React from 'react'

export function Header({ theme }) {
  return (
    <header style={styles.header}>
      <div style={styles.logoContainer}>
        <div style={{
          ...styles.logoIcon,
          background: `${theme.primary}1A`,
          border: `1px solid ${theme.primary}33`,
        }}>
          <svg 
            width="32" 
            height="32" 
            viewBox="0 0 32 32" 
            fill="none"
          >
            <circle cx="16" cy="16" r="14" stroke={theme.primary} strokeWidth="2" fill="none" />
            <circle cx="16" cy="16" r="10" stroke={theme.secondary} strokeWidth="1" fill="none" opacity="0.5" />
            <circle cx="11" cy="13" r="2" fill={theme.eyeColor} />
            <circle cx="21" cy="13" r="2" fill={theme.eyeColor} />
            <path d="M12 20 Q16 23 20 20" stroke={theme.mouthColor} strokeWidth="2" fill="none" strokeLinecap="round" />
          </svg>
        </div>
        <div style={styles.logoText}>
          <span style={{
            ...styles.logoTitle,
            color: theme.primary,
          }}>MC ICK</span>
          <span style={styles.logoSubtitle}>AI Host System</span>
        </div>
      </div>
      
      <div style={{
        ...styles.statusContainer,
        background: `${theme.primary}0D`,
        border: `1px solid ${theme.primary}33`,
      }}>
        <div style={styles.statusDot} />
        <span style={styles.statusText}>SYSTEM ACTIVE</span>
      </div>
    </header>
  )
}

const styles = {
  header: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: '80px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '0 40px',
    background: 'linear-gradient(180deg, rgba(250, 249, 246, 0.95) 0%, rgba(250, 249, 246, 0) 100%)',
    zIndex: 100,
  },
  logoContainer: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  logoIcon: {
    width: '48px',
    height: '48px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: '12px',
  },
  logoText: {
    display: 'flex',
    flexDirection: 'column',
  },
  logoTitle: {
    fontFamily: "'Orbitron', sans-serif",
    fontSize: '24px',
    fontWeight: '700',
    letterSpacing: '2px',
  },
  logoSubtitle: {
    fontFamily: "'Rajdhani', sans-serif",
    fontSize: '12px',
    fontWeight: '500',
    color: '#4A4A4A',
    letterSpacing: '3px',
    textTransform: 'uppercase',
  },
  statusContainer: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '8px 16px',
    borderRadius: '20px',
  },
  statusDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    background: '#22C55E',
    boxShadow: '0 0 10px #22C55E',
    animation: 'pulse 2s ease-in-out infinite',
  },
  statusText: {
    fontFamily: "'Orbitron', sans-serif",
    fontSize: '11px',
    fontWeight: '500',
    color: '#4A4A4A',
    letterSpacing: '2px',
  },
}
