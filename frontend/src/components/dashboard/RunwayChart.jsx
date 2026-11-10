import React from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div style={{
        background: '#1f2937',
        border: '1px solid rgba(255,255,255,0.15)',
        padding: '0.75rem 1rem',
        borderRadius: '8px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
        fontSize: '0.85rem'
      }}>
        <div style={{ fontWeight: 700, marginBottom: '0.35rem', color: '#f3f4f6' }}>{data.month_name}</div>
        <div style={{ color: '#38bdf8' }}>Cash Reserves: ${data.cash_balance?.toLocaleString()}</div>
        <div style={{ color: '#34d399' }}>Projected Revenue: ${data.projected_revenue?.toLocaleString()}</div>
        <div style={{ color: '#f87171' }}>Total Burn: ${data.total_expenses?.toLocaleString()}</div>
        <div style={{ color: '#c084fc', fontSize: '0.75rem', marginTop: '0.2rem' }}>
          Software Subscriptions: ${data.subscription_expenses?.toLocaleString()}
        </div>
      </div>
    );
  }
  return null;
};

const RunwayChart = ({ timeline, title = "Cash Runway & Liquidity Trajectory" }) => {
  if (!timeline || timeline.length === 0) {
    return (
      <div className="card" style={{ height: '340px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
        No projection timeline data available.
      </div>
    );
  }

  return (
    <div className="card" style={{ height: '380px', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <div>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>{title}</h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            12-month forward simulation modeling revenue variability & recurring commitments
          </p>
        </div>
        <div style={{ display: 'flex', gap: '1rem', fontSize: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#0070ba' }}></span>
            <span>Liquid Reserves</span>
          </div>
        </div>
      </div>

      <div style={{ flex: 1, width: '100%' }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={timeline} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="cashGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#0070ba" stopOpacity={0.6}/>
                <stop offset="95%" stopColor="#0070ba" stopOpacity={0.0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
            <XAxis
              dataKey="month_name"
              stroke="#6b7280"
              fontSize={12}
              tickLine={false}
            />
            <YAxis
              stroke="#6b7280"
              fontSize={12}
              tickLine={false}
              tickFormatter={(v) => `$${v >= 1000 ? (v / 1000).toFixed(0) + 'k' : v}`}
            />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine y={0} stroke="#ef4444" strokeDasharray="4 4" label={{ value: 'Zero Cash Threshold', fill: '#ef4444', fontSize: 11, position: 'insideTopRight' }} />
            <Area
              type="monotone"
              dataKey="cash_balance"
              stroke="#00cfde"
              strokeWidth={2.5}
              fillOpacity={1}
              fill="url(#cashGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default RunwayChart;

