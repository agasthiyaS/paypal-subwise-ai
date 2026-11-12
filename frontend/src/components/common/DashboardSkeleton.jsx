import React from 'react';

/**
 * DashboardSkeleton
 * Renders pulse placeholders matching fintech card layouts during progressive loading.
 */
export const StatCardSkeleton = () => (
  <div className="fintech-card" style={{ padding: '1.25rem', height: '100%', minHeight: '120px' }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
      <div style={{ width: '40%', height: '14px', background: '#e2e8f0', borderRadius: '4px', animation: 'pulse 1.5s infinite' }} />
      <div style={{ width: '28px', height: '28px', background: '#e2e8f0', borderRadius: '8px', animation: 'pulse 1.5s infinite' }} />
    </div>
    <div style={{ width: '65%', height: '28px', background: '#cbd5e1', borderRadius: '6px', marginBottom: '0.5rem', animation: 'pulse 1.5s infinite' }} />
    <div style={{ width: '50%', height: '12px', background: '#f1f5f9', borderRadius: '4px', animation: 'pulse 1.5s infinite' }} />
  </div>
);

export const ChartCardSkeleton = ({ title = 'Loading Analytics...', height = 300 }) => (
  <div className="fintech-card" style={{ padding: '1.5rem', height: '100%' }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
      <div style={{ width: '180px', height: '18px', background: '#e2e8f0', borderRadius: '4px', animation: 'pulse 1.5s infinite' }} />
      <div style={{ width: '80px', height: '14px', background: '#f1f5f9', borderRadius: '4px', animation: 'pulse 1.5s infinite' }} />
    </div>
    <div style={{
      height: `${height}px`,
      background: '#f8fafc',
      borderRadius: '8px',
      border: '1px dashed #cbd5e1',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      color: '#94a3b8',
      fontSize: '0.9rem'
    }}>
      <span>{title}</span>
    </div>
  </div>
);

export const SectionRetryCard = ({ title = 'Failed to load section', onRetry }) => (
  <div className="fintech-card" style={{ padding: '1.5rem', textAlign: 'center', border: '1px dashed #fca5a5', background: '#fef2f2' }}>
    <p style={{ color: '#991b1b', fontSize: '0.92rem', marginBottom: '0.75rem' }}>
      {title}
    </p>
    {onRetry && (
      <button
        onClick={onRetry}
        className="btn-fintech btn-fintech-outline btn-sm"
        style={{ borderColor: '#f87171', color: '#b91c1c' }}
      >
        Retry
      </button>
    )}
  </div>
);

export default {
  StatCardSkeleton,
  ChartCardSkeleton,
  SectionRetryCard,
};
