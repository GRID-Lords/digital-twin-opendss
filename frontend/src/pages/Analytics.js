import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import { useDigitalTwin } from '../context/DigitalTwinContext';
import { FiTrendingUp, FiAlertTriangle, FiTarget } from 'react-icons/fi';

const AnalyticsContainer = styled.div`
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
  letter-spacing: -0.025em;
`;

const AnalyticsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
  gap: 1.5rem;

  @media (max-width: 1200px) {
    grid-template-columns: 1fr;
  }
`;

const AnalyticsSection = styled.div`
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
`;

const SectionTitle = styled.h3`
  font-size: 0.875rem;
  font-weight: 600;
  margin-bottom: 1.25rem;
  color: #475569;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;

  svg {
    color: #3b82f6;
    font-size: 1.25rem;
  }
`;

const AnomalyItem = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.875rem 1rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-left: 3px solid ${props => props.severity === 'high' ? '#dc2626' : '#f59e0b'};
  border-radius: 6px;
  margin-bottom: 0.5rem;
  border-left: 3px solid ${props => props.severity === 'high' ? '#ef4444' : '#f59e0b'};
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: rgba(255, 255, 255, 0.1);
    transform: translateX(4px);
  }
`;

const AnomalyInfo = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
`;

const AnomalyAsset = styled.div`
  font-size: 0.875rem;
  font-weight: 500;
  color: #334155;
`;

const AnomalyScore = styled.div`
  font-size: 0.75rem;
  color: #64748b;
`;

const AnomalySeverity = styled.div`
  font-size: 0.75rem;
  padding: 0.25rem 0.625rem;
  border-radius: 4px;
  background: ${props => props.severity === 'high' ? '#fef2f2' : '#fffbeb'};
  color: ${props => props.severity === 'high' ? '#dc2626' : '#f59e0b'};
  border: 1px solid ${props => props.severity === 'high' ? '#fca5a5' : '#fde68a'};
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
`;

const PredictionItem = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.875rem 1rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-left: 3px solid #3b82f6;
  border-radius: 6px;
  margin-bottom: 0.5rem;
  transition: all 0.2s ease;

  &:hover {
    background: #eff6ff;
  }
`;

const PredictionInfo = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
`;

const PredictionAsset = styled.div`
  font-size: 0.875rem;
  font-weight: 500;
  color: #334155;
`;

const PredictionHealth = styled.div`
  font-size: 0.75rem;
  color: #64748b;
`;

const PredictionUrgency = styled.div`
  font-size: 0.75rem;
  padding: 0.25rem 0.625rem;
  border-radius: 4px;
  background: ${props => {
    switch (props.urgency) {
      case 'critical': return '#fef2f2';
      case 'high': return '#fffbeb';
      case 'medium': return '#eff6ff';
      default: return '#f8fafc';
    }
  }};
  color: ${props => {
    switch (props.urgency) {
      case 'critical': return '#dc2626';
      case 'high': return '#f59e0b';
      case 'medium': return '#3b82f6';
      default: return '#64748b';
    }
  }};
  border: 1px solid ${props => {
    switch (props.urgency) {
      case 'critical': return '#fca5a5';
      case 'high': return '#fde68a';
      case 'medium': return '#93c5fd';
      default: return '#e2e8f0';
    }
  }};
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
`;

const OptimizationItem = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.875rem 1rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-left: 3px solid #16a34a;
  border-radius: 6px;
  margin-bottom: 0.5rem;
  transition: all 0.2s ease;

  &:hover {
    background: #f0fdf4;
  }
`;

const OptimizationInfo = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
`;

const OptimizationAction = styled.div`
  font-size: 0.875rem;
  font-weight: 500;
  color: #334155;
`;

const OptimizationDescription = styled.div`
  font-size: 0.75rem;
  color: #64748b;
`;

const OptimizationPriority = styled.div`
  font-size: 0.75rem;
  padding: 0.25rem 0.625rem;
  border-radius: 4px;
  background: ${props => {
    switch (props.priority) {
      case 'high': return '#fef2f2';
      case 'medium': return '#fffbeb';
      case 'low': return '#eff6ff';
      default: return '#f8fafc';
    }
  }};
  color: ${props => {
    switch (props.priority) {
      case 'high': return '#dc2626';
      case 'medium': return '#f59e0b';
      case 'low': return '#3b82f6';
      default: return '#64748b';
    }
  }};
  border: 1px solid ${props => {
    switch (props.priority) {
      case 'high': return '#fca5a5';
      case 'medium': return '#fde68a';
      case 'low': return '#93c5fd';
      default: return '#e2e8f0';
    }
  }};
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
`;

const EmptyState = styled.div`
  text-align: center;
  padding: 2rem;
  color: #64748b;
  font-size: 0.875rem;
