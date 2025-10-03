import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { FileText, Filter, Download, RefreshCw, AlertCircle, Info, AlertTriangle, CheckCircle } from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const LoggingContainer = styled.div`
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
  display: flex;
  align-items: center;
  gap: 0.5rem;
  letter-spacing: -0.025em;

  svg {
    color: #3b82f6;
  }
`;

const Controls = styled.div`
  display: flex;
  gap: 1rem;
  align-items: center;
`;

const FilterContainer = styled.div`
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
`;

const FilterGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
`;

const FilterGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
`;

const Label = styled.label`
  color: #475569;
  font-size: 0.875rem;
  font-weight: 500;
`;

const Select = styled.select`
  background: #ffffff;
  border: 1px solid #e2e8f0;
  color: #334155;
  padding: 0.5rem;
  border-radius: 6px;
  font-size: 0.875rem;

  &:focus {
    outline: none;
    border-color: #3b82f6;
  }
`;

const Button = styled.button`
  background: ${props => props.variant === 'primary' ? '#3b82f6' : '#ffffff'};
  border: 1px solid ${props => props.variant === 'primary' ? '#3b82f6' : '#e2e8f0'};
  color: ${props => props.variant === 'primary' ? '#ffffff' : '#334155'};
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;

  &:hover {
    background: ${props => props.variant === 'primary' ? '#2563eb' : '#f8fafc'};
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  svg {
    width: 16px;
    height: 16px;
  }
`;

const LogsContainer = styled.div`
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
`;

const LogEntry = styled.div`
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-left: 3px solid ${props => {
    switch (props.severity) {
      case 'high': return '#dc2626';
      case 'medium': return '#f59e0b';
      case 'low': return '#16a34a';
      default: return '#3b82f6';
    }
  }};
  border-radius: 6px;
  padding: 1rem;
  margin-bottom: 0.75rem;
  transition: all 0.2s;

  &:hover {
    background: ${props => {
      switch (props.severity) {
        case 'high': return '#fef2f2';
        case 'medium': return '#fffbeb';
        case 'low': return '#f0fdf4';
        default: return '#eff6ff';
      }
    }};
  }
`;

const LogHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: start;
  margin-bottom: 0.5rem;
`;

const LogType = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #334155;
  font-weight: 600;
  font-size: 0.9rem;

  svg {
    width: 16px;
    height: 16px;
  }
`;

const LogTime = styled.div`
  color: #64748b;
  font-size: 0.8rem;
`;

const LogDescription = styled.div`
  color: #475569;
  font-size: 0.875rem;
  margin-bottom: 0.5rem;
`;

const LogMeta = styled.div`
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
`;

const MetaTag = styled.span`
  background: #e2e8f0;
  color: #475569;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
`;

const SeverityBadge = styled.span`
  background: ${props => {
    switch (props.severity) {
      case 'high': return '#fef2f2';
      case 'medium': return '#fffbeb';
      case 'low': return '#f0fdf4';
      default: return '#eff6ff';
    }
  }};
  color: ${props => {
    switch (props.severity) {
      case 'high': return '#dc2626';
      case 'medium': return '#f59e0b';
      case 'low': return '#16a34a';
      default: return '#3b82f6';
    }
  }};
  border: 1px solid ${props => {
    switch (props.severity) {
      case 'high': return '#fca5a5';
      case 'medium': return '#fde68a';
      case 'low': return '#86efac';
      default: return '#93c5fd';
    }
  }};
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
`;

const EmptyState = styled.div`
  text-align: center;
  padding: 3rem;
  color: #64748b;
`;

const PaginationContainer = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
`;

const PaginationInfo = styled.div`
  color: #64748b;
  font-size: 0.875rem;
`;

const PaginationControls = styled.div`
  display: flex;
  gap: 0.5rem;
