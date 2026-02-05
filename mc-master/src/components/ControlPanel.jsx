import React, { useState, useRef, useEffect } from 'react'

export function ControlPanel({ 
  currentState, 
  onStateChange, 
  currentTheme, 
  onThemeChange, 
  theme,
  connected,
  statusMessage,
  onTextInput,
  onVoiceInput,
  onTypingStart,
  onTypingEnd
}) {
  const [textInput, setTextInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const typingTimeoutRef = useRef(null)

  // Handle typing detection
  const handleInputChange = (e) => {
    const value = e.target.value
    setTextInput(value)
    
    // If user starts typing, trigger listening state
    if (value.length > 0 && !isTyping) {
      setIsTyping(true)
      if (onTypingStart) onTypingStart()
    }
    
    // Clear existing timeout
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current)
    }
    
    // Set timeout to detect when user stops typing
    if (value.length > 0) {
      typingTimeoutRef.current = setTimeout(() => {
        // User stopped typing but hasn't submitted
        // Keep listening state as they may continue
      }, 1000)
    } else {
      // Input is empty, return to idle
      setIsTyping(false)
      if (onTypingEnd) onTypingEnd()
    }
  }

  // Clean up timeout on unmount
  useEffect(() => {
    return () => {
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current)
      }
    }
  }, [])

  const handleTextSubmit = (e) => {
    e.preventDefault()
    if (textInput.trim() && onTextInput) {
      setIsTyping(false)
      onTextInput(textInput.trim())
      setTextInput('')
    }
  }

  const handleInputBlur = () => {
    // If input loses focus and is empty, return to idle
    if (!textInput.trim()) {
      setIsTyping(false)
      if (onTypingEnd) onTypingEnd()
    }
  }

  const handleVoiceClick = () => {
    if (onVoiceInput) {
      onVoiceInput()
    }
  }

  const states = [
    { id: 'idle', label: 'IDLE', icon: '◯' },
    { id: 'speaking', label: 'SPEAK', icon: '◉' },
    { id: 'listening', label: 'LISTEN', icon: '◎' },
  ]

  const themeOptions = [
    { id: 'ruby', label: 'RUBY', colors: ['#DC2626'] },
    { id: 'spectrum', label: 'SPECTRUM', colors: ['#2563EB', '#DC2626', '#16A34A'] },
  ]
  
  return (
    <div style={styles.container}>
      <div style={{
        ...styles.panel,
        border: `1px solid ${theme.primary}33`,
      }}>
        {/* Connection Status Indicator */}
        <div style={styles.connectionStatus}>
          <div style={{
            ...styles.statusDot,
            backgroundColor: connected ? '#16A34A' : '#DC2626',
            boxShadow: connected ? '0 0 8px #16A34A66' : '0 0 8px #DC262666',
          }} />
          <div style={styles.statusText}>{statusMessage}</div>
        </div>

        {/* Text Input */}
        <form onSubmit={handleTextSubmit} style={styles.inputForm}>
          <input
            type="text"
            value={textInput}
            onChange={handleInputChange}
            onBlur={handleInputBlur}
            placeholder="Type your message..."
            disabled={!connected || currentState === 'speaking'}
            style={{
              ...styles.textInput,
              border: `1px solid ${theme.primary}33`,
              opacity: connected && currentState !== 'speaking' ? 1 : 0.5,
            }}
          />
          <button
            type="submit"
            disabled={!connected || !textInput.trim() || currentState === 'speaking'}
            style={{
              ...styles.sendButton,
              background: theme.primary,
              opacity: (!connected || !textInput.trim() || currentState === 'speaking') ? 0.5 : 1,
            }}
          >
            SEND
          </button>
        </form>

        {/* Voice Input Button */}
        <button
          onClick={handleVoiceClick}
          disabled={!connected}
          style={{
            ...styles.voiceButton,
            background: `${theme.primary}15`,
            border: `2px solid ${theme.primary}`,
            opacity: connected ? 1 : 0.5,
          }}
          title="Hold to record voice (5 seconds)"
        >
          <span style={styles.voiceIcon}>🎤</span>
          <span style={styles.voiceLabel}>VOICE</span>
        </button>

        <div style={{
          ...styles.dividerVertical,
          background: `${theme.primary}33`,
        }} />

        <div style={styles.label}>MODE</div>
        <div style={styles.buttonGroup}>
          {states.map((state) => (
            <button
              key={state.id}
              style={{
                ...styles.button,
                background: `${theme.primary}0D`,
                border: `1px solid ${theme.primary}33`,
                ...(currentState === state.id ? {
                  background: theme.primary,
                  border: `1px solid ${theme.primary}`,
                  boxShadow: `0 0 20px ${theme.primary}66`,
                  color: '#ffffff',
                } : {}),
              }}
              onClick={() => onStateChange(state.id)}
            >
              <span style={styles.buttonIcon}>{state.icon}</span>
              <span style={styles.buttonLabel}>{state.label}</span>
            </button>
          ))}
        </div>

        {/* Theme Switcher */}
        <div style={{
          ...styles.themeSwitcher,
          borderLeft: `1px solid ${theme.primary}33`,
        }}>
          <div style={styles.themeLabel}>THEME</div>
          <div style={styles.themeButtonGroup}>
            {themeOptions.map((t) => (
              <button
                key={t.id}
                style={{
                  ...styles.themeButton,
                  border: currentTheme === t.id 
                    ? `2px solid ${theme.primary}` 
                    : '2px solid transparent',
                  boxShadow: currentTheme === t.id 
                    ? `0 0 10px ${theme.primary}44` 
                    : 'none',
                }}
                onClick={() => onThemeChange(t.id)}
                title={t.label}
              >
                <div style={styles.themeColorPreview}>
                  {t.colors.map((color, i) => (
                    <div
                      key={i}
                      style={{
                        ...styles.themeColorDot,
                        backgroundColor: color,
                      }}
                    />
                  ))}
                </div>
                <span style={styles.themeButtonLabel}>{t.label}</span>
              </button>
            ))}
          </div>
        </div>
        
        <div style={{
          ...styles.info,
          borderLeft: `1px solid ${theme.primary}33`,
        }}>
          <div style={styles.infoRow}>
            <span style={styles.infoLabel}>Current State:</span>
            <span style={{
              ...styles.infoValue,
              color: theme.primary,
            }}>{currentState.toUpperCase()}</span>
          </div>
          <div style={{
            ...styles.divider,
            background: `${theme.primary}1A`,
          }} />
          <div style={styles.hint}>
            {currentState === 'idle' && 'Avatar is in standby mode'}
            {currentState === 'speaking' && 'Avatar is actively speaking'}
            {currentState === 'listening' && 'Avatar is listening for input'}
          </div>
        </div>
      </div>
    </div>
  )
}

