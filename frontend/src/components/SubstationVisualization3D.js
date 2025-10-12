import React, { useRef, useState, useEffect, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Text, Box, Sphere, Cylinder, Cone, Ring, Line } from '@react-three/drei';
import * as THREE from 'three';
import axios from 'axios';
import styled from 'styled-components';
import { motion } from 'framer-motion';

const Container = styled.div`
  width: 100%;
  height: 700px;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  border-radius: 12px;
  box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
  overflow: hidden;
  position: relative;
`;



// Enhanced 3D Components

const PowerTransformer = ({ position, id, data = {} }) => {
  const meshRef = useRef();
  const [hovered, setHovered] = useState(false);

  useFrame((state) => {
    if (meshRef.current && data.loading > 80) {
      // Vibration effect for high load
      meshRef.current.position.x = position[0] + Math.sin(state.clock.elapsedTime * 10) * 0.01;
    }
  });

  const loading = data.loading || 75;
  const temperature = data.temperature || 65;
  const color = temperature > 85 ? '#ff0000' : temperature > 75 ? '#ff9900' : '#00ff00';

  return (
    <group position={position}>
      {/* Main transformer tank */}
      <Box
        ref={meshRef}
        args={[3, 4, 2.5]}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
      >
        <meshStandardMaterial
          color={hovered ? '#5a67d8' : '#4a5568'}
          metalness={0.6}
          roughness={0.4}
        />
      </Box>

      {/* HV Bushings (400kV) */}
      {[-1, 0, 1].map((x, i) => (
        <group key={`hv-${i}`} position={[x, 2.5, 0]}>
          <Cylinder args={[0.15, 0.1, 1.5, 16]}>
            <meshStandardMaterial color="#8b4513" />
          </Cylinder>
          <Sphere args={[0.2]} position={[0, 0.8, 0]}>
            <meshStandardMaterial color="#ffd700" metalness={0.8} />
          </Sphere>
        </group>
      ))}

      {/* LV Bushings (220kV) */}
      {[-0.8, 0, 0.8].map((x, i) => (
        <group key={`lv-${i}`} position={[x, -2.5, 0]}>
          <Cylinder args={[0.12, 0.08, 1.2, 16]}>
            <meshStandardMaterial color="#8b4513" />
          </Cylinder>
          <Sphere args={[0.15]} position={[0, -0.7, 0]}>
            <meshStandardMaterial color="#87ceeb" metalness={0.8} />
          </Sphere>
        </group>
      ))}

      {/* Radiator fins */}
      {[-2, -1, 1, 2].map((z, i) => (
        <Box key={`rad-${i}`} args={[0.1, 3, 0.8]} position={[2, 0, z * 0.5]}>
          <meshStandardMaterial color="#2d3748" />
        </Box>
      ))}

      {/* Oil conservator */}
      <Cylinder args={[0.6, 0.6, 2, 16]} position={[0, 3, 0]} rotation={[0, 0, Math.PI / 2]}>
        <meshStandardMaterial color="#4a5568" />
      </Cylinder>

      {/* Temperature indicator */}
      <Box args={[0.2, temperature / 200, 0.2]} position={[-1.8, -1, 1.3]}>
        <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.5} />
      </Box>

      {/* Label */}
      <Text position={[0, 4, 0]} fontSize={0.4} color="white" anchorX="center">
        {id}: 315 MVA
      </Text>
      <Text position={[0, 3.5, 0]} fontSize={0.3} color="#94a3b8" anchorX="center">
        {loading.toFixed(1)}% Load | {temperature}°C
      </Text>
    </group>
  );
};