`;

const PageButton = styled.button`
  padding: 0.5rem 0.75rem;
  border: 1px solid #e2e8f0;
  background: ${props => props.active ? '#3b82f6' : '#ffffff'};
  color: ${props => props.active ? '#ffffff' : '#334155'};
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.875rem;
  transition: all 0.2s;

  &:hover:not(:disabled) {
    background: ${props => props.active ? '#2563eb' : '#f8fafc'};
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const StatsBar = styled.div`
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
`;

const StatChip = styled.div`
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #475569;
  font-size: 0.875rem;

  strong {
    color: #3b82f6;
    font-weight: 600;
  }
`;

// Fallback data when backend is unavailable
const FALLBACK_LOGS = [
  {
    type: 'fault',
    severity: 'high',
    description: 'Transformer T1 overcurrent detected - Phase A: 1250A (threshold: 1000A)',
    timestamp: new Date(Date.now() - 15 * 60000).toISOString(),
    acknowledged: false,
    duration: 15
  },
  {
    type: 'alarm',
    severity: 'high',
    description: 'Circuit Breaker CB3 failed to respond to open command',
    timestamp: new Date(Date.now() - 45 * 60000).toISOString(),
    acknowledged: false,
    duration: 45
  },
  {
    type: 'warning',
    severity: 'medium',
    description: 'High ambient temperature in Substation A - 42°C (threshold: 40°C)',
    timestamp: new Date(Date.now() - 90 * 60000).toISOString(),
    acknowledged: true,
    duration: 90
  },
  {
    type: 'fault',
    severity: 'high',
    description: 'Bus voltage out of range - 400kV: 385.2kV (range: 390-410kV)',
    timestamp: new Date(Date.now() - 2 * 3600000).toISOString(),
    acknowledged: true,
    duration: 120
  },
  {
    type: 'alarm',
    severity: 'medium',
    description: 'Communication loss with RTU-5 for 5 minutes',
    timestamp: new Date(Date.now() - 3 * 3600000).toISOString(),
    acknowledged: true,
    duration: 5
  },
  {
    type: 'maintenance',
    severity: 'low',
    description: 'Scheduled maintenance window started for Feeder F2',
    timestamp: new Date(Date.now() - 4 * 3600000).toISOString(),
    acknowledged: true,
    duration: 240
  },
  {
    type: 'warning',
    severity: 'medium',
    description: 'Load imbalance detected - Phase difference: 18% (threshold: 15%)',
    timestamp: new Date(Date.now() - 6 * 3600000).toISOString(),
    acknowledged: true,
    duration: 30
  },
  {
    type: 'alarm',
    severity: 'high',
    description: 'SCADA server backup failed - Check storage system',
    timestamp: new Date(Date.now() - 8 * 3600000).toISOString(),
    acknowledged: true,
    duration: 10
  },
  {
    type: 'warning',
    severity: 'medium',
    description: 'Network latency increased - RTU response time: 250ms (threshold: 200ms)',
    timestamp: new Date(Date.now() - 10 * 3600000).toISOString(),
    acknowledged: true,
    duration: 45
  },
  {
    type: 'fault',
    severity: 'high',
    description: 'Ground fault detected on Feeder F7 - Isolation required',
    timestamp: new Date(Date.now() - 12 * 3600000).toISOString(),
    acknowledged: true,
    duration: 180
  },
  {
    type: 'maintenance',
    severity: 'low',
    description: 'Scheduled firmware update completed for Circuit Breaker CB1',
    timestamp: new Date(Date.now() - 14 * 3600000).toISOString(),
    acknowledged: true,
    duration: 60
  }
];

const Logging = () => {
  const [logs, setLogs] = useState(FALLBACK_LOGS);
  const [loading, setLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [filters, setFilters] = useState({
    days: 7,
    eventType: '',
    severity: ''
  });
  const itemsPerPage = 10;

  useEffect(() => {
    fetchLogs();
  }, []);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/alerts', {
        params: {
          limit: 100,
          unresolved_only: filters.eventType === 'unresolved'
        }
      });
      if (response.data.alerts && response.data.alerts.length > 0) {
        setLogs(response.data.alerts);
      }
    } catch (error) {
      // Keep fallback data on error
      console.error('Error fetching alerts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({ ...prev, [field]: value }));
    setCurrentPage(1); // Reset to first page when filters change
  };

  const exportLogs = () => {
    const dataStr = JSON.stringify(logs, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `logs_${new Date().toISOString()}.json`;
    link.click();
    toast.success('Logs exported successfully');
  };

  const getEventIcon = (type) => {
    switch (type) {
      case 'fault': return <AlertCircle />;
      case 'alarm': return <AlertTriangle />;
      case 'warning': return <AlertTriangle />;
      case 'maintenance': return <CheckCircle />;
      default: return <Info />;
    }
  };

  const filteredLogs = logs.filter(log => {
    if (filters.severity && log.severity !== filters.severity) return false;
    if (filters.eventType && log.type !== filters.eventType) return false;
    return true;
  });

  // Pagination
  const totalPages = Math.ceil(filteredLogs.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedLogs = filteredLogs.slice(startIndex, startIndex + itemsPerPage);

  const stats = {
    total: filteredLogs.length,
    faults: filteredLogs.filter(l => l.type === 'fault').length,
    alarms: filteredLogs.filter(l => l.type === 'alarm').length,
    warnings: filteredLogs.filter(l => l.type === 'warning').length,
    unacknowledged: filteredLogs.filter(l => !l.acknowledged).length
  };

  return (
    <LoggingContainer>
      <PageHeader>
        <Title>
          <FileText />
          System Logging
        </Title>
        <Controls>
          <Button onClick={fetchLogs} disabled={loading}>
            <RefreshCw />
            {loading ? 'Loading...' : 'Refresh'}
          </Button>
          <Button variant="primary" onClick={exportLogs}>
            <Download />
            Export
          </Button>
        </Controls>
      </PageHeader>

      <FilterContainer>
        <Label style={{ fontSize: '1rem', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Filter size={16} />
          Filters
        </Label>
        <FilterGrid>
          <FilterGroup>
            <Label>Time Period</Label>
            <Select
              value={filters.days}
              onChange={(e) => handleFilterChange('days', e.target.value)}
            >
              <option value="1">Last 24 hours</option>
              <option value="3">Last 3 days</option>
              <option value="7">Last 7 days</option>
              <option value="30">Last 30 days</option>
            </Select>
          </FilterGroup>

          <FilterGroup>
            <Label>Event Type</Label>
            <Select
              value={filters.eventType}
              onChange={(e) => handleFilterChange('eventType', e.target.value)}
            >
              <option value="">All Types</option>
              <option value="fault">Faults</option>
              <option value="alarm">Alarms</option>
              <option value="warning">Warnings</option>
              <option value="maintenance">Maintenance</option>
              <option value="operation">Operations</option>
            </Select>
          </FilterGroup>

          <FilterGroup>
            <Label>Severity</Label>
            <Select
              value={filters.severity}
              onChange={(e) => handleFilterChange('severity', e.target.value)}
            >
              <option value="">All Severities</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </Select>
          </FilterGroup>
        </FilterGrid>
      </FilterContainer>

      <LogsContainer>
        <StatsBar>
          <StatChip>
            <strong>{stats.total}</strong> Total Events
          </StatChip>
          <StatChip>
            <strong>{stats.faults}</strong> Faults
          </StatChip>
          <StatChip>
            <strong>{stats.alarms}</strong> Alarms
          </StatChip>
          <StatChip>
            <strong>{stats.warnings}</strong> Warnings
          </StatChip>
          <StatChip>
            <strong>{stats.unacknowledged}</strong> Unacknowledged
          </StatChip>
        </StatsBar>

        {loading ? (
          <EmptyState>Loading logs...</EmptyState>
        ) : filteredLogs.length === 0 ? (
          <EmptyState>No logs found for the selected filters</EmptyState>
        ) : (
          <>
            {paginatedLogs.map((log, index) => (
              <LogEntry key={index} severity={log.severity}>
                <LogHeader>
                  <LogType>
                    {getEventIcon(log.type)}
                    {log.type.charAt(0).toUpperCase() + log.type.slice(1)}
                  </LogType>
                  <LogTime>
                    {new Date(log.timestamp).toLocaleString('en-IN', {
                      timeZone: 'Asia/Kolkata',
                      year: 'numeric',
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                      second: '2-digit'
                    })}
                  </LogTime>
                </LogHeader>
                <LogDescription>{log.description}</LogDescription>
                <LogMeta>
                  <SeverityBadge severity={log.severity}>
                    {log.severity}
                  </SeverityBadge>
                  {log.acknowledged && (
                    <MetaTag>✓ Acknowledged</MetaTag>
                  )}
                  {log.duration && (
                    <MetaTag>Duration: {log.duration}min</MetaTag>
                  )}
                </LogMeta>
              </LogEntry>
            ))}

            {totalPages > 1 && (
              <PaginationContainer>
                <PaginationInfo>
                  Showing {startIndex + 1}-{Math.min(startIndex + itemsPerPage, filteredLogs.length)} of {filteredLogs.length}
                </PaginationInfo>
                <PaginationControls>
                  <PageButton
                    onClick={() => setCurrentPage(prev => prev - 1)}
                    disabled={currentPage === 1}
                  >
                    Previous
                  </PageButton>
                  {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
                    <PageButton
                      key={page}
                      active={currentPage === page}
                      onClick={() => setCurrentPage(page)}
                    >
                      {page}
                    </PageButton>
                  ))}
                  <PageButton
                    onClick={() => setCurrentPage(prev => prev + 1)}
                    disabled={currentPage === totalPages}
                  >
                    Next
                  </PageButton>
                </PaginationControls>
              </PaginationContainer>
            )}
          </>
        )}
      </LogsContainer>
    </LoggingContainer>
  );
};

export default Logging;
