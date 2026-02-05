import React, { useEffect, useRef } from 'react'

export function AudioVisualizer({ state, theme }) {
  const barsRef = useRef([])
  const animationRef = useRef(null)
  
  useEffect(() => {
    const animate = () => {
      barsRef.current.forEach((bar, index) => {
        if (bar) {
          let height
          const time = Date.now() / 1000
          const offset = index * 0.3
          
          if (state === 'speaking') {
            // Active waveform for speaking
            height = 20 + Math.sin(time * 10 + offset) * 15 + 
                    Math.sin(time * 15 + offset * 2) * 10
          } else if (state === 'listening') {
            // Subtle pulsing for listening
            height = 15 + Math.sin(time * 4 + offset) * 8
          } else {
            // Minimal movement for idle
            height = 8 + Math.sin(time * 2 + offset) * 3
          }
          
          bar.style.height = `${Math.max(4, height)}px`
        }
      })
      
      animationRef.current = requestAnimationFrame(animate)
    }
    
    animate()
    
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }
  }, [state])
  
  const barCount = 12
  
  // Get bar color based on state
  const getBarColor = (index) => {
    if (state === 'idle') return '#D1D5DB'
    if (state === 'speaking') return theme.mouthColor
    if (state === 'listening') return theme.eyeColor
    return theme.primary
  }
  
  return (
    <div style={styles.container}>
      <div style={{
        ...styles.visualizer,
        border: `1px solid ${theme.primary}33`,
      }}>
        {Array.from({ length: barCount }).map((_, index) => (
          <div
            key={index}
            ref={(el) => (barsRef.current[index] = el)}
            style={{
              ...styles.bar,
              backgroundColor: getBarColor(index),
              opacity: state === 'idle' ? 0.5 : 0.8,
            }}
          />
        ))}
      </div>
      
      <div style={styles.labelContainer}>
        <span style={styles.label}>AUDIO</span>
        <span 
          style={{
            ...styles.status,
            color: state === 'idle' ? '#9CA3AF' : theme.primary,
          }}
        >
          {state === 'speaking' ? 'OUTPUT' : state === 'listening' ? 'INPUT' : 'STANDBY'}
        </span>
      </div>
    </div>
  )
}

const styles = {
  container: {
    position: 'absolute',
    top: '100px',
    right: '40px',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'flex-end',
    gap: '8px',
    zIndex: 50,
  },
  visualizer: {
    display: 'flex',
    alignItems: 'center',
    gap: '3px',
    padding: '12px 16px',
    background: 'rgba(250, 249, 246, 0.9)',
    backdropFilter: 'blur(10px)',
    borderRadius: '8px',
    boxShadow: '0 2px 10px rgba(0, 0, 0, 0.05)',
    height: '60px',
  },
  bar: {
    width: '4px',
    borderRadius: '2px',
    transition: 'background-color 0.3s ease',
  },
  labelContainer: {
    display: 'flex',
    gap: '8px',
    alignItems: 'center',
  },
  label: {
    fontFamily: "'Orbitron', sans-serif",
    fontSize: '10px',
    fontWeight: '500',
    color: '#9CA3AF',
    letterSpacing: '2px',
  },
  status: {
    fontFamily: "'Orbitron', sans-serif",
    fontSize: '10px',
    fontWeight: '600',
    letterSpacing: '1px',
  },
}