const CircuitBreaker = ({ position, id, isOpen = false, voltage = 400 }) => {
  const [localOpen, setLocalOpen] = useState(isOpen);

  const handleClick = () => {
    setLocalOpen(!localOpen);
    // API call would go here
  };

  const color = voltage === 400 ? '#ff6b6b' : '#4ecdc4';

  return (
    <group position={position} onClick={handleClick}>
      {/* SF6 Chamber */}
      <Cylinder args={[0.5, 0.5, 1.5, 16]}>
        <meshStandardMaterial color="#666666" metalness={0.7} />
      </Cylinder>

      {/* Interrupting chamber */}
      <Box args={[0.8, 0.3, 0.3]} position={[0, 0, 0]}>
        <meshStandardMaterial color={localOpen ? '#ff4444' : '#44ff44'} />
      </Box>

      {/* Fixed contacts */}
      <Cylinder args={[0.1, 0.1, 0.5, 8]} position={[-0.5, 0, 0]} rotation={[0, 0, Math.PI / 2]}>
        <meshStandardMaterial color="#copper" metalness={0.9} />
      </Cylinder>
      <Cylinder args={[0.1, 0.1, 0.5, 8]} position={[0.5, 0, 0]} rotation={[0, 0, Math.PI / 2]}>
        <meshStandardMaterial color="#copper" metalness={0.9} />
      </Cylinder>

      {/* Moving contact */}
      <Box
        args={[0.6, 0.1, 0.1]}
        position={[0, localOpen ? 0.3 : 0, 0]}
        rotation={[0, 0, localOpen ? Math.PI / 8 : 0]}
      >
        <meshStandardMaterial color="#ffd700" metalness={0.9} />
      </Box>

      {/* Status indicator */}
      <Sphere args={[0.1]} position={[0, 1, 0]}>
        <meshStandardMaterial
          color={localOpen ? '#ff0000' : '#00ff00'}
          emissive={localOpen ? '#ff0000' : '#00ff00'}
          emissiveIntensity={0.5}
        />
      </Sphere>

      <Text position={[0, 1.5, 0]} fontSize={0.25} color="white" anchorX="center">
        {id}
      </Text>
    </group>
  );
};

const CurrentTransformer = ({ position, id }) => {
  return (
    <group position={position}>
      {/* CT toroid */}
      <Ring args={[0.4, 0.6, 16, 8]}>
        <meshStandardMaterial color="#ff9800" />
      </Ring>

      {/* Secondary terminals */}
      <Box args={[0.15, 0.3, 0.1]} position={[0, -0.5, 0]}>
        <meshStandardMaterial color="#333333" />
      </Box>

      <Text position={[0, 0.8, 0]} fontSize={0.2} color="#94a3b8" anchorX="center">
        {id}
      </Text>
    </group>
  );
};

const CVT = ({ position, id }) => {
  return (
    <group position={position}>
      {/* Capacitor stack */}
      {[0, 0.3, 0.6].map((y, i) => (
        <Cylinder key={i} args={[0.25, 0.25, 0.25, 16]} position={[0, y, 0]}>
          <meshStandardMaterial color="#00bcd4" />
        </Cylinder>
      ))}

      {/* Electromagnetic unit */}
      <Box args={[0.3, 0.4, 0.3]} position={[0, -0.4, 0]}>
        <meshStandardMaterial color="#666666" />
      </Box>

      <Text position={[0, 1, 0]} fontSize={0.2} color="#94a3b8" anchorX="center">
        {id}
      </Text>
    </group>
  );
};

const LightningArrester = ({ position, id }) => {
  return (
    <group position={position}>
      {/* Arrester stack */}
      {[0, 0.5, 1, 1.5].map((y, i) => (
        <Cylinder key={i} args={[0.15, 0.15, 0.4, 8]} position={[0, y, 0]}>
          <meshStandardMaterial color="#ffeb3b" />
        </Cylinder>
      ))}

      {/* Ground connection */}
      <Box args={[0.05, 2, 0.05]} position={[0.2, -1, 0]}>
        <meshStandardMaterial color="#8b4513" />
      </Box>

      <Text position={[0, 2, 0]} fontSize={0.2} color="#94a3b8" anchorX="center">
        {id}
      </Text>
    </group>
  );
};

const Isolator = ({ position, id, isOpen = false }) => {
  const [localOpen, setLocalOpen] = useState(isOpen);

  return (
    <group position={position} onClick={() => setLocalOpen(!localOpen)}>
      {/* Base insulators */}
      <Cylinder args={[0.1, 0.1, 0.8, 8]} position={[-0.4, 0, 0]}>
        <meshStandardMaterial color="#8b4513" />
      </Cylinder>
      <Cylinder args={[0.1, 0.1, 0.8, 8]} position={[0.4, 0, 0]}>
        <meshStandardMaterial color="#8b4513" />
      </Cylinder>

      {/* Blade */}
      <Box
        args={[0.8, 0.05, 0.1]}
        position={[localOpen ? -0.2 : 0, 0.4, 0]}
        rotation={[0, 0, localOpen ? Math.PI / 4 : 0]}
      >
        <meshStandardMaterial color="#9c27b0" metalness={0.8} />
      </Box>

      <Text position={[0, 1, 0]} fontSize={0.2} color="#94a3b8" anchorX="center">
        {id}
      </Text>
    </group>
  );
};

