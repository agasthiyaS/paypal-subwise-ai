import React from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';

const SubscriptionSpendingChart = ({ data = [], currentSpend }) => {
  const safeData = data || [];
  const hasData = safeData.length > 0 && safeData.some(d => (d.subscriptions || 0) > 0);
  const displaySpend = currentSpend !== undefined 
    ? currentSpend 
    : (safeData.length > 0 ? (safeData[safeData.length - 1]?.subscriptions || 0) : 0);

  return (
    <div className="fintech-card" style={{ height: '370px', display: 'flex', flexDirection: 'column' }}>
      <div style={{ marginBottom: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--navy-slate)' }}>
            Monthly Subscription Spending Progression
          </h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Recurring SaaS commitments over historical and projected months
          </p>
        </div>
        <div style={{ fontSize: '0.78rem', color: 'var(--navy-primary)', fontWeight: 700, background: 'var(--paypal-blue-subtle)', padding: '0.2rem 0.6rem', borderRadius: '4px' }}>
          Current: ${Number(displaySpend).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}/mo
        </div>
      </div>

      <div style={{ flex: 1, width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        {!hasData ? (
          <div style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.95rem' }}>
            No recurring subscription commitments detected yet.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={safeData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="subSpendGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#0070ba" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#0070ba" stopOpacity={0.0} />
                </linearGradient>
              </defs>
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
                tickFormatter={(v) => `$${v}`}
              />
              <Tooltip
                formatter={(val) => [`$${Number(val).toLocaleString()}`, 'SaaS Commitments']}
                contentStyle={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #cbd5e1',
                  borderRadius: '8px',
                  fontSize: '0.85rem',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.08)'
                }}
              />
              <Area
                type="monotone"
                dataKey="subscriptions"
                stroke="#0070ba"
                strokeWidth={2.5}
                fillOpacity={1}
                fill="url(#subSpendGradient)"
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
};

export default SubscriptionSpendingChart;

