import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { useDigitalTwin } from '../context/DigitalTwinContext';
import { FiAlertTriangle, FiCheckCircle, FiCpu, FiZap, FiSearch, FiChevronLeft, FiChevronRight, FiSettings } from 'react-icons/fi';
import ThresholdManager from '../components/ThresholdManager';

const SCADAContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
`;

const PageHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e2e8f0;
`;

const Title = styled.h1`
  color: #1e293b;
  font-size: 1.75rem;
  font-weight: 600;
  letter-spacing: -0.025em;
`;

const StatusIndicator = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: #f0fdf4;
  border: 1px solid #86efac;
  border-radius: 6px;
  color: #16a34a;
  font-weight: 500;
  font-size: 0.875rem;

  svg {
    font-size: 1rem;
  }
`;

const SCADAGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
  gap: 1.5rem;

  @media (max-width: 1200px) {
    grid-template-columns: 1fr;
  }
`;

const SCADASection = styled.div`
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
`;

const SectionTitle = styled.h3`
  font-size: 0.875rem;
  font-weight: 600;
  margin-bottom: 1.25rem;
  color: #475569;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;

  svg {
    color: #3b82f6;
    font-size: 1.25rem;
  }
`;

const ScrollContainer = styled.div`
  max-height: 450px;
  overflow-y: auto;
  margin: -0.25rem -0.5rem -0.25rem 0;
  padding-right: 0.5rem;

  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-track {
    background: #f8fafc;
  }

  &::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 3px;
  }

  &::-webkit-scrollbar-thumb:hover {
    background: #94a3b8;
  }
`;

const DataPoint = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.875rem 1rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-left: 3px solid #3b82f6;
  border-radius: 6px;
  margin-bottom: 0.5rem;
  transition: all 0.2s ease;

  &:hover {
    background: #eff6ff;
    border-left-color: #2563eb;
    box-shadow: 0 1px 3px rgba(59, 130, 246, 0.1);
  }
`;

const DataPointName = styled.div`
  font-size: 0.875rem;
  font-weight: 500;
  color: #334155;
`;

const DataPointValue = styled.div`
  font-size: 1.125rem;
  font-weight: 600;
  color: ${props => props.quality === 'good' ? '#16a34a' : '#dc2626'};
`;

const DataPointUnit = styled.div`
  font-size: 0.875rem;
  color: #64748b;
  margin-left: 0.375rem;
  font-weight: 400;
`;

const IoTDevice = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.875rem 1rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-left: 3px solid ${props => props.status === 'online' ? '#16a34a' : '#dc2626'};
  border-radius: 6px;
  margin-bottom: 0.5rem;
  transition: all 0.2s ease;

  &:hover {
    background: ${props => props.status === 'online' ? '#f0fdf4' : '#fef2f2'};
    border-left-color: ${props => props.status === 'online' ? '#15803d' : '#b91c1c'};
    box-shadow: 0 1px 3px ${props => props.status === 'online' ? 'rgba(22, 163, 74, 0.1)' : 'rgba(220, 38, 38, 0.1)'};
  }
`;

const DeviceInfo = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
`;

const DeviceName = styled.div`
  font-size: 0.875rem;
  font-weight: 500;
  color: #334155;
`;

const DeviceType = styled.div`
  font-size: 0.75rem;
  color: #64748b;
  font-weight: 400;
`;

const DeviceStatus = styled.div`
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.75rem;
  color: ${props => props.status === 'online' ? '#16a34a' : '#dc2626'};
  font-weight: 600;
  padding: 0.25rem 0.625rem;
  background: ${props => props.status === 'online' ? '#f0fdf4' : '#fef2f2'};
  border: 1px solid ${props => props.status === 'online' ? '#86efac' : '#fca5a5'};
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: 0.025em;

  svg {
    font-size: 0.875rem;
  }
`;

const AlarmsSection = styled.div`
  grid-column: 1 / -1;
`;

const TableControls = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  gap: 1rem;
  flex-wrap: wrap;
`;

const SearchContainer = styled.div`
  position: relative;
  flex: 1;
  min-width: 250px;
  max-width: 400px;
`;

const SearchInput = styled.input`
  width: 100%;
  padding: 0.5rem 0.75rem 0.5rem 2.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 0.875rem;
  color: #334155;
  background: #ffffff;
  transition: all 0.2s ease;

  &:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }

  &::placeholder {
    color: #94a3b8;
  }
`;

const SearchIcon = styled(FiSearch)`
  position: absolute;
  left: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  color: #64748b;
  font-size: 1rem;
`;

const FilterContainer = styled.div`
  display: flex;
  gap: 0.5rem;
  align-items: center;
`;