const Busbar = ({ position, voltage, length = 15 }) => {
  const color = voltage === 400 ? '#ffd700' : '#87ceeb';

  return (
    <group position={position}>
      {/* Main bus conductor */}
      <Box args={[length, 0.4, 0.4]}>
        <meshStandardMaterial color={color} metalness={0.8} roughness={0.2} />
      </Box>

      {/* Support insulators */}
      {[-6, -3, 0, 3, 6].map((x, i) => (
        <Cylinder key={i} args={[0.15, 0.15, 1, 8]} position={[x, -0.7, 0]}>
          <meshStandardMaterial color="#8b4513" />
        </Cylinder>
      ))}

      <Text position={[0, 0.8, 0]} fontSize={0.4} color="white" anchorX="center">
        {voltage} kV Bus
      </Text>
    </group>
  );
};

const ShuntReactor = ({ position, id, rating }) => {
  return (
    <group position={position}>
      {/* Reactor tank */}
      <Cylinder args={[1.2, 1.2, 3, 16]}>
        <meshStandardMaterial color="#8bc34a" />
      </Cylinder>

      {/* Bushings */}
      {[0, 1.2, -1.2].map((angle, i) => (
        <group key={i} position={[Math.cos(angle) * 0.8, 1.8, Math.sin(angle) * 0.8]}>
          <Cylinder args={[0.1, 0.08, 0.8, 8]}>
            <meshStandardMaterial color="#8b4513" />
          </Cylinder>
        </group>
      ))}

      {/* Cooling fins */}
      {[0, 90, 180, 270].map((angle, i) => (
        <Box key={i} args={[0.1, 2.5, 0.6]}
          position={[Math.cos(angle * Math.PI / 180) * 1.4, 0, Math.sin(angle * Math.PI / 180) * 1.4]}>
          <meshStandardMaterial color="#666666" />
        </Box>
      ))}

      <Text position={[0, 2.5, 0]} fontSize={0.3} color="white" anchorX="center">
        {id}: {rating}
      </Text>
    </group>
  );
};

const CapacitorBank = ({ position, id, capacity }) => {
  return (
    <group position={position}>
      {/* Capacitor units in rack formation */}
      {[0, 1, 2].map((row) =>
        [0, 1, 2].map((col) => (
          <Cylinder
            key={`${row}-${col}`}
            args={[0.25, 0.25, 0.8, 16]}
            position={[col * 0.6 - 0.6, row * 0.9 - 0.9, 0]}
          >
            <meshStandardMaterial color="#00e676" />
          </Cylinder>
        ))
      )}

      {/* Frame */}
      <Box args={[2, 0.1, 1]} position={[0, -1.5, 0]}>
        <meshStandardMaterial color="#333333" />
      </Box>

      {/* Fence */}
      {[-1, 1].map((x) => (
        <Box key={x} args={[0.05, 2, 1]} position={[x, 0, 0]}>
          <meshStandardMaterial color="#666666" opacity={0.5} transparent />
        </Box>
      ))}

      <Text position={[0, 1.5, 0]} fontSize={0.3} color="white" anchorX="center">
        {id}: {capacity} MVAR
      </Text>
    </group>
  );
};

const WaveTrap = ({ position, id }) => {
  return (
    <group position={position}>
      {/* Inductor coil */}
      <Cylinder args={[0.3, 0.3, 1, 16]}>
        <meshStandardMaterial color="#e91e63" />
      </Cylinder>

      {/* Tuning capacitor */}
      <Box args={[0.4, 0.2, 0.4]} position={[0, 0.7, 0]}>
        <meshStandardMaterial color="#666666" />
      </Box>

      <Text position={[0, 1.2, 0]} fontSize={0.2} color="#94a3b8" anchorX="center">
        {id}
      </Text>
    </group>
  );
};

