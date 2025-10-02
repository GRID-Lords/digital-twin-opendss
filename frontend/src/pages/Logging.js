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
  margin-bottom: 1rem;
`;

const Title = styled.h1`
  color: #f1f5f9;
  font-size: 2rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 0.5rem;

  svg {
    color: #64748b;
  }
`;

const Controls = styled.div`
  display: flex;
  gap: 1rem;
  align-items: center;
`;

const FilterContainer = styled.div`
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
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
  color: #94a3b8;
  font-size: 0.875rem;
  font-weight: 500;
`;

const Select = styled.select`
  background: #0f172a;
  border: 1px solid #334155;
  color: #f1f5f9;
  padding: 0.5rem;
  border-radius: 6px;
  font-size: 0.875rem;

  &:focus {
    outline: none;
    border-color: #3b82f6;
  }
`;

const Input = styled.input`
  background: #0f172a;
  border: 1px solid #334155;
  color: #f1f5f9;
  padding: 0.5rem;
  border-radius: 6px;
  font-size: 0.875rem;

  &:focus {
    outline: none;
    border-color: #3b82f6;
  }
`;

const Button = styled.button`
  background: ${props => props.variant === 'primary' ? '#3b82f6' : '#334155'};
  border: 1px solid ${props => props.variant === 'primary' ? '#3b82f6' : '#475569'};
  color: #f1f5f9;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;

  &:hover {
    background: ${props => props.variant === 'primary' ? '#2563eb' : '#475569'};
  }

  svg {
    width: 16px;
    height: 16px;
  }
`;

const LogsContainer = styled.div`
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
  max-height: 600px;
  overflow-y: auto;
`;

const LogEntry = styled.div`
  background: #0f172a;
  border: 1px solid #334155;
  border-left: 3px solid ${props => {
    switch (props.severity) {
      case 'high': return '#ef4444';
      case 'medium': return '#f59e0b';
      case 'low': return '#10b981';
      default: return '#3b82f6';
    }
  }};
  border-radius: 6px;
  padding: 1rem;
  margin-bottom: 0.75rem;
  transition: all 0.2s;

  &:hover {
    background: #1e293b;
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
  color: #f1f5f9;
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
  color: #cbd5e1;
  font-size: 0.875rem;
  margin-bottom: 0.5rem;
`;

const LogMeta = styled.div`
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
`;

const MetaTag = styled.span`
  background: #334155;
  color: #94a3b8;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
`;

const SeverityBadge = styled.span`
  background: ${props => {
    switch (props.severity) {
      case 'high': return '#fee2e2';
      case 'medium': return '#fed7aa';
      case 'low': return '#dcfce7';
      default: return '#dbeafe';
    }
  }};
  color: ${props => {
    switch (props.severity) {
      case 'high': return '#991b1b';
      case 'medium': return '#c2410c';
      case 'low': return '#166534';
      default: return '#1e40af';
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

const StatsBar = styled.div`
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
`;

const StatChip = styled.div`
  background: #0f172a;
  border: 1px solid #334155;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #cbd5e1;
  font-size: 0.875rem;

  strong {
    color: #f1f5f9;
    font-weight: 600;
  }
`;

const Logging = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    days: 7,
    eventType: '',
    severity: ''
  });

  useEffect(() => {
    fetchLogs();
  }, []);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/historical/system-events', {
        params: {
          days: filters.days,
          event_type: filters.eventType || undefined
        }
      });
      setLogs(response.data.events || []);
    } catch (error) {
      toast.error('Failed to fetch logs');
      console.error('Error fetching logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({ ...prev, [field]: value }));
  };

  const applyFilters = () => {
    fetchLogs();
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
    return true;
  });

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

          <FilterGroup style={{ display: 'flex', alignItems: 'flex-end' }}>
            <Button variant="primary" onClick={applyFilters}>
              Apply Filters
            </Button>
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
          filteredLogs.map((log, index) => (
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
          ))
        )}
      </LogsContainer>
    </LoggingContainer>
  );
};

export default Logging;
