import React, { useState } from 'react';
import styled from 'styled-components';
import { FiAlertTriangle, FiInfo, FiCheckCircle, FiXCircle, FiFilter } from 'react-icons/fi';

const TableContainer = styled.div`
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  overflow: hidden;
`;

const TableHeader = styled.div`
  padding: 1rem 1.25rem;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const TableTitle = styled.h3`
  font-size: 0.9375rem;
  font-weight: 600;
  color: #0f172a;
`;

const FilterBar = styled.div`
  display: flex;
  gap: 0.5rem;
  align-items: center;
`;

const FilterButton = styled.button`
  padding: 0.375rem 0.75rem;
  border: 1px solid ${props => props.active ? '#3b82f6' : '#e2e8f0'};
  background: ${props => props.active ? '#eff6ff' : 'white'};
  color: ${props => props.active ? '#3b82f6' : '#64748b'};
  border-radius: 6px;
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    border-color: #3b82f6;
    background: #eff6ff;
    color: #3b82f6;
  }
`;

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
`;

const Thead = styled.thead`
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
`;

const Th = styled.th`
  text-align: left;
  padding: 0.75rem 1.25rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
`;

const Tbody = styled.tbody``;

const Tr = styled.tr`
  border-bottom: 1px solid #f1f5f9;
  transition: background 0.15s;

  &:hover {
    background: #f8fafc;
  }

  &:last-child {
    border-bottom: none;
  }
`;

const Td = styled.td`
  padding: 0.875rem 1.25rem;
  font-size: 0.8125rem;
  color: #0f172a;
`;

const AlertIcon = styled.div`
  font-size: 1.125rem;
  color: ${props => {
    switch (props.severity) {
      case 'high': return '#dc2626';
      case 'medium': return '#f59e0b';
      case 'low': return '#16a34a';
      default: return '#64748b';
    }
  }};
  display: flex;
  align-items: center;
`;

const SeverityBadge = styled.span`
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.625rem;
  border-radius: 9999px;
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
  background: ${props => {
    switch (props.severity) {
      case 'high': return '#fef2f2';
      case 'medium': return '#fef3c7';
      case 'low': return '#f0fdf4';
      default: return '#f1f5f9';
    }
  }};
  color: ${props => {
    switch (props.severity) {
      case 'high': return '#dc2626';
      case 'medium': return '#d97706';
      case 'low': return '#16a34a';
      default: return '#64748b';
    }
  }};
`;

const Pagination = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.875rem 1.25rem;
  border-top: 1px solid #e2e8f0;
  background: #f8fafc;
`;

const PageInfo = styled.div`
  font-size: 0.8125rem;
  color: #64748b;
`;

const PageButtons = styled.div`
  display: flex;
  gap: 0.5rem;