const PowerFlowLine = ({ start, end, voltage, power, color }) => {
  const particleRef = useRef();
  const [progress, setProgress] = useState(0);

  useFrame((state, delta) => {
    setProgress((prev) => {
      const newProgress = prev + delta * 0.3; // Animation speed
      return newProgress > 1 ? 0 : newProgress;
    });
  });

  // Calculate particle position along the path
  const particlePosition = useMemo(() => {
    return [
      start[0] + (end[0] - start[0]) * progress,
      start[1] + (end[1] - start[1]) * progress,
      start[2] + (end[2] - start[2]) * progress,
    ];
  }, [start, end, progress]);

  const lineColor = color || (voltage === 400 ? '#FFEB3B' : '#4FC3F7');
  const particleColor = voltage === 400 ? '#FFC107' : '#00BCD4';

  return (
    <group>
      {/* Power flow line */}
      <Line
        points={[start, end]}
        color={lineColor}
        lineWidth={2}
        opacity={0.6}
        transparent
      />

      {/* Animated particle showing direction */}
      <Sphere ref={particleRef} args={[0.15]} position={particlePosition}>
        <meshStandardMaterial
          color={particleColor}
          emissive={particleColor}
          emissiveIntensity={0.8}
        />
      </Sphere>

      {/* Power value label at midpoint */}
      {power && (
        <Text
          position={[
            (start[0] + end[0]) / 2,
            (start[1] + end[1]) / 2 + 0.5,
            (start[2] + end[2]) / 2,
          ]}
          fontSize={0.3}
          color="#fff"
          anchorX="center"
        >
          {power.toFixed(1)} MW
        </Text>
      )}
    </group>
  );
};

const ControlBuilding = ({ position }) => {
  return (
    <group position={position}>
      {/* Building structure */}
      <Box args={[4, 2.5, 3]}>
        <meshStandardMaterial color="#795548" />
      </Box>

      {/* Roof */}
      <Box args={[4.2, 0.2, 3.2]} position={[0, 1.35, 0]}>
        <meshStandardMaterial color="#5d4037" />
      </Box>

      {/* Windows */}
      {[-1, 0, 1].map((x, i) => (
        <Box key={i} args={[0.8, 0.8, 0.1]} position={[x, 0.5, 1.51]}>
          <meshStandardMaterial color="#64b5f6" emissive="#64b5f6" emissiveIntensity={0.2} />
        </Box>
      ))}

      {/* Door */}
      <Box args={[0.8, 1.5, 0.1]} position={[0, -0.5, 1.51]}>
        <meshStandardMaterial color="#424242" />
      </Box>

      <Text position={[0, 2, 0]} fontSize={0.3} color="white" anchorX="center">
        Control Room
      </Text>
    </group>
  );
};

const AuxiliaryTransformer = ({ position, id }) => {
  return (
    <group position={position}>
      <Box args={[1, 1.5, 1]}>
        <meshStandardMaterial color="#607d8b" />
      </Box>

      {/* Bushings */}
      <Cylinder args={[0.05, 0.05, 0.5, 8]} position={[0, 1, 0]}>
        <meshStandardMaterial color="#8b4513" />
      </Cylinder>

      <Text position={[0, 1.5, 0]} fontSize={0.2} color="#94a3b8" anchorX="center">
        {id}: 1 MVA
      </Text>
    </group>
  );
};

