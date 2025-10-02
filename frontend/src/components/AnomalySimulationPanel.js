import React, { useState } from 'react';
import styled from 'styled-components';
import axios from 'axios';
import toast from 'react-hot-toast';
import { AlertCircle, Zap, Thermometer, Activity, Shield, Power } from 'lucide-react';

const Container = styled.div`
  background: #1e293b;
  border-radius: 12px;
  padding: 2rem;
  margin-top: 2rem;
  box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
`;

const Title = styled.h2`
  color: #f1f5f9;
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;

  svg {
    color: #ef4444;
  }
`;

const Description = styled.p`
  color: #94a3b8;
  margin-bottom: 2rem;
  font-size: 0.95rem;
  line-height: 1.5;
`;

const ScenariosGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
`;

const ScenarioCard = styled.div`
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 8px;
  padding: 1.5rem;
  transition: all 0.3s;

  &:hover {
    border-color: #6366f1;
    transform: translateY(-2px);
  }
`;

const ScenarioHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
`;

const ScenarioIcon = styled.div`
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: ${props => props.color}20;

  svg {
    width: 24px;
    height: 24px;
    color: ${props => props.color};
  }
`;

const ScenarioInfo = styled.div`
  flex: 1;
`;

const ScenarioName = styled.h3`
  color: #f1f5f9;
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
`;

const ScenarioType = styled.div`
  color: #64748b;
  font-size: 0.875rem;
`;

const ScenarioDescription = styled.p`
  color: #94a3b8;
  font-size: 0.875rem;
  margin-bottom: 1rem;
  line-height: 1.4;
`;

const ParametersSection = styled.div`
  margin-bottom: 1rem;
`;

const ParameterRow = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
`;

const ParameterLabel = styled.label`
  color: #94a3b8;
  font-size: 0.875rem;
`;

const ParameterInput = styled.input`
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 4px;
  color: #f1f5f9;
  padding: 0.25rem 0.5rem;
  width: 100px;
  font-size: 0.875rem;

  &:focus {
    outline: none;
    border-color: #6366f1;
  }
`;

const ParameterSelect = styled.select`
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 4px;
  color: #f1f5f9;
  padding: 0.25rem 0.5rem;
  width: 120px;
  font-size: 0.875rem;

  &:focus {
    outline: none;
    border-color: #6366f1;
  }
