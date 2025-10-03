import React from 'react';
import styled from 'styled-components';
import { FiAlertTriangle, FiInfo, FiCheckCircle, FiXCircle } from 'react-icons/fi';

const AlertsContainer = styled.div`
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  padding: 1.25rem;
  color: #0f172a;
`;

const AlertsTitle = styled.h3`
  font-size: 0.9375rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: #0f172a;
`;

const AlertList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
`;

const AlertItem = styled.div`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: #f8fafc;
  border-radius: 6px;
  border-left: 3px solid ${props => props.severity === 'high' ? '#dc2626' : props.severity === 'medium' ? '#f59e0b' : '#16a34a'};
  transition: all 0.2s ease;

  &:hover {
    background: #f1f5f9;
    box-shadow: 0 2px 4px 0 rgb(0 0 0 / 0.05);
  }
`;

const AlertIcon = styled.div`
  font-size: 1.125rem;
  color: ${props => props.severity === 'high' ? '#dc2626' : props.severity === 'medium' ? '#f59e0b' : '#16a34a'};
`;

const AlertContent = styled.div`
  flex: 1;
`;

const AlertMessage = styled.div`
  font-size: 0.8125rem;
  font-weight: 500;
  margin-bottom: 0.25rem;
  color: #0f172a;
`;

const AlertTime = styled.div`
  font-size: 0.75rem;
  color: #64748b;
`;

const AlertSeverity = styled.div`
  font-size: 0.6875rem;
  padding: 0.25rem 0.5rem;
  border-radius: 9999px;
  background: ${props => props.severity === 'high' ? '#fef2f2' : props.severity === 'medium' ? '#fef3c7' : '#f0fdf4'};
  color: ${props => props.severity === 'high' ? '#dc2626' : props.severity === 'medium' ? '#d97706' : '#16a34a'};
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
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