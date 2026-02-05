/**
 * VoiceBox API Service
 * Handles WebSocket communication with the VoiceBox backend
 */

class VoiceBoxAPI {
  constructor() {
    this.ws = null
    this.connected = false
    this.listeners = new Map()
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectDelay = 2000
    this.audioContext = null
    this.mediaRecorder = null
    this.audioChunks = []
  }

  /**
   * Connect to the WebSocket server
   */
  connect(url = 'ws://localhost:8000/ws') {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(url)

        this.ws.onopen = () => {
          console.log('Connected to VoiceBox server')
          this.connected = true
          this.reconnectAttempts = 0
          this.emit('connected')
          resolve()
        }

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            this.handleMessage(data)
          } catch (error) {
            console.error('Error parsing message:', error)
          }
        }

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error)
          this.emit('error', error)
          reject(error)
        }

        this.ws.onclose = () => {
          console.log('Disconnected from VoiceBox server')
          this.connected = false
          this.emit('disconnected')
          this.attemptReconnect()
        }
      } catch (error) {
        console.error('Failed to connect:', error)
        reject(error)
      }
    })
  }

  /**
   * Attempt to reconnect after disconnection
   */
  attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`)
      
      setTimeout(() => {
        this.connect().catch(err => {
          console.error('Reconnection failed:', err)
        })
      }, this.reconnectDelay)
    } else {
      console.error('Max reconnection attempts reached')
      this.emit('reconnect_failed')
    }
  }

  /**
   * Handle incoming messages
   */
  handleMessage(data) {
    const { type, data: payload } = data

    switch (type) {
      case 'state_change':
        this.emit('state_change', payload?.state || data.state)
        break
      
      case 'response':
        this.emit('response', payload)
        break
      
      case 'status':
        this.emit('status', payload)
        break
      
      case 'error':
        this.emit('error', payload)
        break
      
      default:
        console.warn('Unknown message type:', type)
    }
  }

  /**
   * Send text input to the server
   */
  async sendText(text) {
    if (!this.connected) {
      throw new Error('Not connected to server')
    }

    const message = {
      type: 'text_input',
      text: text
    }

    this.ws.send(JSON.stringify(message))
  }

  /**
   * Initialize audio recording
   */
  async initAudioRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 16000
        } 
      })
      
      this.mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm'
      })
      
      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.audioChunks.push(event.data)
        }
      }
      
      this.mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' })
        this.audioChunks = []
        
        // Convert to base64 and send
        const reader = new FileReader()
        reader.onloadend = () => {
          const base64Audio = reader.result.split(',')[1]
          this.sendAudio(base64Audio)
        }
        reader.readAsDataURL(audioBlob)
      }
      
      return true
    } catch (error) {
      console.error('Failed to initialize audio recording:', error)
      throw error
    }
  }

  /**
   * Start recording audio
   */
  startRecording() {
    if (!this.mediaRecorder) {
      throw new Error('Audio recording not initialized')
    }
    
    this.audioChunks = []
    this.mediaRecorder.start()
    this.emit('recording_started')
  }

  /**
   * Stop recording audio
   */
  stopRecording() {
    if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
      this.mediaRecorder.stop()
      this.emit('recording_stopped')
    }
  }

  /**
   * Send audio data to the server
   */
  async sendAudio(audioBase64) {
    if (!this.connected) {
      throw new Error('Not connected to server')
    }

    const message = {
      type: 'audio_input',
      audio: audioBase64
    }

    this.ws.send(JSON.stringify(message))
  }

  /**
   * Request status update
   */
  async getStatus() {
    if (!this.connected) {
      throw new Error('Not connected to server')
    }

    const message = {
      type: 'get_status'
    }

    this.ws.send(JSON.stringify(message))
  }

  /**
   * Manually set state (for testing)
   */
  async setState(state) {
    if (!this.connected) {
      throw new Error('Not connected to server')
    }

    const message = {
      type: 'state_change',
      state: state
    }

    this.ws.send(JSON.stringify(message))
  }

  /**
   * Play audio from base64 data
   */
  async playAudio(base64Audio) {
    try {
      // Convert base64 to blob
      const audioData = atob(base64Audio)
      const arrayBuffer = new ArrayBuffer(audioData.length)
      const view = new Uint8Array(arrayBuffer)
      
      for (let i = 0; i < audioData.length; i++) {
        view[i] = audioData.charCodeAt(i)
      }
      
      const blob = new Blob([arrayBuffer], { type: 'audio/wav' })
      const url = URL.createObjectURL(blob)
      
      const audio = new Audio(url)
      audio.play()
      
      return new Promise((resolve, reject) => {
        audio.onended = () => {
          URL.revokeObjectURL(url)
          resolve()
        }
        audio.onerror = (error) => {
          URL.revokeObjectURL(url)
          reject(error)
        }
      })
    } catch (error) {
      console.error('Failed to play audio:', error)
      throw error
    }
  }

  /**
   * Add event listener
   */
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, [])
    }
    this.listeners.get(event).push(callback)
  }

  /**
   * Remove event listener
   */
  off(event, callback) {
    if (!this.listeners.has(event)) return
    
    const callbacks = this.listeners.get(event)
    const index = callbacks.indexOf(callback)
    if (index > -1) {
      callbacks.splice(index, 1)
    }
  }

  /**
   * Emit event to listeners
   */
  emit(event, data) {
    if (!this.listeners.has(event)) return
    
    const callbacks = this.listeners.get(event)
    callbacks.forEach(callback => {
      try {
        callback(data)
      } catch (error) {
        console.error(`Error in ${event} listener:`, error)
      }
    })
  }

  /**
   * Disconnect from server
   */
  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
      this.connected = false
    }
    
    // Stop recording if active
    if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
      this.mediaRecorder.stop()
    }
  }

  /**
   * Check if connected
   */
  isConnected() {
    return this.connected
  }
}

// Export singleton instance
export const voiceboxApi = new VoiceBoxAPI()
export default voiceboxApi
