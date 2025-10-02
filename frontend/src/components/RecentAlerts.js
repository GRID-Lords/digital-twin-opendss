import React from 'react';
import styled from 'styled-components';
import { FiAlertTriangle, FiInfo, FiCheckCircle, FiXCircle } from 'react-icons/fi';

const AlertsContainer = styled.div`
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
  padding: 1.5rem;
  color: #f1f5f9;
`;

const AlertsTitle = styled.h3`
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: #f1f5f9;
`;

const AlertList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
`;

const AlertItem = styled.div`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  border-left: 3px solid ${props => props.severity === 'high' ? '#ef4444' : props.severity === 'medium' ? '#f59e0b' : '#4ade80'};
  transition: all 0.2s ease;
  
  &:hover {
    background: #334155;
  }
`;

const AlertIcon = styled.div`
  font-size: 1.2rem;
  color: ${props => props.severity === 'high' ? '#ef4444' : props.severity === 'medium' ? '#f59e0b' : '#4ade80'};
`;

const AlertContent = styled.div`
  flex: 1;
`;

const AlertMessage = styled.div`
  font-size: 0.9rem;
  font-weight: 500;
  margin-bottom: 0.25rem;
`;

const AlertTime = styled.div`
  font-size: 0.8rem;
  color: #94a3b8;
`;

const AlertSeverity = styled.div`
  font-size: 0.8rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  background: ${props => props.severity === 'high' ? 'rgba(239, 68, 68, 0.2)' : props.severity === 'medium' ? 'rgba(245, 158, 11, 0.2)' : 'rgba(74, 222, 128, 0.2)'};
  color: ${props => props.severity === 'high' ? '#ef4444' : props.severity === 'medium' ? '#f59e0b' : '#4ade80'};
  font-weight: 500;
  text-transform: uppercase;
`;

const RecentAlerts = () => {
  // Sample alerts data
  const alerts = [
    {
      id: 1,
      message: 'Transformer TX1 temperature above normal threshold',
      time: '2 minutes ago',
      severity: 'medium',
      icon: FiAlertTriangle
    },
    {
      id: 2,
      message: 'Circuit breaker CB_400kV status changed to open',
      time: '5 minutes ago',
      severity: 'high',
      icon: FiXCircle
    },
    {
      id: 3,
      message: 'Load balancing optimization completed successfully',
      time: '8 minutes ago',
      severity: 'low',
      icon: FiCheckCircle
    },
    {
      id: 4,
      message: 'New IoT device TEMP_SENSOR_001 connected',
      time: '12 minutes ago',
      severity: 'low',
      icon: FiInfo
    },
    {
      id: 5,
      message: 'Voltage stability improved to 98.5%',
      time: '15 minutes ago',
      severity: 'low',
      icon: FiCheckCircle
    }
  ];

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'high': return '#ef4444';
      case 'medium': return '#f59e0b';
      case 'low': return '#4ade80';
      default: return '#6b7280';
    }
  };

  return (
    <AlertsContainer>
      <AlertsTitle>Recent Alerts & Notifications</AlertsTitle>
      <AlertList>
        {alerts.map((alert) => (
          <AlertItem key={alert.id} severity={alert.severity}>
            <AlertIcon severity={alert.severity}>
              <alert.icon />
            </AlertIcon>
            <AlertContent>
              <AlertMessage>{alert.message}</AlertMessage>
              <AlertTime>{alert.time}</AlertTime>
            </AlertContent>
            <AlertSeverity severity={alert.severity}>
              {alert.severity}
            </AlertSeverity>
          </AlertItem>
        ))}
      </AlertList>
    </AlertsContainer>
  );
};

export default RecentAlerts;