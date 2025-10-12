import React, { useState } from 'react';
import styled from 'styled-components';
import axios from 'axios';
import toast from 'react-hot-toast';
import { AlertCircle, Zap, Thermometer, Activity, Shield, Power } from 'lucide-react';

const Container = styled.div`
  background: #ffffff;
  border-radius: 10px;
  padding: 1.25rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  border: 1px solid #e5e7eb;
  height: 900px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
`;

const Title = styled.h2`
  color: #1f2937;
  font-size: 1.1rem;
  font-weight: 700;
  margin-bottom: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;

  svg {
    width: 18px;
    height: 18px;
    color: #3b82f6;
  }
`;

const Description = styled.p`
  color: #6b7280;
  margin-bottom: 1rem;
  font-size: 0.75rem;
  line-height: 1.4;
`;

const ScenariosGrid = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1rem;
  flex: 1;
  overflow-y: auto;
  padding-right: 0.5rem;

  /* Hide scrollbar but keep scrollability */
  &::-webkit-scrollbar {
    display: none;
  }
  -ms-overflow-style: none;
  scrollbar-width: none;
`;

const ScenarioCard = styled.div`
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 0.85rem;
  transition: all 0.2s;

  &:hover {
    border-color: #3b82f6;
    box-shadow: 0 1px 3px rgba(59, 130, 246, 0.1);
  }
`;

const ScenarioHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-bottom: 0.6rem;
`;

const ScenarioIcon = styled.div`
  width: 30px;
  height: 30px;
  border-radius: 5px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: ${props => props.color}15;
  flex-shrink: 0;

  svg {
    width: 16px;
    height: 16px;
    color: ${props => props.color};
  }
`;

const ScenarioInfo = styled.div`
  flex: 1;
  min-width: 0;
`;

const ScenarioName = styled.h3`
  color: #1f2937;
  font-size: 0.875rem;
  font-weight: 600;
  margin-bottom: 0.1rem;
`;

const ScenarioType = styled.div`
  color: #64748b;
  font-size: 0.7rem;
`;

const ScenarioDescription = styled.p`
  display: none;
`;

const ParametersSection = styled.div`
  margin-bottom: 0.6rem;
  background: #f9fafb;
  padding: 0.6rem;
  border-radius: 5px;
  border: 1px solid #e5e7eb;
`;

const ParameterRow = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.4rem;

  &:last-child {
    margin-bottom: 0;
  }
`;

const ParameterLabel = styled.label`
  color: #4b5563;
  font-size: 0.7rem;
  font-weight: 500;
`;

const ParameterInput = styled.input`
  background: #ffffff;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  color: #1f2937;
  padding: 0.2rem 0.4rem;
  width: 70px;
  font-size: 0.7rem;

  &:focus {
    outline: none;
    border-color: #3b82f6;
  }
`;

const ParameterSelect = styled.select`
  background: #ffffff;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  color: #1f2937;
  padding: 0.2rem 0.4rem;
  width: 85px;
  font-size: 0.7rem;

  &:focus {
    outline: none;
    border-color: #3b82f6;
  }
`;

const SimulateButton = styled.button`
  width: 100%;
  background: ${props => props.isRunning ?
    'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)' :
    'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)'};
  color: white;
  border: none;
  border-radius: 5px;
  padding: 0.5rem;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: ${props => props.isRunning ?
    '0 1px 3px rgba(239, 68, 68, 0.2)' :
    '0 1px 3px rgba(59, 130, 246, 0.2)'};

  &:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: ${props => props.isRunning ?
      '0 2px 4px rgba(239, 68, 68, 0.3)' :
      '0 2px 4px rgba(59, 130, 246, 0.3)'};
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`;

const StatusMessage = styled.div`
  background: ${props => props.type === 'error' ? '#fef2f2' : '#f0fdf4'};
  border: 1px solid ${props => props.type === 'error' ? '#fca5a5' : '#86efac'};
  border-radius: 6px;
  padding: 0.75rem;
  margin-top: 1rem;
  color: ${props => props.type === 'error' ? '#dc2626' : '#16a34a'};
  font-size: 0.75rem;
  font-weight: 500;
`;

const AnomalySimulationPanel = () => {
  const [runningScenarios, setRunningScenarios] = useState({});
  const [statusMessage, setStatusMessage] = useState(null);
  const [scenarioParams, setScenarioParams] = useState({
    voltage_sag: { severity: 0.85, location: 'Bus400_1' },
    voltage_surge: { severity: 1.12, location: 'Bus220_1' },
    overload: { load_factor: 1.2, transformer: 'TR1' },
    ground_fault: { resistance: 5, location: 'Line400_1' },
    harmonics: { thd: 5, order: 5, source: 'CAP1' },
    frequency_deviation: { deviation: 0.3, type: 'under' }
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
        { key: 'transformer', label: 'Transformer', type: 'select', options: ['TR1', 'TR2', 'AUX_TR1', 'AUX_TR2'] }
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
        { key: 'location', label: 'Location', type: 'select', options: ['Line220_1', 'Line220_2', 'Line400_1', 'Line400_2'] }
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
        { key: 'type', label: 'Type', type: 'select', options: ['under', 'over'] }
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
    // Start the scenario
    try {
      const params = scenarioParams[scenario.id];

      const response = await axios.post('/api/simulation/anomaly', {
        type: scenario.id,
        severity: params.severity,
        location: params.location,
        parameters: params
      });

      setRunningScenarios(prev => ({ ...prev, [scenario.id]: true }));
      setStatusMessage({
        type: 'success',
        text: `${scenario.name} simulation started. Anomaly is now active and persisting...`
      });
      toast.success(`${scenario.name} simulation started`);

    } catch (error) {
      toast.error(`Failed to start ${scenario.name}`);
      setStatusMessage({ type: 'error', text: `Failed to start ${scenario.name}: ${error.response?.data?.detail || error.message}` });
    }
  };

  const clearAllAnomalies = async () => {
    try {
      const response = await axios.post('/api/simulation/clear');

      setRunningScenarios({});
      setStatusMessage({ type: 'success', text: 'All anomalies cleared. System back to normal.' });
      toast.success('System restored to normal operation');

      // Clear status after 3 seconds
      setTimeout(() => setStatusMessage(null), 3000);
    } catch (error) {
      toast.error('Failed to clear anomalies');
      setStatusMessage({ type: 'error', text: `Failed to clear anomalies: ${error.message}` });
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
              disabled={runningScenarios[scenario.id]}
            >
              {runningScenarios[scenario.id] ? 'Anomaly Active' : 'Start Simulation'}
            </SimulateButton>
          </ScenarioCard>
        ))}
      </ScenariosGrid>

      <SimulateButton
        onClick={clearAllAnomalies}
        isRunning={true}
        style={{ marginTop: '0.5rem' }}
      >
        🔧 Clear All Anomalies
      </SimulateButton>

      {statusMessage && (
        <StatusMessage type={statusMessage.type}>
          {statusMessage.text}
        </StatusMessage>
      )}
    </Container>
  );
};

export default AnomalySimulationPanel;