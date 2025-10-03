import React from "react";
import styled from "styled-components";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  Cell,
  LabelList,
  Tooltip,
} from "recharts";

const Card = styled.div`
  background: hsl(0 0% 100%);
  border: 1px solid hsl(214.3 31.8% 91.4%);
  border-radius: 0.5rem;
  padding: 1.5rem;
`;

const CardHeader = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1rem;
`;

const CardTitle = styled.h3`
  font-size: 0.875rem;
  font-weight: 600;
  color: hsl(222.2 84% 4.9%);
  letter-spacing: -0.025em;
`;

const CardDescription = styled.p`
  font-size: 0.875rem;
  color: hsl(215.4 16.3% 46.9%);
  line-height: 1.5;
`;

const Legend = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1rem;
  padding: 0.75rem;
  background: hsl(210 40% 98%);
  border-radius: 0.375rem;
`;

const LegendItem = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: hsl(215.4 16.3% 46.9%);
`;

const LegendDot = styled.div`
  width: 12px;
  height: 12px;
  border-radius: 2px;
  background: ${(props) => props.color};
`;

/**
 * VoltageProfileChart - Displays voltage measurements across assets
 *
 * Expected Backend Format (from /api/assets):
 * {
 *   "assets": [
 *     {
 *       "id": "TX1_400_220",
 *       "name": "TX1 Main Transformer",
 *       "status": "operational",
 *       "health": 95.0,
 *       "parameters": {
 *         "voltage": "400 kV",         // Rated voltage (string)
 *         "hv_voltage": 399.2,         // Measured HV voltage (number)
 *         "lv_voltage": 220.1,         // Measured LV voltage (number)
 *         "temperature": "45.0°C",
 *         ...other parameters
 *       }
 *     }
 *   ],
 *   "total_assets": 76
 * }
 */
const VoltageProfileChart = ({ assets }) => {
  // Backend returns: { assets: [...] } or just [...]
  // Handle both formats for flexibility
  const assetsArray = Array.isArray(assets)
    ? assets
    : (assets?.assets || []);

  let voltageData = assetsArray
    .filter((asset) => {
      if (!asset || !asset.parameters) return false;
      // Backend provides hv_voltage or lv_voltage as measured values
      const measuredVoltage =
        asset.parameters.hv_voltage || asset.parameters.lv_voltage;
      return measuredVoltage && measuredVoltage > 0;
    })
    .map((asset) => {
      // Get measured voltage from real-time data
      const measuredVoltage =
        asset.parameters.hv_voltage || asset.parameters.lv_voltage || 0;

      // Get rated voltage from voltage parameter (e.g., "400 kV" -> 400)
      const ratedVoltage = parseFloat(
        (asset.parameters.voltage || "0").replace(/[^\d.]/g, "")
      );

      return {
        name: asset.name || asset.id,
        voltage: measuredVoltage,
        ratedVoltage: ratedVoltage,
        status: asset.status,
      };
    })
    .sort((a, b) => b.voltage - a.voltage)
    .slice(0, 20);

  // If no real data, use dummy data in BACKEND FORMAT for testing
  if (voltageData.length === 0) {
    const dummyBackendAssets = [
      // Excellent (±0-2%)
      { id: "TX1_Main", name: "TX1 Main Transformer", status: "operational",
        parameters: { voltage: "400 kV", hv_voltage: 399.2 } },
      { id: "TX2_Main", name: "TX2 Main Transformer", status: "operational",
        parameters: { voltage: "400 kV", hv_voltage: 400.8 } },
      { id: "BUS_400kV_A", name: "400kV Bus A", status: "operational",
        parameters: { voltage: "220 kV", lv_voltage: 221.5 } },

      // Good (±2-5%)
      { id: "CB_400kV_1", name: "CB 400kV Line 1", status: "operational",
        parameters: { voltage: "400 kV", hv_voltage: 387.5 } },
      { id: "CB_400kV_2", name: "CB 400kV Line 2", status: "operational",
        parameters: { voltage: "400 kV", hv_voltage: 412.0 } },
      { id: "LINE_220kV_1", name: "220kV Feeder 1", status: "operational",
        parameters: { voltage: "220 kV", lv_voltage: 210.5 } },
      { id: "BUS_220kV_B", name: "220kV Bus B", status: "operational",
        parameters: { voltage: "220 kV", lv_voltage: 229.8 } },

      // Warning (±5-10%)
      { id: "TX3_Dist", name: "TX3 Distribution", status: "warning",
        parameters: { voltage: "400 kV", hv_voltage: 368.0 } },
      { id: "CB_220kV_2", name: "CB 220kV Line 2", status: "warning",
        parameters: { voltage: "220 kV", lv_voltage: 241.0 } },
      { id: "LINE_33kV_1", name: "33kV Feeder 1", status: "warning",
        parameters: { voltage: "33 kV", lv_voltage: 30.5 } },
      { id: "BUS_33kV_A", name: "33kV Bus A", status: "warning",
        parameters: { voltage: "33 kV", lv_voltage: 35.8 } },

      // Critical (>±10%)
      { id: "CB_Faulty_1", name: "CB Faulty Unit", status: "fault",
        parameters: { voltage: "400 kV", hv_voltage: 345.0 } },
      { id: "LINE_Overload", name: "Overloaded Line", status: "fault",
        parameters: { voltage: "220 kV", lv_voltage: 252.5 } },
      { id: "TX_Critical", name: "Critical Transformer", status: "fault",
        parameters: { voltage: "33 kV", lv_voltage: 28.0 } },
      { id: "BUS_LowV", name: "Low Voltage Bus", status: "fault",
        parameters: { voltage: "220 kV", lv_voltage: 190.0 } },
    ];

    // Process dummy data through same pipeline
    voltageData = dummyBackendAssets.map((asset) => {
      const measuredVoltage = asset.parameters.hv_voltage || asset.parameters.lv_voltage || 0;
      const ratedVoltage = parseFloat((asset.parameters.voltage || "0").replace(/[^\d.]/g, ""));

      return {
        name: asset.name || asset.id,
        voltage: measuredVoltage,
        ratedVoltage: ratedVoltage,
        status: asset.status,
      };
    });
  }

  // Color based on voltage deviation from rated voltage - BLUE THEME
  const getBarColorByVoltage = (voltage, ratedVoltage) => {
    if (!ratedVoltage || ratedVoltage === 0) {
      return "#3b82f6"; // Default blue if no rated voltage
    }

    const deviation = Math.abs(((voltage - ratedVoltage) / ratedVoltage) * 100);

    if (deviation <= 2) {
      return "#10b981"; // Green - Excellent (within ±2%)
    } else if (deviation <= 5) {
      return "#f59e0b"; // Amber - Good (±2-5%)
    } else if (deviation <= 10) {
      return "#f97316"; // Orange - Warning (±5-10%)
    } else {
      return "#ef4444"; // Red - Critical (>±10%)
    }
  };

  const getVoltageStatus = (voltage, ratedVoltage) => {
    if (!ratedVoltage || ratedVoltage === 0) return "Unknown";
    const deviation = Math.abs(((voltage - ratedVoltage) / ratedVoltage) * 100);

    if (deviation <= 2) return "Excellent";
    if (deviation <= 5) return "Good";
    if (deviation <= 10) return "Warning";
    return "Critical";
  };

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      const deviation = data.ratedVoltage
        ? ((data.voltage - data.ratedVoltage) / data.ratedVoltage) * 100
        : 0;
      const voltageStatus = getVoltageStatus(data.voltage, data.ratedVoltage);
      const barColor = getBarColorByVoltage(data.voltage, data.ratedVoltage);

      return (
        <div
          style={{
            background: "white",
            padding: "1rem",
            borderRadius: "0.5rem",
            border: "1px solid #e5e7eb",
            boxShadow:
              "0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)",
            minWidth: "220px",
          }}
        >
          <div
            style={{
              fontWeight: 600,
              fontSize: "0.875rem",
              marginBottom: "0.75rem",
              color: "#1f2937",
              borderBottom: "1px solid #e5e7eb",
              paddingBottom: "0.5rem",
            }}
          >
            {data.name}
          </div>

          <div
            style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <span style={{ color: "#6b7280", fontSize: "0.8125rem" }}>
                Measured:
              </span>
              <span
                style={{
                  fontWeight: 600,
                  fontSize: "0.875rem",
                  color: barColor,
                }}
              >
                {data.voltage.toFixed(2)} kV
              </span>
            </div>

            {data.ratedVoltage > 0 && (
              <>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <span style={{ color: "#6b7280", fontSize: "0.8125rem" }}>
                    Rated:
                  </span>
                  <span
                    style={{
                      fontWeight: 500,
                      fontSize: "0.8125rem",
                      color: "#1f2937",
                    }}
                  >
                    {data.ratedVoltage} kV
                  </span>
                </div>

                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <span style={{ color: "#6b7280", fontSize: "0.8125rem" }}>
                    Deviation:
                  </span>
                  <span
                    style={{
                      fontWeight: 600,
                      fontSize: "0.8125rem",
                      color: barColor,
                    }}
                  >
                    {deviation > 0 ? "+" : ""}
                    {deviation.toFixed(2)}%
                  </span>
                </div>

                <div
                  style={{
                    marginTop: "0.25rem",
                    padding: "0.375rem 0.5rem",
                    borderRadius: "0.25rem",
                    background: `${barColor}15`,
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <span style={{ color: "#6b7280", fontSize: "0.75rem" }}>
                    Health:
                  </span>
                  <span
                    style={{
                      fontWeight: 600,
                      fontSize: "0.75rem",
                      color: barColor,
                      textTransform: "uppercase",
                      letterSpacing: "0.025em",
                    }}
                  >
                    {voltageStatus}
                  </span>
                </div>
              </>
            )}

            <div
              style={{
                marginTop: "0.25rem",
                fontSize: "0.75rem",
                color: "#9ca3af",
                fontStyle: "italic",
              }}
            >
              Asset Status: {data.status}
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Voltage Profile Across Assets</CardTitle>
        <CardDescription>
          Real-time voltage measurements for {voltageData.length} key assets,
          color-coded by deviation from rated values
        </CardDescription>
      </CardHeader>

      <Legend>
        <LegendItem>
          <LegendDot color="#10b981" />
          <span>Excellent (±0-2%)</span>
        </LegendItem>
        <LegendItem>
          <LegendDot color="#f59e0b" />
          <span>Good (±2-5%)</span>
        </LegendItem>
        <LegendItem>
          <LegendDot color="#f97316" />
          <span>Warning (±5-10%)</span>
        </LegendItem>
        <LegendItem>
          <LegendDot color="#ef4444" />
          <span>Critical &gt;±10%</span>
        </LegendItem>
      </Legend>

      <ResponsiveContainer
        width="100%"
        height={Math.max(300, voltageData.length * 35)}
      >
        <BarChart
          data={voltageData}
          layout="vertical"
          margin={{ top: 5, right: 50, left: 10, bottom: 5 }}
        >
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="hsl(214.3 31.8% 91.4%)"
            horizontal={false}
          />
          <YAxis
            dataKey="name"
            type="category"
            stroke="hsl(215.4 16.3% 46.9%)"
            fontSize={12}
            tick={{ fill: "hsl(215.4 16.3% 46.9%)" }}
            tickLine={false}
            axisLine={false}
            tickMargin={10}
            hide
          />
          <XAxis
            dataKey="voltage"
            type="number"
            stroke="hsl(215.4 16.3% 46.9%)"
            fontSize={12}
            tick={{ fill: "hsl(215.4 16.3% 46.9%)" }}
            tickLine={false}
            axisLine={false}
            hide
          />
          <Tooltip
            content={<CustomTooltip />}
            cursor={{ fill: "hsl(210 40% 96.1%)" }}
          />
          <Bar dataKey="voltage" layout="vertical" radius={4}>
            {voltageData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={getBarColorByVoltage(entry.voltage, entry.ratedVoltage)}
              />
            ))}
            <LabelList
              dataKey="name"
              position="insideLeft"
              offset={8}
              style={{ fill: "white", fontSize: 12, fontWeight: 500 }}
            />
            <LabelList
              dataKey="voltage"
              position="right"
              offset={8}
              style={{
                fill: "hsl(222.2 84% 4.9%)",
                fontSize: 12,
                fontWeight: 500,
              }}
              formatter={(value) => `${value.toFixed(2)} kV`}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </Card>
  );
};

export default VoltageProfileChart;
