import React, { useRef, useState, useEffect } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Text, Box, Sphere, Cylinder } from '@react-three/drei';
import * as THREE from 'three';
import axios from 'axios';
import styled from 'styled-components';
import { motion } from 'framer-motion';

const Container = styled.div`
  width: 100%;
  height: 600px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
  overflow: hidden;
  position: relative;
`;

const ControlPanel = styled.div`
  position: absolute;
  top: 20px;
  right: 20px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  z-index: 100;
`;

const ViewButton = styled(motion.button)`
  display: inline-block;
  margin: 5px;
  padding: 8px 12px;
  background: #6366f1;
  color: #0f172a;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;

  &:hover {
    background: #4f46e5;
  }
`;

const InfoPanel = styled.div`
  position: absolute;
  bottom: 20px;
  left: 20px;
  background: rgba(0, 0, 0, 0.8);
  color: #0f172a;
  border-radius: 8px;
  padding: 15px;
  max-width: 300px;
  font-size: 12px;
`;

// 3D Components

const Transformer = ({ position, id, data = {} }) => {
  const meshRef = useRef();
  const [hovered, setHovered] = useState(false);

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y += 0.001;
    }
  });

  // Color based on loading
  const loading = data.loading || 75;
  const color = loading > 90 ? '#ff0000' : loading > 70 ? '#ffaa00' : '#00ff00';

  return (
    <group position={position}>
      {/* Transformer body */}
      <Box
        ref={meshRef}
        args={[2, 3, 2]}
        position={[0, 0, 0]}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
      >
        <meshStandardMaterial color={hovered ? '#ff6b6b' : '#4a5568'} />
      </Box>

      {/* Windings */}
      <Cylinder args={[0.8, 0.8, 0.5, 32]} position={[0, 1.8, 0]}>
        <meshStandardMaterial color="#ffd700" />
      </Cylinder>
      <Cylinder args={[0.8, 0.8, 0.5, 32]} position={[0, -1.8, 0]}>
        <meshStandardMaterial color="#87ceeb" />
      </Cylinder>

      {/* Radiators */}
      {[-1, 0, 1].map((x, i) => (
        <Box key={i} args={[0.1, 2.5, 1.5]} position={[x * 0.8 + 1.5, 0, 0]}>
          <meshStandardMaterial color="#2d3748" />
        </Box>
      ))}

      {/* Loading indicator */}
      <Box args={[0.3, loading / 30, 0.3]} position={[0, 3 + loading / 60, 0]}>
        <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.5} />
      </Box>

      {/* Label */}
      <Text
        position={[0, 4, 0]}
        fontSize={0.5}
        color="white"
        anchorX="center"
        anchorY="middle"
      >
        {id}
      </Text>
    </group>
  );
};

const CircuitBreaker = ({ position, id, isOpen = false, onClick }) => {
  const [localOpen, setLocalOpen] = useState(isOpen);

  const handleClick = () => {
    setLocalOpen(!localOpen);
    if (onClick) onClick(id, !localOpen);
  };

  return (
    <group position={position} onClick={handleClick}>
      {/* Breaker body */}
      <Box args={[1, 0.5, 0.5]} position={[0, 0, 0]}>
        <meshStandardMaterial color={localOpen ? '#ff4444' : '#44ff44'} />
      </Box>

      {/* Contacts */}
      <Sphere args={[0.15]} position={[-0.6, 0, 0]}>
        <meshStandardMaterial color="#silver" metalness={0.8} />
      </Sphere>
      <Sphere args={[0.15]} position={[0.6, 0, 0]}>
        <meshStandardMaterial color="#silver" metalness={0.8} />
      </Sphere>

      {/* Moving contact */}
      <Box
        args={[0.8, 0.1, 0.1]}
        position={[0, localOpen ? 0.3 : 0, 0]}
        rotation={[0, 0, localOpen ? Math.PI / 6 : 0]}
      >
        <meshStandardMaterial color="#copper" metalness={0.9} />
      </Box>

      {/* Label */}
      <Text
        position={[0, 0.8, 0]}
        fontSize={0.3}
        color="white"
        anchorX="center"
      >
        {id}
      </Text>
    </group>
  );
};

