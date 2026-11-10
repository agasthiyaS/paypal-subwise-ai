import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';

const CashFlowTrendChart = ({ data = [] }) => {
  const safeData = data || [];
  const hasData = safeData.length > 0 && safeData.some(d => (d.balance || 0) > 0);

  return (
    <div className="fintech-card" style={{ height: '370px', display: 'flex', flexDirection: 'column' }}>
      <div style={{ marginBottom: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--navy-slate)' }}>
            Cash-Flow Trends & Liquidity Horizon
          </h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Cumulative available operating capital against 6-month safety buffer
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', fontSize: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#003087' }}></span>
            <span>Available Balance</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <span style={{ width: '10px', height: '2px', background: '#f59e0b' }}></span>
            <span>Safety Buffer ($35k)</span>
          </div>
        </div>
      </div>

      <div style={{ flex: 1, width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        {!hasData ? (
          <div style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.95rem' }}>
            No liquidity trend data available. Sync transactions to track cash balance.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={safeData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis
                dataKey="month"
                stroke="#64748b"
                fontSize={12}
                tickLine={false}
                axisLine={{ stroke: '#e2e8f0' }}
              />
              <YAxis
                stroke="#64748b"
                fontSize={12}
                tickLine={false}
                axisLine={{ stroke: '#e2e8f0' }}
                tickFormatter={(v) => `$${v >= 1000 ? (v / 1000).toFixed(0) + 'k' : v}`}
              />
              <Tooltip
                formatter={(val) => [`$${Number(val).toLocaleString()}`, 'Operating Cash']}
                contentStyle={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #cbd5e1',
                  borderRadius: '8px',
                  fontSize: '0.85rem',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.08)'
                }}
              />
              <ReferenceLine y={35000} stroke="#f59e0b" strokeDasharray="4 4" />
              <Line
                type="monotone"
                dataKey="balance"
                stroke="#003087"
                strokeWidth={3}
                dot={{ fill: '#003087', r: 3 }}
                activeDot={{ r: 6, fill: '#0070ba' }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
};

export default CashFlowTrendChart;

