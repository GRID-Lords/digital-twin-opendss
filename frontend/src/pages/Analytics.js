import React, { useEffect } from 'react';
import styled from 'styled-components';
import { useDigitalTwin } from '../context/DigitalTwinContext';
import { FiTrendingUp, FiAlertTriangle, FiTarget, FiBarChart3 } from 'react-icons/fi';

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
  color: white;
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
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 1.5rem;
  color: white;
`;

const SectionTitle = styled.h3`
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: white;
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
  color: rgba(255, 255, 255, 0.6);
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
  color: rgba(255, 255, 255, 0.6);
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
  color: rgba(255, 255, 255, 0.6);
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

const Analytics = () => {
  const { aiAnalysis, fetchAIAnalysis } = useDigitalTwin();

  useEffect(() => {
    fetchAIAnalysis();
  }, [fetchAIAnalysis]);

  const anomalies = aiAnalysis.anomalies || [];
  const predictions = aiAnalysis.predictions || [];
  const optimization = aiAnalysis.optimization || {};

  return (
    <AnalyticsContainer>
      <PageHeader>
        <Title>🧠 AI/ML Analytics</Title>
      </PageHeader>

      <AnalyticsGrid>
        <AnalyticsSection>
          <SectionTitle>
            <FiAlertTriangle />
            Anomaly Detection
          </SectionTitle>
          {anomalies.length > 0 ? (
            anomalies.map((anomaly, index) => (
              <AnomalyItem key={index} severity={anomaly.severity}>
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
            <div style={{ color: 'rgba(255, 255, 255, 0.6)', textAlign: 'center', padding: '2rem' }}>
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
            <div style={{ color: 'rgba(255, 255, 255, 0.6)', textAlign: 'center', padding: '2rem' }}>
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
          <div style={{ color: 'rgba(255, 255, 255, 0.6)', textAlign: 'center', padding: '2rem' }}>
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
            <div style={{ fontSize: '0.9rem', color: 'rgba(255, 255, 255, 0.7)', marginBottom: '0.5rem' }}>
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