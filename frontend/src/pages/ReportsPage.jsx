import React, { useState, useEffect, useMemo } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, Legend,
} from 'recharts';
import {
  FileText, Download, TrendingUp, TrendingDown, RefreshCw, AlertCircle,
  Brain, ShieldAlert, Activity, Zap, Info, CheckCircle2, AlertTriangle, XCircle,
  Calendar, Layers, Check,
} from 'lucide-react';
import { transactionsAPI, subscriptionsAPI, recommendationsAPI, paypalAPI, financialIntelligenceAPI, reportsAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { classifyFinancialTransactions, isValidOperatingTransaction } from '../utils/financialClassification';

const fmt = (n) => `$${Number(n || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

const CATEGORY_COLORS = [
  '#003087', '#009cde', '#10b981', '#f59e0b', '#8b5cf6',
  '#ef4444', '#14b8a6', '#f97316', '#6366f1', '#84cc16',
];

/** Mini summary card for reports page */
const ReportMetric = ({ label, value, sub, color = 'var(--navy-slate)', bg = 'var(--bg-surface)' }) => (
  <div className="fintech-card" style={{ padding: '1.15rem 1.35rem', background: bg }}>
    <div style={{ fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
      {label}
    </div>
    <div style={{ fontSize: '1.65rem', fontWeight: 800, color, lineHeight: 1.15, fontFamily: 'JetBrains Mono, monospace' }}>{value}</div>
    {sub && <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>{sub}</div>}
  </div>
);

/** Empty state component */
const EmptyState = ({ onSync, syncing }) => (
  <div style={{
    display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
    padding: '4rem 2rem', textAlign: 'center', gap: '1.25rem',
    background: 'var(--bg-surface)', borderRadius: 'var(--radius-lg)',
    border: '1.5px dashed var(--border-light)',
  }}>
    <FileText size={48} color="var(--text-muted)" strokeWidth={1.25} />
    <div>
      <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--navy-slate)', marginBottom: '0.5rem' }}>
        No Report Data Available
      </div>
      <div style={{ color: 'var(--text-muted)', fontSize: '0.95rem', maxWidth: '480px' }}>
        Sync your PayPal Sandbox transactions to generate financial reports and track recurring commitments.
      </div>
    </div>
    <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', justifyContent: 'center' }}>
      <button
        onClick={() => onSync(false)}
        disabled={syncing}
        style={{
          display: 'inline-flex', alignItems: 'center', gap: '0.5rem',
          padding: '0.75rem 1.5rem', background: 'var(--navy-primary)', color: '#fff',
          border: 'none', borderRadius: 'var(--radius-md)', fontSize: '0.95rem',
          fontWeight: 700, cursor: syncing ? 'not-allowed' : 'pointer', opacity: syncing ? 0.7 : 1,
        }}
      >
        <RefreshCw size={16} className={syncing ? 'spin' : ''} />
        Sync PayPal Sandbox
      </button>
    </div>
  </div>
);

/* ------------------------------------------------------------------ */
/* Financial Intelligence helper components (Stage 5)                 */
/* ------------------------------------------------------------------ */

const fmtMoney = (n) =>
  `$${Number(n || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

const SEVERITY_STYLES = {
  high:   { bg: '#fff1f2', border: '#fecdd3', color: '#be123c', icon: <XCircle   size={16} /> },
  medium: { bg: '#fffbeb', border: '#fde68a', color: '#b45309', icon: <AlertTriangle size={16} /> },
  low:    { bg: '#f0fdf4', border: '#bbf7d0', color: '#15803d', icon: <Info       size={16} /> },
};

const HealthBadge = ({ score, label }) => {
  let bg = '#f1f5f9', color = '#64748b';
  if (score === null || score === undefined) { bg = '#f1f5f9'; color = '#64748b'; }
  else if (score >= 80) { bg = '#d1fae5'; color = '#065f46'; }
  else if (score >= 65) { bg = '#fef9c3'; color = '#854d0e'; }
  else if (score >= 45) { bg = '#ffedd5'; color = '#9a3412'; }
  else                  { bg = '#fee2e2'; color = '#991b1b'; }

  return (
    <div style={{
      display: 'inline-flex', alignItems: 'center', gap: '0.65rem',
      background: bg, border: `1.5px solid ${color}30`,
      borderRadius: '10px', padding: '0.65rem 1.25rem',
    }}>
      <span style={{ fontSize: '2rem', fontWeight: 900, color, fontFamily: 'JetBrains Mono, monospace', lineHeight: 1 }}>
        {score !== null && score !== undefined ? score : '—'}
      </span>
      <div>
        <div style={{ fontSize: '0.72rem', fontWeight: 700, color, textTransform: 'uppercase', letterSpacing: '0.07em' }}>
          Health Score
        </div>
        <div style={{ fontSize: '0.82rem', fontWeight: 600, color }}>{label}</div>
      </div>
    </div>
  );
};

const MetricRow = ({ label, value, sub, mono = true, highlight }) => (
  <div style={{
    display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
    padding: '0.6rem 0', borderBottom: '1px solid var(--border-light)',
  }}>
    <div style={{ fontSize: '0.88rem', color: 'var(--text-muted)', flex: 1 }}>{label}</div>
    <div style={{ textAlign: 'right' }}>
      <div style={{
        fontSize: '0.95rem', fontWeight: 700,
        fontFamily: mono ? 'JetBrains Mono, monospace' : undefined,
        color: highlight || 'var(--navy-slate)',
      }}>{value}</div>
      {sub && <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>{sub}</div>}
    </div>
  </div>
);

const RiskCard = ({ risk }) => {
  const style = SEVERITY_STYLES[risk.severity] || SEVERITY_STYLES.low;
  return (
    <div style={{
      background: style.bg, border: `1.5px solid ${style.border}`,
      borderRadius: '10px', padding: '1rem 1.25rem', marginBottom: '0.75rem',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem' }}>
        <span style={{ color: style.color }}>{style.icon}</span>
        <span style={{ fontWeight: 700, fontSize: '0.92rem', color: style.color }}>{risk.title}</span>
        <span style={{
          marginLeft: 'auto', fontSize: '0.68rem', fontWeight: 800,
          textTransform: 'uppercase', letterSpacing: '0.08em',
          background: style.color + '18', color: style.color,
          padding: '0.15rem 0.5rem', borderRadius: '4px',
        }}>{risk.severity}</span>
      </div>
      <p style={{ fontSize: '0.85rem', color: '#374151', margin: '0 0 0.4rem 0' }}>{risk.description}</p>
      <p style={{ fontSize: '0.78rem', color: '#6b7280', margin: '0 0 0.4rem 0' }}>
        <strong>Evidence:</strong> {risk.supporting_evidence}
      </p>
      <p style={{ fontSize: '0.78rem', color: '#1d4ed8', margin: 0 }}>
        <strong>Action:</strong> {risk.mitigation_action}
      </p>
    </div>
  );
};

const BriefingMarkdown = ({ md }) => {
  if (!md) return null;
  // Simple markdown renderer for the briefing sections
  const lines = md.split('\n');
  return (
    <div style={{ fontSize: '0.9rem', color: '#374151', lineHeight: 1.7 }}>
      {lines.map((line, i) => {
        if (line.startsWith('#### ')) {
          return <h4 key={i} style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--navy-slate)', margin: '1rem 0 0.35rem' }}>{line.replace('#### ', '')}</h4>;
        }
        if (line.startsWith('### ')) {
          return <h3 key={i} style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--navy-slate)', margin: '0.5rem 0 0.35rem' }}>{line.replace('### ', '')}</h3>;
        }
        if (line.startsWith('**') && line.endsWith('**')) {
          return <p key={i} style={{ fontWeight: 700, margin: '0.2rem 0' }}>{line.replace(/\*\*/g, '')}</p>;
        }
        if (line.startsWith('- ')) {
          return <div key={i} style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.25rem' }}><span style={{ color: 'var(--navy-primary)' }}>•</span><span>{line.replace('- ', '')}</span></div>;
        }
        if (line.trim() === '') return <div key={i} style={{ height: '0.35rem' }} />;
        return <p key={i} style={{ margin: '0.25rem 0' }}>{line}</p>;
      })}
    </div>
  );
};

const FinancialIntelligenceSection = ({ intelligence: intel, loading, error, onRetry }) => {
  const [briefingOpen, setBriefingOpen] = useState(false);

  if (loading) {
    return (
      <div className="fintech-card" style={{ padding: '2.5rem', textAlign: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.75rem', color: 'var(--text-muted)' }}>
          <RefreshCw size={22} className="spin" />
          <span style={{ fontSize: '1rem' }}>Loading Financial Intelligence…</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="fintech-card" style={{ padding: '1.75rem', borderLeft: '4px solid #f87171' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.75rem' }}>
          <AlertCircle size={20} color="#ef4444" />
          <span style={{ fontWeight: 700, color: '#dc2626' }}>Financial Intelligence Unavailable</span>
        </div>
        <p style={{ color: '#6b7280', fontSize: '0.9rem', margin: '0 0 1rem' }}>{error}</p>
        <button onClick={onRetry} style={{
          display: 'inline-flex', alignItems: 'center', gap: '0.4rem',
          padding: '0.55rem 1.1rem', background: 'var(--navy-primary)', color: '#fff',
          border: 'none', borderRadius: '8px', fontSize: '0.9rem', fontWeight: 600, cursor: 'pointer',
        }}><RefreshCw size={14} /> Retry</button>
      </div>
    );
  }

  if (!intel) return null;

  const isInsufficient = intel.data_sufficiency_status === 'insufficient_data';
  const ha  = intel.historical_actuals    || {};
  const fc  = intel.forward_commitments   || {};
  const pe  = intel.projected_estimates   || {};
  const hi  = intel.financial_health_index || {};
  const mb  = intel.monthly_briefing       || {};
  const risks = intel.risk_intelligence   || [];

  const runwayColor =
    pe.runway_status?.startsWith('Cash') ? '#065f46' :
    pe.runway_status?.startsWith('Adequate') ? '#15803d' :
    pe.runway_status?.startsWith('Moderate') ? '#b45309' : '#991b1b';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>

      {/* ── Section Header ── */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', paddingBottom: '0.5rem', borderBottom: '2px solid var(--border-light)' }}>
        <Brain size={24} color="var(--navy-primary)" />
        <div>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--navy-slate)', margin: 0, letterSpacing: '-0.02em' }}>
            Financial Intelligence
          </h2>
          <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', margin: 0 }}>
            {intel.company_name} · Powered by SubWise AI · All figures from verified PayPal ledger data
          </p>
        </div>
        <div style={{ marginLeft: 'auto' }}>
          <HealthBadge score={hi.score} label={hi.status_label} />
        </div>
      </div>

      {/* ── Insufficient Data State ── */}
      {isInsufficient && (
        <div className="fintech-card" style={{ padding: '2rem', borderLeft: '4px solid #f59e0b', background: '#fffbeb' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.75rem' }}>
            <AlertTriangle size={20} color="#d97706" />
            <span style={{ fontWeight: 700, color: '#92400e', fontSize: '1rem' }}>Insufficient Operating Data for Full Analysis</span>
          </div>
          <p style={{ color: '#78350f', fontSize: '0.9rem', margin: '0 0 1rem' }}>
            {mb.overall_financial_position}
          </p>
          {intel.required_records_for_analysis?.length > 0 && (
            <div>
              <div style={{ fontWeight: 700, fontSize: '0.85rem', color: '#92400e', marginBottom: '0.5rem' }}>Required for full analysis:</div>
              {intel.required_records_for_analysis.map((r, i) => (
                <div key={i} style={{ display: 'flex', gap: '0.5rem', fontSize: '0.85rem', color: '#78350f', marginBottom: '0.25rem' }}>
                  <span>•</span><span>{r}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Three-Column Metric Grid ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem' }}>

        {/* Historical Actuals */}
        <div className="fintech-card" style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <Activity size={18} color="var(--navy-primary)" />
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--navy-slate)', margin: 0 }}>Historical Actuals</h3>
            <span style={{ fontSize: '0.68rem', background: '#dbeafe', color: '#1d4ed8', padding: '0.1rem 0.4rem', borderRadius: '4px', fontWeight: 700, marginLeft: 'auto' }}>VERIFIED</span>
          </div>
          <MetricRow label="Monthly Revenue" value={fmtMoney(ha.historical_monthly_operating_revenue)} highlight="#065f46" />
          <MetricRow label="Monthly Subscriptions" value={fmtMoney(ha.historical_monthly_subscription_expenses)} />
          <MetricRow label="Other Operating Expenses" value={fmtMoney(ha.historical_monthly_non_sub_expenses)} />
          <MetricRow
            label="Net Monthly Cash Flow"
            value={fmtMoney(ha.historical_monthly_net_cash_flow)}
            highlight={ha.historical_monthly_net_cash_flow >= 0 ? '#065f46' : '#991b1b'}
          />
          {ha.verified_available_cash !== null && ha.verified_available_cash !== undefined && (
            <MetricRow label="Available Cash" value={fmtMoney(ha.verified_available_cash)} sub="Ledger-derived estimate" />
          )}
          <div style={{ marginTop: '0.85rem', padding: '0.65rem', background: '#fef3c7', borderRadius: '6px', fontSize: '0.75rem', color: '#92400e' }}>
            ⚠️ {ha.paypal_balance_note}
          </div>
        </div>

        {/* Forward Commitments */}
        <div className="fintech-card" style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <CheckCircle2 size={18} color="#059669" />
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--navy-slate)', margin: 0 }}>Forward Commitments</h3>
          </div>
          <MetricRow label="Confirmed Monthly" value={fmtMoney(fc.confirmed_monthly_subscription_commitments)} highlight="#065f46" />
          <MetricRow label="Confirmed Annual" value={fmtMoney(fc.confirmed_annual_subscription_commitments)} />
          <MetricRow
            label="Potential Monthly"
            value={fmtMoney(fc.potential_monthly_subscription_commitments)}
            sub="Unconfirmed — not contractual"
            highlight="#b45309"
          />
          <MetricRow
            label="Upcoming (60 days)"
            value={`${fc.upcoming_renewals_count_next_60_days} renewal${fc.upcoming_renewals_count_next_60_days !== 1 ? 's' : ''}`}
            sub={fmtMoney(fc.upcoming_renewals_amount_next_60_days) + ' confirmed'}
          />
          <div style={{ marginTop: '0.85rem', padding: '0.55rem 0.75rem', background: '#f0fdf4', borderRadius: '6px', fontSize: '0.78rem', color: '#15803d' }}>
            Potential commitments are not confirmed contractual payments. Confirm with your team before budgeting.
          </div>
        </div>

        {/* Projected Estimates */}
        <div className="fintech-card" style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <TrendingUp size={18} color="#7c3aed" />
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--navy-slate)', margin: 0 }}>6-Month Projections</h3>
            <span style={{ fontSize: '0.68rem', background: '#ede9fe', color: '#6d28d9', padding: '0.1rem 0.4rem', borderRadius: '4px', fontWeight: 700, marginLeft: 'auto' }}>ESTIMATED</span>
          </div>
          <MetricRow label="Runway Status" value={pe.runway_status} mono={false} highlight={runwayColor} />
          {pe.estimated_runway_months !== null && pe.estimated_runway_months !== undefined && (
            <MetricRow label="Est. Runway" value={`${pe.estimated_runway_months} months`} />
          )}
          <MetricRow label="Baseline Monthly Revenue" value={fmtMoney(pe.projected_monthly_revenue_baseline)} />
          <MetricRow label="Projected Net Cash Flow" value={fmtMoney(pe.projected_monthly_net_cash_flow)}
            highlight={pe.projected_monthly_net_cash_flow >= 0 ? '#065f46' : '#991b1b'} />
          {pe.projected_lowest_cash_balance !== null && pe.projected_lowest_cash_balance !== undefined && (
            <MetricRow label="Lowest Projected Balance" value={fmtMoney(pe.projected_lowest_cash_balance)}
              highlight={pe.projected_lowest_cash_balance < 0 ? '#991b1b' : '#374151'} />
          )}
          {pe.projected_shortfall_month && (
            <MetricRow label="Shortfall Month" value={pe.projected_shortfall_month} mono={false} highlight="#991b1b" />
          )}
          <div style={{ marginTop: '0.85rem', padding: '0.55rem 0.75rem', background: '#f5f3ff', borderRadius: '6px', fontSize: '0.78rem', color: '#5b21b6' }}>
            {pe.runway_explanation}
          </div>
        </div>
      </div>

      {/* ── Risk Intelligence ── */}
      {risks.length > 0 && (
        <div className="fintech-card" style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '1.1rem' }}>
            <ShieldAlert size={20} color="#dc2626" />
            <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--navy-slate)', margin: 0 }}>
              Risk Intelligence
            </h3>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginLeft: 'auto' }}>
              {risks.length} risk trigger{risks.length !== 1 ? 's' : ''} identified
            </span>
          </div>
          {risks.map((r, i) => <RiskCard key={i} risk={r} />)}
        </div>
      )}

      {/* ── Monthly Business Briefing ── */}
      <div className="fintech-card" style={{ padding: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '1rem' }}>
          <Zap size={20} color="var(--navy-primary)" />
          <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--navy-slate)', margin: 0 }}>
            Executive Financial Briefing
          </h3>
          <div style={{ marginLeft: 'auto', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <span style={{
              fontSize: '0.7rem', fontWeight: 700, padding: '0.2rem 0.55rem', borderRadius: '4px',
              background: mb.is_ai_generated ? '#dbeafe' : '#f1f5f9',
              color: mb.is_ai_generated ? '#1d4ed8' : '#475569',
              border: `1px solid ${mb.is_ai_generated ? '#bfdbfe' : '#e2e8f0'}`,
            }}>
              {mb.is_ai_generated ? '✨ AI-Enhanced' : '⚙️ Deterministic'}
            </span>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{mb.generation_model}</span>
          </div>
        </div>

        {/* Quick summary cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '0.85rem', marginBottom: '1.25rem' }}>
          {[
            { label: '📌 Financial Position',    text: mb.overall_financial_position },
            { label: '📊 Revenue & Expenses',    text: mb.revenue_and_expense_summary },
            { label: '💳 Subscription Overview', text: mb.subscription_spending_overview },
            { label: '📅 Upcoming Obligations',  text: mb.upcoming_payment_obligations },
          ].map(({ label, text }, i) => (
            <div key={i} style={{
              background: 'var(--bg-hover, #f8fafc)', borderRadius: '8px',
              padding: '0.85rem 1rem', border: '1px solid var(--border-light)',
            }}>
              <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--navy-primary)', marginBottom: '0.35rem' }}>{label}</div>
              <p style={{ fontSize: '0.82rem', color: '#374151', margin: 0, lineHeight: 1.55 }}>
                {text?.length > 160 ? text.slice(0, 160) + '…' : text}
              </p>
            </div>
          ))}
        </div>

        {/* Recommended Actions */}
        {mb.recommended_cfo_actions?.length > 0 && (
          <div style={{ background: '#eff6ff', borderRadius: '8px', padding: '1rem', marginBottom: '1rem' }}>
            <div style={{ fontWeight: 700, fontSize: '0.88rem', color: 'var(--navy-primary)', marginBottom: '0.5rem' }}>
              Recommended Actions
            </div>
            {mb.recommended_cfo_actions.map((a, i) => (
              <div key={i} style={{ display: 'flex', gap: '0.5rem', fontSize: '0.85rem', color: '#1e3a5f', marginBottom: '0.3rem' }}>
                <span style={{ color: 'var(--navy-primary)', fontWeight: 700 }}>{i + 1}.</span>
                <span>{a}</span>
              </div>
            ))}
          </div>
        )}

        {/* Full Briefing Toggle */}
        <button
          onClick={() => setBriefingOpen(o => !o)}
          style={{
            display: 'inline-flex', alignItems: 'center', gap: '0.4rem',
            background: 'transparent', border: '1.5px solid var(--navy-primary)',
            color: 'var(--navy-primary)', borderRadius: '8px',
            padding: '0.5rem 1rem', fontSize: '0.88rem', fontWeight: 700, cursor: 'pointer',
          }}
        >
          <FileText size={14} />
          {briefingOpen ? 'Hide Full Briefing' : 'View Full Briefing'}
        </button>

        {briefingOpen && (
          <div style={{ marginTop: '1rem', padding: '1.25rem', background: '#f8fafc', borderRadius: '8px', border: '1px solid var(--border-light)' }}>
            <BriefingMarkdown md={mb.full_briefing_markdown} />
          </div>
        )}
      </div>

      {/* ── Transparency Disclosure ── */}
      <div style={{
        padding: '0.9rem 1.1rem',
        background: '#f8fafc', borderRadius: '8px',
        border: '1px solid var(--border-light)',
        fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: 1.6,
      }}>
        <span style={{ fontWeight: 700, color: 'var(--navy-slate)' }}>Transparency: </span>
        {intel.transparency_disclosure}
        {hi.scoring_methodology && (
          <div style={{ marginTop: '0.4rem' }}>
            <span style={{ fontWeight: 700 }}>Scoring: </span>{hi.scoring_methodology}
          </div>
        )}
      </div>

    </div>
  );
};

/* ------------------------------------------------------------------ */
/* Stage 6: Report Views                                              */
/* ------------------------------------------------------------------ */

const MonthlyReportView = ({ report }) => {
  if (!report || !report.monthly_breakdown || report.monthly_breakdown.length === 0) {
    return (
      <div className="fintech-card" style={{ padding: '3rem 2rem', textAlign: 'center' }}>
        <Calendar size={40} color="var(--text-muted)" style={{ margin: '0 auto 1rem', display: 'block' }} />
        <div style={{ fontWeight: 700, fontSize: '1.1rem', color: 'var(--navy-slate)', marginBottom: '0.4rem' }}>
          No Monthly Performance Records Found
        </div>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: '440px', margin: '0 auto' }}>
          No completed operating transactions exist for the selected reporting period. Synchronize your PayPal ledger to view historical cash movements.
        </p>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
        <div className="fintech-card" style={{ padding: '1.25rem' }}>
          <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Total Operating Revenue</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#065f46', fontFamily: 'JetBrains Mono, monospace', marginTop: '0.35rem' }}>
            {fmtMoney(report.total_operating_revenue)}
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Avg: {fmtMoney(report.average_monthly_revenue)}/mo</div>
        </div>
        <div className="fintech-card" style={{ padding: '1.25rem' }}>
          <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Software Subscriptions</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#003087', fontFamily: 'JetBrains Mono, monospace', marginTop: '0.35rem' }}>
            {fmtMoney(report.total_confirmed_sub_expenses)}
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Confirmed commitments</div>
        </div>
        <div className="fintech-card" style={{ padding: '1.25rem' }}>
          <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Total Operating Expenses</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#991b1b', fontFamily: 'JetBrains Mono, monospace', marginTop: '0.35rem' }}>
            {fmtMoney(report.total_operating_expenses)}
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Avg: {fmtMoney(report.average_monthly_expenses)}/mo</div>
        </div>
        <div className="fintech-card" style={{ padding: '1.25rem' }}>
          <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Net Operating Cash Flow</div>
          <div style={{
            fontSize: '1.6rem', fontWeight: 800,
            color: report.net_operating_cashflow >= 0 ? '#065f46' : '#991b1b',
            fontFamily: 'JetBrains Mono, monospace', marginTop: '0.35rem'
          }}>
            {report.net_operating_cashflow >= 0 ? '+' : ''}{fmtMoney(report.net_operating_cashflow)}
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Operating surplus / deficit</div>
        </div>
      </div>

      <div className="fintech-card" style={{ padding: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--navy-slate)', margin: 0 }}>
            Monthly Statement of Operating Cash Flows ({report.monthly_breakdown.length} Months)
          </h3>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Period: {report.reporting_period}</span>
        </div>
        <div className="fintech-table-wrapper">
          <table className="fintech-table">
            <thead>
              <tr>
                <th>Month</th>
                <th style={{ textAlign: 'right' }}>Operating Revenue</th>
                <th style={{ textAlign: 'right' }}>Software Subs</th>
                <th style={{ textAlign: 'right' }}>Non-Sub Expenses</th>
                <th style={{ textAlign: 'right' }}>Total Outflows</th>
                <th style={{ textAlign: 'right' }}>Net Operating Cash</th>
                <th style={{ textAlign: 'center' }}>Transactions</th>
                <th style={{ textAlign: 'right' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {report.monthly_breakdown.map((row) => (
                <tr key={row.month_key}>
                  <td style={{ fontWeight: 700, color: 'var(--navy-slate)' }}>{row.month_label}</td>
                  <td style={{ textAlign: 'right', color: '#065f46', fontWeight: 600 }}>{fmtMoney(row.operating_revenue)}</td>
                  <td style={{ textAlign: 'right', color: '#003087', fontWeight: 600 }}>{fmtMoney(row.confirmed_subscription_expenses)}</td>
                  <td style={{ textAlign: 'right', color: '#64748b' }}>{fmtMoney(row.non_sub_expenses)}</td>
                  <td style={{ textAlign: 'right', color: '#991b1b', fontWeight: 600 }}>{fmtMoney(row.total_operating_expenses)}</td>
                  <td style={{
                    textAlign: 'right', fontWeight: 700,
                    color: row.net_operating_cashflow >= 0 ? '#065f46' : '#991b1b',
                  }}>
                    {row.net_operating_cashflow >= 0 ? '+' : ''}{fmtMoney(row.net_operating_cashflow)}
                  </td>
                  <td style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>{row.operating_transaction_count}</td>
                  <td style={{ textAlign: 'right' }}>
                    <span style={{
                      fontSize: '0.7rem', fontWeight: 700, padding: '0.15rem 0.45rem', borderRadius: '4px',
                      background: 'var(--emerald-bg)', color: 'var(--emerald-dark)',
                      border: '1px solid var(--emerald-border, #bbf7d0)',
                    }}>
                      ACTUAL
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

const SubscriptionsReportView = ({ report }) => {
  if (!report || !report.items || report.items.length === 0) {
    return (
      <div className="fintech-card" style={{ padding: '3rem 2rem', textAlign: 'center' }}>
        <Layers size={40} color="var(--text-muted)" style={{ margin: '0 auto 1rem', display: 'block' }} />
        <div style={{ fontWeight: 700, fontSize: '1.1rem', color: 'var(--navy-slate)', marginBottom: '0.4rem' }}>
          No Subscriptions Recorded
        </div>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: '440px', margin: '0 auto' }}>
          Synchronize recurring disbursements from PayPal to detect software subscriptions and track price creep.
        </p>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
        <div className="fintech-card" style={{ padding: '1.25rem' }}>
          <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Confirmed Subscriptions</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#003087', fontFamily: 'JetBrains Mono, monospace', marginTop: '0.35rem' }}>
            {report.confirmed_subscriptions_count}
          </div>
          <div style={{ fontSize: '0.78rem', color: '#065f46', marginTop: '0.25rem' }}>{fmtMoney(report.total_confirmed_monthly_commitments)}/mo committed</div>
        </div>
        <div className="fintech-card" style={{ padding: '1.25rem' }}>
          <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Annual Contractual Run Rate</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#0f172a', fontFamily: 'JetBrains Mono, monospace', marginTop: '0.35rem' }}>
            {fmtMoney(report.total_confirmed_annual_commitments)}
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Confirmed 12-month commitment</div>
        </div>
        <div className="fintech-card" style={{ padding: '1.25rem' }}>
          <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Potential Trials</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#b45309', fontFamily: 'JetBrains Mono, monospace', marginTop: '0.35rem' }}>
            {report.potential_subscriptions_count}
          </div>
          <div style={{ fontSize: '0.78rem', color: '#b45309', marginTop: '0.25rem' }}>{fmtMoney(report.total_potential_monthly_commitments)}/mo awaiting 2nd cycle</div>
        </div>
      </div>

      <div className="fintech-card" style={{ padding: '1.5rem' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--navy-slate)', marginBottom: '1rem' }}>
          Subscription Commitment Roster ({report.items.length} Software Vendors)
        </h3>
        <div className="fintech-table-wrapper">
          <table className="fintech-table">
            <thead>
              <tr>
                <th>Vendor</th>
                <th>Category</th>
                <th>Frequency</th>
                <th style={{ textAlign: 'right' }}>Latest Amount</th>
                <th style={{ textAlign: 'right' }}>Monthly Eq.</th>
                <th style={{ textAlign: 'right' }}>Annual Run Rate</th>
                <th style={{ textAlign: 'center' }}>Classification</th>
                <th style={{ textAlign: 'center' }}>Price Creep</th>
                <th style={{ textAlign: 'right' }}>Next Billing</th>
              </tr>
            </thead>
            <tbody>
              {report.items.map((sub, idx) => (
                <tr key={sub.id || idx}>
                  <td style={{ fontWeight: 700, color: 'var(--navy-slate)' }}>{sub.vendor_name}</td>
                  <td style={{ color: 'var(--text-muted)' }}>{sub.category}</td>
                  <td style={{ textTransform: 'capitalize' }}>{sub.billing_frequency}</td>
                  <td style={{ textAlign: 'right', fontWeight: 600 }}>{fmtMoney(sub.latest_amount)}</td>
                  <td style={{ textAlign: 'right', fontWeight: 700, color: '#003087' }}>{fmtMoney(sub.monthly_equivalent)}</td>
                  <td style={{ textAlign: 'right', color: 'var(--text-muted)' }}>{fmtMoney(sub.annual_run_rate)}</td>
                  <td style={{ textAlign: 'center' }}>
                    <span style={{
                      fontSize: '0.7rem', fontWeight: 700, padding: '0.15rem 0.5rem', borderRadius: '4px',
                      background: sub.detection_type === 'confirmed' ? '#dbeafe' : '#fef3c7',
                      color: sub.detection_type === 'confirmed' ? '#1d4ed8' : '#92400e',
                    }}>
                      {sub.detection_type?.toUpperCase()}
                    </span>
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    {sub.has_price_creep ? (
                      <span style={{
                        fontSize: '0.7rem', fontWeight: 700, padding: '0.15rem 0.45rem', borderRadius: '4px',
                        background: '#fee2e2', color: '#991b1b',
                      }}>
                        +{sub.price_change_pct}% ESCALATION
                      </span>
                    ) : (
                      <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Normal</span>
                    )}
                  </td>
                  <td style={{ textAlign: 'right', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                    {sub.next_billing_date || '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

const RenewalsReportView = ({ report }) => {
  if (!report || !report.scheduled_renewals || report.scheduled_renewals.length === 0) {
    return (
      <div className="fintech-card" style={{ padding: '3rem 2rem', textAlign: 'center' }}>
        <Calendar size={40} color="var(--text-muted)" style={{ margin: '0 auto 1rem', display: 'block' }} />
        <div style={{ fontWeight: 700, fontSize: '1.1rem', color: 'var(--navy-slate)', marginBottom: '0.4rem' }}>
          No Scheduled Renewals
        </div>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: '440px', margin: '0 auto' }}>
          Upcoming contractual renewal dates populate automatically once recurring vendor subscriptions are detected.
        </p>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
        <div className="fintech-card" style={{ padding: '1.25rem' }}>
          <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>60-Day Renewal Obligations</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#003087', fontFamily: 'JetBrains Mono, monospace', marginTop: '0.35rem' }}>
            {fmtMoney(report.total_upcoming_60_days_amount)}
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Across {report.total_upcoming_60_days_count} upcoming payment(s)</div>
        </div>
        <div className="fintech-card" style={{ padding: '1.25rem' }}>
          <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Renewal Concentration</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, color: report.monthly_concentration_warnings?.length > 0 ? '#dc2626' : '#059669', fontFamily: 'JetBrains Mono, monospace', marginTop: '0.35rem' }}>
            {report.monthly_concentration_warnings?.length > 0 ? 'Warning' : 'Balanced'}
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>{report.monthly_concentration_warnings?.length || 0} spike cluster(s) detected</div>
        </div>
        <div className="fintech-card" style={{ padding: '1.25rem' }}>
          <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Unknown Renewal Dates</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#64748b', fontFamily: 'JetBrains Mono, monospace', marginTop: '0.35rem' }}>
            {report.unknown_renewal_date_count}
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Active subs awaiting date anchor</div>
        </div>
      </div>

      {report.monthly_concentration_warnings?.length > 0 && (
        <div className="fintech-card" style={{ padding: '1.25rem', borderLeft: '4px solid #f59e0b', background: '#fffbeb' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <AlertTriangle size={18} color="#d97706" />
            <span style={{ fontWeight: 700, color: '#92400e', fontSize: '0.95rem' }}>Renewal Concentration Alerts</span>
          </div>
          {report.monthly_concentration_warnings.map((w, idx) => (
            <p key={idx} style={{ color: '#78350f', fontSize: '0.88rem', margin: '0 0 0.35rem 0' }}>• {w}</p>
          ))}
        </div>
      )}

      <div className="fintech-card" style={{ padding: '1.5rem' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--navy-slate)', marginBottom: '1rem' }}>
          Upcoming Renewal Calendar Schedule ({report.scheduled_renewals.length} Payments)
        </h3>
        <div className="fintech-table-wrapper">
          <table className="fintech-table">
            <thead>
              <tr>
                <th>Expected Date</th>
                <th>Vendor</th>
                <th>Billing Cadence</th>
                <th style={{ textAlign: 'right' }}>Amount</th>
                <th style={{ textAlign: 'center' }}>Classification</th>
                <th style={{ textAlign: 'center' }}>Date Provenance</th>
                <th style={{ textAlign: 'right' }}>Concentration Risk</th>
              </tr>
            </thead>
            <tbody>
              {report.scheduled_renewals.map((pmt, idx) => (
                <tr key={idx}>
                  <td style={{ fontWeight: 700, color: 'var(--navy-slate)' }}>{pmt.expected_payment_date}</td>
                  <td style={{ fontWeight: 600 }}>{pmt.vendor_name}</td>
                  <td style={{ textTransform: 'capitalize' }}>{pmt.billing_frequency}</td>
                  <td style={{ textAlign: 'right', fontWeight: 700, color: '#003087' }}>{fmtMoney(pmt.expected_payment_amount)}</td>
                  <td style={{ textAlign: 'center' }}>
                    <span style={{
                      fontSize: '0.7rem', fontWeight: 700, padding: '0.15rem 0.45rem', borderRadius: '4px',
                      background: pmt.detection_type === 'confirmed' ? '#dbeafe' : '#fef3c7',
                      color: pmt.detection_type === 'confirmed' ? '#1d4ed8' : '#92400e',
                    }}>
                      {pmt.detection_type?.toUpperCase()}
                    </span>
                  </td>
                  <td style={{ textAlign: 'center', fontSize: '0.8rem', color: pmt.is_date_confirmed ? '#065f46' : '#b45309' }}>
                    {pmt.is_date_confirmed ? 'Confirmed Anchor' : 'Estimated Cadence'}
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    {pmt.is_high_concentration ? (
                      <span style={{ fontSize: '0.7rem', fontWeight: 700, padding: '0.15rem 0.45rem', borderRadius: '4px', background: '#fee2e2', color: '#991b1b' }}>
                        SPIKE CLUSTER
                      </span>
                    ) : (
                      <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Normal</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

const ForecastReportView = ({ report }) => {
  if (!report || !report.scenarios || Object.keys(report.scenarios).length === 0 || !report.scenarios.baseline?.timeline?.length) {
    return (
      <div className="fintech-card" style={{ padding: '3rem 2rem', textAlign: 'center' }}>
        <TrendingUp size={40} color="var(--text-muted)" style={{ margin: '0 auto 1rem', display: 'block' }} />
        <div style={{ fontWeight: 700, fontSize: '1.1rem', color: 'var(--navy-slate)', marginBottom: '0.4rem' }}>
          Insufficient Data for Forward Forecast
        </div>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: '440px', margin: '0 auto' }}>
          Forward cash-flow projections require at least 1 month of verified operating sales transactions and confirmed software renewals.
        </p>
      </div>
    );
  }

  const bScen = report.scenarios.baseline;
  const oScen = report.scenarios.optimistic || bScen;
  const cScen = report.scenarios.conservative || bScen;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
        <div className="fintech-card" style={{ padding: '1.25rem', borderLeft: '4px solid #059669' }}>
          <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#065f46', textTransform: 'uppercase' }}>Optimistic (+15% Growth)</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#065f46', fontFamily: 'JetBrains Mono, monospace', marginTop: '0.35rem' }}>
            {fmtMoney(oScen.monthly_projected_revenue)}/mo
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Net: {fmtMoney(oScen.monthly_projected_net_cashflow)}/mo</div>
        </div>
        <div className="fintech-card" style={{ padding: '1.25rem', borderLeft: '4px solid #003087' }}>
          <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#003087', textTransform: 'uppercase' }}>Baseline (Historical 0%)</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#003087', fontFamily: 'JetBrains Mono, monospace', marginTop: '0.35rem' }}>
            {fmtMoney(bScen.monthly_projected_revenue)}/mo
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Net: {fmtMoney(bScen.monthly_projected_net_cashflow)}/mo</div>
        </div>
        <div className="fintech-card" style={{ padding: '1.25rem', borderLeft: '4px solid #dc2626' }}>
          <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#991b1b', textTransform: 'uppercase' }}>Conservative (-20% Drop)</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#991b1b', fontFamily: 'JetBrains Mono, monospace', marginTop: '0.35rem' }}>
            {fmtMoney(cScen.monthly_projected_revenue)}/mo
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Net: {fmtMoney(cScen.monthly_projected_net_cashflow)}/mo</div>
        </div>
      </div>

      <div className="fintech-card" style={{ padding: '1.5rem' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--navy-slate)', marginBottom: '0.5rem' }}>
          Six-Month Multi-Scenario Cash-Flow Trajectory
        </h3>
        <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
          {report.assumptions_disclosure}
        </p>
        <div className="fintech-table-wrapper">
          <table className="fintech-table">
            <thead>
              <tr>
                <th>Month</th>
                <th style={{ textAlign: 'right' }}>Optimistic (+15%)</th>
                <th style={{ textAlign: 'right' }}>Baseline (0%)</th>
                <th style={{ textAlign: 'right' }}>Conservative (-20%)</th>
                <th style={{ textAlign: 'right' }}>Confirmed Software</th>
                <th style={{ textAlign: 'right' }}>Baseline Net Cash</th>
                <th style={{ textAlign: 'right' }}>Closing Cash (Base)</th>
              </tr>
            </thead>
            <tbody>
              {bScen.timeline.map((bM, i) => {
                const oM = oScen.timeline[i] || bM;
                const cM = cScen.timeline[i] || bM;
                return (
                  <tr key={bM.month_index}>
                    <td style={{ fontWeight: 700, color: 'var(--navy-slate)' }}>{bM.month_name}</td>
                    <td style={{ textAlign: 'right', color: '#065f46', fontWeight: 600 }}>{fmtMoney(oM.projected_revenue)}</td>
                    <td style={{ textAlign: 'right', color: '#003087', fontWeight: 600 }}>{fmtMoney(bM.projected_revenue)}</td>
                    <td style={{ textAlign: 'right', color: '#991b1b', fontWeight: 600 }}>{fmtMoney(cM.projected_revenue)}</td>
                    <td style={{ textAlign: 'right', color: '#64748b' }}>{fmtMoney(bM.projected_confirmed_sub_expenses)}</td>
                    <td style={{ textAlign: 'right', fontWeight: 700, color: bM.projected_net_cashflow >= 0 ? '#065f46' : '#991b1b' }}>
                      {bM.projected_net_cashflow >= 0 ? '+' : ''}{fmtMoney(bM.projected_net_cashflow)}
                    </td>
                    <td style={{ textAlign: 'right', fontWeight: 700, color: bM.is_cash_depleted ? '#991b1b' : 'var(--navy-slate)' }}>
                      {bM.projected_closing_balance !== null ? fmtMoney(bM.projected_closing_balance) : '—'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

/**
 * Safely extracts an array from various API response shapes:
 * - Direct array: [ ... ]
 * - Wrapper object with specific key: { subscriptions: [ ... ] } or { items: [ ... ] }
 * - Paginated / generic wrapper: { data: [ ... ] }
 * Never returns null, undefined, or a non-array.
 */
export const safeExtractArray = (res, preferredKey) => {
  if (Array.isArray(res)) return res;
  if (res && typeof res === 'object') {
    if (preferredKey && Array.isArray(res[preferredKey])) return res[preferredKey];
    if (Array.isArray(res.subscriptions)) return res.subscriptions;
    if (Array.isArray(res.items)) return res.items;
    if (Array.isArray(res.data)) return res.data;
    if (Array.isArray(res.transactions)) return res.transactions;
    if (Array.isArray(res.recommendations)) return res.recommendations;
  }
  return [];
};

/**
 * ReportsPage — Financial summary reports with charts and export.
 * Fetches real data from backend API; shows empty state when no transactions exist.
 */
const ReportsPage = () => {
  const { business } = useAuth();

  // Data state
  const [transactions, setTransactions] = useState([]);
  const [subscriptions, setSubscriptions] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [analysis, setAnalysis] = useState(null);
  const [intelligence, setIntelligence] = useState(null);
  const [intelLoading, setIntelLoading] = useState(true);
  const [intelError, setIntelError] = useState('');
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState('');
  const [exportMsg, setExportMsg] = useState('');

  // Stage 6 Reporting & Export state
  const [activeReportType, setActiveReportType] = useState('comprehensive');
  const [activePeriod, setActivePeriod] = useState('all');
  const [exportingPdf, setExportingPdf] = useState(false);
  const [exportingCsv, setExportingCsv] = useState(false);
  const [reportData, setReportData] = useState(null);
  const [reportLoading, setReportLoading] = useState(false);
  const [reportError, setReportError] = useState('');
  const [csvMenuOpen, setCsvMenuOpen] = useState(false);

  /* ------------------------------------------------------------------ */
  /* Data fetch                                                          */
  /* ------------------------------------------------------------------ */
  const fetchAll = async () => {
    setLoading(true);
    setError('');
    try {
      const [txRes, subRes, recRes, analysisRes] = await Promise.allSettled([
        transactionsAPI.getTransactions({ limit: 500 }),
        subscriptionsAPI.getSubscriptions(),
        recommendationsAPI.getRecommendations(),
        subscriptionsAPI.getAnalysis(),
      ]);

      if (txRes.status === 'fulfilled') {
        setTransactions(safeExtractArray(txRes.value, 'transactions'));
      } else {
        console.warn('Transactions fetch failed:', txRes.reason);
        setTransactions([]);
      }

      if (subRes.status === 'fulfilled') {
        setSubscriptions(safeExtractArray(subRes.value, 'subscriptions'));
      } else {
        console.warn('Subscriptions fetch failed:', subRes.reason);
        setSubscriptions([]);
      }

      if (recRes.status === 'fulfilled') {
        setRecommendations(safeExtractArray(recRes.value, 'recommendations'));
      } else {
        console.warn('Recommendations fetch failed:', recRes.reason);
        setRecommendations([]);
      }

      if (analysisRes.status === 'fulfilled') {
        setAnalysis(analysisRes.value && typeof analysisRes.value === 'object' ? analysisRes.value : null);
      } else {
        console.warn('Analysis fetch failed:', analysisRes.reason);
        setAnalysis(null);
      }

      if (txRes.status === 'rejected' && subRes.status === 'rejected') {
        setError('Failed to load transaction and subscription data. Please check your connection.');
      }
    } catch (err) {
      console.error('ReportsPage fetch error:', err);
      setError('Failed to load report data. Please check your connection and try again.');
    } finally {
      setLoading(false);
    }
  };

  const fetchIntelligence = async () => {
    setIntelLoading(true);
    setIntelError('');
    try {
      const data = await financialIntelligenceAPI.getOverview();
      setIntelligence(data);
    } catch (err) {
      console.error('Financial Intelligence fetch error:', err);
      setIntelError(err?.response?.data?.detail || 'Failed to load Financial Intelligence overview.');
    } finally {
      setIntelLoading(false);
    }
  };

  const fetchReportData = async (type = activeReportType, period = activePeriod) => {
    setReportLoading(true);
    setReportError('');
    try {
      let res = null;
      if (type === 'monthly') {
        res = await reportsAPI.getMonthlyReport({ period });
      } else if (type === 'subscriptions') {
        res = await reportsAPI.getSubscriptionsReport();
      } else if (type === 'renewals') {
        res = await reportsAPI.getRenewalsReport();
      } else if (type === 'forecast') {
        res = await reportsAPI.getForecastReport();
      } else if (type === 'comprehensive') {
        res = await reportsAPI.getComprehensiveReport({ period });
      }
      setReportData(res);
    } catch (err) {
      console.error('Report fetch error:', err);
      setReportError(err?.response?.data?.detail || `Failed to load ${type} report.`);
      setReportData(null);
    } finally {
      setReportLoading(false);
    }
  };

  useEffect(() => {
    fetchAll();
    fetchIntelligence();
  }, []);

  useEffect(() => {
    fetchReportData(activeReportType, activePeriod);
  }, [activeReportType, activePeriod]);

  /* ------------------------------------------------------------------ */
  /* Sync handler                                                        */
  /* ------------------------------------------------------------------ */
  const handleSync = async () => {
    setSyncing(true);
    setError('');
    try {
      await paypalAPI.sync({ days_back: 90 });
      await fetchAll();
    } catch (err) {
      const msg = err?.response?.data?.detail || err?.message || 'Sync failed';
      setError(msg);
    } finally {
      setSyncing(false);
    }
  };

  /* ------------------------------------------------------------------ */
  /* Derived computations from real data                                 */
  /* ------------------------------------------------------------------ */

  const safeTransactions = Array.isArray(transactions) ? transactions : [];
  const safeSubscriptions = Array.isArray(subscriptions) ? subscriptions : [];
  const safeRecommendations = Array.isArray(recommendations) ? recommendations : [];

  // Build monthly aggregates from real operating transactions
  const monthlyMap = {};
  const baseCurrency = (business?.currency || 'USD').toUpperCase();

  safeTransactions.forEach((tx) => {
    if (!tx || !tx.transaction_date) return;
    // Strictly filter out funding, internal SubWise test payments, and currency conversion legs
    if (!isValidOperatingTransaction(tx, safeTransactions)) return;

    // Currency isolation: only aggregate transactions matching the business base currency
    const txCurr = (tx.currency || baseCurrency).toUpperCase();
    if (txCurr !== baseCurrency) return;

    const d = new Date(tx.transaction_date);
    const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
    const label = d.toLocaleString('default', { month: 'short', year: 'numeric' });
    if (!monthlyMap[key]) {
      monthlyMap[key] = { key, month: label, income: 0, expenses: 0, subscriptions: 0 };
    }
    const amt = parseFloat(tx.gross_amount || tx.amount || 0);
    if (tx.transaction_type === 'credit' || (tx.transaction_type !== 'debit' && amt > 0)) {
      monthlyMap[key].income += Math.abs(amt);
    } else {
      monthlyMap[key].expenses += Math.abs(amt);
    }
  });

  // Add subscription costs to monthly buckets
  safeSubscriptions.forEach((sub) => {
    if (!sub) return;
    const monthAmt = parseFloat(sub.latest_amount || sub.amount || 0);
    Object.keys(monthlyMap).forEach((key) => {
      monthlyMap[key].subscriptions += monthAmt;
    });
  });

  const historicalMonths = Object.values(monthlyMap)
    .sort((a, b) => a.key.localeCompare(b.key))
    .slice(-12); // Last 12 months

  // YTD (all historical months)
  const ytdIncome = historicalMonths.reduce((s, d) => s + d.income, 0);
  const ytdExpenses = historicalMonths.reduce((s, d) => s + d.expenses, 0);
  const ytdSubSpend = historicalMonths.reduce((s, d) => s + d.subscriptions, 0);
  const ytdNet = ytdIncome - ytdExpenses;

  // Waste = zombie + redundant subscriptions
  const wasteMonthly = safeSubscriptions
    .filter((s) => s && ['zombie', 'redundant'].includes((s.status || '').toLowerCase()))
    .reduce((acc, s) => acc + parseFloat(s.latest_amount || s.amount || 0), 0);
  const monthCount = Math.max(historicalMonths.length, 1);
  const wasteYTD = wasteMonthly * monthCount;

  // Potential annual savings from recommendations
  const potentialSavingsTotal = safeRecommendations.reduce(
    (s, r) => s + parseFloat(r?.potential_annual_saving || r?.potentialAnnualSaving || 0), 0
  );

  // Category breakdown for pie chart from real subscriptions (7 Canonical Categories)
  const categoryData = useMemo(() => {
    if (analysis?.category_analysis && Array.isArray(analysis.category_analysis) && analysis.category_analysis.length > 0) {
      return analysis.category_analysis
        .filter((c) => c && c.monthly_spend > 0)
        .map((c, i) => ({
          name: c.category,
          value: parseFloat(c.monthly_spend.toFixed(2)),
          color: CATEGORY_COLORS[i % CATEGORY_COLORS.length],
        }));
    }
    const categoryMap = {};
    safeSubscriptions.forEach((sub) => {
      if (!sub) return;
      const cat = sub.category || sub.vendor_category || 'Other SaaS';
      const amt = parseFloat(sub.latest_amount || sub.amount || 0);
      categoryMap[cat] = (categoryMap[cat] || 0) + amt;
    });
    return Object.entries(categoryMap).map(([name, value], i) => ({
      name,
      value: parseFloat(value.toFixed(2)),
      color: CATEGORY_COLORS[i % CATEGORY_COLORS.length],
    }));
  }, [analysis, safeSubscriptions]);

  // Date range label
  const dateLabel = historicalMonths.length > 1
    ? `${historicalMonths[0].month} – ${historicalMonths[historicalMonths.length - 1].month}`
    : historicalMonths.length === 1
      ? historicalMonths[0].month
      : 'No data';

  const companyName = (!business?.company_name || business.company_name.toLowerCase().includes('demo')) ? 'My Business' : business.company_name;
  const hasData = safeTransactions.length > 0;

  /* ------------------------------------------------------------------ */
  /* Stage 6: Export Handlers (PDF & CSV with formula injection defense) */
  /* ------------------------------------------------------------------ */
  const handleDownloadPDF = async () => {
    setExportingPdf(true);
    setExportMsg('');
    try {
      const res = await reportsAPI.downloadPDF(activeReportType, { period: activePeriod });
      const blob = new Blob([res.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      const cleanBiz = (companyName || 'subwise').toLowerCase().replace(/[^a-z0-9]/g, '_');
      link.setAttribute('download', `subwise_${activeReportType}_report_${cleanBiz}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      setExportMsg('✓ PDF Report compiled & downloaded successfully.');
    } catch (err) {
      console.error('PDF export error:', err);
      setExportMsg('Failed to generate PDF. Check connection and try again.');
    } finally {
      setExportingPdf(false);
      setTimeout(() => setExportMsg(''), 5000);
    }
  };

  const handleDownloadCSV = async (exportType) => {
    const target = exportType || (
      activeReportType === 'subscriptions' ? 'subscriptions' :
      activeReportType === 'renewals' ? 'renewals' :
      activeReportType === 'forecast' ? 'forecast' :
      activeReportType === 'monthly' ? 'monthly' : 'transactions'
    );
    setExportingCsv(true);
    setCsvMenuOpen(false);
    setExportMsg('');
    try {
      const res = await reportsAPI.downloadCSV(target, { period: activePeriod });
      const blob = new Blob([res.data], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      const cleanBiz = (companyName || 'subwise').toLowerCase().replace(/[^a-z0-9]/g, '_');
      link.setAttribute('download', `subwise_${target}_export_${cleanBiz}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      setExportMsg(`✓ CSV (${target}) exported with formula injection protection.`);
    } catch (err) {
      console.error('CSV export error:', err);
      setExportMsg('Failed to export CSV. Please try again.');
    } finally {
      setExportingCsv(false);
      setTimeout(() => setExportMsg(''), 5000);
    }
  };

  /* ------------------------------------------------------------------ */
  /* Render                                                              */
  /* ------------------------------------------------------------------ */
  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh', flexDirection: 'column', gap: '1rem' }}>
        <RefreshCw size={32} color="var(--navy-primary)" className="spin" />
        <div style={{ color: 'var(--text-muted)', fontSize: '1rem' }}>Loading report data…</div>
      </div>
    );
  }

  const REPORT_TABS = [
    { id: 'comprehensive', label: 'Executive Intelligence', icon: <Brain size={16} /> },
    { id: 'monthly',       label: 'Monthly Performance',    icon: <Activity size={16} /> },
    { id: 'subscriptions', label: 'Software Overhead',      icon: <Layers size={16} /> },
    { id: 'renewals',      label: 'Renewal Calendar',       icon: <Calendar size={16} /> },
    { id: 'forecast',      label: '6-Month Forecast',       icon: <TrendingUp size={16} /> },
  ];

  const PERIOD_OPTIONS = [
    { id: 'all',          label: 'All Available' },
    { id: 'last_30_days', label: 'Last 30 Days' },
    { id: 'last_90_days', label: 'Last 90 Days' },
    { id: 'last_180_days',label: 'Last 180 Days' },
    { id: 'ytd',          label: 'Year-to-Date' },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.35rem' }}>

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--navy-slate)', letterSpacing: '-0.02em', marginBottom: '0.2rem' }}>
            Financial Reports &amp; Export Intelligence
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem' }}>
            {companyName} · {dateLabel} · {hasData ? `${transactions.length} transactions recorded` : 'No transactions synced'}
          </p>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.5rem' }}>
          <div style={{ display: 'flex', gap: '0.55rem', flexWrap: 'wrap', position: 'relative' }}>
            {/* Sync PayPal Button */}
            <button
              onClick={() => handleSync(false)}
              disabled={syncing}
              className="btn-fintech btn-fintech-outline btn-sm"
              style={{
                display: 'inline-flex', alignItems: 'center', gap: '0.45rem',
                minHeight: '36px', padding: '0.45rem 0.95rem', fontSize: '0.85rem'
              }}
            >
              <RefreshCw size={14} className={syncing ? 'spin' : ''} />
              {syncing ? 'Syncing…' : 'Sync PayPal'}
            </button>

            {/* Export CSV Menu Button */}
            <div style={{ position: 'relative' }}>
              <button
                onClick={() => setCsvMenuOpen(o => !o)}
                disabled={exportingCsv}
                className="btn-fintech btn-fintech-outline btn-sm"
                style={{
                  display: 'inline-flex', alignItems: 'center', gap: '0.45rem',
                  minHeight: '36px', padding: '0.45rem 0.95rem', fontSize: '0.85rem'
                }}
              >
                <Download size={14} />
                {exportingCsv ? 'Exporting…' : 'Export CSV ▾'}
              </button>

              {csvMenuOpen && (
                <div style={{
                  position: 'absolute', top: '100%', right: 0, marginTop: '0.4rem',
                  background: '#fff', border: '1px solid var(--border-light)', borderRadius: '8px',
                  boxShadow: '0 10px 25px rgba(0,0,0,0.1)', zIndex: 50, minWidth: '220px',
                  padding: '0.4rem', display: 'flex', flexDirection: 'column', gap: '0.2rem',
                }}>
                  <div style={{ fontSize: '0.72rem', fontWeight: 800, color: 'var(--text-muted)', padding: '0.4rem 0.6rem', textTransform: 'uppercase' }}>
                    CSV Export (Formula-Protected)
                  </div>
                  {[
                    { type: 'transactions', label: 'Ledger Transactions' },
                    { type: 'subscriptions', label: 'Subscription Overhead' },
                    { type: 'renewals', label: 'Upcoming Renewals' },
                    { type: 'monthly', label: 'Monthly Statement' },
                    { type: 'forecast', label: '6-Month Scenarios' },
                  ].map((opt) => (
                    <button
                      key={opt.type}
                      onClick={() => handleDownloadCSV(opt.type)}
                      style={{
                        textAlign: 'left', padding: '0.45rem 0.65rem', background: 'transparent',
                        border: 'none', borderRadius: '6px', fontSize: '0.82rem', fontWeight: 600,
                        color: 'var(--navy-slate)', cursor: 'pointer',
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bg-subtle)'}
                      onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Download PDF Report Button */}
            <button
              onClick={handleDownloadPDF}
              disabled={exportingPdf}
              className="btn-fintech btn-fintech-primary btn-sm"
              style={{
                display: 'inline-flex', alignItems: 'center', gap: '0.45rem',
                minHeight: '36px', padding: '0.45rem 1rem', fontSize: '0.85rem'
              }}
            >
              {exportingPdf ? (
                <>
                  <RefreshCw size={15} className="spin" />
                  Generating PDF…
                </>
              ) : (
                <>
                  <FileText size={16} />
                  Download PDF Report
                </>
              )}
            </button>
          </div>

          {exportMsg && (
            <div style={{ fontSize: '0.85rem', color: exportMsg.startsWith('✓') ? '#059669' : 'var(--text-muted)', maxWidth: '400px', textAlign: 'right', fontWeight: 600 }}>
              {exportMsg}
            </div>
          )}
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: '0.75rem',
          padding: '1rem 1.25rem', background: 'var(--rose-bg)',
          border: '1.5px solid var(--rose-border, #fecaca)',
          borderRadius: 'var(--radius-md)', color: 'var(--rose-dark)',
          fontSize: '0.95rem', fontWeight: 600,
        }}>
          <AlertCircle size={18} />
          {error}
        </div>
      )}

      {/* Stage 6: Report Category Tabs */}
      <div style={{
        display: 'flex', gap: '0.4rem', borderBottom: '2px solid var(--border-light)',
        paddingBottom: '0.1rem', flexWrap: 'wrap',
      }}>
        {REPORT_TABS.map((tab) => {
          const isActive = activeReportType === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveReportType(tab.id)}
              style={{
                display: 'inline-flex', alignItems: 'center', gap: '0.5rem',
                padding: '0.75rem 1.2rem',
                background: isActive ? '#dbeafe' : 'transparent',
                color: isActive ? '#003087' : 'var(--text-muted)',
                border: 'none', borderBottom: isActive ? '3px solid #003087' : '3px solid transparent',
                fontWeight: isActive ? 800 : 600, fontSize: '0.92rem',
                cursor: 'pointer', transition: 'all 0.15s ease',
                marginBottom: '-2px',
              }}
            >
              {tab.icon}
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Reporting Period Filter (for supported categories) */}
      {['comprehensive', 'monthly'].includes(activeReportType) && (
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          flexWrap: 'wrap', gap: '0.75rem', padding: '0.85rem 1.25rem',
          background: 'var(--bg-surface)', borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-light)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', fontWeight: 700, color: 'var(--navy-slate)' }}>
            <Calendar size={16} color="var(--navy-primary)" />
            <span>Reporting Period:</span>
          </div>
          <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
            {PERIOD_OPTIONS.map((p) => {
              const isSelected = activePeriod === p.id;
              return (
                <button
                  key={p.id}
                  onClick={() => setActivePeriod(p.id)}
                  style={{
                    padding: '0.35rem 0.85rem',
                    background: isSelected ? 'var(--navy-primary)' : 'var(--bg-hover, #f1f5f9)',
                    color: isSelected ? '#fff' : '#475569',
                    border: isSelected ? '1px solid var(--navy-primary)' : '1px solid #cbd5e1',
                    borderRadius: '20px', fontSize: '0.8rem', fontWeight: 700,
                    cursor: 'pointer',
                  }}
                >
                  {p.label}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Active Tab View Rendering */}
      {reportLoading ? (
        <div className="fintech-card" style={{ padding: '3.5rem', textAlign: 'center' }}>
          <RefreshCw size={28} className="spin" color="var(--navy-primary)" style={{ margin: '0 auto 0.75rem', display: 'block' }} />
          <div style={{ fontSize: '0.95rem', color: 'var(--text-muted)' }}>Loading report data…</div>
        </div>
      ) : reportError ? (
        <div className="fintech-card" style={{ padding: '2.5rem', textAlign: 'center', background: '#fff1f2', border: '1.5px solid #fecaca' }}>
          <AlertCircle size={36} color="#e11d48" style={{ margin: '0 auto 0.75rem', display: 'block' }} />
          <div style={{ fontWeight: 700, fontSize: '1.05rem', color: '#9f1239', marginBottom: '0.4rem' }}>
            Unable to Load Report
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: '420px', margin: '0 auto 1.25rem' }}>
            {reportError}
          </p>
          <button
            onClick={() => fetchReportData(activeReportType, activePeriod)}
            style={{
              padding: '0.6rem 1.25rem',
              background: 'var(--navy-primary)', color: '#fff',
              border: 'none', borderRadius: 'var(--radius-md)',
              fontWeight: 700, fontSize: '0.88rem', cursor: 'pointer',
            }}
          >
            Retry Report Fetch
          </button>
        </div>
      ) : activeReportType === 'monthly' ? (
        <MonthlyReportView report={reportData} />
      ) : activeReportType === 'subscriptions' ? (
        <SubscriptionsReportView report={reportData} />
      ) : activeReportType === 'renewals' ? (
        <RenewalsReportView report={reportData} />
      ) : activeReportType === 'forecast' ? (
        <ForecastReportView report={reportData} />
      ) : (
        /* Executive Comprehensive View */
        <>
          {!hasData ? (
            <EmptyState onSync={handleSync} syncing={syncing} />
          ) : (
            <>
          {/* YTD Summary Metrics */}
          <div>
            <h2 style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--navy-slate)', marginBottom: '1.15rem', letterSpacing: '-0.02em' }}>
              Period Summary ({historicalMonths.length} Month{historicalMonths.length !== 1 ? 's' : ''})
            </h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))', gap: '1.35rem' }}>
              <ReportMetric
                label="Total Income"
                value={fmt(ytdIncome)}
                sub={dateLabel}
                color="var(--emerald-dark)"
                bg="var(--emerald-bg)"
              />
              <ReportMetric
                label="Total Expenses"
                value={fmt(ytdExpenses)}
                sub={dateLabel}
                color="var(--rose-dark)"
                bg="var(--rose-bg)"
              />
              <ReportMetric
                label="Net Cash Flow"
                value={`${ytdNet > 0 ? '+' : ''}${fmt(ytdNet)}`}
                sub="Income minus expenses"
                color={ytdNet > 0 ? 'var(--emerald-dark)' : 'var(--rose-dark)'}
              />
              <ReportMetric
                label="Subscription Spend"
                value={fmt(ytdSubSpend)}
                sub="All detected recurring SaaS"
                color="var(--navy-primary)"
                bg="var(--paypal-blue-subtle)"
              />
              <ReportMetric
                label="Identified Waste"
                value={fmt(wasteYTD)}
                sub="Zombie + Redundant subscriptions"
                color="var(--amber-dark)"
                bg="var(--amber-bg)"
              />
              <ReportMetric
                label="Potential Annual Savings"
                value={fmt(potentialSavingsTotal)}
                sub="If all AI recommendations applied"
                color="var(--emerald-dark)"
                bg="var(--emerald-bg)"
              />
            </div>
          </div>

          {/* Monthly Table */}
          <div className="fintech-card" style={{ padding: '1.5rem' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--navy-slate)', marginBottom: '1.25rem' }}>
              Monthly Cash Flow Report
            </h3>
            {historicalMonths.length === 0 ? (
              <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '2rem', fontSize: '0.95rem' }}>
                No monthly data to display.
              </div>
            ) : (
              <div className="fintech-table-wrapper">
                <table className="fintech-table">
                  <thead>
                    <tr>
                      <th>Month</th>
                      <th style={{ textAlign: 'right' }}>Income</th>
                      <th style={{ textAlign: 'right' }}>Operating Expenses</th>
                      <th style={{ textAlign: 'right' }}>Subscription Costs</th>
                      <th style={{ textAlign: 'right' }}>Sub as % of Revenue</th>
                      <th style={{ textAlign: 'right' }}>Net Cash</th>
                    </tr>
                  </thead>
                  <tbody>
                    {historicalMonths.map((row) => {
                      const net = row.income - row.expenses;
                      const subPct = row.income > 0 ? ((row.subscriptions / row.income) * 100).toFixed(1) : '0.0';
                      return (
                        <tr key={row.key}>
                          <td style={{ fontWeight: 600, color: 'var(--navy-slate)' }}>{row.month}</td>
                          <td style={{ textAlign: 'right', color: 'var(--emerald-dark)', fontWeight: 600 }}>{fmt(row.income)}</td>
                          <td style={{ textAlign: 'right', color: 'var(--text-body)' }}>{fmt(row.expenses)}</td>
                          <td style={{ textAlign: 'right', color: 'var(--navy-primary)', fontWeight: 600 }}>{fmt(row.subscriptions)}</td>
                          <td style={{ textAlign: 'right' }}>
                            <span style={{
                              fontSize: '0.8rem', fontWeight: 700,
                              color: parseFloat(subPct) > 12 ? 'var(--amber-dark)' : 'var(--emerald-dark)',
                            }}>
                              {subPct}%
                            </span>
                          </td>
                          <td style={{ textAlign: 'right', fontWeight: 700, color: net > 0 ? 'var(--emerald-dark)' : 'var(--rose-dark)' }}>
                            {net > 0 ? '+' : ''}{fmt(net)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                  <tfoot>
                    <tr style={{ background: 'var(--bg-subtle)', fontWeight: 700 }}>
                      <td style={{ fontWeight: 700, color: 'var(--navy-slate)' }}>Total (Period)</td>
                      <td style={{ textAlign: 'right', color: 'var(--emerald-dark)' }}>{fmt(ytdIncome)}</td>
                      <td style={{ textAlign: 'right', color: 'var(--text-body)' }}>{fmt(ytdExpenses)}</td>
                      <td style={{ textAlign: 'right', color: 'var(--navy-primary)' }}>{fmt(ytdSubSpend)}</td>
                      <td style={{ textAlign: 'right', color: 'var(--text-muted)' }}>
                        {ytdIncome > 0 ? ((ytdSubSpend / ytdIncome) * 100).toFixed(1) : '0.0'}% avg
                      </td>
                      <td style={{ textAlign: 'right', color: ytdNet > 0 ? 'var(--emerald-dark)' : 'var(--rose-dark)' }}>
                        {ytdNet > 0 ? '+' : ''}{fmt(ytdNet)}
                      </td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            )}
          </div>

          {/* Charts Row */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '1.25rem' }}>

            {/* Bar Chart: Monthly Income vs Expenses */}
            <div className="fintech-card" style={{ padding: '1.5rem' }}>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--navy-slate)', marginBottom: '1rem' }}>
                Monthly Income vs Expenses
              </h3>
              {historicalMonths.length === 0 ? (
                <div style={{ height: 240, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                  No monthly data
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={historicalMonths} margin={{ top: 5, right: 15, left: 5, bottom: 0 }} barGap={4}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border-light)" />
                    <XAxis dataKey="month" tick={{ fontSize: 10, fill: 'var(--text-muted)' }} />
                    <YAxis tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 10, fill: 'var(--text-muted)' }} width={45} />
                    <Tooltip formatter={(v) => fmt(v)} />
                    <Legend wrapperStyle={{ fontSize: '0.8rem' }} />
                    <Bar dataKey="income" name="Income" fill="#10b981" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="expenses" name="Expenses" fill="#ef4444" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>

            {/* Donut: Subscription Category Breakdown */}
            <div className="fintech-card" style={{ padding: '1.5rem' }}>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--navy-slate)', marginBottom: '1rem' }}>
                Subscription Cost by Category
              </h3>
              {categoryData.length === 0 ? (
                <div style={{ height: 240, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                  No subscription categories detected
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={240}>
                  <PieChart>
                    <Pie
                      data={categoryData}
                      cx="50%"
                      cy="50%"
                      innerRadius={55}
                      outerRadius={90}
                      dataKey="value"
                      nameKey="name"
                      paddingAngle={2}
                    >
                      {categoryData.map((entry, i) => (
                        <Cell key={i} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(v) => fmt(v)} />
                    <Legend
                      layout="vertical"
                      align="right"
                      verticalAlign="middle"
                      wrapperStyle={{ fontSize: '0.72rem', paddingLeft: '0.5rem' }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* Subscription-Level Optimization Report */}
          <div className="fintech-card" style={{ padding: '1.5rem' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--navy-slate)', marginBottom: '1.25rem' }}>
              Subscription Optimization Report
            </h3>
            {safeSubscriptions.length === 0 ? (
              <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '2rem', fontSize: '0.95rem' }}>
                No subscriptions detected. Sync transactions to identify recurring payments.
              </div>
            ) : (
              <div className="fintech-table-wrapper">
                <table className="fintech-table">
                  <thead>
                    <tr>
                      <th>Subscription</th>
                      <th>Category</th>
                      <th style={{ textAlign: 'right' }}>Monthly Cost</th>
                      <th style={{ textAlign: 'right' }}>Annual Cost</th>
                      <th>Status</th>
                      <th style={{ textAlign: 'right' }}>Confidence</th>
                      <th style={{ textAlign: 'right' }}>Recommended Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {safeSubscriptions.map((sub, sIdx) => {
                      const rec = safeRecommendations.find((r) =>
                        r && r.vendor_name && sub && sub.vendor_name &&
                        (r.vendor_name.toLowerCase().includes(sub.vendor_name.toLowerCase().split(' ')[0]) ||
                         sub.vendor_name.toLowerCase().includes(r.vendor_name.toLowerCase().split(' ')[0]))
                      );
                      const rawAction = rec?.action_type || rec?.type || null;
                      const actionLabel = rawAction ? rawAction.replace(/_/g, ' ') : (sub.status?.toLowerCase() === 'active' ? 'Keep' : '—');
                      const actionColor = {
                        'consolidate': 'var(--paypal-blue)',
                        'cancel': 'var(--rose-dark)',
                        'downgrade': 'var(--amber-dark)',
                        'switch annual': 'var(--emerald-dark)',
                        'keep': 'var(--emerald-dark)',
                      }[actionLabel.toLowerCase()] || 'var(--text-muted)';
                      
                      const rawAmt = parseFloat(sub.latest_amount || sub.amount || 0);
                      const cadence = (sub.cadence || 'monthly').toLowerCase();
                      const monthlyAmt = cadence === 'annual' ? rawAmt / 12.0 : (cadence === 'quarterly' ? rawAmt / 3.0 : (cadence === 'weekly' ? rawAmt * (52.0 / 12.0) : rawAmt));
                      const annualAmt = cadence === 'annual' ? rawAmt : (cadence === 'quarterly' ? rawAmt * 4.0 : (cadence === 'weekly' ? rawAmt * 52.0 : rawAmt * 12.0));

                      const statusRaw = (sub.status || 'active').toLowerCase();
                      const statusLabel = statusRaw.charAt(0).toUpperCase() + statusRaw.slice(1);
                      const confidence = sub.confidence_score != null
                        ? `${Math.round(parseFloat(sub.confidence_score) * 100)}%`
                        : '—';
                      return (
                        <tr key={sub.id}>
                          <td>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', flexWrap: 'wrap' }}>
                              <span style={{ fontWeight: 600, color: 'var(--navy-slate)' }}>
                                {sub.vendor_name || sub.name || sub.merchant || '—'}
                              </span>
                              {sub.detection_type === 'potential' && (
                                <span style={{ fontSize: '0.65rem', fontWeight: 700, padding: '0.1rem 0.35rem', borderRadius: '4px', background: '#fef3c7', color: '#b45309', border: '1px solid #fde68a' }}>
                                  Potential
                                </span>
                              )}
                              {sub.billing_type === 'variable' && (
                                <span style={{ fontSize: '0.65rem', fontWeight: 700, padding: '0.1rem 0.35rem', borderRadius: '4px', background: '#ede9fe', color: '#6d28d9', border: '1px solid #ddd6fe' }}>
                                  Variable
                                </span>
                              )}
                            </div>
                            <div style={{ fontSize: '0.72rem', color: 'var(--text-caption)', textTransform: 'capitalize' }}>
                              {cadence} billing (${rawAmt.toFixed(2)})
                            </div>
                          </td>
                          <td style={{ fontSize: '0.84rem', color: 'var(--text-body)' }}>{sub.category || sub.vendor_category || '—'}</td>
                          <td style={{ textAlign: 'right', fontWeight: 600, color: 'var(--navy-slate)' }}>{fmt(monthlyAmt)}</td>
                          <td style={{ textAlign: 'right', color: 'var(--text-body)' }}>{fmt(annualAmt)}</td>
                          <td>
                            <span style={{
                              fontSize: '0.72rem', fontWeight: 700,
                              padding: '0.2rem 0.5rem', borderRadius: '4px',
                              background: statusRaw === 'active' ? 'var(--emerald-bg)' : statusRaw === 'at_risk' ? 'var(--amber-bg)' : 'var(--rose-bg)',
                              color: statusRaw === 'active' ? 'var(--emerald-dark)' : statusRaw === 'at_risk' ? 'var(--amber-dark)' : 'var(--rose-dark)',
                            }}>
                              {statusLabel}
                            </span>
                          </td>
                          <td style={{
                            textAlign: 'right', fontWeight: 700,
                            color: parseFloat(sub.confidence_score || 0) > 0.7 ? 'var(--emerald-dark)' : parseFloat(sub.confidence_score || 0) > 0.4 ? 'var(--amber-dark)' : 'var(--rose-dark)',
                          }}>
                            {confidence}
                          </td>
                          <td style={{ textAlign: 'right', fontSize: '0.78rem', fontWeight: 700, color: actionColor, textTransform: 'capitalize' }}>
                            {actionLabel}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Transaction-Level Report */}
          <div className="fintech-card" style={{ padding: '1.5rem' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--navy-slate)', marginBottom: '1.25rem' }}>
              Transaction Summary by Month
            </h3>
            {historicalMonths.length === 0 ? (
              <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '2rem', fontSize: '0.95rem' }}>
                No transaction data available.
              </div>
            ) : (
              <div className="fintech-table-wrapper">
                <table className="fintech-table">
                  <thead>
                    <tr>
                      <th>Month</th>
                      <th style={{ textAlign: 'right' }}>Income</th>
                      <th style={{ textAlign: 'right' }}>Expenses</th>
                      <th style={{ textAlign: 'right' }}>Closing Balance</th>
                      <th style={{ textAlign: 'right' }}>Period</th>
                    </tr>
                  </thead>
                  <tbody>
                    {historicalMonths.map((row, idx) => {
                      const net = row.income - row.expenses;
                      return (
                        <tr key={row.key}>
                          <td style={{ fontWeight: 600, color: 'var(--navy-slate)' }}>{row.month}</td>
                          <td style={{ textAlign: 'right', color: 'var(--emerald-dark)', fontWeight: 600 }}>{fmt(row.income)}</td>
                          <td style={{ textAlign: 'right', color: 'var(--rose-dark)', fontWeight: 600 }}>{fmt(row.expenses)}</td>
                          <td style={{ textAlign: 'right', fontWeight: 700, color: net >= 0 ? 'var(--emerald-dark)' : 'var(--rose-dark)' }}>{net >= 0 ? '+' : ''}{fmt(net)}</td>
                          <td style={{ textAlign: 'right' }}>
                            <span style={{
                              fontSize: '0.72rem', fontWeight: 700, padding: '0.2rem 0.5rem', borderRadius: '4px',
                              background: 'var(--emerald-bg)', color: 'var(--emerald-dark)',
                              border: '1px solid var(--emerald-border, #bbf7d0)',
                            }}>
                              ACTUAL
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}

      {/* ============================================================ */}
      {/* Stage 5: Financial Intelligence Section                       */}
      {/* ============================================================ */}
      <FinancialIntelligenceSection
        intelligence={intelligence}
        loading={intelLoading}
        error={intelError}
        onRetry={fetchIntelligence}
      />
        </>
      )}

      {/* Footer */}
      <div style={{
        textAlign: 'center', padding: '1rem',
        fontSize: '0.78rem', color: 'var(--text-caption)',
        borderTop: '1px solid var(--border-light)',
      }}>
        {hasData
          ? `📊 Report generated from ${transactions.length} real transactions for ${companyName}. Data sourced from your connected PayPal account.`
          : `📊 Connect your PayPal Sandbox account to generate real financial reports for ${companyName}.`}
      </div>
    </div>
  );
};

export default ReportsPage;
