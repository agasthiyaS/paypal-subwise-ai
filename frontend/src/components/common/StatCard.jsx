import React from 'react';
import { ArrowUpRight, ArrowDownRight } from 'lucide-react';

const StatCard = ({ title, value, subtext, icon: Icon, trendPct, isPositiveGood = true, alert = false }) => {
  const isPositive = trendPct > 0;
  const isGood = isPositiveGood ? isPositive : !isPositive;

  return (
    <div
      className="fintech-card stat-box"
      style={alert ? { borderColor: 'var(--amber-border)', backgroundColor: 'var(--amber-bg)' } : {}}
    >
      <div className="stat-top-row">
        <span>{title}</span>
        {Icon && (
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '10px',
            background: alert ? '#fef3c7' : 'var(--paypal-blue-subtle)',
            color: alert ? 'var(--amber-dark)' : 'var(--paypal-blue)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Icon size={22} />
          </div>
        )}
      </div>

      <div className="stat-main-number" style={alert ? { color: 'var(--amber-dark)' } : {}}>
        {value}
      </div>

      <div className="stat-bottom-row">
        {trendPct !== undefined && trendPct !== null && (
          <span style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.25rem',
            fontWeight: 700,
            color: isGood ? 'var(--emerald-dark)' : 'var(--rose-dark)'
          }}>
            {isPositive ? <ArrowUpRight size={17} /> : <ArrowDownRight size={17} />}
            {isPositive ? `+${trendPct}%` : `${trendPct}%`}
          </span>
        )}
        <span>{subtext}</span>
      </div>
    </div>
  );
};

export default StatCard;
