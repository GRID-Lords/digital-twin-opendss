import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { FileText, Filter, Download, RefreshCw, AlertCircle, Info, AlertTriangle, CheckCircle, X, ExternalLink, Gauge } from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';
import ReactMarkdown from 'react-markdown';

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

// Dialog Components
const DialogOverlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 2rem;
`;

const DialogContainer = styled.div`
  background: white;
  border-radius: 12px;
  max-width: 800px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
`;

const DialogHeader = styled.div`
  padding: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f8fafc;
`;

const DialogTitle = styled.h2`
  color: #1e293b;
  font-size: 1.25rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin: 0;

  svg {
    width: 24px;
    height: 24px;
  }
`;

const CloseButton = styled.button`
  background: none;
  border: none;
  cursor: pointer;
  color: #64748b;
  padding: 0.5rem;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;

  &:hover {
    background: #e2e8f0;
    color: #1e293b;
  }

  svg {
    width: 20px;
    height: 20px;
  }
`;

const DialogBody = styled.div`
  padding: 1.5rem;
  overflow-y: auto;
  flex: 1;
`;

const DialogMeta = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: #f8fafc;
  border-radius: 8px;
`;

const MetaItem = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
`;

const MetaLabel = styled.span`
  color: #64748b;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
`;

const MetaValue = styled.span`
  color: #1e293b;
  font-size: 0.875rem;
  font-weight: 500;
`;

const ActionSection = styled.div`
  margin-top: 1.5rem;
  padding: 1rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
`;

const ActionTitle = styled.h3`
  color: #1e293b;
  font-size: 0.9375rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
`;

const ActionGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
`;

const MarkdownContent = styled.div`
  color: #334155;
  font-size: 0.9375rem;
  line-height: 1.7;
  margin-top: 2rem;

  h1, h2, h3, h4, h5, h6 {
    color: #1e293b;
    margin-top: 1.5rem;
    margin-bottom: 0.75rem;
    font-weight: 600;
  }

  h1 { font-size: 1.5rem; }
  h2 { font-size: 1.25rem; }
  h3 { font-size: 1.1rem; }

  p {
    margin-bottom: 1rem;
  }

  ul, ol {
    margin-left: 1.5rem;
    margin-bottom: 1rem;
  }

  li {
    margin-bottom: 0.5rem;
  }

  strong {
    color: #1e293b;
    font-weight: 600;
  }

  code {
    background: #f1f5f9;
    padding: 0.125rem 0.375rem;
    border-radius: 4px;
    font-size: 0.875em;
    font-family: 'Courier New', monospace;
  }

  pre {
    background: #f1f5f9;
    padding: 1rem;
    border-radius: 6px;
    overflow-x: auto;
    margin-bottom: 1rem;
  }

  blockquote {
    border-left: 4px solid #3b82f6;
    padding-left: 1rem;
    margin-left: 0;
    color: #64748b;
    font-style: italic;
  }
`;

const ViewDetailsButton = styled.button`
  background: #3b82f6;
  color: white;
  border: none;
  padding: 0.375rem 0.75rem;
  border-radius: 4px;
  font-size: 0.75rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.375rem;
  transition: all 0.2s;
  font-weight: 500;

  &:hover {
    background: #2563eb;
  }

  svg {
    width: 14px;
    height: 14px;
  }
`;

const SystemStateSection = styled.div`
  margin: 1.5rem 0;
  padding: 1rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
`;

const SystemStateTitle = styled.h3`
  color: #1e293b;
  font-size: 0.9375rem;
  font-weight: 600;
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

const SystemStateGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.75rem;
`;

