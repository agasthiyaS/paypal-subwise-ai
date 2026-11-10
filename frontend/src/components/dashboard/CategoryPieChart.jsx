import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

const CategoryPieChart = ({ data = [] }) => {
  const safeData = data || [];
  const total = safeData.reduce((acc, curr) => acc + (curr.value || 0), 0);

  return (
    <div className="fintech-card" style={{ height: '370px', display: 'flex', flexDirection: 'column' }}>
      <div style={{ marginBottom: '0.75rem' }}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--navy-slate)' }}>
          Subscription Category Breakdown
        </h3>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          Portfolio concentration across software operational functions
        </p>
      </div>

      <div style={{ flex: 1, width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        {safeData.length === 0 || total === 0 ? (
          <div style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.95rem' }}>
            No categorized subscription expenses detected yet.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={safeData}
                cx="50%"
                cy="48%"
                innerRadius={58}
                outerRadius={88}
                paddingAngle={3}
                dataKey="value"
              >
                {safeData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color || '#0070ba'} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value, name) => [
                  `$${Number(value).toFixed(2)} (${total > 0 ? ((value / total) * 100).toFixed(1) : 0}%)`,
                  name
                ]}
                contentStyle={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #cbd5e1',
                  borderRadius: '8px',
                  fontSize: '0.82rem',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.08)'
                }}
              />
              <Legend
                verticalAlign="bottom"
                height={36}
                iconType="circle"
                wrapperStyle={{ fontSize: '0.75rem', paddingTop: '8px' }}
              />
            </PieChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
};

export default CategoryPieChart;

