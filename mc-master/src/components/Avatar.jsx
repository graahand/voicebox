import React, { useRef, useMemo } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'

export function Avatar({ state, theme }) {
  const groupRef = useRef()
  const leftEyeRef = useRef()
  const rightEyeRef = useRef()
  const leftEyelidRef = useRef()
  const rightEyelidRef = useRef()
  const mouthRef = useRef()
  const innerRingRef = useRef()
  const outerRingRef = useRef()
  const pulseRingRef = useRef()
  
  // Animation state refs
  const blinkTimer = useRef(0)
  const blinkState = useRef(1) // 1 = open, 0 = closed
  const speakTimer = useRef(0)
  const listenTimer = useRef(0)
  
  // Fixed colors for Doraemon-style eyes
  const eyeballColor = useMemo(() => new THREE.Color('#DC2626'), []) // Red eyeball
  const eyelidColor = useMemo(() => new THREE.Color('#1A1A1A'), []) // Black eyelid border
  const mouthLineColor = useMemo(() => new THREE.Color('#1A1A1A'), []) // Black mouth line
  
  // Theme-based colors for decorative elements
  const ringColor1 = useMemo(() => new THREE.Color(theme.ringColor1), [theme.ringColor1])
  const ringColor2 = useMemo(() => new THREE.Color(theme.ringColor2), [theme.ringColor2])
  const primaryColor = useMemo(() => new THREE.Color(theme.primary), [theme.primary])
  const offWhite = useMemo(() => new THREE.Color(theme.offWhite), [theme.offWhite])
  
  useFrame((frameState, delta) => {
    const time = frameState.clock.elapsedTime
    
    // === BLINKING ANIMATION ===
    blinkTimer.current += delta
    
    // Random blink every 2-5 seconds
    if (blinkTimer.current > 2 + Math.random() * 3) {
      blinkTimer.current = 0
      // Quick blink animation
      blinkState.current = 0
      setTimeout(() => { blinkState.current = 1 }, 150)
    }
    
    // Apply blink to eyes (scale Y for closing effect)
    if (leftEyeRef.current && rightEyeRef.current) {
      const targetScale = blinkState.current
      leftEyeRef.current.scale.y = THREE.MathUtils.lerp(
        leftEyeRef.current.scale.y,
        targetScale,
        0.3
      )
      rightEyeRef.current.scale.y = THREE.MathUtils.lerp(
        rightEyeRef.current.scale.y,
        targetScale,
        0.3
      )
    }
    
    // Apply blink to eyelids too
    if (leftEyelidRef.current && rightEyelidRef.current) {
      const targetScale = blinkState.current
      leftEyelidRef.current.scale.y = THREE.MathUtils.lerp(
        leftEyelidRef.current.scale.y,
        targetScale,
        0.3
      )
      rightEyelidRef.current.scale.y = THREE.MathUtils.lerp(
        rightEyelidRef.current.scale.y,
        targetScale,
        0.3
      )
    }
    
    // === STATE-BASED ANIMATIONS ===
    if (state === 'speaking') {
      speakTimer.current += delta * 12
      
      // Mouth line animation - more sensitive oscillation for clear trough/peak
      if (mouthRef.current) {
        // Create dramatic wave movement between thin (trough) and thick (peak)
        const wave1 = Math.abs(Math.sin(speakTimer.current)) * 0.4
        const wave2 = Math.abs(Math.sin(speakTimer.current * 2.5)) * 0.25
        const wave3 = Math.abs(Math.sin(speakTimer.current * 4.1)) * 0.15
        const mouthWave = wave1 + wave2 + wave3
        // Scale from 1 (trough/thin) to ~4 (peak/slightly thicker but still a line)
        mouthRef.current.scale.y = 1 + mouthWave * 4
      }
      
      // Energetic ring rotation
      if (innerRingRef.current) {
        innerRingRef.current.rotation.z += delta * 2
      }
      if (outerRingRef.current) {
        outerRingRef.current.rotation.z -= delta * 1.5
      }
      
      // Pulse effect
      if (pulseRingRef.current) {
        const pulse = 1 + Math.sin(time * 6) * 0.1
        pulseRingRef.current.scale.set(pulse, pulse, 1)
        pulseRingRef.current.material.opacity = 0.6
      }
      
    } else if (state === 'listening') {
      listenTimer.current += delta * 3
      
      // Mouth stays as a neutral line when listening
      if (mouthRef.current) {
        mouthRef.current.scale.y = THREE.MathUtils.lerp(
          mouthRef.current.scale.y,
          1.0,
          0.1
        )
      }
      
      // Gentle pulsing rings
      if (innerRingRef.current) {
        innerRingRef.current.rotation.z += delta * 0.8
        const listenPulse = 1 + Math.sin(time * 2) * 0.08
        innerRingRef.current.scale.set(listenPulse, listenPulse, 1)
      }
      if (outerRingRef.current) {
        outerRingRef.current.rotation.z -= delta * 0.5
      }
      
      // Breathing pulse - more prominent when listening
      if (pulseRingRef.current) {
        const breathe = 1 + Math.sin(time * 2) * 0.15
        pulseRingRef.current.scale.set(breathe, breathe, 1)
        pulseRingRef.current.material.opacity = 0.5
      }
      
    } else {
      // IDLE state
      // Mouth returns to neutral thin line
      if (mouthRef.current) {
        mouthRef.current.scale.y = THREE.MathUtils.lerp(
          mouthRef.current.scale.y,
          1.0,
          0.1
        )
      }
      
      // Slow ambient rotation
      if (innerRingRef.current) {
        innerRingRef.current.rotation.z += delta * 0.2
      }
      if (outerRingRef.current) {
        outerRingRef.current.rotation.z -= delta * 0.15
      }
      
      // Subtle idle pulse
      if (pulseRingRef.current) {
        const idlePulse = 1 + Math.sin(time * 0.8) * 0.03
        pulseRingRef.current.scale.set(idlePulse, idlePulse, 1)
        pulseRingRef.current.material.opacity = 0.2
      }
    }
    
    // Subtle head movement
    if (groupRef.current) {
      groupRef.current.rotation.y = Math.sin(time * 0.5) * 0.05
      groupRef.current.rotation.x = Math.sin(time * 0.3) * 0.02
    }
  })
  
  return (
    <group ref={groupRef}>
      {/* Main face circle - Off-white base */}
      <mesh position={[0, 0, 0]}>
        <circleGeometry args={[1.5, 64]} />
        <meshStandardMaterial 
          color={offWhite}
          metalness={0.1}
          roughness={0.3}
        />
      </mesh>
      
      {/* Face border ring */}
      <mesh position={[0, 0, 0.01]}>
        <ringGeometry args={[1.45, 1.55, 64]} />
        <meshStandardMaterial 
          color={primaryColor}
          metalness={0.5}
          roughness={0.2}
        />
      </mesh>
      
      {/* Inner decorative ring */}
      <mesh ref={innerRingRef} position={[0, 0, 0.02]}>
        <ringGeometry args={[1.6, 1.65, 64]} />
        <meshStandardMaterial 
          color={ringColor1}
          metalness={0.3}
          roughness={0.4}
          transparent
          opacity={0.8}
        />
      </mesh>
      
      {/* Outer decorative ring */}
      <mesh ref={outerRingRef} position={[0, 0, 0.02]}>
        <ringGeometry args={[1.75, 1.78, 32]} />
        <meshStandardMaterial 
          color={ringColor2}
          metalness={0.4}
          roughness={0.3}
          transparent
          opacity={0.6}
        />
      </mesh>
      
      {/* Pulse ring for state indication */}
      <mesh ref={pulseRingRef} position={[0, 0, -0.01]}>
        <ringGeometry args={[1.85, 1.95, 64]} />
        <meshBasicMaterial 
          color={state === 'speaking' ? '#DC2626' : state === 'listening' ? '#DC2626' : '#E5E5E5'}
          transparent
          opacity={state === 'idle' ? 0.2 : 0.5}
        />
      </mesh>
      
      {/* ========== LEFT EYE - Doraemon Style ========== */}
      <group position={[-0.45, 0.3, 0.1]}>
        {/* Black eyelid/border - outer ring */}
        <mesh ref={leftEyelidRef}>
          <ringGeometry args={[0.22, 0.3, 32]} />
          <meshStandardMaterial 
            color={eyelidColor}
            metalness={0.3}
            roughness={0.4}
          />
        </mesh>
        {/* White eye background */}
        <mesh position={[0, 0, 0.005]}>
          <circleGeometry args={[0.22, 32]} />
          <meshStandardMaterial 
            color="#FFFFFF"
            metalness={0.1}
            roughness={0.3}
          />
        </mesh>
        {/* Red eyeball/pupil */}
        <mesh ref={leftEyeRef} position={[0, 0, 0.01]}>
          <circleGeometry args={[0.12, 32]} />
          <meshStandardMaterial 
            color={eyeballColor}
            metalness={0.5}
            roughness={0.2}
            emissive={eyeballColor}
            emissiveIntensity={0.4}
          />
        </mesh>
        {/* Eye highlight/reflection */}
        <mesh position={[0.04, 0.04, 0.02]}>
          <circleGeometry args={[0.03, 16]} />
          <meshBasicMaterial color="#ffffff" />
        </mesh>
      </group>
      
      {/* ========== RIGHT EYE - Doraemon Style ========== */}
      <group position={[0.45, 0.3, 0.1]}>
        {/* Black eyelid/border - outer ring */}
        <mesh ref={rightEyelidRef}>
          <ringGeometry args={[0.22, 0.3, 32]} />
          <meshStandardMaterial 
            color={eyelidColor}
            metalness={0.3}
            roughness={0.4}
          />
        </mesh>
        {/* White eye background */}
        <mesh position={[0, 0, 0.005]}>
          <circleGeometry args={[0.22, 32]} />
          <meshStandardMaterial 
            color="#FFFFFF"
            metalness={0.1}
            roughness={0.3}
          />
        </mesh>
        {/* Red eyeball/pupil */}
        <mesh ref={rightEyeRef} position={[0, 0, 0.01]}>
          <circleGeometry args={[0.12, 32]} />
          <meshStandardMaterial 
            color={eyeballColor}
            metalness={0.5}
            roughness={0.2}
            emissive={eyeballColor}
            emissiveIntensity={0.4}
          />
        </mesh>
        {/* Eye highlight/reflection */}
        <mesh position={[0.04, 0.04, 0.02]}>
          <circleGeometry args={[0.03, 16]} />
          <meshBasicMaterial color="#ffffff" />
        </mesh>
      </group>
      
      {/* ========== MOUTH - Single Thin Line ========== */}
      <group position={[0, -0.4, 0.1]}>
        {/* Single thin mouth line */}
        <mesh ref={mouthRef}>
          <planeGeometry args={[0.5, 0.006]} />
          <meshBasicMaterial 
            color={mouthLineColor}
            side={THREE.DoubleSide}
          />
        </mesh>
      </group>
      
      {/* Decorative elements - circuit-like lines */}
      <CircuitLines theme={theme} />
      
      {/* Tech accents */}
      <TechAccents state={state} theme={theme} />
    </group>
  )
}