`;

const PageButton = styled.button`
  padding: 0.375rem 0.75rem;
  border: 1px solid #e2e8f0;
  background: ${props => props.active ? '#3b82f6' : 'white'};
  color: ${props => props.active ? 'white' : '#64748b'};
  border-radius: 6px;
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;

  &:hover:not(:disabled) {
    border-color: #3b82f6;
    background: ${props => props.active ? '#2563eb' : '#eff6ff'};
    color: ${props => props.active ? 'white' : '#3b82f6'};
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const AlertsTable = () => {
  const [filter, setFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 5;

  const allAlerts = [
    {
      id: 1,
      message: 'Transformer TX1 temperature above normal threshold',
      time: '2 minutes ago',
      severity: 'medium',
      type: 'Temperature',
      icon: FiAlertTriangle
    },
    {
      id: 2,
      message: 'Circuit breaker CB_400kV status changed to open',
      time: '5 minutes ago',
      severity: 'high',
      type: 'Status Change',
      icon: FiXCircle
    },
    {
      id: 3,
      message: 'Load balancing optimization completed successfully',
      time: '8 minutes ago',
      severity: 'low',
      type: 'System',
      icon: FiCheckCircle
    },
    {
      id: 4,
      message: 'New IoT device TEMP_SENSOR_001 connected',
      time: '12 minutes ago',
      severity: 'low',
      type: 'Device',
      icon: FiInfo
    },
    {
      id: 5,
      message: 'Voltage stability improved to 98.5%',
      time: '15 minutes ago',
      severity: 'low',
      type: 'Performance',
      icon: FiCheckCircle
    },
    {
      id: 6,
      message: 'High current detected on Feeder F1',
      time: '20 minutes ago',
      severity: 'high',
      type: 'Overcurrent',
      icon: FiAlertTriangle
    },
    {
      id: 7,
      message: 'Protection relay R1 tripped',
      time: '25 minutes ago',
      severity: 'high',
      type: 'Protection',
      icon: FiXCircle
    },
    {
      id: 8,
      message: 'Scheduled maintenance completed for Bay 2',
      time: '30 minutes ago',
      severity: 'low',
      type: 'Maintenance',
      icon: FiInfo
    }
  ];

  const filteredAlerts = filter === 'all'
    ? allAlerts
    : allAlerts.filter(alert => alert.severity === filter);

  const totalPages = Math.ceil(filteredAlerts.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentAlerts = filteredAlerts.slice(startIndex, endIndex);

  const handleFilterChange = (newFilter) => {
    setFilter(newFilter);
    setCurrentPage(1);
  };

  return (
    <TableContainer>
      <TableHeader>
        <TableTitle>Recent Alerts & Notifications</TableTitle>
        <FilterBar>
          <FiFilter style={{ color: '#64748b', fontSize: '0.875rem' }} />
          <FilterButton
            active={filter === 'all'}
            onClick={() => handleFilterChange('all')}
          >
            All
          </FilterButton>
          <FilterButton
            active={filter === 'high'}
            onClick={() => handleFilterChange('high')}
          >
            High
          </FilterButton>
          <FilterButton
            active={filter === 'medium'}
            onClick={() => handleFilterChange('medium')}
          >
            Medium
          </FilterButton>
          <FilterButton
            active={filter === 'low'}
            onClick={() => handleFilterChange('low')}
          >
            Low
          </FilterButton>
        </FilterBar>
      </TableHeader>

      <Table>
        <Thead>
          <tr>
            <Th style={{ width: '40px' }}></Th>
            <Th>Alert Message</Th>
            <Th style={{ width: '120px' }}>Type</Th>
            <Th style={{ width: '100px' }}>Severity</Th>
            <Th style={{ width: '120px' }}>Time</Th>
          </tr>
        </Thead>
        <Tbody>
          {currentAlerts.map((alert) => (
            <Tr key={alert.id}>
              <Td>
                <AlertIcon severity={alert.severity}>
                  <alert.icon />
                </AlertIcon>
              </Td>
              <Td style={{ fontWeight: 500 }}>{alert.message}</Td>
              <Td style={{ color: '#64748b' }}>{alert.type}</Td>
              <Td>
                <SeverityBadge severity={alert.severity}>
                  {alert.severity}
                </SeverityBadge>
              </Td>
              <Td style={{ color: '#64748b' }}>{alert.time}</Td>
            </Tr>
          ))}
        </Tbody>
      </Table>

      <Pagination>
        <PageInfo>
          Showing {startIndex + 1}-{Math.min(endIndex, filteredAlerts.length)} of {filteredAlerts.length}
        </PageInfo>
        <PageButtons>
          <PageButton
            onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
            disabled={currentPage === 1}
          >
            Previous
          </PageButton>
          {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
            <PageButton
              key={page}
              active={page === currentPage}
              onClick={() => setCurrentPage(page)}
            >
              {page}
            </PageButton>
          ))}
          <PageButton
            onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
            disabled={currentPage === totalPages}
          >
            Next
          </PageButton>
        </PageButtons>
      </Pagination>
    </TableContainer>
  );
};

export default AlertsTable;
