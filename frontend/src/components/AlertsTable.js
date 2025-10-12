import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { FiAlertTriangle, FiInfo, FiCheckCircle, FiXCircle, FiFilter } from 'react-icons/fi';
import axios from 'axios';

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

const ExpandableRow = styled.tr`
  background: #f8fafc;
`;

const ExpandedCell = styled.td`
  padding: 1rem 1.25rem;
  border-bottom: 1px solid #e2e8f0;
  font-size: 0.8125rem;
  color: #475569;
  line-height: 1.6;
  white-space: pre-wrap;
`;

const MessageCell = styled(Td)`
  cursor: pointer;

  &:hover {
    color: #3b82f6;
  }
`;

const AlertsTable = ({ sourceFilter = null }) => {
  const [filter, setFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedAlert, setExpandedAlert] = useState(null);
  const itemsPerPage = 5;

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const extractSummary = (fullMessage) => {
    // Extract just the first line or first sentence before "**Root Cause:**"
    if (!fullMessage) return 'No description';

    // If message has root cause analysis, extract just the title
    const rootCauseIndex = fullMessage.indexOf('**Root Cause:**');
    if (rootCauseIndex > 0) {
      return fullMessage.substring(0, rootCauseIndex).trim();
    }

    // Otherwise, take first 100 characters
    if (fullMessage.length > 100) {
      return fullMessage.substring(0, 100) + '...';
    }

    return fullMessage;
  };

  const fetchAlerts = async () => {
    try {
      const response = await axios.get('/api/alerts', {
        params: {
          limit: 100,
          unresolved_only: false
        }
      });

      if (response.data && response.data.alerts) {
        // Format alerts for display
        const formattedAlerts = response.data.alerts.map(alert => {
          const fullMessage = alert.description || alert.message || 'No description';
          return {
            id: alert.id,
            message: extractSummary(fullMessage),
            fullMessage: fullMessage,
            time: formatTimeAgo(alert.timestamp),
            timestamp: alert.timestamp,
            severity: alert.severity || 'medium',
            type: alert.type || 'System',
            source: alert.type || 'system',
            icon: getIconForType(alert.type),
            data: alert.data
          };
        });

        // Add dummy alerts if no real alerts exist
        if (formattedAlerts.length === 0) {
          formattedAlerts.push(
            {
              id: 'dummy-1',
              message: 'Transformer TR1 temperature elevated to 87°C',
              fullMessage: 'Transformer TR1 operating temperature has increased to 87°C, exceeding normal operating range of 75°C. Cooling system efficiency should be verified.',
              time: '25 minutes ago',
              timestamp: new Date(Date.now() - 25 * 60 * 1000).toISOString(),
              severity: 'medium',
              type: 'Temperature',
              source: 'temperature',
              icon: FiAlertTriangle,
              data: { temperature: 87, threshold: 85 }
            },
            {
              id: 'dummy-2',
              message: 'Circuit Breaker CB_400_3 high operation count detected',
              fullMessage: 'Circuit Breaker CB_400_3 has reached 9,850 operations, approaching the maintenance threshold of 10,000 operations. Schedule maintenance inspection soon.',
              time: '2 hours ago',
              timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
              severity: 'low',
              type: 'Maintenance',
              source: 'maintenance',
              icon: FiInfo,
              data: { operations: 9850, threshold: 10000 }
            }
          );
        }

        setAlerts(formattedAlerts);
      }
    } catch (error) {
      console.error('Error fetching alerts:', error);
    } finally {
      setLoading(false);
    }
  };

  const getIconForType = (type) => {
    if (type?.includes('manual_alerts')) return FiAlertTriangle;
    if (type?.includes('temperature')) return FiAlertTriangle;
    if (type?.includes('voltage')) return FiXCircle;
    if (type?.includes('anomaly')) return FiAlertTriangle;
    return FiInfo;
  };

  const formatTimeAgo = (timestamp) => {
    if (!timestamp) return 'Unknown';

    try {
      const date = new Date(timestamp);
      const now = new Date();
      const diffMs = now - date;
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMins / 60);
      const diffDays = Math.floor(diffHours / 24);

      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
      if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
      return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
    } catch (e) {
      return 'Unknown';
    }
  };

  // Apply both severity filter and source filter (if provided)
  let filteredAlerts = alerts;

  if (sourceFilter) {
    filteredAlerts = filteredAlerts.filter(alert => alert.source === sourceFilter);
  }

  if (filter !== 'all') {
    filteredAlerts = filteredAlerts.filter(alert => alert.severity === filter);
  }

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
            <React.Fragment key={alert.id}>
              <Tr>
                <Td>
                  <AlertIcon severity={alert.severity}>
                    <alert.icon />
                  </AlertIcon>
                </Td>
                <MessageCell
                  style={{ fontWeight: 500 }}
                  onClick={() => setExpandedAlert(expandedAlert === alert.id ? null : alert.id)}
                  title="Click to see full details"
                >
                  {alert.message}
                  {alert.fullMessage !== alert.message && expandedAlert !== alert.id && (
                    <span style={{ color: '#3b82f6', marginLeft: '0.5rem', fontSize: '0.75rem' }}>
                      (click for details)
                    </span>
                  )}
                </MessageCell>
                <Td style={{ color: '#64748b' }}>{alert.type}</Td>
                <Td>
                  <SeverityBadge severity={alert.severity}>
                    {alert.severity}
                  </SeverityBadge>
                </Td>
                <Td style={{ color: '#64748b' }}>{alert.time}</Td>
              </Tr>
              {expandedAlert === alert.id && alert.fullMessage !== alert.message && (
                <ExpandableRow>
                  <ExpandedCell colSpan="5">
                    <strong>Full Details:</strong>
                    <div style={{ marginTop: '0.5rem' }}>{alert.fullMessage}</div>
                  </ExpandedCell>
                </ExpandableRow>
              )}
            </React.Fragment>
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
