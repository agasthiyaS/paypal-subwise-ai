import React, { useState } from 'react';
import { recommendationsAPI } from '../../services/api';
import { CheckCircle2, Copy, FileText, ChevronRight, XCircle } from 'lucide-react';

const ActionCard = ({ recommendation, onStatusChanged }) => {
  const [showScript, setShowScript] = useState(false);
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(false);

  const getActionColor = (action) => {
    switch (action) {
      case 'CANCEL': return { bg: 'rgba(239, 68, 68, 0.15)', text: '#f87171', border: 'rgba(239, 68, 68, 0.3)' };
      case 'CONSOLIDATE': return { bg: 'rgba(168, 85, 247, 0.15)', text: '#c084fc', border: 'rgba(168, 85, 247, 0.3)' };
      case 'DOWNGRADE': return { bg: 'rgba(245, 158, 11, 0.15)', text: '#fbbf24', border: 'rgba(245, 158, 11, 0.3)' };
      case 'SWITCH_ANNUAL': return { bg: 'rgba(16, 185, 129, 0.15)', text: '#34d399', border: 'rgba(16, 185, 129, 0.3)' };
      default: return { bg: 'rgba(59, 130, 246, 0.15)', text: '#60a5fa', border: 'rgba(59, 130, 246, 0.3)' };
    }
  };

  const color = getActionColor(recommendation.action_type);

  const handleCopyScript = () => {
    if (recommendation.negotiation_script) {
      navigator.clipboard.writeText(recommendation.negotiation_script);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleStatusUpdate = async (newStatus) => {
    setLoading(true);
    try {
      await recommendationsAPI.updateRecommendation(recommendation.id, { status: newStatus });
      if (onStatusChanged) onStatusChanged();
    } catch (err) {
      alert('Failed to update recommendation');
    } finally {
      setLoading(false);
    }
  };

  const isApplied = recommendation.status === 'applied';

  return (
    <div className="card" style={{ padding: '2rem', opacity: isApplied ? 0.6 : 1, transition: 'all 0.2s ease' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.15rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <span className="badge" style={{ background: color.bg, color: color.text, border: `1.5px solid ${color.border}`, fontSize: '0.88rem', fontWeight: 700 }}>
            {recommendation.action_type.replace('_', ' ')}
          </span>
          <h4 style={{ fontSize: '1.35rem', fontWeight: 700, color: 'var(--navy-slate)' }}>{recommendation.title}</h4>
        </div>

        {/* Quantified Impact Badge */}
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '1.65rem', fontWeight: 800, color: 'var(--emerald-dark)', fontFamily: 'JetBrains Mono, monospace' }}>
            +${recommendation.potential_monthly_saving.toFixed(2)}/mo
          </div>
          <div style={{ fontSize: '0.92rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            +${recommendation.potential_annual_saving.toLocaleString()}/yr • +{recommendation.runway_impact_days} days runway
          </div>
        </div>
      </div>

      <p style={{ fontSize: '1rem', color: 'var(--text-body)', lineHeight: '1.65', marginBottom: '1.25rem' }}>
        {recommendation.rationale}
      </p>

      {recommendation.action_plan && (
        <div style={{
          background: 'var(--bg-tertiary)',
          borderRadius: 'var(--radius-md)',
          padding: '0.65rem 0.85rem',
          fontSize: '0.82rem',
          color: 'var(--text-primary)',
          marginBottom: '1rem',
          borderLeft: '3px solid #0070ba'
        }}>
          <strong>Implementation Action:</strong> {recommendation.action_plan}
        </div>
      )}

      {/* Script Expandable */}
      {recommendation.negotiation_script && (
        <div style={{ marginBottom: '1rem' }}>
          <button
            onClick={() => setShowScript(!showScript)}
            className="btn btn-secondary btn-sm"
            style={{ fontSize: '0.78rem' }}
          >
            <FileText size={14} />
            <span>{showScript ? 'Hide Supplier Negotiation Script' : 'View Supplier Negotiation Script'}</span>
            <ChevronRight size={14} style={{ transform: showScript ? 'rotate(90deg)' : 'none', transition: 'transform 0.2s' }} />
          </button>

          {showScript && (
            <div style={{
              marginTop: '0.5rem',
              background: '#0d1117',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: 'var(--radius-md)',
              padding: '1rem',
              position: 'relative'
            }}>
              <button
                onClick={handleCopyScript}
                className="btn btn-secondary btn-sm"
                style={{ position: 'absolute', top: '10px', right: '10px', fontSize: '0.75rem', padding: '0.3rem 0.6rem' }}
              >
                <Copy size={13} />
                <span>{copied ? 'Copied!' : 'Copy Script'}</span>
              </button>
              <pre style={{
                whiteSpace: 'pre-wrap',
                fontSize: '0.8rem',
                color: '#e5e7eb',
                lineHeight: '1.5',
                paddingRight: '5rem'
              }}>
                {recommendation.negotiation_script}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* Actions */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.6rem', borderTop: '1px solid var(--border-color)', paddingTop: '0.75rem' }}>
        {isApplied ? (
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: '#10b981', fontSize: '0.85rem', fontWeight: 600 }}>
            <CheckCircle2 size={16} /> Strategy Implemented
          </span>
        ) : (
          <>
            <button
              onClick={() => handleStatusUpdate('dismissed')}
              disabled={loading}
              className="btn btn-secondary btn-sm"
            >
              <XCircle size={14} /> Dismiss
            </button>
            <button
              onClick={() => handleStatusUpdate('applied')}
              disabled={loading}
              className="btn btn-primary btn-sm"
            >
              <CheckCircle2 size={14} /> Apply Strategy
            </button>
          </>
        )}
      </div>
    </div>
  );
};

export default ActionCard;