`;

// Fallback AI data
const FALLBACK_ANOMALIES = [
  { asset_id: 'Transformer_T1', anomaly_score: 0.85, severity: 'high' },
  { asset_id: 'CircuitBreaker_CB3', anomaly_score: 0.72, severity: 'medium' }
];

const FALLBACK_PREDICTIONS = [
  { asset_id: 'Transformer_T2', current_health: 82.5, predicted_health: 75.3, urgency: 'medium' },
  { asset_id: 'Transformer_T1', current_health: 88.2, predicted_health: 84.6, urgency: 'low' }
];

const FALLBACK_OPTIMIZATION = {
  recommendations: [
    { action: 'Adjust load distribution', description: 'Reduce T1 load by 10% to improve efficiency', priority: 'medium' },
    { action: 'Schedule maintenance', description: 'Plan CB3 maintenance within 30 days', priority: 'high' }
  ],
  optimization_score: 87.3
};
const InsightsSection = styled.div`
  background: linear-gradient(135deg, #1e40af 0%, #7c3aed 100%);
  border: 1px solid #4f46e5;
  border-radius: 12px;
  padding: 2rem;
  margin-bottom: 2rem;
  color: #f1f5f9;
`;

const InsightsSummary = styled.div`
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 1.5rem;
  line-height: 1.6;
`;

const InsightsGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  margin-top: 1.5rem;

  @media (max-width: 1200px) {
    grid-template-columns: 1fr;
  }
`;

const InsightCard = styled.div`
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 1rem;
`;

const InsightTitle = styled.h4`
  font-size: 0.9rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #e0e7ff;
`;

const InsightList = styled.ul`
  list-style: none;
  padding: 0;
  margin: 0;
`;

const InsightItem = styled.li`
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
  padding-left: 1.25rem;
  position: relative;
  line-height: 1.5;

  &:before {
    content: "•";
    position: absolute;
    left: 0;
    color: #60a5fa;
    font-weight: bold;
  }
`;

const StatusBadge = styled.div`
  display: inline-block;
  padding: 0.5rem 1rem;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 6px;
  font-size: 0.85rem;
  margin-top: 1rem;
`;

const Analytics = () => {
  const { aiAnalysis, fetchAIAnalysis } = useDigitalTwin();
  const navigate = useNavigate();

  useEffect(() => {
    if (fetchAIAnalysis) {
      fetchAIAnalysis();
    }

  const anomalies = (aiAnalysis?.anomalies && aiAnalysis.anomalies.length > 0)
    ? aiAnalysis.anomalies
    : FALLBACK_ANOMALIES;

  const predictions = (aiAnalysis?.predictions && aiAnalysis.predictions.length > 0)
    ? aiAnalysis.predictions
    : FALLBACK_PREDICTIONS;

  const optimization = (aiAnalysis?.optimization && Object.keys(aiAnalysis.optimization).length > 0)
    ? aiAnalysis.optimization
    : FALLBACK_OPTIMIZATION;
    fetchAIAnalysis();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const anomalies = aiAnalysis.anomalies || [];
  const predictions = aiAnalysis.predictions || [];
  const optimization = aiAnalysis.optimization || {};
  const llmInsights = aiAnalysis.llm_insights || {};

  const handleAnomalyClick = (anomaly, index) => {
    navigate(`/analytics/${anomaly.asset_id || index}`);
  };

  return (
    <AnalyticsContainer>
      <PageHeader>
        <Title>AI/ML Analytics</Title>
      </PageHeader>

      {llmInsights.summary && (
        <InsightsSection>
          <InsightsSummary>{llmInsights.summary}</InsightsSummary>

          <InsightsGrid>
            {llmInsights.critical_findings && llmInsights.critical_findings.length > 0 && (
              <InsightCard>
                <InsightTitle>🔍 Critical Findings</InsightTitle>
                <InsightList>
                  {llmInsights.critical_findings.map((finding, idx) => (
                    <InsightItem key={idx}>{finding}</InsightItem>
                  ))}
                </InsightList>
              </InsightCard>
            )}

            {llmInsights.recommendations && llmInsights.recommendations.length > 0 && (
              <InsightCard>
                <InsightTitle>💡 Recommendations</InsightTitle>
                <InsightList>
                  {llmInsights.recommendations.map((rec, idx) => (
                    <InsightItem key={idx}>{rec}</InsightItem>
                  ))}
                </InsightList>
              </InsightCard>
            )}
          </InsightsGrid>

          {llmInsights.health_assessment && (
            <StatusBadge>{llmInsights.health_assessment}</StatusBadge>
          )}

          {llmInsights.operational_status && (
            <StatusBadge style={{ marginLeft: '1rem' }}>{llmInsights.operational_status}</StatusBadge>
          )}

          {llmInsights.circuit_analysis && (
            <div style={{
              marginTop: '1.5rem',
              padding: '1rem',
              background: 'rgba(59, 130, 246, 0.15)',
              borderRadius: '8px',
              borderLeft: '4px solid #3b82f6'
            }}>
              <div style={{ fontSize: '0.85rem', color: '#60a5fa', marginBottom: '0.5rem', fontWeight: 600 }}>
                🔌 CIRCUIT TOPOLOGY ANALYSIS
              </div>
              <div style={{ fontSize: '0.9rem', lineHeight: 1.6 }}>
                {llmInsights.circuit_analysis}
              </div>
            </div>
          )}
        </InsightsSection>
      )}

      <AnalyticsGrid>
        <AnalyticsSection>
          <SectionTitle>
            <FiAlertTriangle />
            Anomaly Detection
          </SectionTitle>
          {anomalies.length > 0 ? (
            anomalies.map((anomaly, index) => (
              <AnomalyItem
                key={index}
                severity={anomaly.severity}
                onClick={() => handleAnomalyClick(anomaly, index)}
              >
                <AnomalyInfo>
                  <AnomalyAsset>{anomaly.asset_id}</AnomalyAsset>
                  <AnomalyScore>Score: {anomaly.anomaly_score?.toFixed(2)}</AnomalyScore>
                </AnomalyInfo>
                <AnomalySeverity severity={anomaly.severity}>
                  {anomaly.severity}
                </AnomalySeverity>
              </AnomalyItem>
            ))
          ) : (
            <EmptyState>No anomalies detected</EmptyState>
          )}
        </AnalyticsSection>

        <AnalyticsSection>
          <SectionTitle>
            <FiTrendingUp />
            Predictive Maintenance
          </SectionTitle>
          {predictions.length > 0 ? (
            predictions.map((prediction, index) => (
              <PredictionItem key={index}>
                <PredictionInfo>
                  <PredictionAsset>{prediction.asset_id}</PredictionAsset>
                  <PredictionHealth>
                    Health: {prediction.current_health?.toFixed(1)}% → {prediction.predicted_health?.toFixed(1)}%
                  </PredictionHealth>
                </PredictionInfo>
                <PredictionUrgency urgency={prediction.urgency}>
                  {prediction.urgency}
                </PredictionUrgency>
              </PredictionItem>
            ))
          ) : (
            <EmptyState>No predictions available</EmptyState>
          )}
        </AnalyticsSection>
      </AnalyticsGrid>

      <AnalyticsSection>
        <SectionTitle>
          <FiTarget />
          Optimization Recommendations
        </SectionTitle>
        {optimization.recommendations && optimization.recommendations.length > 0 ? (
          optimization.recommendations.map((rec, index) => (
            <OptimizationItem key={index}>
              <OptimizationInfo>
                <OptimizationAction>{rec.action}</OptimizationAction>
                <OptimizationDescription>{rec.description}</OptimizationDescription>
              </OptimizationInfo>
              <OptimizationPriority priority={rec.priority}>
                {rec.priority}
              </OptimizationPriority>
            </OptimizationItem>
          ))
        ) : (
          <EmptyState>No optimization recommendations available</EmptyState>
        )}

        {optimization.optimization_score && (
          <div style={{
            marginTop: '1rem',
            padding: '1.5rem',
            background: '#eff6ff',
            borderRadius: '8px',
            textAlign: 'center',
            border: '1px solid #bfdbfe'
          }}>
            <div style={{ fontSize: '0.875rem', color: '#64748b', marginBottom: '0.5rem', fontWeight: '500' }}>
              Overall Optimization Score
            </div>
            <div style={{ fontSize: '2.5rem', fontWeight: '700', color: '#3b82f6' }}>
              {optimization.optimization_score.toFixed(1)}%
            </div>
          </div>
        )}
      </AnalyticsSection>
    </AnalyticsContainer>
  );
};

export default Analytics;