const styles = {
  container: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    display: 'flex',
    justifyContent: 'center',
    padding: '20px',
    background: 'linear-gradient(0deg, rgba(250, 249, 246, 0.95) 0%, rgba(250, 249, 246, 0) 100%)',
    zIndex: 100,
  },
  panel: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
    padding: '16px 32px',
    background: 'rgba(250, 249, 246, 0.9)',
    backdropFilter: 'blur(10px)',
    borderRadius: '16px',
    border: '1px solid rgba(220, 38, 38, 0.2)',
    boxShadow: '0 4px 30px rgba(0, 0, 0, 0.05)',
  },
  connectionStatus: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  statusDot: {
    width: '10px',
    height: '10px',
    borderRadius: '50%',
    animation: 'pulse 2s infinite',
  },
  statusText: {
    fontFamily: "'Rajdhani', sans-serif",
    fontSize: '11px',
    color: '#6B7280',
    fontWeight: '500',
  },
  inputForm: {
    display: 'flex',
    gap: '8px',
    alignItems: 'center',
  },
  textInput: {
    fontFamily: "'Rajdhani', sans-serif",
    fontSize: '14px',
    padding: '10px 16px',
    background: 'rgba(250, 249, 246, 0.8)',
    border: '1px solid rgba(220, 38, 38, 0.2)',
    borderRadius: '8px',
    outline: 'none',
    width: '300px',
    transition: 'all 0.3s ease',
  },
  sendButton: {
    fontFamily: "'Orbitron', sans-serif",
    fontSize: '10px',
    fontWeight: '600',
    letterSpacing: '1px',
    padding: '10px 20px',
    background: '#DC2626',
    color: '#ffffff',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    outline: 'none',
  },
  voiceButton: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '4px',
    padding: '12px 20px',
    borderRadius: '12px',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    outline: 'none',
  },
  voiceIcon: {
    fontSize: '20px',
  },
  voiceLabel: {
    fontFamily: "'Orbitron', sans-serif",
    fontSize: '9px',
    fontWeight: '600',
    letterSpacing: '1px',
    color: '#4A4A4A',
  },
  dividerVertical: {
    width: '1px',
    height: '50px',
    background: 'rgba(220, 38, 38, 0.2)',
  },
  label: {
    fontFamily: "'Orbitron', sans-serif",
    fontSize: '11px',
    fontWeight: '600',
    color: '#4A4A4A',
    letterSpacing: '2px',
  },
  buttonGroup: {
    display: 'flex',
    gap: '8px',
  },
  button: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '4px',
    padding: '12px 24px',
    background: 'rgba(220, 38, 38, 0.05)',
    border: '1px solid rgba(220, 38, 38, 0.2)',
    borderRadius: '12px',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    outline: 'none',
  },
  buttonActive: {
    background: '#DC2626',
    border: '1px solid #DC2626',
    boxShadow: '0 0 20px rgba(220, 38, 38, 0.4)',
  },
  buttonIcon: {
    fontSize: '20px',
    color: 'inherit',
  },
  buttonLabel: {
    fontFamily: "'Orbitron', sans-serif",
    fontSize: '10px',
    fontWeight: '600',
    letterSpacing: '1px',
    color: 'inherit',
  },
  themeSwitcher: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
    padding: '0 16px',
  },
  themeLabel: {
    fontFamily: "'Orbitron', sans-serif",
    fontSize: '9px',
    fontWeight: '600',
    color: '#6B7280',
    letterSpacing: '2px',
    textAlign: 'center',
  },
  themeButtonGroup: {
    display: 'flex',
    gap: '6px',
  },
  themeButton: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '4px',
    padding: '8px 12px',
    background: 'rgba(250, 249, 246, 0.8)',
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    outline: 'none',
  },
  themeColorPreview: {
    display: 'flex',
    gap: '3px',
  },
  themeColorDot: {
    width: '10px',
    height: '10px',
    borderRadius: '50%',
  },
  themeButtonLabel: {
    fontFamily: "'Orbitron', sans-serif",
    fontSize: '8px',
    fontWeight: '500',
    letterSpacing: '1px',
    color: '#4A4A4A',
  },
  info: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
    padding: '0 16px',
    minWidth: '180px',
  },
  infoRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  infoLabel: {
    fontFamily: "'Rajdhani', sans-serif",
    fontSize: '12px',
    color: '#4A4A4A',
  },
  infoValue: {
    fontFamily: "'Orbitron', sans-serif",
    fontSize: '12px',
    fontWeight: '600',
    color: '#DC2626',
    letterSpacing: '1px',
  },
  divider: {
    height: '1px',
    background: 'rgba(220, 38, 38, 0.1)',
  },
  hint: {
    fontFamily: "'Rajdhani', sans-serif",
    fontSize: '11px',
    color: '#6B7280',
    fontStyle: 'italic',
  },
}

// Add hover styles via CSS-in-JS workaround
const buttonHoverStyle = document.createElement('style')
buttonHoverStyle.textContent = `
  button:hover {
    background: rgba(220, 38, 38, 0.15) !important;
    transform: translateY(-2px);
  }
  button:active {
    transform: translateY(0);
  }
`
if (typeof document !== 'undefined') {
  document.head.appendChild(buttonHoverStyle)
}