const DieselGenerator = ({ position }) => {
  const engineRef = useRef();

  useFrame((state) => {
    if (engineRef.current) {
      engineRef.current.rotation.z += 0.02;
    }
  });

  return (
    <group position={position}>
      {/* Generator housing */}
      <Box args={[2, 1.5, 1]}>
        <meshStandardMaterial color="#ffc107" />
      </Box>

      {/* Engine cylinder */}
      <Cylinder ref={engineRef} args={[0.3, 0.3, 0.5, 8]} position={[0.5, 0, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <meshStandardMaterial color="#333333" />
      </Cylinder>

      {/* Exhaust */}
      <Cylinder args={[0.1, 0.05, 1, 8]} position={[-0.8, 1, 0]}>
        <meshStandardMaterial color="#666666" />
      </Cylinder>

      <Text position={[0, 1.5, 0]} fontSize={0.25} color="white" anchorX="center">
        Emergency DG
      </Text>
    </group>
  );
};

// Main 3D Scene
const Scene = ({ assets, metrics }) => {
  const groupRef = useRef();

  // Extract power flow data from metrics
  const activePower = metrics.total_power || 420;
  const incomingPower1 = (activePower * 0.55) || 231;
  const incomingPower2 = (activePower * 0.45) || 189;
  const outgoingPower1 = (activePower * 0.33) || 140;
  const outgoingPower2 = (activePower * 0.35) || 147;
  const outgoingPower3 = (activePower * 0.32) || 133;

  return (
    <>
      {/* Enhanced Lighting Setup */}
      <ambientLight intensity={0.8} />

      {/* Main directional light (sun-like) */}
      <directionalLight
        position={[10, 20, 10]}
        intensity={1.5}
        castShadow
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
      />

      {/* Fill lights from multiple angles */}
      <pointLight position={[20, 15, 20]} intensity={1.2} color="#ffffff" />
      <pointLight position={[-20, 15, -20]} intensity={1.2} color="#ffffff" />
      <pointLight position={[20, 15, -20]} intensity={0.8} color="#e0e7ff" />
      <pointLight position={[-20, 15, 20]} intensity={0.8} color="#e0e7ff" />

      {/* Overhead spotlight for better visibility */}
      <spotLight
        position={[0, 35, 0]}
        angle={0.6}
        penumbra={0.5}
        intensity={1.5}
        castShadow
      />

      {/* Hemisphere light for ambient reflection */}
      <hemisphereLight
        skyColor="#87ceeb"
        groundColor="#2d3748"
        intensity={0.6}
      />

      {/* Ground */}
      <Box args={[80, 0.2, 60]} position={[0, -5, 0]}>
        <meshStandardMaterial color="#1a1a2e" />
      </Box>

      {/* Grid */}
      <gridHelper args={[80, 40]} position={[0, -4.9, 0]} />

      <group ref={groupRef}>
        {/* 400kV Switchyard */}
        <group position={[0, 0, -15]}>
          <Busbar position={[-10, 8, 0]} voltage={400} />
          <Busbar position={[10, 8, 0]} voltage={400} />

          {/* Incoming lines equipment */}
          <LightningArrester position={[-20, 0, 0]} id="LA400_1" />
          <LightningArrester position={[20, 0, 0]} id="LA400_2" />

          <WaveTrap position={[-22, 0, 0]} id="WT1" />
          <WaveTrap position={[22, 0, 0]} id="WT2" />

          <CVT position={[-12, 0, 0]} id="CVT400_1" />
          <CVT position={[12, 0, 0]} id="CVT400_2" />

          <CurrentTransformer position={[-10, 5, 0]} id="CT400_1" />
          <CurrentTransformer position={[10, 5, 0]} id="CT400_2" />

          <CircuitBreaker position={[-10, 3, 0]} id="CB400_1" voltage={400} />
          <CircuitBreaker position={[10, 3, 0]} id="CB400_2" voltage={400} />

          <Isolator position={[-10, 1, 0]} id="ISO400_1" />
          <Isolator position={[10, 1, 0]} id="ISO400_2" />
        </group>

        {/* Power Transformers */}
        <PowerTransformer
          position={[-10, 0, 0]}
          id="TR1"
          data={{ loading: 78, temperature: 72 }}
        />
        <PowerTransformer
          position={[10, 0, 0]}
          id="TR2"
          data={{ loading: 65, temperature: 68 }}
        />

        {/* 220kV Switchyard */}
        <group position={[0, 0, 15]}>
          <Busbar position={[-10, 5, 0]} voltage={220} length={10} />
          <Busbar position={[0, 5, 0]} voltage={220} length={8} />
          <Busbar position={[10, 5, 0]} voltage={220} length={10} />

          <CircuitBreaker position={[-10, 2, 0]} id="CB220_1" voltage={220} />
          <CircuitBreaker position={[0, 2, 0]} id="CB220_2" voltage={220} />
          <CircuitBreaker position={[10, 2, 0]} id="CB220_3" voltage={220} />

          <Isolator position={[-10, 0, 0]} id="ISO220_1" />
          <Isolator position={[0, 0, 0]} id="ISO220_2" />
          <Isolator position={[10, 0, 0]} id="ISO220_3" />

          <CurrentTransformer position={[-10, -2, 0]} id="CT220_1" />
          <CurrentTransformer position={[0, -2, 0]} id="CT220_2" />
          <CurrentTransformer position={[10, -2, 0]} id="CT220_3" />

          <CVT position={[-8, -2, 0]} id="CVT220_1" />
          <CVT position={[8, -2, 0]} id="CVT220_2" />

          <LightningArrester position={[-12, -3, 0]} id="LA220_1" />
          <LightningArrester position={[12, -3, 0]} id="LA220_2" />
        </group>

        {/* Reactive Power Compensation */}
        <group position={[25, 0, 0]}>
          <ShuntReactor position={[0, 0, -5]} id="SR1" rating="50 MVAR" />
          <ShuntReactor position={[0, 0, 5]} id="SR2" rating="50 MVAR" />

          <CapacitorBank position={[5, 0, -5]} id="CAP1" capacity={30} />
          <CapacitorBank position={[5, 0, 5]} id="CAP2" capacity={30} />
        </group>

        {/* Auxiliary Systems */}
        <group position={[-25, 0, 10]}>
          <ControlBuilding position={[0, 1.25, 0]} />
          <AuxiliaryTransformer position={[5, 0, 0]} id="AUX_TR1" />
          <AuxiliaryTransformer position={[5, 0, 3]} id="AUX_TR2" />
          <DieselGenerator position={[0, 0, 6]} />
        </group>

        {/* Animated Power Flow Lines */}
        {/* 400kV Incoming lines to busbars */}
        <PowerFlowLine
          start={[-20, 0, -15]}
          end={[-10, 8, -15]}
          voltage={400}
          power={incomingPower1}
        />
        <PowerFlowLine
          start={[20, 0, -15]}
          end={[10, 8, -15]}
          voltage={400}
          power={incomingPower2}
        />

        {/* 400kV Busbars to Transformers */}
        <PowerFlowLine
          start={[-10, 8, -15]}
          end={[-10, 2, -5]}
          voltage={400}
          power={incomingPower1}
        />
        <PowerFlowLine
          start={[10, 8, -15]}
          end={[10, 2, -5]}
          voltage={400}
          power={incomingPower2}
        />

        {/* Transformers to 220kV Busbars */}
        <PowerFlowLine
          start={[-10, -2, 5]}
          end={[-10, 5, 15]}
          voltage={220}
          power={incomingPower1}
        />
        <PowerFlowLine
          start={[10, -2, 5]}
          end={[10, 5, 15]}
          voltage={220}
          power={incomingPower2}
        />

        {/* 220kV Busbars to outgoing feeders */}
        <PowerFlowLine
          start={[-10, 5, 15]}
          end={[-10, -3, 20]}
          voltage={220}
          power={outgoingPower1}
        />
        <PowerFlowLine
          start={[0, 5, 15]}
          end={[0, -3, 20]}
          voltage={220}
          power={outgoingPower2}
        />
        <PowerFlowLine
          start={[10, 5, 15]}
          end={[10, -3, 20]}
          voltage={220}
          power={outgoingPower3}
        />
      </group>

      <OrbitControls
        enablePan={true}
        enableZoom={true}
        enableRotate={true}
        minDistance={10}
        maxDistance={60}
        target={[0, 0, 0]}
      />
    </>
  );
};

const SubstationVisualization3D = () => {
  const [assets, setAssets] = useState({});
  const [metrics, setMetrics] = useState({});

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [assetsRes, metricsRes] = await Promise.all([
          axios.get('/api/assets'),
          axios.get('/api/metrics')
        ]);
        setAssets(assetsRes.data);
        setMetrics(metricsRes.data);
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 10000); // Reduced frequency
    return () => clearInterval(interval);
  }, []);

  return (
    <Container>
      <Canvas
        camera={{ position: [25, 20, 25], fov: 60 }}
        gl={{ preserveDrawingBuffer: true }}
      >
        <Scene assets={assets} metrics={metrics} />
      </Canvas>
    </Container>
  );
};

export default SubstationVisualization3D;