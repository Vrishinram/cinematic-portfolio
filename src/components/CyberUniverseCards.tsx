'use client';

import React, { useRef, useMemo, useState } from 'react';
import { useFrame, useLoader } from '@react-three/fiber';
import { TextureLoader, Vector3, DoubleSide } from 'three';
import { RoundedBox } from '@react-three/drei';
import * as THREE from 'three';

// --------------------------------------------------------------------------
// Tech Stack Configuration & Orbital Coordinate Layout
// Open horseshoe distribution expanded by ~30%, with character exclusion zone
// --------------------------------------------------------------------------
export interface ToolCardConfig {
  name: string;
  title: string;
  icon: string;
  rx: number; // 0..1 reference horizontal position
  ry: number; // 0..1 reference vertical position
  scale: number;
  aspect: number;
}

export const TOOLS_CONFIG: ToolCardConfig[] = [
  // Left Wing (Horseshoe):
  { name: 'wireshark', title: 'Wireshark', icon: '/tools/wireshark.png', rx: 0.22, ry: 0.11, scale: 0.95, aspect: 1.35 },
  { name: 'splunk', title: 'Splunk Enterprise', icon: '/tools/splunk.png', rx: 0.13, ry: 0.36, scale: 1.10, aspect: 0.89 },
  { name: 'nmap', title: 'Nmap Port Scanner', icon: '/tools/nmap.png', rx: 0.26, ry: 0.33, scale: 0.85, aspect: 1.14 },
  { name: 'metasploit', title: 'Metasploit Framework', icon: '/tools/metasploit.png', rx: 0.23, ry: 0.49, scale: 0.82, aspect: 0.99 },
  { name: 'burpsuite', title: 'Burp Suite Pro', icon: '/tools/burpsuite.png', rx: 0.17, ry: 0.65, scale: 0.90, aspect: 0.98 },
  { name: 'docker', title: 'Docker Security Containers', icon: '/tools/docker.png', rx: 0.285, ry: 0.73, scale: 0.85, aspect: 1.02 },

  // Right Wing (Horseshoe - Exactly ONE Claude, ONE ChatGPT):
  { name: 'claude', title: 'Claude 3.5 Sonnet / Red Teaming', icon: '/tools/claude.png', rx: 0.78, ry: 0.14, scale: 1.10, aspect: 0.82 },
  { name: 'langchain', title: 'LangChain AI Agent Defense', icon: '/tools/langchain.png', rx: 0.87, ry: 0.35, scale: 0.90, aspect: 1.04 },
  { name: 'chatgpt', title: 'OpenAI GPT-4o Security Audits', icon: '/tools/chatgpt.png', rx: 0.77, ry: 0.45, scale: 0.90, aspect: 1.25 },
  { name: 'snort', title: 'Snort NIDS', icon: '/tools/snort.png', rx: 0.84, ry: 0.58, scale: 0.92, aspect: 1.75 },
  { name: 'python', title: 'Python Security Automation', icon: '/tools/python.png', rx: 0.71, ry: 0.70, scale: 0.88, aspect: 1.02 },
  { name: 'linux', title: 'Kali Linux OS', icon: '/tools/linux.png', rx: 0.82, ry: 0.77, scale: 0.88, aspect: 1.05 },
];

// Central character silhouette exclusion buffer:
// (x: [-1.2, 1.2], y: [-2, 2.5], z: [-0.5, 0.5])
const EXCLUSION_X = 1.2;
const EXCLUSION_Y_MIN = -2.0;
const EXCLUSION_Y_MAX = 2.5;
const EXCLUSION_Z = 0.5;

function computeOrbitalPosition(rx: number, ry: number, radiusMul = 1.30): [number, number, number] {
  const normX = (rx - 0.5) * 2.0 * radiusMul;
  const normY = -(ry - 0.5) * 2.0 * 1.15;

  // Horseshoe arc coordinates:
  let x = normX * 3.8;
  let y = normY * 2.2;
  // Parabolic horseshoe depth push:
  let z = -0.8 + (1.0 - Math.abs(normX)) * 0.9;

  // Enforce exclusion zone so no card ever penetrates the character silhouette:
  if (Math.abs(x) < EXCLUSION_X && y > EXCLUSION_Y_MIN && y < EXCLUSION_Y_MAX && Math.abs(z) < EXCLUSION_Z) {
    const signX = x >= 0 ? 1 : -1;
    x = signX * (EXCLUSION_X + 0.35);
    z = z - 0.45;
  }

  return [x, y, z];
}

// --------------------------------------------------------------------------
// Individual Floating Glassmorphism Tech Card Component
// --------------------------------------------------------------------------
interface CardItemProps {
  config: ToolCardConfig;
  index: number;
}

