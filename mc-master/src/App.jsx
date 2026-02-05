import React, { useState, useCallback, useMemo, useEffect, useRef } from 'react'
import { Canvas } from '@react-three/fiber'
import { Scene } from './components/Scene'
import { Header } from './components/Header'
import { ControlPanel } from './components/ControlPanel'
import { StatusIndicator } from './components/StatusIndicator'
import { AudioVisualizer } from './components/AudioVisualizer'
import { ConnectionStatus } from './components/ConnectionStatus'
import { getThemeColors } from './themes'
import { voiceboxApi } from './services/voiceboxApi'

// Avatar states: 'idle' | 'speaking' | 'listening'
function App() {
  const [avatarState, setAvatarState] = useState('idle')
  const [currentTheme, setCurrentTheme] = useState('ruby')
  const [connected, setConnected] = useState(false)
  const [statusMessage, setStatusMessage] = useState('Initializing...')
  const [isPlayingAudio, setIsPlayingAudio] = useState(false)
  const isPlayingAudioRef = useRef(false)
  
  const theme = useMemo(() => getThemeColors(currentTheme), [currentTheme])

  // Connect to VoiceBox backend
  useEffect(() => {
    const connectToBackend = async () => {
      try {
        setStatusMessage('Connecting to VoiceBox...')
        await voiceboxApi.connect()
        setConnected(true)
        setStatusMessage('Connected')
      } catch (error) {
        console.error('Failed to connect:', error)
        setStatusMessage('Connection failed. Retrying...')
      }
    }

    // Set up event listeners
    voiceboxApi.on('state_change', (state) => {
      console.log('State changed to:', state, 'isPlayingAudio:', isPlayingAudioRef.current)
      // Don't switch to idle if audio is currently playing
      // The response handler will set idle after audio completes
      if (state === 'idle' && isPlayingAudioRef.current) {
        console.log('Ignoring idle state change - audio is playing')
        return
      }
      setAvatarState(state)
    })

    voiceboxApi.on('connected', () => {
      setConnected(true)
      setStatusMessage('Connected')
    })

    voiceboxApi.on('disconnected', () => {
      setConnected(false)
      setStatusMessage('Disconnected')
    })

    voiceboxApi.on('error', (error) => {
      console.error('VoiceBox error:', error)
      if (error?.message) {
        setStatusMessage(error.message)
      } else {
        setStatusMessage('Error occurred')
      }
      setAvatarState('idle')
    })

    voiceboxApi.on('status', (status) => {
      console.log('Status update:', status)
      if (status.initialized) {
        setStatusMessage('Ready')
        setAvatarState(status.current_state || 'idle')
      } else {
        setStatusMessage('Initializing...')
      }
    })

    voiceboxApi.on('response', async (data) => {
      console.log('Response received:', data)
      
      if (!data.success) {
        setStatusMessage(data.error || 'Error processing request')
        setAvatarState('idle')
        return
      }
      
      if (data.audio_data) {
        try {
          // Set speaking state during audio playback
          console.log('Starting audio playback, setting speaking state')
          setIsPlayingAudio(true)
          isPlayingAudioRef.current = true
          setAvatarState('speaking')
          setStatusMessage('Speaking...')
          await voiceboxApi.playAudio(data.audio_data)
          // Return to idle after audio finishes
          console.log('Audio playback finished, setting idle state')
          setIsPlayingAudio(false)
          isPlayingAudioRef.current = false
          setAvatarState('idle')
          setStatusMessage('Ready')
        } catch (error) {
          console.error('Failed to play audio:', error)
          setStatusMessage('Audio playback failed')
          setIsPlayingAudio(false)
          isPlayingAudioRef.current = false
          setAvatarState('idle')
        }
      } else {
        // No audio, just show response text
        setAvatarState('idle')
        setStatusMessage('Ready')
      }
    })

    // Connect to backend
    connectToBackend()

    // Cleanup on unmount
    return () => {
      voiceboxApi.disconnect()
    }
  }, [])

  const handleStateChange = useCallback((newState) => {
    setAvatarState(newState)
  }, [])

  const handleThemeChange = useCallback((themeName) => {
    setCurrentTheme(themeName)
  }, [])

  // Handle typing state - switch to listening when user types
  const handleTypingStart = useCallback(() => {
    if (avatarState === 'idle') {
      setAvatarState('listening')
    }
  }, [avatarState])

  const handleTypingEnd = useCallback(() => {
    if (avatarState === 'listening') {
      setAvatarState('idle')
    }
  }, [avatarState])

  const handleTextInput = useCallback(async (text) => {
    if (!voiceboxApi.isConnected()) {
      console.error('Not connected to VoiceBox')
      return
    }
    
    try {
      setAvatarState('listening')
      setStatusMessage('Processing...')
      await voiceboxApi.sendText(text)
    } catch (error) {
      console.error('Failed to send text:', error)
      setStatusMessage('Error sending message')
      setAvatarState('idle')
    }
  }, [])

  const handleVoiceInput = useCallback(async () => {
    if (!voiceboxApi.isConnected()) {
      console.error('Not connected to VoiceBox')
      return
    }
    
    try {
      // Initialize recording if not already done
      if (!voiceboxApi.mediaRecorder) {
        await voiceboxApi.initAudioRecording()
      }
      
      // Start recording
      voiceboxApi.startRecording()
      setAvatarState('listening')
      setStatusMessage('Listening...')
      
      // Stop after 5 seconds
      setTimeout(() => {
        voiceboxApi.stopRecording()
        setStatusMessage('Processing...')
      }, 5000)
      
    } catch (error) {
      console.error('Failed to record audio:', error)
      setStatusMessage('Microphone access denied')
      setAvatarState('idle')
    }
  }, [])

  const dynamicStyles = useMemo(() => ({
    backgroundPattern: {
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundImage: `
        radial-gradient(circle at 25% 25%, ${theme.primary}08 0%, transparent 50%),
        radial-gradient(circle at 75% 75%, ${theme.secondary}08 0%, transparent 50%),
        linear-gradient(${theme.primary}05 1px, transparent 1px),
        linear-gradient(90deg, ${theme.primary}05 1px, transparent 1px)
      `,
      backgroundSize: '100% 100%, 100% 100%, 50px 50px, 50px 50px',
      pointerEvents: 'none',
    },
    cornerTopLeft: {
      top: '20px',
      left: '20px',
      borderTop: `3px solid ${theme.primary}`,
      borderLeft: `3px solid ${theme.secondary}`,
    },
    cornerTopRight: {
      top: '20px',
      right: '20px',
      borderTop: `3px solid ${theme.secondary}`,
      borderRight: `3px solid ${theme.tertiary}`,
    },
    cornerBottomLeft: {
      bottom: '20px',
      left: '20px',
      borderBottom: `3px solid ${theme.tertiary}`,
      borderLeft: `3px solid ${theme.primary}`,
    },
    cornerBottomRight: {
      bottom: '20px',
      right: '20px',
      borderBottom: `3px solid ${theme.primary}`,
      borderRight: `3px solid ${theme.secondary}`,
    },
  }), [theme])

  return (
    <div style={styles.container}>
      {/* Background pattern */}
      <div style={dynamicStyles.backgroundPattern} />
      
      {/* Header */}
      <Header theme={theme} />
      
      {/* Connection Status */}
      <ConnectionStatus 
        connected={connected}
        statusMessage={statusMessage}
        theme={theme}
      />
      
      {/* Main 3D Canvas */}
      <div style={styles.canvasContainer}>
        <Canvas
          camera={{ position: [0, 0, 5], fov: 50 }}
          style={styles.canvas}
        >
          <Scene avatarState={avatarState} theme={theme} />
        </Canvas>
        
        {/* Overlay elements */}
        <StatusIndicator state={avatarState} theme={theme} />
        <AudioVisualizer state={avatarState} theme={theme} />
      </div>
      
      {/* Control Panel */}
      <ControlPanel 
        currentState={avatarState} 
        onStateChange={handleStateChange}
        currentTheme={currentTheme}
        onThemeChange={handleThemeChange}
        theme={theme}
        connected={connected}
        statusMessage={statusMessage}
        onTextInput={handleTextInput}
        onVoiceInput={handleVoiceInput}
        onTypingStart={handleTypingStart}
        onTypingEnd={handleTypingEnd}
      />
      
      {/* Decorative corners */}
      <div style={{ ...styles.corner, ...dynamicStyles.cornerTopLeft }} />
      <div style={{ ...styles.corner, ...dynamicStyles.cornerTopRight }} />
      <div style={{ ...styles.corner, ...dynamicStyles.cornerBottomLeft }} />
      <div style={{ ...styles.corner, ...dynamicStyles.cornerBottomRight }} />
    </div>
  )
}

const styles = {
  container: {
    width: '100%',
    height: '100vh',
    position: 'relative',
    background: 'linear-gradient(135deg, #FAF9F6 0%, #F5F5F0 50%, #FAF9F6 100%)',
    overflow: 'hidden',
  },
  canvasContainer: {
    position: 'absolute',
    top: '80px',
    left: 0,
    right: 0,
    bottom: '100px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  canvas: {
    width: '100%',
    height: '100%',
  },
  corner: {
    position: 'absolute',
    width: '60px',
    height: '60px',
    pointerEvents: 'none',
  },
}

export default App
