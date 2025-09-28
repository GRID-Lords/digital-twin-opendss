import React from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';

const Card = styled(motion.div)`
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 1.5rem;
  color: white;
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
  }
`;

const CardHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
`;

const CardTitle = styled.h3`
  font-size: 0.9rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.8);
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const CardIcon = styled.div`
  font-size: 1.5rem;
  opacity: 0.8;
`;

const CardValue = styled.div`
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  color: ${props => props.color || 'white'};
`;

const CardTrend = styled.div`
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.8rem;
  color: ${props => props.positive ? '#4ade80' : '#ef4444'};
  font-weight: 500;
`;

const TrendIcon = styled.span`
  font-size: 0.7rem;
`;

const MetricCard = ({ title, value, icon, color, trend }) => {
  const isPositive = trend?.startsWith('+');
  
  return (
    <Card
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      whileHover={{ scale: 1.02 }}
    >
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardIcon>{icon}</CardIcon>
      </CardHeader>
      <CardValue color={color}>{value}</CardValue>
      {trend && (
        <CardTrend positive={isPositive}>
          <TrendIcon>{isPositive ? '↗' : '↘'}</TrendIcon>
          {trend}
        </CardTrend>
      )}
    </Card>
  );
};

export default MetricCard;