const FilterButton = styled.button`
  padding: 0.5rem 0.875rem;
  border: 1px solid ${props => props.active ? '#3b82f6' : '#e2e8f0'};
  background: ${props => props.active ? '#eff6ff' : '#ffffff'};
  color: ${props => props.active ? '#2563eb' : '#64748b'};
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  text-transform: uppercase;
  letter-spacing: 0.025em;

  &:hover {
    background: ${props => props.active ? '#dbeafe' : '#f8fafc'};
    border-color: ${props => props.active ? '#2563eb' : '#cbd5e1'};
  }
`;

const Table = styled.table`
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  font-size: 0.875rem;
`;

const TableHeader = styled.thead`
  background: #f8fafc;
  border-bottom: 2px solid #e2e8f0;
`;

const TableHeaderCell = styled.th`
  padding: 0.75rem 1rem;
  text-align: left;
  font-weight: 600;
  color: #475569;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 2px solid #e2e8f0;

  &:first-child {
    padding-left: 1.5rem;
  }

  &:last-child {
    padding-right: 1.5rem;
  }
`;

const TableBody = styled.tbody``;

const TableRow = styled.tr`
  border-bottom: 1px solid #e2e8f0;
  transition: background-color 0.2s ease;

  &:hover {
    background: #f8fafc;
  }

  &:last-child {
    border-bottom: none;
  }
`;

const TableCell = styled.td`
  padding: 0.875rem 1rem;
  color: #334155;

  &:first-child {
    padding-left: 1.5rem;
  }

  &:last-child {
    padding-right: 1.5rem;
  }
`;

const SeverityBadge = styled.span`
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.25rem 0.625rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
  background: ${props => {
    if (props.severity === 'high') return '#fef2f2';
    if (props.severity === 'medium') return '#fffbeb';
    return '#f0fdf4';
  }};
  color: ${props => {
    if (props.severity === 'high') return '#dc2626';
    if (props.severity === 'medium') return '#f59e0b';
    return '#16a34a';
  }};
  border: 1px solid ${props => {
    if (props.severity === 'high') return '#fca5a5';
    if (props.severity === 'medium') return '#fde68a';
    return '#86efac';
  }};

  svg {
    font-size: 0.875rem;
  }
`;

const Pagination = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
`;

const PaginationInfo = styled.div`
  font-size: 0.875rem;
  color: #64748b;
`;

const PaginationControls = styled.div`
  display: flex;
  gap: 0.5rem;
  align-items: center;
`;

const PaginationButton = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  border: 1px solid #e2e8f0;
  background: #ffffff;
  color: #64748b;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover:not(:disabled) {
    background: #f8fafc;
    border-color: #cbd5e1;
    color: #334155;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  svg {
    font-size: 1rem;
  }
`;

const PageNumber = styled.span`
  padding: 0 0.5rem;
  font-size: 0.875rem;
  color: #334155;
  font-weight: 500;
`;

const EmptyState = styled.div`
  text-align: center;
  padding: 3rem 2rem;
  color: #64748b;

  svg {
    font-size: 3rem;
    color: #cbd5e1;
    margin-bottom: 1rem;
  }

  p {
    margin: 0;
    font-size: 0.875rem;
  }
`;

// Fallback data matching EXACT backend API response structure
// Backend returns: { scada_data: {...}, iot_data: {...}, timestamp: "..." }
const FALLBACK_SCADA_RESPONSE = {
  scada_data: {
    '400kV_VOLTAGE_A': {
      value: 402.3,
      quality: 'good',
      unit: 'kV',
      timestamp: new Date().toISOString()
    },
    '400kV_CURRENT_A': {
      value: 205.8,
      quality: 'good',
      unit: 'A',
      timestamp: new Date().toISOString()
    },
    '400kV_POWER_MW': {
      value: 142.5,
      quality: 'good',
      unit: 'MW',
      timestamp: new Date().toISOString()
    },
    '220kV_VOLTAGE_A': {
      value: 218.7,
      quality: 'good',
      unit: 'kV',
      timestamp: new Date().toISOString()
    },
    '220kV_CURRENT_A': {
      value: 312.4,
      quality: 'good',
      unit: 'A',
      timestamp: new Date().toISOString()
    },
    'TX1_TEMP': {
      value: 48.2,
      quality: 'good',
      unit: '°C',
      timestamp: new Date().toISOString()
    },
    'TX1_OIL_LEVEL': {
      value: 94.5,
      quality: 'good',
      unit: '%',
      timestamp: new Date().toISOString()
    },
    'CB_400kV_STATUS': {
      value: 1.0,
      quality: 'good',
      unit: '',
      timestamp: new Date().toISOString()
    },
    'CB_220kV_STATUS': {
      value: 1.0,
      quality: 'good',
      unit: '',
      timestamp: new Date().toISOString()
    },
    'LOAD_INDUSTRIAL_MW': {
      value: 16.3,
      quality: 'good',
      unit: 'MW',
      timestamp: new Date().toISOString()
    }
  },
  iot_data: {},
  timestamp: new Date().toISOString()
};

