import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div style={{
        backgroundColor: '#ffffff',
        border: '1px solid #cbd5e1',
        borderRadius: '8px',
        padding: '0.75rem 1rem',
        boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
        fontSize: '0.85rem'
      }}>
        <div style={{ fontWeight: 700, marginBottom: '0.35rem', color: '#0f172a' }}>{label}</div>
        <div style={{ color: '#059669', fontWeight: 600 }}>
          Income: ${payload[0]?.value?.toLocaleString()}
        </div>
        <div style={{ color: '#dc2626', fontWeight: 600 }}>
          Expenses: ${payload[1]?.value?.toLocaleString()}
        </div>
        <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.25rem' }}>
          Net Flow: ${(payload[0]?.value - payload[1]?.value)?.toLocaleString()}
        </div>
      </div>
    );
  }
  return null;
};

const IncomeExpenseChart = ({ data = [] }) => {
  const safeData = data || [];
  const hasData = safeData.length > 0 && safeData.some(d => (d.income || 0) > 0 || (d.expenses || 0) > 0);

  return (
    <div className="fintech-card" style={{ height: '370px', display: 'flex', flexDirection: 'column' }}>
      <div style={{ marginBottom: '1rem' }}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--navy-slate)' }}>
          Business Income vs. Total Expenses
        </h3>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          Monthly comparison of cash inflows and operating disbursements
        </p>
      </div>

      <div style={{ flex: 1, width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        {!hasData ? (
          <div style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.95rem' }}>
            No transaction history available to plot cash inflows and outflows.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={safeData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
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
              <Tooltip content={<CustomTooltip />} />
              <Legend
                verticalAlign="top"
                align="right"
                iconType="circle"
                wrapperStyle={{ fontSize: '0.8rem', paddingBottom: '10px' }}
              />
              <Bar dataKey="income" name="Business Income" fill="#10b981" radius={[4, 4, 0, 0]} maxBarSize={30} />
              <Bar dataKey="expenses" name="Total Expenses" fill="#f87171" radius={[4, 4, 0, 0]} maxBarSize={30} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
};

export default IncomeExpenseChart;

