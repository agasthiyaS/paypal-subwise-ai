import React from 'react';
import { Sparkles, CheckCircle2, Clock, Loader2, ShieldCheck, Layers, Home, User, Building2 } from 'lucide-react';

/**
 * FinancialWorkspaceLoader
 *
 * Professional fintech loading experience for SubWise AI.
 * Displays honest, stage-based progress indicators while financial datasets,
 * subscription detection, health scores, and predictive directives initialize.
 */
const FinancialWorkspaceLoader = ({
  stages = {
    overview: 'active',    // 'pending' | 'active' | 'complete'
    data: 'pending',
    health: 'pending',
    intelligence: 'pending',
  },
  accountType = 'business',
  companyName = 'Workspace',
  isDemo = true,
}) => {
  const STAGE_CONFIG = [
    {
      key: 'overview',
      label: 'Preparing financial overview',
      description: 'Resolving active account profile, base currency, and operating constraints',
    },
    {
      key: 'data',
      label: 'Loading transactions and subscriptions',
      description: 'Syncing ledger disbursements and detecting recurring obligations',
    },
    {
      key: 'health',
      label: 'Calculating financial health',
      description: 'Evaluating runway liquidity, budget adherence, and burn ratios',
    },
    {
      key: 'intelligence',
      label: 'Preparing forecasts and recommendations',
      description: 'Synthesizing forward cash projections and calendar-aware directives',
    },
  ];

  const getAccountIcon = () => {
    if (accountType === 'household') return <Home size={16} />;
    if (accountType === 'individual') return <User size={16} />;
    return <Building2 size={16} />;
  };

  const getAccountLabel = () => {
    if (accountType === 'household') return 'Household Financial Workspace';
    if (accountType === 'individual') return 'Personal Cashflow Workspace';
    return 'Business Intelligence Workspace';
  };

  return (
    <div style={{
      minHeight: '70vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '2.5rem 1.5rem',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      <div className="fintech-card" style={{
        maxWidth: '560px',
        width: '100%',
        padding: '2.75rem 2.25rem',
        borderRadius: '16px',
        border: '1px solid #e2e8f0',
        boxShadow: '0 12px 32px rgba(15,23,42,0.06)',
        background: '#ffffff'
      }}>
        {/* Top Header Badge */}
        <div style={{ textAlign: 'center', marginBottom: '1.75rem' }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.45rem',
            padding: '0.35rem 0.85rem',
            borderRadius: '9999px',
            background: isDemo ? '#faf5ff' : '#eff6ff',
            border: `1px solid ${isDemo ? '#ddd6fe' : '#bfdbfe'}`,
            color: isDemo ? '#7c3aed' : '#0070ba',
            fontSize: '0.8rem',
            fontWeight: 700,
            marginBottom: '1rem'
          }}>
            {getAccountIcon()}
            <span>{isDemo ? 'Demo Mode' : 'Sandbox Sync'} • {getAccountLabel()}</span>
          </div>

          <h2 style={{
            fontSize: '1.65rem',
            fontWeight: 800,
            color: 'var(--navy-slate)',
            letterSpacing: '-0.02em',
            marginBottom: '0.45rem',
            lineHeight: 1.3
          }}>
            Preparing your financial workspace
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.94rem', margin: '0 auto', maxWidth: '420px', lineHeight: 1.5 }}>
            Setting up your financial insights, subscriptions and forecasts for <strong>{companyName}</strong>...
          </p>
        </div>

        {/* Honest 4-Stage Progress Indicators */}
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '1rem',
          background: '#f8fafc',
          padding: '1.5rem',
          borderRadius: '12px',
          border: '1px solid #f1f5f9',
          marginBottom: '1.75rem'
        }}>
          {STAGE_CONFIG.map((stage, idx) => {
            const status = stages[stage.key] || 'pending';
            const isComplete = status === 'complete';
            const isActive = status === 'active';

            return (
              <div
                key={stage.key}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '0.9rem',
                  opacity: status === 'pending' ? 0.5 : 1,
                  transition: 'opacity 0.25s ease'
                }}
              >
                {/* Status Indicator Icon */}
                <div style={{
                  width: '26px',
                  height: '26px',
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                  marginTop: '1px',
                  background: isComplete ? '#ecfdf5' : (isActive ? '#eff6ff' : '#f1f5f9'),
                  border: `1px solid ${isComplete ? '#a7f3d0' : (isActive ? '#bfdbfe' : '#e2e8f0')}`,
                  color: isComplete ? '#059669' : (isActive ? '#0070ba' : '#94a3b8')
                }}>
                  {isComplete ? (
                    <CheckCircle2 size={16} />
                  ) : isActive ? (
                    <Loader2 size={15} className="spinner" style={{ animation: 'spin 1.2s linear infinite' }} />
                  ) : (
                    <span style={{ fontSize: '0.75rem', fontWeight: 700 }}>{idx + 1}</span>
                  )}
                </div>

                <div style={{ flex: 1 }}>
                  <div style={{
                    fontSize: '0.92rem',
                    fontWeight: isActive || isComplete ? 700 : 500,
                    color: isComplete ? '#0f172a' : (isActive ? '#0070ba' : '#64748b'),
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem'
                  }}>
                    <span>{stage.label}</span>
                    {isComplete && (
                      <span style={{ fontSize: '0.72rem', color: '#059669', fontWeight: 600 }}>Ready</span>
                    )}
                    {isActive && (
                      <span style={{ fontSize: '0.72rem', color: '#0070ba', fontWeight: 600 }}>In progress</span>
                    )}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '0.15rem' }}>
                    {stage.description}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Assurance Footnote */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '0.5rem',
          fontSize: '0.82rem',
          color: '#64748b'
        }}>
          <ShieldCheck size={16} color="#059669" />
          <span>Strict profile isolation • Zero modification to real PayPal history</span>
        </div>
      </div>
    </div>
  );
};

export default FinancialWorkspaceLoader;