// Circuit-like decorative lines
function CircuitLines({ theme }) {
  return (
    <group position={[0, 0, 0.03]}>
      {/* Left circuit */}
      <mesh position={[-1.1, 0, 0]} rotation={[0, 0, Math.PI / 4]}>
        <boxGeometry args={[0.02, 0.5, 0.01]} />
        <meshBasicMaterial color={theme.primary} transparent opacity={0.4} />
      </mesh>
      <mesh position={[-1.2, 0.3, 0]}>
        <circleGeometry args={[0.04, 16]} />
        <meshBasicMaterial color={theme.secondary} transparent opacity={0.6} />
      </mesh>
      
      {/* Right circuit */}
      <mesh position={[1.1, 0, 0]} rotation={[0, 0, -Math.PI / 4]}>
        <boxGeometry args={[0.02, 0.5, 0.01]} />
        <meshBasicMaterial color={theme.tertiary} transparent opacity={0.4} />
      </mesh>
      <mesh position={[1.2, 0.3, 0]}>
        <circleGeometry args={[0.04, 16]} />
        <meshBasicMaterial color={theme.primary} transparent opacity={0.6} />
      </mesh>
      
      {/* Top accent */}
      <mesh position={[0, 1.0, 0]}>
        <boxGeometry args={[0.6, 0.02, 0.01]} />
        <meshBasicMaterial color={theme.secondary} transparent opacity={0.3} />
      </mesh>
      
      {/* Bottom accent */}
      <mesh position={[0, -1.0, 0]}>
        <boxGeometry args={[0.4, 0.02, 0.01]} />
        <meshBasicMaterial color={theme.tertiary} transparent opacity={0.3} />
      </mesh>
    </group>
  )
}