const Busbar = ({ position, voltage, length = 10 }) => {
  const color = voltage === 400 ? '#ff6b6b' : voltage === 220 ? '#4ecdc4' : '#95e1d3';

  return (
    <group position={position}>
      <Box args={[length, 0.3, 0.3]}>
        <meshStandardMaterial color={color} metalness={0.7} roughness={0.3} />
      </Box>
      <Text
        position={[0, 0.6, 0]}
        fontSize={0.4}
        color="white"
        anchorX="center"
      >
        {voltage} kV Bus
      </Text>
    </group>
  );
};

const CapacitorBank = ({ position, id, capacity }) => {
  return (
    <group position={position}>
      {/* Capacitor units */}
      {[0, 1, 2].map((i) => (
        <Cylinder
          key={i}
          args={[0.3, 0.3, 1, 16]}
          position={[i * 0.8 - 0.8, 0, 0]}
        >
          <meshStandardMaterial color="#00ff00" />
        </Cylinder>
      ))}

      {/* Frame */}
      <Box args={[3, 0.1, 1.5]} position={[0, -0.6, 0]}>
        <meshStandardMaterial color="#333333" />
      </Box>

      <Text
        position={[0, 1, 0]}
        fontSize={0.3}
        color="white"
        anchorX="center"
      >
        {id}: {capacity} MVAR
      </Text>
    </group>
  );
};

const ProtectionRelay = ({ position, id, type }) => {
  const [triggered] = useState(false);

  return (
    <group position={position}>
      <Box args={[0.5, 0.8, 0.3]}>
        <meshStandardMaterial color={triggered ? '#ff0000' : '#0088cc'} />
      </Box>

      {/* Display */}
      <Box args={[0.3, 0.2, 0.01]} position={[0, 0.2, 0.16]}>
        <meshStandardMaterial color="#000000" />
      </Box>

      {/* LEDs */}
      {[-0.15, 0, 0.15].map((x, i) => (
        <Sphere key={i} args={[0.03]} position={[x, -0.2, 0.16]}>
          <meshStandardMaterial
            color={triggered ? '#ff0000' : '#00ff00'}
            emissive={triggered ? '#ff0000' : '#00ff00'}
            emissiveIntensity={0.5}
          />
        </Sphere>
      ))}

      <Text
        position={[0, 0.6, 0]}
        fontSize={0.2}
        color="white"
        anchorX="center"
      >
        {id}
      </Text>
    </group>
  );
};

