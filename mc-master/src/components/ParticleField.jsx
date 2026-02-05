import React, { useRef, useMemo } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'

export function ParticleField({ count = 100, theme }) {
  const meshRef = useRef()
  
  // Generate random positions for particles
  const particles = useMemo(() => {
    const positions = new Float32Array(count * 3)
    const scales = new Float32Array(count)
    
    for (let i = 0; i < count; i++) {
      // Spread particles in a sphere around the avatar
      const theta = Math.random() * Math.PI * 2
      const phi = Math.acos(2 * Math.random() - 1)
      const radius = 3 + Math.random() * 4
      
      positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta)
      positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta)
      positions[i * 3 + 2] = radius * Math.cos(phi) - 2 // Offset back
      
      scales[i] = Math.random() * 0.5 + 0.5
    }
    
    return { positions, scales }
  }, [count])
  
  // Create geometry with positions
  const geometry = useMemo(() => {
    const geo = new THREE.BufferGeometry()
    geo.setAttribute('position', new THREE.BufferAttribute(particles.positions, 3))
    geo.setAttribute('scale', new THREE.BufferAttribute(particles.scales, 1))
    return geo
  }, [particles])
  
  useFrame((state) => {
    const time = state.clock.elapsedTime
    
    if (meshRef.current) {
      // Slow rotation of entire particle field
      meshRef.current.rotation.y = time * 0.05
      meshRef.current.rotation.x = Math.sin(time * 0.1) * 0.1
    }
  })
  
  return (
    <points ref={meshRef} geometry={geometry}>
      <pointsMaterial
        size={0.03}
        color={theme.primary}
        transparent
        opacity={0.6}
        sizeAttenuation
        blending={THREE.AdditiveBlending}
      />
    </points>
  )
}