`;

const SimulateButton = styled.button`
  width: 100%;
  background: ${props => props.isRunning ? '#ef4444' : '#6366f1'};
  color: white;
  border: none;
  border-radius: 6px;
  padding: 0.75rem;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;

  &:hover:not(:disabled) {
    background: ${props => props.isRunning ? '#dc2626' : '#4f46e5'};
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const StatusMessage = styled.div`
  background: ${props => props.type === 'error' ? '#dc262620' : '#10b98120'};
  border: 1px solid ${props => props.type === 'error' ? '#dc2626' : '#10b981'};
  border-radius: 6px;
  padding: 1rem;
  margin-top: 1.5rem;
  color: ${props => props.type === 'error' ? '#fca5a5' : '#86efac'};
  font-size: 0.875rem;
`;

const AnomalySimulationPanel = () => {
  const [runningScenarios, setRunningScenarios] = useState({});
  const [statusMessage, setStatusMessage] = useState(null);
  const [scenarioParams, setScenarioParams] = useState({
    voltage_sag: { severity: 0.8, duration: 5, location: 'Bus220_1' },
    voltage_surge: { severity: 1.15, duration: 3, location: 'Bus400_1' },
    overload: { load_factor: 1.5, transformer: 'TR1', duration: 10 },
    ground_fault: { resistance: 10, location: 'Line220_1', duration: 0.1 },
    harmonics: { thd: 8, order: 5, source: 'CAP1' },
    frequency_deviation: { deviation: 0.5, duration: 2, type: 'under' }
  });

  const scenarios = [
    {
      id: 'voltage_sag',
      name: 'Voltage Sag',
      type: 'Power Quality',
      icon: <Zap />,
      color: '#f59e0b',
      description: 'Simulates voltage drop below nominal levels, typically caused by large motor starts or faults.',
      parameters: [
        { key: 'severity', label: 'Severity (p.u.)', type: 'number', min: 0.5, max: 0.9, step: 0.1 },
        { key: 'duration', label: 'Duration (s)', type: 'number', min: 1, max: 60, step: 1 },
        { key: 'location', label: 'Location', type: 'select', options: ['Bus220_1', 'Bus220_2', 'Bus400_1', 'Bus400_2'] }
      ]
    },
    {
      id: 'voltage_surge',
      name: 'Voltage Surge',
      type: 'Power Quality',
      icon: <Zap />,
      color: '#ef4444',
      description: 'Simulates voltage rise above nominal levels due to capacitor switching or load rejection.',
      parameters: [
        { key: 'severity', label: 'Severity (p.u.)', type: 'number', min: 1.1, max: 1.3, step: 0.05 },
        { key: 'duration', label: 'Duration (s)', type: 'number', min: 0.5, max: 30, step: 0.5 },
        { key: 'location', label: 'Location', type: 'select', options: ['Bus400_1', 'Bus400_2', 'Bus220_1', 'Bus220_2'] }
      ]
    },
    {
      id: 'overload',
      name: 'Transformer Overload',
      type: 'Thermal',
      icon: <Thermometer />,
      color: '#dc2626',
      description: 'Simulates excessive loading on transformers causing temperature rise and efficiency loss.',
      parameters: [
        { key: 'load_factor', label: 'Load Factor', type: 'number', min: 1.1, max: 2.0, step: 0.1 },
        { key: 'transformer', label: 'Transformer', type: 'select', options: ['TR1', 'TR2', 'AUX_TR1', 'AUX_TR2'] },
        { key: 'duration', label: 'Duration (min)', type: 'number', min: 1, max: 60, step: 5 }
      ]
    },
    {
      id: 'ground_fault',
      name: 'Ground Fault',
      type: 'Protection',
      icon: <Shield />,
      color: '#7c3aed',
      description: 'Simulates single line to ground fault with varying fault resistance.',
      parameters: [
        { key: 'resistance', label: 'Fault Resistance (Ω)', type: 'number', min: 0, max: 100, step: 10 },
        { key: 'location', label: 'Location', type: 'select', options: ['Line220_1', 'Line220_2', 'Line400_1', 'Line400_2'] },
        { key: 'duration', label: 'Duration (cycles)', type: 'number', min: 1, max: 10, step: 1 }
      ]
    },
    {
      id: 'harmonics',
      name: 'Harmonic Distortion',
      type: 'Power Quality',
      icon: <Activity />,
      color: '#06b6d4',
      description: 'Simulates harmonic distortion from non-linear loads or capacitor resonance.',
      parameters: [
        { key: 'thd', label: 'THD (%)', type: 'number', min: 5, max: 15, step: 1 },
        { key: 'order', label: 'Harmonic Order', type: 'select', options: ['3', '5', '7', '11', '13'] },
        { key: 'source', label: 'Source', type: 'select', options: ['CAP1', 'CAP2', 'SR1', 'SR2'] }
      ]
    },
    {
      id: 'frequency_deviation',
      name: 'Frequency Event',
      type: 'System Stability',
      icon: <Power />,
      color: '#10b981',
      description: 'Simulates system frequency deviation due to generation-load imbalance.',
      parameters: [
        { key: 'deviation', label: 'Deviation (Hz)', type: 'number', min: 0.1, max: 2.0, step: 0.1 },
        { key: 'type', label: 'Type', type: 'select', options: ['under', 'over'] },
        { key: 'duration', label: 'Duration (s)', type: 'number', min: 1, max: 30, step: 1 }
      ]
    }
  ];

  const handleParameterChange = (scenarioId, paramKey, value) => {
    setScenarioParams(prev => ({
      ...prev,
      [scenarioId]: {
        ...prev[scenarioId],
        [paramKey]: value
      }
    }));
  };

  const simulateScenario = async (scenario) => {
    const isRunning = runningScenarios[scenario.id];

    if (isRunning) {
      // Stop the scenario
      try {
        const response = await axios.post('/api/simulation/stop', {
          scenario_id: scenario.id
        });

        setRunningScenarios(prev => ({ ...prev, [scenario.id]: false }));
        setStatusMessage({ type: 'success', text: `${scenario.name} simulation stopped` });
        toast.success(`${scenario.name} simulation stopped`);

        // Clear status after 3 seconds
        setTimeout(() => setStatusMessage(null), 3000);
      } catch (error) {
        toast.error(`Failed to stop ${scenario.name}`);
        setStatusMessage({ type: 'error', text: `Failed to stop ${scenario.name}: ${error.message}` });
      }
    } else {
      // Start the scenario
      try {
        const params = scenarioParams[scenario.id];

        const response = await axios.post('/api/simulation/anomaly', {
          type: scenario.id,
          parameters: params,
          visualization: '3d'
        });

        setRunningScenarios(prev => ({ ...prev, [scenario.id]: true }));
        setStatusMessage({
          type: 'success',
          text: `${scenario.name} simulation started. OpenDSS is analyzing the impact...`
        });
        toast.success(`${scenario.name} simulation started`);

        // Auto-stop after duration
        const duration = (params.duration || 5) * 1000;
        setTimeout(() => {
          setRunningScenarios(prev => ({ ...prev, [scenario.id]: false }));
          setStatusMessage({ type: 'success', text: `${scenario.name} simulation completed` });
        }, duration);

      } catch (error) {
        toast.error(`Failed to start ${scenario.name}`);
        setStatusMessage({ type: 'error', text: `Failed to start ${scenario.name}: ${error.message}` });
      }
    }
  };

  return (
    <Container>
      <Title>
        <AlertCircle />
        Anomaly Simulation Control Panel
      </Title>

      <Description>
        Trigger various electrical anomalies and fault conditions in the OpenDSS simulation.
        These scenarios will affect the real-time power flow calculations and trigger appropriate
        protection responses in the digital twin.
      </Description>

      <ScenariosGrid>
        {scenarios.map(scenario => (
          <ScenarioCard key={scenario.id}>
            <ScenarioHeader>
              <ScenarioIcon color={scenario.color}>
                {scenario.icon}
              </ScenarioIcon>
              <ScenarioInfo>
                <ScenarioName>{scenario.name}</ScenarioName>
                <ScenarioType>{scenario.type}</ScenarioType>
              </ScenarioInfo>
            </ScenarioHeader>

            <ScenarioDescription>
              {scenario.description}
            </ScenarioDescription>

            <ParametersSection>
              {scenario.parameters.map(param => (
                <ParameterRow key={param.key}>
                  <ParameterLabel>{param.label}:</ParameterLabel>
                  {param.type === 'select' ? (
                    <ParameterSelect
                      value={scenarioParams[scenario.id][param.key]}
                      onChange={(e) => handleParameterChange(scenario.id, param.key, e.target.value)}
                      disabled={runningScenarios[scenario.id]}
                    >
                      {param.options.map(option => (
                        <option key={option} value={option}>{option}</option>
                      ))}
                    </ParameterSelect>
                  ) : (
                    <ParameterInput
                      type="number"
                      value={scenarioParams[scenario.id][param.key]}
                      onChange={(e) => handleParameterChange(scenario.id, param.key, parseFloat(e.target.value))}
                      min={param.min}
                      max={param.max}
                      step={param.step}
                      disabled={runningScenarios[scenario.id]}
                    />
                  )}
                </ParameterRow>
              ))}
            </ParametersSection>

            <SimulateButton
              onClick={() => simulateScenario(scenario)}
              isRunning={runningScenarios[scenario.id]}
            >
              {runningScenarios[scenario.id] ? 'Stop Simulation' : 'Start Simulation'}
            </SimulateButton>
          </ScenarioCard>
        ))}
      </ScenariosGrid>

      {statusMessage && (
        <StatusMessage type={statusMessage.type}>
          {statusMessage.text}
        </StatusMessage>
      )}
    </Container>
  );
};

export default AnomalySimulationPanel;