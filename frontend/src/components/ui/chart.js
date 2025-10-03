import React from 'react';
import styled from 'styled-components';

const ChartContainerWrapper = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1rem;

  [data-chart] {
    --color-1: var(--chart-1);
    --color-2: var(--chart-2);
    --color-3: var(--chart-3);
    --color-4: var(--chart-4);
    --color-5: var(--chart-5);
  }
`;

export const ChartContainer = React.forwardRef(({ config, children, className, ...props }, ref) => {
  const id = React.useId();

  return (
    <ChartContainerWrapper ref={ref} className={className} {...props}>
      <style>
        {Object.entries(config).map(
          ([key, value]) => `
            [data-chart="${id}"] {
              --color-${key}: ${value.color};
            }
          `
        ).join('')}
      </style>
      <div data-chart={id} style={{ width: '100%', height: '100%' }}>
        {children}
      </div>
    </ChartContainerWrapper>
  );
});

ChartContainer.displayName = 'ChartContainer';

const TooltipWrapper = styled.div`
  background: white;
  padding: 0.75rem;
  border-radius: 0.5rem;
  border: 1px solid hsl(214.3 31.8% 91.4%);
  box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
`;

const TooltipLabel = styled.p`
  font-size: 0.875rem;
  font-weight: 600;
  color: hsl(222.2 84% 4.9%);
  margin-bottom: 0.5rem;
`;

const TooltipContent = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
`;

const TooltipItem = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8125rem;
`;

const TooltipIndicator = styled.div`
  width: 0.625rem;
  height: 0.625rem;
  border-radius: 50%;
  background: ${props => props.color};
`;

const TooltipValue = styled.span`
  color: hsl(215.4 16.3% 46.9%);

  strong {
    color: hsl(222.2 84% 4.9%);
    font-weight: 600;
    margin-left: 0.25rem;
  }
`;

export const ChartTooltip = ({ active, payload, label }) => {
  if (!active || !payload || payload.length === 0) {
    return null;
  }

  return (
    <TooltipWrapper>
      {label && <TooltipLabel>{label}</TooltipLabel>}
      <TooltipContent>
        {payload.map((item, index) => (
          <TooltipItem key={index}>
            <TooltipIndicator color={item.color || item.fill} />
            <TooltipValue>
              {item.name || item.dataKey}: <strong>{item.value}</strong>
            </TooltipValue>
          </TooltipItem>
        ))}
      </TooltipContent>
    </TooltipWrapper>
  );
};

ChartTooltip.displayName = 'ChartTooltip';

const LegendWrapper = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  justify-content: center;
  padding-top: 1rem;
`;

const LegendItem = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8125rem;
  color: hsl(215.4 16.3% 46.9%);
`;

const LegendIndicator = styled.div`
  width: 0.75rem;
  height: 0.75rem;
  border-radius: 50%;
  background: ${props => props.color};
`;

export const ChartLegend = ({ payload }) => {
  if (!payload || payload.length === 0) {
    return null;
  }

  return (
    <LegendWrapper>
      {payload.map((item, index) => (
        <LegendItem key={index}>
          <LegendIndicator color={item.color} />
          <span>{item.value}</span>
        </LegendItem>
      ))}
    </LegendWrapper>
  );
};

ChartLegend.displayName = 'ChartLegend';

export const ChartTooltipContent = ChartTooltip;
