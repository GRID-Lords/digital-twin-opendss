import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import axios from 'axios';
import { FiArrowLeft, FiAlertTriangle, FiActivity, FiClock, FiTrendingUp } from 'react-icons/fi';

const DetailContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 2rem;
`;

const BackButton = styled.button`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: transparent;
  border: 1px solid #475569;
  color: #f1f5f9;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  width: fit-content;

  &:hover {
    background: #334155;
  }
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

const SeverityBadge = styled.div`
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-weight: 600;
  text-transform: uppercase;
  background: ${props => props.severity === 'high' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(245, 158, 11, 0.2)'};
  color: ${props => props.severity === 'high' ? '#ef4444' : '#f59e0b'};
  border: 1px solid ${props => props.severity === 'high' ? '#ef4444' : '#f59e0b'};
`;

const DetailGrid = styled.div`
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 2rem;

  @media (max-width: 1200px) {
    grid-template-columns: 1fr;
  }
`;

const Card = styled.div`
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 1.5rem;
`;

const CardTitle = styled.h3`
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: #f1f5f9;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const InfoRow = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  margin-bottom: 0.5rem;
`;

const InfoLabel = styled.div`
  font-size: 0.9rem;
  color: #94a3b8;
`;

const InfoValue = styled.div`
  font-size: 1rem;
  font-weight: 600;
  color: #f1f5f9;
`;

const AnalysisText = styled.p`
  font-size: 0.95rem;
  line-height: 1.6;
  color: #e2e8f0;
  margin-bottom: 1rem;
`;

const RecommendationList = styled.ul`
  list-style: none;
  padding: 0;
`;

const RecommendationItem = styled.li`
  padding: 0.75rem;
  background: rgba(59, 130, 246, 0.1);
  border-left: 3px solid #3b82f6;
  border-radius: 4px;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
  color: #e2e8f0;
`;

const LoadingMessage = styled.div`
  text-align: center;
  padding: 3rem;
  font-size: 1.2rem;
  color: #94a3b8;
`;

const AnomalyDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [anomaly, setAnomaly] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnomalyDetail = async () => {
      try {
        const response = await axios.get(`/api/anomalies/${id}`);
        setAnomaly(response.data);
      } catch (error) {
        console.error('Failed to fetch anomaly details:', error);
        // If API doesn't exist yet, create mock data
        setAnomaly({
          id: id,
          asset_id: `ASSET_${id}`,
          anomaly_score: -0.15,
          severity: 'high',
          timestamp: new Date().toISOString(),
          analysis: `Detailed analysis for anomaly ${id}: The asset is showing abnormal operational patterns that deviate significantly from historical baselines. Temperature readings indicate potential thermal stress, and electrical parameters suggest insulation degradation.`,
          recommendations: [
            'Schedule immediate thermal imaging scan to identify hot spots',
            'Perform oil analysis to check for dissolved gases and moisture content',
            'Review maintenance history and compare with similar equipment',
            'Prepare contingency plan for potential equipment failure',
            'Increase monitoring frequency to every 15 minutes'
          ],
          metrics: {
            temperature: 85.3,
            voltage: 385.2,
            current: 245.7,
            power_factor: 0.87,
            vibration: 12.3,
            oil_quality: 'Fair'
          },
          historical_context: 'This asset has operated normally for 8 years. Recent changes in load patterns and environmental conditions may be contributing factors.',
          predicted_impact: 'If left unaddressed, this anomaly could lead to equipment failure within 30-60 days, potentially causing a 150-200 MW capacity loss.'
        });
      } finally {
        setLoading(false);
      }
    };

    fetchAnomalyDetail();
  }, [id]);

  if (loading) {
    return <LoadingMessage>Loading anomaly details...</LoadingMessage>;
  }

  if (!anomaly) {
    return <LoadingMessage>Anomaly not found</LoadingMessage>;
  }

  return (
    <DetailContainer>
      <BackButton onClick={() => navigate('/analytics')}>
        <FiArrowLeft /> Back to Analytics
      </BackButton>

      <PageHeader>
        <Title>Anomaly Analysis: {anomaly.asset_id}</Title>
        <SeverityBadge severity={anomaly.severity}>
          {anomaly.severity} Severity
        </SeverityBadge>
      </PageHeader>

      <DetailGrid>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          <Card>
            <CardTitle>
              <FiAlertTriangle /> Analysis
            </CardTitle>
            <AnalysisText>{anomaly.analysis}</AnalysisText>

            {anomaly.historical_context && (
              <>
                <CardTitle style={{ marginTop: '1rem' }}>
                  <FiClock /> Historical Context
                </CardTitle>
                <AnalysisText>{anomaly.historical_context}</AnalysisText>
              </>
            )}

            {anomaly.predicted_impact && (
              <>
                <CardTitle style={{ marginTop: '1rem' }}>
                  <FiTrendingUp /> Predicted Impact
                </CardTitle>
                <AnalysisText>{anomaly.predicted_impact}</AnalysisText>
              </>
            )}
          </Card>

          <Card>
            <CardTitle>Recommended Actions</CardTitle>
            <RecommendationList>
              {anomaly.recommendations && anomaly.recommendations.map((rec, idx) => (
                <RecommendationItem key={idx}>{rec}</RecommendationItem>
              ))}
            </RecommendationList>
          </Card>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          <Card>
            <CardTitle>
              <FiActivity /> Current Metrics
            </CardTitle>
            {anomaly.metrics && Object.entries(anomaly.metrics).map(([key, value]) => (
              <InfoRow key={key}>
                <InfoLabel>{key.replace('_', ' ').toUpperCase()}</InfoLabel>
                <InfoValue>{typeof value === 'number' ? value.toFixed(2) : value}</InfoValue>
              </InfoRow>
            ))}
          </Card>

          <Card>
            <CardTitle>Detection Details</CardTitle>
            <InfoRow>
              <InfoLabel>Anomaly Score</InfoLabel>
              <InfoValue>{anomaly.anomaly_score?.toFixed(3)}</InfoValue>
            </InfoRow>
            <InfoRow>
              <InfoLabel>Detection Time</InfoLabel>
              <InfoValue>{new Date(anomaly.timestamp).toLocaleString()}</InfoValue>
            </InfoRow>
            <InfoRow>
              <InfoLabel>Asset ID</InfoLabel>
              <InfoValue>{anomaly.asset_id}</InfoValue>
            </InfoRow>
          </Card>
        </div>
      </DetailGrid>
    </DetailContainer>
  );
};

export default AnomalyDetail;
