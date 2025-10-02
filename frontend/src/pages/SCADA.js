import React, { useEffect } from 'react';
import styled from 'styled-components';
import { useDigitalTwin } from '../context/DigitalTwinContext';
import { FiActivity, FiAlertTriangle, FiCheckCircle } from 'react-icons/fi';

const SCADAContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 2rem;
`;

const PageHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
`;

const Title = styled.h1`
  color: #f1f5f9;
  font-size: 2rem;
  font-weight: 700;
`;

const StatusIndicator = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(74, 222, 128, 0.2);
  border: 1px solid rgba(74, 222, 128, 0.3);
  border-radius: 8px;
  color: #4ade80;
  font-weight: 500;
`;

const SCADAGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  
  @media (max-width: 1200px) {
    grid-template-columns: 1fr;
  }
`;

const SCADASection = styled.div`
  background: #ffffff;
  
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
  padding: 1.5rem;
  color: #0f172a;
`;

const SectionTitle = styled.h3`
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: #0f172a;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const DataPoint = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  margin-bottom: 0.5rem;
  transition: all 0.2s ease;
  
  &:hover {
    background: #ffffff;
  }
`;

const DataPointName = styled.div`
  font-size: 0.9rem;
  font-weight: 500;
`;

const DataPointValue = styled.div`
  font-size: 1rem;
  font-weight: 600;
  color: ${props => props.quality === 'good' ? '#4ade80' : '#ef4444'};
`;

const DataPointUnit = styled.div`
  font-size: 0.8rem;
  color: #94a3b8;
  margin-left: 0.25rem;
`;

const IoTDevice = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  margin-bottom: 0.5rem;
  transition: all 0.2s ease;
  
  &:hover {
    background: #ffffff;
  }
`;

const DeviceInfo = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
`;

const DeviceName = styled.div`
  font-size: 0.9rem;
  font-weight: 500;
`;

const DeviceType = styled.div`
  font-size: 0.8rem;
  color: #94a3b8;
`;

const DeviceStatus = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: ${props => props.status === 'online' ? '#4ade80' : '#ef4444'};
`;

const AlarmsSection = styled.div`
  grid-column: 1 / -1;
`;

const AlarmItem = styled.div`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  margin-bottom: 0.5rem;
  border-left: 3px solid ${props => props.severity === 'high' ? '#ef4444' : '#f59e0b'};
`;

const AlarmIcon = styled.div`
  font-size: 1.2rem;
  color: ${props => props.severity === 'high' ? '#ef4444' : '#f59e0b'};
`;

const AlarmContent = styled.div`
  flex: 1;
`;

const AlarmMessage = styled.div`
  font-size: 0.9rem;
  font-weight: 500;
  margin-bottom: 0.25rem;
`;

const AlarmTime = styled.div`
  font-size: 0.8rem;
  color: #94a3b8;
`;

const SCADA = () => {
  const { scadaData, iotDevices } = useDigitalTwin();

  // No need to fetch on mount - DigitalTwinContext already handles auto-refresh

  const scadaPoints = scadaData.scada_data || {};
  const iotData = iotDevices || {};

  // Sample alarms data
  const alarms = [
    {
      id: 1,
      message: '400kV voltage out of range: 385.2 kV',
      time: '2 minutes ago',
      severity: 'high'
    },
    {
      id: 2,
      message: 'High transformer temperature: 85.3°C',
      time: '5 minutes ago',
      severity: 'medium'
    },
    {
      id: 3,
      message: 'Circuit breaker CB_400kV is open',
      time: '8 minutes ago',
      severity: 'high'
    }
  ];

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
            <FiActivity />
            SCADA Data Points
          </SectionTitle>
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
        </SCADASection>

        <SCADASection>
          <SectionTitle>
            <FiActivity />
            IoT Devices
          </SectionTitle>
          {Object.entries(iotData).map(([deviceId, device]) => (
            <IoTDevice key={deviceId}>
              <DeviceInfo>
                <DeviceName>{deviceId}</DeviceName>
                <DeviceType>{device.device_type}</DeviceType>
              </DeviceInfo>
              <DeviceStatus status={device.status}>
                <FiCheckCircle />
                {device.status}
              </DeviceStatus>
            </IoTDevice>
          ))}
        </SCADASection>
      </SCADAGrid>

      <AlarmsSection>
        <SCADASection>
          <SectionTitle>
            <FiAlertTriangle />
            Active Alarms
          </SectionTitle>
          {alarms.map((alarm) => (
            <AlarmItem key={alarm.id} severity={alarm.severity}>
              <AlarmIcon severity={alarm.severity}>
                <FiAlertTriangle />
              </AlarmIcon>
              <AlarmContent>
                <AlarmMessage>{alarm.message}</AlarmMessage>
                <AlarmTime>{alarm.time}</AlarmTime>
              </AlarmContent>
            </AlarmItem>
          ))}
        </SCADASection>
      </AlarmsSection>
    </SCADAContainer>
  );
};

export default SCADA;