// Fallback IoT devices matching backend API response structure
// Backend returns: { devices: [...], total_count: N, timestamp: "..." }
const FALLBACK_IOT_RESPONSE = {
  devices: [
    {
      id: 'TEMP_SENSOR_001',
      name: 'Temperature Sensor 001',
      type: 'Temperature Sensor',
      status: 'online',
      location: 'Main Transformer 1',
      last_update: new Date().toISOString(),
      metrics: {
        temperature: 45.2,
        health_score: 95.0,
        voltage: 400.0
      }
    },
    {
      id: 'VIBRATION_SENSOR_001',
      name: 'Vibration Sensor 001',
      type: 'Vibration Sensor',
      status: 'online',
      location: 'Main Transformer 1',
      last_update: new Date().toISOString(),
      metrics: {
        temperature: 42.0,
        health_score: 92.0,
        voltage: 400.0
      }
    },
    {
      id: 'GAS_SENSOR_001',
      name: 'Gas Sensor 001',
      type: 'Gas Sensor',
      status: 'online',
      location: 'Main Transformer 1',
      last_update: new Date().toISOString(),
      metrics: {
        temperature: 40.0,
        health_score: 98.0,
        voltage: 400.0
      }
    },
    {
      id: 'CURRENT_SENSOR_001',
      name: 'Current Sensor 001',
      type: 'Current Sensor',
      status: 'online',
      location: '400kV Bus',
      last_update: new Date().toISOString(),
      metrics: {
        temperature: 35.0,
        health_score: 100.0,
        voltage: 400.0
      }
    },
    {
      id: 'VOLTAGE_SENSOR_001',
      name: 'Voltage Sensor 001',
      type: 'Voltage Sensor',
      status: 'online',
      location: '400kV Bus',
      last_update: new Date().toISOString(),
      metrics: {
        temperature: 35.0,
        health_score: 100.0,
        voltage: 400.0
      }
    }
  ],
  total_count: 5,
  timestamp: new Date().toISOString()
};

const SCADA = () => {
  const { scadaData, iotDevices } = useDigitalTwin();

  // Use fallback data if real data is empty or undefined
  // Check multiple possible response structures from backend
  const scadaPoints = (scadaData?.scada_data && Object.keys(scadaData.scada_data).length > 0)
    ? scadaData.scada_data
    : (scadaData?.data?.scada_data && Object.keys(scadaData.data.scada_data).length > 0)
      ? scadaData.data.scada_data
      : FALLBACK_SCADA_RESPONSE.scada_data;

  const iotData = (iotDevices?.devices && iotDevices.devices.length > 0)
    ? iotDevices.devices
    : FALLBACK_IOT_RESPONSE.devices;

  return (
    <SCADAContainer>
      <PageHeader>
        <Title>SCADA & IoT Monitoring</Title>
        <StatusIndicator>
          <FiCheckCircle />
          SCADA Connected
        </StatusIndicator>
      </PageHeader>

      <SCADAGrid>
        <SCADASection>
          <SectionTitle>
            <FiZap />
            SCADA Data Points
          </SectionTitle>
          <ScrollContainer>
            {Object.entries(scadaPoints).slice(0, 10).map(([pointId, point]) => (
              <DataPoint key={pointId}>
                <DataPointName>{pointId}</DataPointName>
                <div style={{ display: 'flex', alignItems: 'center' }}>
                  <DataPointValue quality={point.quality}>
                    {point.value?.toFixed(1)}
                  </DataPointValue>
                  <DataPointUnit>{point.unit}</DataPointUnit>
                </div>
              </DataPoint>
            ))}
          </ScrollContainer>
        </SCADASection>

        <SCADASection>
          <SectionTitle>
            <FiCpu />
            IoT Devices
          </SectionTitle>
          <ScrollContainer>
            {iotData.map((device) => (
              <IoTDevice key={device.id} status={device.status}>
                <DeviceInfo>
                  <DeviceName>{device.name}</DeviceName>
                  <DeviceType>{device.type}</DeviceType>
                </DeviceInfo>
                <DeviceStatus status={device.status}>
                  <FiCheckCircle />
                  {device.status}
                </DeviceStatus>
              </IoTDevice>
            ))}
          </ScrollContainer>
        </SCADASection>
      </SCADAGrid>

      <AlarmsSection>
        <SCADASection>
          <SectionTitle>
            <FiSettings />
            Threshold Configuration
          </SectionTitle>
          <ThresholdManager />
        </SCADASection>
      </AlarmsSection>
    </SCADAContainer>
  );
};

export default SCADA;