function CardItem({ config, index }: CardItemProps) {
  const meshRef = useRef<THREE.Group>(null);
  const [hovered, setHovered] = useState(false);

  // Load tool logo texture
  const texture = useLoader(TextureLoader, config.icon);
  texture.generateMipmaps = true;
  texture.minFilter = THREE.LinearMipmapLinearFilter;

  // Base home position in expanded horseshoe
  const basePos = useMemo(() => computeOrbitalPosition(config.rx, config.ry, 1.32), [config.rx, config.ry]);

  // Per-card unique float phase and speeds
  const phase = useMemo(() => index * 0.55 + 0.3, [index]);
  const speed = useMemo(() => 0.65 + (index % 4) * 0.12, [index]);

  // Card dimensions based on aspect ratio
  const cardW = 1.05 * config.scale;
  const cardH = (1.05 / config.aspect) * config.scale;
  const cardDepth = 0.08;

  useFrame(({ clock }) => {
    if (!meshRef.current) return;
    const t = clock.getElapsedTime() * speed + phase;

    // Subtle natural floating & breathing
    const floatY = Math.sin(t) * 0.045;
    const floatX = Math.cos(t * 0.75) * 0.02;
    const floatRotX = Math.sin(t * 0.6) * 0.025 + (hovered ? 0.08 : 0);
    const floatRotY = Math.cos(t * 0.5) * 0.035 + (hovered ? -0.1 : 0);

    let curX = basePos[0] + floatX;
    let curY = basePos[1] + floatY;
    let curZ = basePos[2] + (hovered ? 0.25 : 0);

    // Enforce exclusion zone during live frame animation
    if (Math.abs(curX) < EXCLUSION_X && curY > EXCLUSION_Y_MIN && curY < EXCLUSION_Y_MAX && Math.abs(curZ) < EXCLUSION_Z) {
      curX = (curX >= 0 ? 1 : -1) * (EXCLUSION_X + 0.35);
      curZ = curZ - 0.45;
    }

    meshRef.current.position.set(curX, curY, curZ);
    meshRef.current.rotation.set(floatRotX, floatRotY, 0);
  });

  return (
    <group
      ref={meshRef}
      onPointerOver={(e) => {
        e.stopPropagation();
        setHovered(true);
        document.body.style.cursor = 'pointer';
      }}
      onPointerOut={() => {
        setHovered(false);
        document.body.style.cursor = 'auto';
      }}
    >
      {/* 
        ========================================================================
        Requirement 1, 3, 4:
        - High-tech Glassmorphism / Dark Acrylic Material
        - transparent: true, opacity: 0.84 (0.80 - 0.88)
        - depthWrite: false (prevents particle & laser ring clipping)
        - emissive: 0xff3b14, emissiveIntensity: 0.15
        - roughness: 0.15, metalness: 0.75
        - RoundedBoxGeometry: radius: 0.08, smoothness: 4
        - renderOrder: 2 (Floating Cards & Foreground Dust)
        ========================================================================
      */}
      <RoundedBox
        args={[cardW, cardH, cardDepth]}
        radius={0.08}
        smoothness={4}
        renderOrder={2}
      >
        <meshPhysicalMaterial
          color="#06070a"
          transparent={true}
          opacity={hovered ? 0.90 : 0.84}
          depthWrite={false}
          roughness={0.15}
          metalness={0.75}
          transmission={0.35}
          ior={1.45}
          reflectivity={0.85}
          emissive="#ff3b14"
          emissiveIntensity={hovered ? 0.30 : 0.15}
          clearcoat={0.9}
          clearcoatRoughness={0.1}
          side={DoubleSide}
        />
      </RoundedBox>

      {/* 1px Neon Edge Outline Accent Strip (Red to Cyan Gradient Glow) */}
      <mesh position={[0, 0, cardDepth * 0.5 + 0.001]} renderOrder={2}>
        <planeGeometry args={[cardW * 0.96, cardH * 0.96]} />
        <meshBasicMaterial
          transparent={true}
          opacity={hovered ? 0.75 : 0.40}
          depthWrite={false}
          color={index % 2 === 0 ? '#ff3b14' : '#00d4ff'}
          wireframe={true}
        />
      </mesh>

      {/* High-Fidelity Tool Logo on Front Acrylic Face */}
      <mesh position={[0, 0, cardDepth * 0.5 + 0.003]} renderOrder={2}>
        <planeGeometry args={[cardW * 0.72, cardH * 0.72]} />
        <meshBasicMaterial
          map={texture}
          transparent={true}
          opacity={hovered ? 1.0 : 0.92}
          depthWrite={false}
        />
      </mesh>
    </group>
  );
}

// --------------------------------------------------------------------------
// Main Orbital Tech Cube System Component for Scene 02 (#universe)
// --------------------------------------------------------------------------
export default function CyberUniverseCards() {
  return (
    <group renderOrder={2}>
      {TOOLS_CONFIG.map((cfg, idx) => (
        <CardItem key={cfg.name} config={cfg} index={idx} />
      ))}
    </group>
  );
}
