import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import { useDigitalTwin } from '../context/DigitalTwinContext';
import { FiTrendingUp, FiAlertTriangle, FiTarget, FiBarChart } from 'react-icons/fi';

const AnalyticsContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 2rem;
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
  font-weight: 600;
`;

const AnalyticsGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  
  @media (max-width: 1200px) {
    grid-template-columns: 1fr;
  }
`;

const AnalyticsSection = styled.div`
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
  padding: 1.5rem;
  color: #f1f5f9;
`;

const SectionTitle = styled.h3`
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: #f1f5f9;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const AnomalyItem = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
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
  font-size: 0.9rem;
  font-weight: 500;
`;

const AnomalyScore = styled.div`
  font-size: 0.8rem;
  color: #94a3b8;
`;

const AnomalySeverity = styled.div`
  font-size: 0.8rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  background: ${props => props.severity === 'high' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(245, 158, 11, 0.2)'};
  color: ${props => props.severity === 'high' ? '#ef4444' : '#f59e0b'};
  font-weight: 500;
  text-transform: uppercase;
`;

const PredictionItem = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  margin-bottom: 0.5rem;
`;

const PredictionInfo = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
`;

const PredictionAsset = styled.div`
  font-size: 0.9rem;
  font-weight: 500;
`;

const PredictionHealth = styled.div`
  font-size: 0.8rem;
  color: #94a3b8;
`;

const PredictionUrgency = styled.div`
  font-size: 0.8rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  background: ${props => {
    switch (props.urgency) {
      case 'critical': return 'rgba(239, 68, 68, 0.2)';
      case 'high': return 'rgba(245, 158, 11, 0.2)';
      case 'medium': return 'rgba(59, 130, 246, 0.2)';
      default: return 'rgba(107, 114, 128, 0.2)';
    }
  }};
  color: ${props => {
    switch (props.urgency) {
      case 'critical': return '#ef4444';
      case 'high': return '#f59e0b';
      case 'medium': return '#3b82f6';
      default: return '#6b7280';
    }
  }};
  font-weight: 500;
  text-transform: uppercase;
`;

const OptimizationItem = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  margin-bottom: 0.5rem;
`;

const OptimizationInfo = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
`;

const OptimizationAction = styled.div`
  font-size: 0.9rem;
  font-weight: 500;
`;

const OptimizationDescription = styled.div`
  font-size: 0.8rem;
  color: #94a3b8;
`;

const OptimizationPriority = styled.div`
  font-size: 0.8rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  background: ${props => {
    switch (props.priority) {
      case 'high': return 'rgba(239, 68, 68, 0.2)';
      case 'medium': return 'rgba(245, 158, 11, 0.2)';
      case 'low': return 'rgba(59, 130, 246, 0.2)';
      default: return 'rgba(107, 114, 128, 0.2)';
    }
  }};
  color: ${props => {
    switch (props.priority) {
      case 'high': return '#ef4444';
      case 'medium': return '#f59e0b';
      case 'low': return '#3b82f6';
      default: return '#6b7280';
    }
  }};
  font-weight: 500;
  text-transform: uppercase;
`;

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
            <div style={{ color: '#94a3b8', textAlign: 'center', padding: '2rem' }}>
              No anomalies detected
            </div>
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
            <div style={{ color: '#94a3b8', textAlign: 'center', padding: '2rem' }}>
              No predictions available
            </div>
          )}
        </AnalyticsSection>
      </AnalyticsGrid>

      <AnalyticsSection>
        <SectionTitle>
          <FiTarget />
          Optimization Recommendations
        </SectionTitle>
        {optimization.recommendations ? (
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
          <div style={{ color: '#94a3b8', textAlign: 'center', padding: '2rem' }}>
            No optimization recommendations available
          </div>
        )}
        
        {optimization.optimization_score && (
          <div style={{ 
            marginTop: '1rem', 
            padding: '1rem', 
            background: 'rgba(255, 255, 255, 0.05)', 
            borderRadius: '8px',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '0.9rem', color: '#94a3b8', marginBottom: '0.5rem' }}>
              Overall Optimization Score
            </div>
            <div style={{ fontSize: '2rem', fontWeight: '600', color: '#4ade80' }}>
              {optimization.optimization_score.toFixed(1)}%
            </div>
          </div>
        )}
      </AnalyticsSection>
    </AnalyticsContainer>
  );
};

export default Analytics;