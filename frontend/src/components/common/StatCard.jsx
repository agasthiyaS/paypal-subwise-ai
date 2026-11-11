import React from 'react';
import { ArrowUpRight, ArrowDownRight } from 'lucide-react';

const StatCard = ({ title, value, subtext, icon: Icon, trendPct, isPositiveGood = true, alert = false, hero = false }) => {
  const isPositive = trendPct > 0;
  const isGood = isPositiveGood ? isPositive : !isPositive;

  return (
    <div
      className="fintech-card stat-box"
      style={{
        borderColor: alert ? '#fde68a' : hero ? '#cbd5e1' : undefined,
        backgroundColor: alert ? '#fffdf7' : hero ? '#fafcff' : undefined,
        boxShadow: hero ? '0 2px 8px rgba(0, 48, 135, 0.06)' : undefined,
      }}
    >
      <div className="stat-top-row">
        <span style={{ fontWeight: 600, color: 'var(--text-muted)' }}>{title}</span>
        {Icon && (
          <div
            style={{
              width: '34px',
              height: '34px',
              borderRadius: '8px',
              background: alert ? '#fef3c7' : hero ? '#eff6ff' : 'var(--bg-subtle)',
              color: alert ? '#b45309' : hero ? 'var(--paypal-blue)' : 'var(--navy-slate)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              border: `1px solid ${alert ? '#fde68a' : hero ? '#bfdbfe' : 'var(--border-light)'}`,
            }}
          >
            <Icon size={17} />
          </div>
        )}
      </div>

      <div
        className="stat-main-number"
        style={{
          color: alert ? '#b45309' : hero ? 'var(--navy-primary)' : 'var(--navy-slate)',
          fontSize: hero ? '1.85rem' : '1.65rem',
        }}
      >
        {value}
      </div>

      <div className="stat-bottom-row" style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
        {trendPct !== undefined && trendPct !== null && (
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.2rem',
              fontWeight: 700,
              color: isGood ? 'var(--emerald-dark)' : 'var(--rose-dark)',
            }}
          >
            {isPositive ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
            {isPositive ? `+${trendPct}%` : `${trendPct}%`}
          </span>
        )}
        <span>{subtext}</span>
      </div>
    </div>
  );
};

export default StatCard;
