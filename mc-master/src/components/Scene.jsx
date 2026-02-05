import React, { useRef } from 'react'
import { Environment, Float } from '@react-three/drei'
import { Avatar } from './Avatar'
import { ParticleField } from './ParticleField'

export function Scene({ avatarState, theme }) {
  return (
    <>
      {/* Lighting */}
      <ambientLight intensity={0.6} />
      <directionalLight 
        position={[5, 5, 5]} 
        intensity={0.8} 
        color="#ffffff"
      />
      <pointLight 
        position={[-5, 0, 5]} 
        intensity={0.5} 
        color={theme.primary} 
      />
      <pointLight 
        position={[5, 0, -5]} 
        intensity={0.3} 
        color={theme.offWhite} 
      />
      
      {/* Main Avatar */}
      <Float 
        speed={2} 
        rotationIntensity={0.1} 
        floatIntensity={0.3}
      >
        <Avatar state={avatarState} theme={theme} />
      </Float>
      
      {/* Background particles */}
      <ParticleField count={100} theme={theme} />
      
      {/* Environment */}
      <Environment preset="studio" />
      
      {/* Floor reflection hint */}
      <mesh 
        rotation={[-Math.PI / 2, 0, 0]} 
        position={[0, -2.5, 0]}
        receiveShadow
      >
        <planeGeometry args={[20, 20]} />
        <meshStandardMaterial 
          color="#F5F5F0"
          transparent
          opacity={0.5}
          metalness={0.1}
          roughness={0.8}
        />
      </mesh>
    </>
  )
}
