import React, { useEffect, useState } from 'react';
import styled from 'styled-components';
import { useDigitalTwin } from '../context/DigitalTwinContext';
import { Database, Clock, HardDrive, Trash2, RefreshCw, Activity } from 'lucide-react';
import toast from 'react-hot-toast';

const Container = styled.div`
  background: #1e293b;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
`;

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
`;

const Title = styled.h2`
  color: #f1f5f9;
  font-size: 1.25rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.5rem;

  svg {
    color: #64748b;
  }
`;

const RefreshButton = styled.button`
  background: #334155;
  border: 1px solid #475569;
  color: #f1f5f9;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s;

  &:hover {
    background: #475569;
  }

  svg {
    width: 16px;
    height: 16px;
  }
`;

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
`;

const StatCard = styled.div`
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 8px;
  padding: 1rem;
`;

const StatLabel = styled.div`
  color: #94a3b8;
  font-size: 0.875rem;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;

  svg {
    width: 14px;
    height: 14px;
  }
`;

const StatValue = styled.div`
  color: #f1f5f9;
  font-size: 1.5rem;
  font-weight: 600;
`;

const StatDetail = styled.div`
  color: #64748b;
  font-size: 0.75rem;
  margin-top: 0.25rem;
`;

const Section = styled.div`
  margin-top: 1.5rem;
`;

const SectionTitle = styled.h3`
  color: #cbd5e1;
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 1rem;
`;

const InfoGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.5rem;
`;

const InfoRow = styled.div`
  display: flex;
  justify-content: space-between;
  padding: 0.5rem;
  background: #0f172a;
  border-radius: 4px;
`;

const InfoLabel = styled.span`
  color: #94a3b8;
  font-size: 0.875rem;
`;

const InfoValue = styled.span`
  color: #f1f5f9;
  font-size: 0.875rem;
  font-weight: 500;
`;

const ActionButtons = styled.div`
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
`;

const ActionButton = styled.button`
  background: ${props => props.danger ? '#dc2626' : '#6366f1'};
  border: none;
  color: white;
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s;

  &:hover {
    opacity: 0.9;
  }

  svg {
    width: 16px;
    height: 16px;
  }
`;

const DataManagement = () => {
  const {
    cacheStats,
    historicalMetrics,
    fetchCacheStats,
    fetchHistoricalMetrics,
    triggerDataCleanup
  } = useDigitalTwin();

  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Fetch cache stats on mount
    fetchCacheStats();
  }, []);

  const handleRefresh = async () => {
    setLoading(true);
    try {
      await fetchCacheStats();
      await fetchHistoricalMetrics(24);
      toast.success('Data statistics refreshed');
    } catch (error) {
      toast.error('Failed to refresh statistics');
    } finally {
      setLoading(false);
    }
  };

  const handleCleanup = async () => {
    if (window.confirm('This will remove old data from the database. Continue?')) {
      try {
        await triggerDataCleanup();
        await fetchCacheStats();
      } catch (error) {
        toast.error('Cleanup failed');
      }
    }
  };

  const formatTime = (timestamp) => {
    if (!timestamp) return 'N/A';
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <Container>
      <Header>
        <Title>
          <Database />
          Data Management & Storage
        </Title>
        <RefreshButton onClick={handleRefresh} disabled={loading}>
          <RefreshCw />
          Refresh
        </RefreshButton>
      </Header>

      <StatsGrid>
        <StatCard>
          <StatLabel>
            <Activity />
            Real-time Cache
          </StatLabel>
          <StatValue>{cacheStats.memory_cache_size || 0}</StatValue>
          <StatDetail>Items in cache</StatDetail>
        </StatCard>

        <StatCard>
          <StatLabel>
            <HardDrive />
            Buffer Size
          </StatLabel>
          <StatValue>{cacheStats.buffer_size || 0}</StatValue>
          <StatDetail>Pending storage</StatDetail>
        </StatCard>

        <StatCard>
          <StatLabel>
            <Clock />
            Last Storage
          </StatLabel>
          <StatValue>{formatTime(cacheStats.last_storage)}</StatValue>
          <StatDetail>Database write</StatDetail>
        </StatCard>

        <StatCard>
          <StatLabel>
            <Database />
            Historical Data
          </StatLabel>
          <StatValue>{historicalMetrics?.length || 0}</StatValue>
          <StatDetail>Records (24h)</StatDetail>
        </StatCard>
      </StatsGrid>

      <Section>
        <SectionTitle>Storage Configuration</SectionTitle>
        <InfoGrid>
          <InfoRow>
            <InfoLabel>Cache TTL:</InfoLabel>
            <InfoValue>{cacheStats.cache_ttl || 60} seconds</InfoValue>
          </InfoRow>
          <InfoRow>
            <InfoLabel>Storage Interval:</InfoLabel>
            <InfoValue>{(cacheStats.storage_interval || 3600) / 60} minutes</InfoValue>
          </InfoRow>
          <InfoRow>
            <InfoLabel>Redis Status:</InfoLabel>
            <InfoValue style={{ color: cacheStats.redis_connected ? '#10b981' : '#ef4444' }}>
              {cacheStats.redis_connected ? 'Connected' : 'Disconnected'}
            </InfoValue>
          </InfoRow>
          <InfoRow>
            <InfoLabel>Redis Keys:</InfoLabel>
            <InfoValue>{cacheStats.redis_keys || 0}</InfoValue>
          </InfoRow>
        </InfoGrid>
      </Section>

      <Section>
        <SectionTitle>Storage Strategy</SectionTitle>
        <InfoGrid>
          <InfoRow>
            <InfoLabel>Real-time Data:</InfoLabel>
            <InfoValue>Cached only (not stored)</InfoValue>
          </InfoRow>
          <InfoRow>
            <InfoLabel>Metrics Storage:</InfoLabel>
            <InfoValue>Every hour (aggregated)</InfoValue>
          </InfoRow>
          <InfoRow>
            <InfoLabel>Critical Events:</InfoLabel>
            <InfoValue>Immediate storage</InfoValue>
          </InfoRow>
          <InfoRow>
            <InfoLabel>Data Retention:</InfoLabel>
            <InfoValue>30 days</InfoValue>
          </InfoRow>
        </InfoGrid>
      </Section>

      <ActionButtons>
        <ActionButton onClick={handleCleanup} danger>
          <Trash2 />
          Clean Old Data
        </ActionButton>
      </ActionButtons>
    </Container>
  );
};

export default DataManagement;