// Main 3D Scene
const Scene = ({ selectedView, anomalyType }) => {
  const [transformerData, setTransformerData] = useState({});

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get('/api/metrics');
        // Update transformer data from API
        setTransformerData(response.data);
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    };

    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, []);

  // Visualize anomaly in 3D
  useEffect(() => {
    if (anomalyType) {
      // Add visual effects for anomalies
      console.log('Visualizing anomaly:', anomalyType);
    }
  }, [anomalyType]);

  return (
    <>
      <ambientLight intensity={0.5} />
      <pointLight position={[10, 10, 10]} />
      <pointLight position={[-10, -10, -10]} />
      <spotLight position={[5, 15, 5]} angle={0.3} penumbra={1} intensity={1} />

      {/* Ground plane */}
      <Box args={[50, 0.1, 50]} position={[0, -5, 0]}>
        <meshStandardMaterial color="#1a1a2e" />
      </Box>

      {/* Grid */}
      <gridHelper args={[50, 50]} position={[0, -4.9, 0]} />

      {/* 400kV Section */}
      <Busbar position={[-8, 5, 0]} voltage={400} />
      <Busbar position={[8, 5, 0]} voltage={400} />

      {/* Transformers */}
      <Transformer position={[-8, 0, 0]} id="TR1" data={transformerData.TR1 || {}} />
      <Transformer position={[8, 0, 0]} id="TR2" data={transformerData.TR2 || {}} />

      {/* 220kV Section */}
      <Busbar position={[-8, -3, 0]} voltage={220} />
      <Busbar position={[0, -3, 0]} voltage={220} />
      <Busbar position={[8, -3, 0]} voltage={220} />

      {/* Circuit Breakers */}
      <CircuitBreaker position={[-8, 3, 0]} id="CB1" />
      <CircuitBreaker position={[8, 3, 0]} id="CB2" />
      <CircuitBreaker position={[-8, -1, 0]} id="CB3" />
      <CircuitBreaker position={[8, -1, 0]} id="CB4" />

      {/* Capacitor Banks */}
      <CapacitorBank position={[12, -3, 0]} id="Cap1" capacity={30} />
      <CapacitorBank position={[15, -3, 0]} id="Cap2" capacity={20} />

      {/* Protection Relays */}
      <ProtectionRelay position={[-12, 0, 0]} id="Relay1" type="Differential" />
      <ProtectionRelay position={[12, 0, 0]} id="Relay2" type="Distance" />

      <OrbitControls
        enablePan={true}
        enableZoom={true}
        enableRotate={true}
        minDistance={5}
        maxDistance={50}
      />
    </>
  );
};

const SubstationVisualization3D = () => {
  const [selectedView, setSelectedView] = useState('overview');
  const [currentAnomaly, setCurrentAnomaly] = useState(null);

  const triggerAnomaly3D = async (type) => {
    setCurrentAnomaly(type);

    try {
      await axios.post('/api/simulation/anomaly', {
        type: type,
        visualization: '3d'
      });

      // Reset after 5 seconds
      setTimeout(() => {
        setCurrentAnomaly(null);
      }, 5000);
    } catch (error) {
      console.error('Error triggering 3D anomaly:', error);
    }
  };

  return (
    <Container>
      <ControlPanel>
        <h4 style={{ margin: '0 0 10px 0' }}>3D View Controls</h4>

        <div>
          <ViewButton onClick={() => setSelectedView('overview')}>
            Overview
          </ViewButton>
          <ViewButton onClick={() => setSelectedView('transformers')}>
            Transformers
          </ViewButton>
          <ViewButton onClick={() => setSelectedView('switchyard')}>
            Switchyard
          </ViewButton>
        </div>

        <div style={{ marginTop: '15px' }}>
          <h5 style={{ margin: '5px 0', fontSize: '12px' }}>Trigger Anomaly</h5>
          <ViewButton onClick={() => triggerAnomaly3D('voltage_fluctuation')}>
            Voltage Fluctuation
          </ViewButton>
          <ViewButton onClick={() => triggerAnomaly3D('overheating')}>
            Overheating
          </ViewButton>
          <ViewButton onClick={() => triggerAnomaly3D('arc_flash')}>
            Arc Flash
          </ViewButton>
        </div>
      </ControlPanel>

      <InfoPanel>
        <h4>Substation Status</h4>
        <div>Total Load: 330 MW</div>
        <div>System Frequency: 50.02 Hz</div>
        <div>Voltage Level: Normal</div>
        {currentAnomaly && (
          <div style={{ color: '#ff6b6b', marginTop: '10px' }}>
            ⚠️ Anomaly Detected: {currentAnomaly.replace('_', ' ').toUpperCase()}
          </div>
        )}
      </InfoPanel>

      <Canvas camera={{ position: [15, 10, 15], fov: 60 }}>
        <Scene selectedView={selectedView} anomalyType={currentAnomaly} />
      </Canvas>
    </Container>
  );
};

export default SubstationVisualization3D;