const StateItem = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
`;

const StateLabel = styled.div`
  font-size: 0.75rem;
  color: #64748b;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const StateValue = styled.div`
  font-size: 0.9375rem;
  color: #1e293b;
  font-weight: 600;
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
  const [selectedAlert, setSelectedAlert] = useState(null);
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

  const handleAssigneeChange = async (alertId, assignee) => {
    try {
      await axios.post('/api/alerts/assign', {
        alert_id: alertId,
        assignee: assignee
      });
      toast.success(`Alert assigned to ${assignee}`);

      // Update local state
      setLogs(logs.map(log =>
        log.id === alertId ? { ...log, assignee: assignee } : log
      ));
      if (selectedAlert && selectedAlert.id === alertId) {
        setSelectedAlert({ ...selectedAlert, assignee: assignee });
      }

      fetchLogs(); // Refresh to get updated data
    } catch (error) {
      toast.error('Failed to assign alert');
      console.error('Error assigning alert:', error);
    }
  };

  const handleStatusChange = async (alertId, status) => {
    try {
      await axios.post('/api/alerts/status', {
        alert_id: alertId,
        status: status
      });
      toast.success(`Alert status updated to ${status}`);

      // Update local state
      setLogs(logs.map(log =>
        log.id === alertId ? { ...log, status: status, resolved: status === 'resolved' } : log
      ));
      if (selectedAlert && selectedAlert.id === alertId) {
        setSelectedAlert({ ...selectedAlert, status: status, resolved: status === 'resolved' });
      }

      fetchLogs(); // Refresh to get updated data
    } catch (error) {
      toast.error('Failed to update alert status');
      console.error('Error updating alert status:', error);
    }
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

  const getSummary = (description) => {
    if (!description) return '';
    // Extract first line or first sentence before **
    const firstLine = description.split('\n')[0];
    // Limit to 120 characters
    return firstLine.length > 120 ? firstLine.substring(0, 120) + '...' : firstLine;
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
                <LogDescription>{getSummary(log.description)}</LogDescription>
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
                  <ViewDetailsButton onClick={() => setSelectedAlert(log)}>
                    <ExternalLink />
                    View Details
                  </ViewDetailsButton>
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

      {/* Alert Details Dialog */}
      {selectedAlert && (
        <DialogOverlay onClick={() => setSelectedAlert(null)}>
          <DialogContainer onClick={(e) => e.stopPropagation()}>
            <DialogHeader>
              <DialogTitle>
                {getEventIcon(selectedAlert.type)}
                Alert Details
              </DialogTitle>
              <CloseButton onClick={() => setSelectedAlert(null)}>
                <X />
              </CloseButton>
            </DialogHeader>

            <DialogBody>
              <DialogMeta>
                <MetaItem>
                  <MetaLabel>Type</MetaLabel>
                  <MetaValue>{selectedAlert.type?.charAt(0).toUpperCase() + selectedAlert.type?.slice(1)}</MetaValue>
                </MetaItem>
                <MetaItem>
                  <MetaLabel>Severity</MetaLabel>
                  <MetaValue>
                    <SeverityBadge severity={selectedAlert.severity}>
                      {selectedAlert.severity}
                    </SeverityBadge>
                  </MetaValue>
                </MetaItem>
                <MetaItem>
                  <MetaLabel>Asset ID</MetaLabel>
                  <MetaValue>{selectedAlert.asset_id || 'N/A'}</MetaValue>
                </MetaItem>
                <MetaItem>
                  <MetaLabel>Timestamp</MetaLabel>
                  <MetaValue>
                    {new Date(selectedAlert.timestamp).toLocaleString('en-IN', {
                      timeZone: 'Asia/Kolkata',
                      year: 'numeric',
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                      second: '2-digit'
                    })}
                  </MetaValue>
                </MetaItem>
                <MetaItem>
                  <MetaLabel>Current Status</MetaLabel>
                  <MetaValue style={{ textTransform: 'capitalize' }}>
                    {selectedAlert.status || 'Pending'}
                  </MetaValue>
                </MetaItem>
                <MetaItem>
                  <MetaLabel>Assigned To</MetaLabel>
                  <MetaValue>{selectedAlert.assignee || 'Unassigned'}</MetaValue>
                </MetaItem>
                {selectedAlert.acknowledged !== undefined && (
                  <MetaItem>
                    <MetaLabel>Acknowledged</MetaLabel>
                    <MetaValue>{selectedAlert.acknowledged ? '✓ Yes' : 'No'}</MetaValue>
                  </MetaItem>
                )}
                {selectedAlert.duration && (
                  <MetaItem>
                    <MetaLabel>Duration</MetaLabel>
                    <MetaValue>{selectedAlert.duration} minutes</MetaValue>
                  </MetaItem>
                )}
              </DialogMeta>

              {/* Action Section for Assignee and Status */}
              <ActionSection>
                <ActionTitle>Alert Management</ActionTitle>
                <ActionGrid>
                  <FilterGroup>
                    <Label>Assign To</Label>
                    <Select
                      value={selectedAlert.assignee || ''}
                      onChange={(e) => handleAssigneeChange(selectedAlert.id, e.target.value)}
                    >
                      <option value="">Unassigned</option>
                      <option value="Person 1">Person 1</option>
                      <option value="Person 2">Person 2</option>
                      <option value="Person 3">Person 3</option>
                      <option value="Person 4">Person 4</option>
                    </Select>
                  </FilterGroup>

                  <FilterGroup>
                    <Label>Status</Label>
                    <Select
                      value={selectedAlert.status || 'pending'}
                      onChange={(e) => handleStatusChange(selectedAlert.id, e.target.value)}
                    >
                      <option value="pending">Pending</option>
                      <option value="in_progress">In Progress</option>
                      <option value="investigating">Investigating</option>
                      <option value="resolved">Resolved</option>
                      <option value="closed">Closed</option>
                    </Select>
                  </FilterGroup>
                </ActionGrid>
              </ActionSection>

              {/* System State at Time of Anomaly */}
              {selectedAlert.data && typeof selectedAlert.data === 'string' &&
               (() => {
                 try {
                   const parsedData = JSON.parse(selectedAlert.data);
                   return parsedData.system_state && Object.keys(parsedData.system_state).length > 0 ? (
                     <SystemStateSection>
                       <SystemStateTitle>
                         <Gauge />
                         System State at Time of Anomaly
                       </SystemStateTitle>
                       <SystemStateGrid>
                         {parsedData.system_state.total_power_mw !== undefined && (
                           <StateItem>
                             <StateLabel>Total Power</StateLabel>
                             <StateValue>{parsedData.system_state.total_power_mw} MW</StateValue>
                           </StateItem>
                         )}
                         {parsedData.system_state.voltage_400kv !== undefined && (
                           <StateItem>
                             <StateLabel>Voltage 400kV</StateLabel>
                             <StateValue>{parsedData.system_state.voltage_400kv} kV</StateValue>
                           </StateItem>
                         )}
                         {parsedData.system_state.voltage_220kv !== undefined && (
                           <StateItem>
                             <StateLabel>Voltage 220kV</StateLabel>
                             <StateValue>{parsedData.system_state.voltage_220kv} kV</StateValue>
                           </StateItem>
                         )}
                         {parsedData.system_state.frequency_hz !== undefined && (
                           <StateItem>
                             <StateLabel>Frequency</StateLabel>
                             <StateValue>{parsedData.system_state.frequency_hz} Hz</StateValue>
                           </StateItem>
                         )}
                         {parsedData.system_state.power_factor !== undefined && (
                           <StateItem>
                             <StateLabel>Power Factor</StateLabel>
                             <StateValue>{parsedData.system_state.power_factor}</StateValue>
                           </StateItem>
                         )}
                         {parsedData.system_state.efficiency !== undefined && (
                           <StateItem>
                             <StateLabel>Efficiency</StateLabel>
                             <StateValue>{parsedData.system_state.efficiency}%</StateValue>
                           </StateItem>
                         )}
                         {parsedData.system_state.losses_mw !== undefined && (
                           <StateItem>
                             <StateLabel>Losses</StateLabel>
                             <StateValue>{parsedData.system_state.losses_mw} MW</StateValue>
                           </StateItem>
                         )}
                         {parsedData.system_state.generation_mw !== undefined && (
                           <StateItem>
                             <StateLabel>Generation</StateLabel>
                             <StateValue>{parsedData.system_state.generation_mw} MW</StateValue>
                           </StateItem>
                         )}
                         {parsedData.system_state.total_load_mw !== undefined && (
                           <StateItem>
                             <StateLabel>Total Load</StateLabel>
                             <StateValue>{parsedData.system_state.total_load_mw} MW</StateValue>
                           </StateItem>
                         )}
                       </SystemStateGrid>
                     </SystemStateSection>
                   ) : null;
                 } catch (e) {
                   return null;
                 }
               })()
              }

              <MarkdownContent>
                <ReactMarkdown>{selectedAlert.description}</ReactMarkdown>
              </MarkdownContent>
            </DialogBody>
          </DialogContainer>
        </DialogOverlay>
      )}
    </LoggingContainer>
  );
};

export default Logging;