// Tech accent dots that respond to state
function TechAccents({ state, theme }) {
  const dotsRef = useRef([])
  
  // Alternate colors for spectrum theme
  const dotColors = [
    theme.primary, theme.secondary,
    theme.tertiary, theme.primary,
    theme.secondary, theme.tertiary,
  ]
  
  useFrame((frameState) => {
    const time = frameState.clock.elapsedTime
    dotsRef.current.forEach((dot, i) => {
      if (dot) {
        const offset = i * 0.5
        let intensity = 0.3
        
        if (state === 'speaking') {
          intensity = 0.5 + Math.sin(time * 8 + offset) * 0.5
        } else if (state === 'listening') {
          intensity = 0.4 + Math.sin(time * 3 + offset) * 0.3
        } else {
          intensity = 0.2 + Math.sin(time * 1 + offset) * 0.1
        }
        
        dot.material.opacity = intensity
      }
    })
  })
  
  const dotPositions = [
    [-0.9, 0.7], [0.9, 0.7],
    [-1.0, -0.5], [1.0, -0.5],
    [-0.7, -0.9], [0.7, -0.9],
  ]
  
  return (
    <group position={[0, 0, 0.04]}>
      {dotPositions.map((pos, i) => (
        <mesh 
          key={i} 
          position={[pos[0], pos[1], 0]}
          ref={el => dotsRef.current[i] = el}
        >
          <circleGeometry args={[0.03, 16]} />
          <meshBasicMaterial 
            color={dotColors[i]} 
            transparent 
            opacity={0.3}
          />
        </mesh>
      ))}
    </group>
  )
}
