import React from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';

const Card = styled(motion.div)`
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
  padding: 1.5rem;
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.3);
  }
`;

const CardHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
`;

const CardTitle = styled.h3`
  font-size: 0.875rem;
  font-weight: 500;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.025em;
`;

const CardIcon = styled.div`
  font-size: 1.5rem;
`;

const CardValue = styled.div`
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  color: #f1f5f9;
`;

const CardTrend = styled.div`
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.875rem;
  color: ${props => props.positive ? '#10b981' : '#ef4444'};
  font-weight: 500;
`;

const TrendIcon = styled.span`
  font-size: 0.875rem;
  font-weight: 600;
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
        {icon && <CardIcon style={{ color }}>{icon}</CardIcon>}
      </CardHeader>
      <CardValue color={color}>{value}</CardValue>
      {trend && (
        <CardTrend positive={isPositive}>
          <TrendIcon></TrendIcon>
          {trend}
        </CardTrend>
      )}
    </Card>
  );
};

export default MetricCard;