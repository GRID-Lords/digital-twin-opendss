import React from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';

const Card = styled(motion.div)`
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  padding: 1.25rem;
  transition: all 0.2s ease;

  &:hover {
    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -1px rgb(0 0 0 / 0.06);
    border-color: #cbd5e1;
  }
`;

const CardHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
`;

const CardTitle = styled.h3`
  font-size: 0.8125rem;
  font-weight: 500;
  color: #64748b;
  letter-spacing: 0.01em;
`;

const CardIcon = styled.div`
  font-size: 1.25rem;
`;

const CardValue = styled.div`
  font-size: 1.75rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #0f172a;
`;

const CardTrend = styled.div`
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.8125rem;
  color: ${props => props.positive ? '#16a34a' : '#dc2626'};
  font-weight: 500;
  background: ${props => props.positive ? '#f0fdf4' : '#fef2f2'};
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;
  width: fit-content;
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