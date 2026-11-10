import React, { useState, useEffect, useMemo } from 'react';
import { recommendationsAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import {
  TrendingUp,
  AlertTriangle,
  Zap,
  ArrowRightLeft,
  CalendarCheck,
  Copy,
  CheckCheck,
  ChevronDown,
  ChevronUp,
  DollarSign,
  Clock,
  RefreshCw,
  Database,
  Sparkles,
  Eye,
  FileText,
  TrendingDown,
  ShieldAlert,
  Info,
  Calculator,
  ShieldCheck,
  Calendar,
  Layers,
  ArrowRight
} from 'lucide-react';

/** Action type config — icon, colors, label */
const ACTION_CONFIG = {
  RENEWAL_RISK: { label: 'Renewal Risk', color: '#ea580c', bg: '#fff7ed', icon: CalendarCheck },
  CASHFLOW_PROTECTION: { label: 'Cash-Flow Protection', color: '#e11d48', bg: '#ffe4e6', icon: ShieldAlert },
  REVIEW: { label: 'Cost Review', color: '#4f46e5', bg: '#eef2ff', icon: Eye },
  RENEGOTIATE: { label: 'Price Increase Review', color: '#7c3aed', bg: '#f5f3ff', icon: FileText },
  CONSOLIDATE: { label: 'Duplicate Tool Review', color: '#0070ba', bg: '#e0f2fe', icon: ArrowRightLeft },
  DOWNGRADE: { label: 'Downgrade Plan', color: '#d97706', bg: '#fffbeb', icon: TrendingDown },
  SWITCH_ANNUAL: { label: 'Annual Billing Analysis', color: '#10b981', bg: '#ecfdf5', icon: CalendarCheck },
  CANCEL: { label: 'Decommission Zombie', color: '#dc2626', bg: '#fef2f2', icon: Zap },
  REVENUE_AUDIT: { label: 'Revenue Ratio Audit', color: '#be123c', bg: '#ffe4e6', icon: ShieldAlert },
};

const CONFIDENCE_CONFIG = {
  high: { label: 'High Confidence', color: '#059669', bg: '#ecfdf5', border: '#a7f3d0' },
  medium: { label: 'Medium Confidence', color: '#d97706', bg: '#fffbeb', border: '#fde68a' },
  low: { label: 'Low Confidence (Trial/Audit)', color: '#6366f1', bg: '#eef2ff', border: '#c7d2fe' },
};

const VERDICT_CONFIG = {
  'Affordable under current assumptions': {
    badge: 'var(--emerald-bg)',
    color: 'var(--emerald-dark)',
    border: 'var(--emerald-border)',
    icon: ShieldCheck,
    title: 'Affordable Under Current Assumptions'
  },
  'Affordable with caution': {
    badge: 'var(--amber-bg)',
    color: 'var(--amber-dark)',
    border: 'var(--amber-border)',
    icon: AlertTriangle,
    title: 'Affordable With Caution'
  },
  'Consider postponing': {
    badge: 'var(--rose-bg)',
    color: 'var(--rose-dark)',
    border: 'var(--rose-border, #fecaca)',
    icon: ShieldAlert,
    title: 'Consider Postponing'
  },
  'Insufficient financial data': {
    badge: 'var(--bg-subtle)',
    color: 'var(--navy-slate)',
    border: 'var(--border-medium)',
    icon: Info,
    title: 'Insufficient Financial Baseline'
  }
};

/** Single recommendation card displaying all intelligence elements */
const RecommendationCard = ({ rec, onApplied }) => {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);
  const [applied, setApplied] = useState(rec.status === 'applied');

  const actionKey = (rec.action_type || rec.type || 'REVIEW').toUpperCase();
  const action = ACTION_CONFIG[actionKey] || ACTION_CONFIG.REVIEW;
  const confidenceKey = (rec.confidence || 'medium').toLowerCase();
  const confidence = CONFIDENCE_CONFIG[confidenceKey] || CONFIDENCE_CONFIG.medium;
  const ActionIcon = action.icon;

  const script = rec.negotiation_script || rec.script_template || rec.scriptTemplate;

  const handleCopy = () => {
    if (!script) return;
    navigator.clipboard.writeText(script);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleApply = async () => {
    try {
      if (rec.id) {
        await recommendationsAPI.updateRecommendation(rec.id, { status: 'applied' });
      }
      setApplied(true);
      if (onApplied) onApplied(rec.id);
    } catch (e) {
      console.error('Failed to update recommendation status', e);
    }
  };

  const monthlySaving = Number(rec.potential_monthly_saving || rec.potentialMonthlySaving || 0);
  const annualSaving = Number(rec.potential_annual_saving || rec.potentialAnnualSaving || monthlySaving * 12);
  const runwayDays = Number(rec.runway_impact_days || rec.runwayImpactDays || Math.round(monthlySaving / 15));

  return (
    <div className="fintech-card" style={{
      padding: '1.65rem 1.85rem',
      borderLeft: `5px solid ${action.color}`,
      opacity: applied ? 0.7 : 1,
      transition: 'opacity 0.2s ease',
      background: 'var(--bg-surface)'
    }}>
      {/* Top Header Row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
        <div style={{ flex: 1, minWidth: '280px' }}>
          <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center', marginBottom: '0.65rem', flexWrap: 'wrap' }}>
            {/* Action Badge */}
            <span style={{
              display: 'inline-flex', alignItems: 'center', gap: '0.35rem',
              fontSize: '0.78rem', fontWeight: 800, padding: '0.3rem 0.75rem',
              background: action.bg, color: action.color,
              borderRadius: '6px', textTransform: 'uppercase', letterSpacing: '0.06em',
            }}>
              <ActionIcon size={14} /> {action.label}
            </span>

            {/* Confidence Level Badge */}
            <span style={{
              fontSize: '0.78rem', fontWeight: 700, padding: '0.3rem 0.75rem',
              background: confidence.bg, color: confidence.color,
              border: `1px solid ${confidence.border}`, borderRadius: '6px',
            }}>
              {confidence.label}
            </span>

            {/* Provider Label */}
            {rec.vendor_name && (
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--navy-slate)', background: 'var(--bg-subtle)', padding: '0.3rem 0.65rem', borderRadius: '6px' }}>
                {rec.vendor_name}
              </span>
            )}

            {applied && (
              <span style={{ fontSize: '0.8rem', fontWeight: 700, padding: '0.3rem 0.75rem', background: 'var(--emerald-bg)', color: 'var(--emerald-dark)', borderRadius: '6px' }}>
                ✓ Applied
              </span>
            )}
          </div>

          <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--navy-slate)', marginBottom: '0.35rem', lineHeight: 1.3 }}>
            {rec.title}
          </h3>
        </div>

        {/* Quantified Financial Impact Panel */}
        <div style={{ textAlign: 'right', flexShrink: 0, minWidth: '150px' }}>
          <div style={{ fontSize: '1.85rem', fontWeight: 800, color: 'var(--emerald-dark)', lineHeight: 1, fontFamily: 'JetBrains Mono, monospace' }}>
            +${monthlySaving.toFixed(0)}/mo
          </div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
            ${annualSaving.toLocaleString()}/yr run-rate
          </div>
          <div style={{ fontSize: '0.82rem', color: 'var(--paypal-blue)', fontWeight: 700, marginTop: '0.3rem', display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '0.35rem' }}>
            <Clock size={13} /> +{runwayDays} days runway
          </div>
        </div>
      </div>

      {/* Identified Issue */}
      {rec.identified_issue && (
        <div style={{
          marginTop: '1rem',
          padding: '0.75rem 1rem',
          background: 'var(--rose-bg)',
          borderRadius: 'var(--radius-md)',
          fontSize: '0.88rem',
          color: 'var(--rose-dark)',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          border: '1px solid var(--rose-border, #fecaca)'
        }}>
          <AlertTriangle size={16} flexShrink={0} />
          <span><strong>Issue:</strong> {rec.identified_issue}</span>
        </div>
      )}

      {/* Supporting Transaction Evidence */}
      {rec.supporting_evidence && (
        <div style={{
          marginTop: '0.75rem',
          padding: '0.75rem 1rem',
          background: 'var(--bg-subtle)',
          borderRadius: 'var(--radius-md)',
          fontSize: '0.85rem',
          color: 'var(--text-body)',
          lineHeight: 1.5,
          borderLeft: '3px solid var(--paypal-blue)'
        }}>
          <div style={{ fontWeight: 700, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)', marginBottom: '0.2rem' }}>
            Supporting Transaction & Calendar Evidence
          </div>
          {rec.supporting_evidence}
        </div>
      )}

      {/* Explanation of Why Generated */}
      {(rec.explanation || rec.rationale) && (
        <div style={{ marginTop: '0.85rem', fontSize: '0.85rem', color: 'var(--text-body)', lineHeight: 1.55 }}>
          <span style={{ fontWeight: 700, color: 'var(--navy-slate)' }}>Why this was generated: </span>
          {rec.explanation || rec.rationale}
        </div>
      )}

      {/* Suggested Action Plan */}
      {(rec.action_plan || rec.actionPlan) && (
        <div style={{ marginTop: '0.85rem', padding: '0.75rem 1rem', background: '#f8fafc', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-light)' }}>
          <div style={{ fontWeight: 700, fontSize: '0.82rem', color: 'var(--navy-slate)', marginBottom: '0.35rem' }}>
            Suggested Action Plan:
          </div>
          <div style={{ fontSize: '0.84rem', color: 'var(--text-body)', lineHeight: 1.6, whiteSpace: 'pre-line' }}>
            {rec.action_plan || rec.actionPlan}
          </div>
        </div>
      )}

      {/* Negotiation Script — Expandable */}
      {script && (
        <div style={{ marginTop: '1rem' }}>
          <button
            onClick={() => setExpanded(!expanded)}
            style={{
              display: 'flex', alignItems: 'center', gap: '0.4rem',
              background: 'none', border: 'none', cursor: 'pointer',
              fontSize: '0.85rem', fontWeight: 700, color: 'var(--paypal-blue)',
              padding: '0.3rem 0',
            }}
          >
            {expanded ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
            {expanded ? 'Hide Supplier Negotiation Script' : 'View Pre-Drafted Negotiation Script'}
          </button>

          {expanded && (
            <div style={{ marginTop: '0.65rem' }}>
              <div style={{
                position: 'relative',
                background: '#f8fafc',
                border: '1px solid var(--border-light)',
                borderRadius: 'var(--radius-md)',
                padding: '1rem 1.15rem',
                fontSize: '0.82rem',
                fontFamily: 'JetBrains Mono, monospace',
                color: 'var(--text-body)',
                lineHeight: 1.6,
                whiteSpace: 'pre-wrap',
                maxHeight: '200px',
                overflowY: 'auto',
              }}>
                {script}
              </div>
              <button
                onClick={handleCopy}
                style={{
                  display: 'inline-flex', alignItems: 'center', gap: '0.45rem',
                  marginTop: '0.5rem',
                  padding: '0.45rem 0.95rem',
                  background: copied ? 'var(--emerald-bg)' : 'var(--bg-subtle)',
                  color: copied ? 'var(--emerald-dark)' : 'var(--navy-slate)',
                  border: `1.5px solid ${copied ? 'var(--emerald-border)' : 'var(--border-light)'}`,
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.8rem',
                  fontWeight: 700,
                  cursor: 'pointer',
                }}
              >
                {copied ? <CheckCheck size={14} /> : <Copy size={14} />}
                {copied ? 'Copied to clipboard' : 'Copy Negotiation Script'}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Action Footer */}
      <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.25rem', paddingTop: '1rem', borderTop: '1px solid var(--border-light)', justifyContent: 'flex-end' }}>
        {!applied && (
          <button
            onClick={handleApply}
            className="btn-fintech btn-fintech-primary btn-sm"
            style={{ fontSize: '0.84rem' }}
          >
            Mark as Applied
          </button>
        )}
      </div>
    </div>
  );
};

/** Interactive Subscription Purchase Decision Simulator Component */
const PurchaseSimulator = () => {
  const [vendor, setVendor] = useState('');
  const [amount, setAmount] = useState('120.00');
  const [cadence, setCadence] = useState('monthly');
  const [firstDate, setFirstDate] = useState(new Date().toISOString().split('T')[0]);
  const [purpose, setPurpose] = useState('Customer Relationship Management');
  const [discountPct, setDiscountPct] = useState('');
  const [simulating, setSimulating] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSimulate = async (e) => {
    if (e) e.preventDefault();
    if (!vendor.trim() || Number(amount) <= 0) {
      setError('Please provide a valid vendor name and positive purchase amount.');
      return;
    }
    setError(null);
    setSimulating(true);

    try {
      const payload = {
        proposed_vendor: vendor.trim(),
        amount: parseFloat(amount),
        cadence: cadence,
        first_payment_date: firstDate || null,
        business_purpose: purpose.trim() || null,
        verified_annual_discount_pct: discountPct ? parseFloat(discountPct) : null,
      };

      const res = await recommendationsAPI.simulatePurchase(payload);
      setResult(res);
    } catch (err) {
      console.error('Purchase simulation error:', err);
      setError(err.response?.data?.detail || 'Simulation evaluation failed.');
    } finally {
      setSimulating(false);
    }
  };

  const verdictCfg = result ? (VERDICT_CONFIG[result.verdict] || VERDICT_CONFIG['Insufficient financial data']) : null;
  const VerdictIcon = verdictCfg ? verdictCfg.icon : Info;

  return (
    <div className="fintech-card" style={{ padding: '2rem', border: '1.5px solid var(--border-light)', borderRadius: 'var(--radius-lg)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
        <div style={{ width: '38px', height: '38px', borderRadius: '10px', background: 'var(--paypal-blue-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Calculator size={20} color="var(--paypal-blue)" />
        </div>
        <div>
          <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--navy-slate)', letterSpacing: '-0.02em', margin: 0 }}>
            Subscription Purchase Decision Simulator
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', margin: '0.2rem 0 0 0' }}>
            Simulate the marginal cash-flow impact, renewal concentration, and liquidity runway before committing to a new subscription.
          </p>
        </div>
      </div>

      {/* Simulator Input Form */}
      <form onSubmit={handleSimulate} style={{ marginTop: '1.5rem', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.25rem' }}>
        <div>
          <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: 'var(--navy-slate)', marginBottom: '0.35rem' }}>
            Proposed Vendor / Software Name
          </label>
          <input
            type="text"
            className="input-fintech"
            value={vendor}
            onChange={(e) => setVendor(e.target.value)}
            placeholder="e.g. HubSpot CRM, Datadog"
            style={{ width: '100%', padding: '0.65rem 0.85rem' }}
          />
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: 'var(--navy-slate)', marginBottom: '0.35rem' }}>
            Subscription Price ($)
          </label>
          <input
            type="number"
            step="0.01"
            className="input-fintech"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder="120.00"
            style={{ width: '100%', padding: '0.65rem 0.85rem', fontFamily: 'JetBrains Mono, monospace' }}
          />
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: 'var(--navy-slate)', marginBottom: '0.35rem' }}>
            Billing Frequency
          </label>
          <select
            className="input-fintech"
            value={cadence}
            onChange={(e) => setCadence(e.target.value)}
            style={{ width: '100%', padding: '0.65rem 0.85rem' }}
          >
            <option value="monthly">Monthly Recurring</option>
            <option value="annual">Annual Pre-Pay</option>
            <option value="quarterly">Quarterly</option>
            <option value="weekly">Weekly</option>
          </select>
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: 'var(--navy-slate)', marginBottom: '0.35rem' }}>
            First Payment Date
          </label>
          <input
            type="date"
            className="input-fintech"
            value={firstDate}
            onChange={(e) => setFirstDate(e.target.value)}
            style={{ width: '100%', padding: '0.65rem 0.85rem' }}
          />
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: 'var(--navy-slate)', marginBottom: '0.35rem' }}>
            Business Purpose (Optional)
          </label>
          <input
            type="text"
            className="input-fintech"
            value={purpose}
            onChange={(e) => setPurpose(e.target.value)}
            placeholder="e.g. Sales Pipeline Management"
            style={{ width: '100%', padding: '0.65rem 0.85rem' }}
          />
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: 'var(--navy-slate)', marginBottom: '0.35rem' }}>
            Verified Annual Discount % (Optional)
          </label>
          <input
            type="number"
            step="0.1"
            className="input-fintech"
            value={discountPct}
            onChange={(e) => setDiscountPct(e.target.value)}
            placeholder="e.g. 15 (if verified)"
            style={{ width: '100%', padding: '0.65rem 0.85rem', fontFamily: 'JetBrains Mono, monospace' }}
          />
        </div>

        <div style={{ gridColumn: '1 / -1', display: 'flex', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
          <button
            type="submit"
            disabled={simulating}
            className="btn-fintech btn-fintech-primary"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.55rem', padding: '0.75rem 1.75rem', fontSize: '0.95rem' }}
          >
            {simulating ? <RefreshCw size={16} className="spin-icon" /> : <Calculator size={16} />}
            <span>{simulating ? 'Evaluating Affordability...' : 'Run Purchase Simulation'}</span>
          </button>
        </div>
      </form>

      {error && (
        <div style={{ marginTop: '1.25rem', padding: '0.85rem 1.15rem', background: '#fee2e2', color: 'var(--rose-dark)', borderRadius: 'var(--radius-sm)', border: '1px solid #fecaca', fontSize: '0.9rem' }}>
          {error}
        </div>
      )}

      {/* Simulation Results Display */}
      {result && verdictCfg && (
        <div style={{ marginTop: '2rem', paddingTop: '1.75rem', borderTop: '1px solid var(--border-light)' }}>
          {/* Prominent Verdict Banner */}
          <div style={{
            padding: '1.25rem 1.5rem',
            background: verdictCfg.badge,
            color: verdictCfg.color,
            borderRadius: 'var(--radius-md)',
            border: `1.5px solid ${verdictCfg.border}`,
            display: 'flex',
            alignItems: 'flex-start',
            gap: '1rem',
            marginBottom: '1.5rem'
          }}>
            <VerdictIcon size={28} style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', flexWrap: 'wrap' }}>
                <span style={{ fontSize: '1.15rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  {verdictCfg.title}
                </span>
                <span style={{ fontSize: '0.75rem', padding: '0.2rem 0.55rem', background: 'rgba(255,255,255,0.8)', borderRadius: '4px', fontWeight: 700 }}>
                  Hypothetical Simulation
                </span>
              </div>
              <p style={{ marginTop: '0.45rem', fontSize: '0.92rem', lineHeight: 1.55, margin: '0.35rem 0 0 0' }}>
                {result.verdict_explanation}
              </p>
            </div>
          </div>

          {/* Key Metric Highlights */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
            <div style={{ padding: '1rem 1.25rem', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)' }}>
              <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Immediate Cash Outflow
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--navy-slate)', fontFamily: 'JetBrains Mono, monospace', marginTop: '0.35rem' }}>
                ${result.immediate_cash_impact.toFixed(2)}
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                Day 1 initial payment
              </div>
            </div>

            <div style={{ padding: '1rem 1.25rem', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)' }}>
              <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Monthly Equivalent Cost
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--paypal-blue)', fontFamily: 'JetBrains Mono, monospace', marginTop: '0.35rem' }}>
                ${result.monthly_equivalent_cost.toFixed(2)}/mo
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                Normalized run-rate
              </div>
            </div>

            <div style={{ padding: '1rem 1.25rem', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)' }}>
              <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Annualized Commitment
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--navy-primary)', fontFamily: 'JetBrains Mono, monospace', marginTop: '0.35rem' }}>
                ${result.annual_cost.toFixed(2)}/yr
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                12-month run-rate obligation
              </div>
            </div>

            <div style={{ padding: '1rem 1.25rem', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)' }}>
              <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Lowest Projected Cash
              </div>
              <div style={{
                fontSize: '1.5rem', fontWeight: 800,
                color: (result.simulated_lowest_balance !== null && result.simulated_lowest_balance < 0) ? 'var(--rose-dark)' : 'var(--emerald-dark)',
                fontFamily: 'JetBrains Mono, monospace', marginTop: '0.35rem'
              }}>
                {result.simulated_lowest_balance !== null ? `$${result.simulated_lowest_balance.toFixed(2)}` : 'Baseline N/A'}
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                {result.projected_shortfall_detected ? 'Liquidity Shortfall Triggered' : 'Cash buffer maintained'}
              </div>
            </div>
          </div>

          {/* Annual vs Monthly Analysis Panel */}
          {result.annual_vs_monthly && (
            <div style={{ padding: '1.25rem 1.5rem', background: '#f8fafc', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)', marginBottom: '1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                <CalendarCheck size={18} color="var(--paypal-blue)" />
                <h4 style={{ margin: 0, fontSize: '0.98rem', fontWeight: 800, color: 'var(--navy-slate)' }}>
                  Annual vs Monthly Billing Analysis
                </h4>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
                <div>
                  <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Monthly Retail Payment:</div>
                  <div style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--navy-slate)', fontFamily: 'JetBrains Mono, monospace' }}>
                    ${result.annual_vs_monthly.monthly_payment_amount.toFixed(2)}/mo
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Annual Pre-Pay Total:</div>
                  <div style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--navy-slate)', fontFamily: 'JetBrains Mono, monospace' }}>
                    ${result.annual_vs_monthly.annual_payment_amount.toFixed(2)}/yr
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Immediate Liquidity Difference:</div>
                  <div style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--navy-primary)', fontFamily: 'JetBrains Mono, monospace' }}>
                    +${result.annual_vs_monthly.immediate_cash_outflow_difference.toFixed(2)}
                  </div>
                </div>
              </div>

              <div style={{ marginTop: '0.75rem', fontSize: '0.84rem', color: 'var(--text-body)', lineHeight: 1.5 }}>
                <strong>Discount Disclosure: </strong>
                {result.annual_vs_monthly.discount_disclosure}
              </div>

              <div style={{ marginTop: '0.35rem', fontSize: '0.84rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
                <strong>Closing Balance Effect: </strong>
                {result.annual_vs_monthly.impact_on_projected_closing_balance}
              </div>
            </div>
          )}

          {/* Renewal Concentration Note */}
          {result.renewal_concentration_effect && (
            <div style={{ padding: '0.85rem 1.15rem', background: '#eff6ff', borderRadius: 'var(--radius-sm)', border: '1px solid #bfdbfe', fontSize: '0.86rem', color: '#1e40af', marginBottom: '1.5rem' }}>
              <strong>Renewal Concentration Impact: </strong>
              {result.renewal_concentration_effect}
            </div>
          )}

          {/* 6-Month Trajectory Table */}
          {result.timeline_comparison && result.timeline_comparison.length > 0 && (
            <div style={{ marginBottom: '1.5rem' }}>
              <div style={{ fontSize: '0.92rem', fontWeight: 800, color: 'var(--navy-slate)', marginBottom: '0.65rem' }}>
                Simulated 6-Month Cash-Flow Trajectory
              </div>
              <div style={{ overflowX: 'auto', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.84rem' }}>
                  <thead>
                    <tr style={{ background: 'var(--bg-subtle)', textAlign: 'left', borderBottom: '1px solid var(--border-light)' }}>
                      <th style={{ padding: '0.65rem 0.85rem', fontWeight: 700 }}>Month</th>
                      <th style={{ padding: '0.65rem 0.85rem', fontWeight: 700 }}>Baseline Balance</th>
                      <th style={{ padding: '0.65rem 0.85rem', fontWeight: 700 }}>Simulated Outflow</th>
                      <th style={{ padding: '0.65rem 0.85rem', fontWeight: 700 }}>Simulated Balance</th>
                      <th style={{ padding: '0.65rem 0.85rem', fontWeight: 700 }}>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.timeline_comparison.map((pt) => (
                      <tr key={pt.month} style={{ borderBottom: '1px solid var(--border-light)' }}>
                        <td style={{ padding: '0.65rem 0.85rem', fontWeight: 700 }}>{pt.month_name}</td>
                        <td style={{ padding: '0.65rem 0.85rem', fontFamily: 'JetBrains Mono, monospace' }}>
                          {pt.baseline_closing_balance !== null ? `$${pt.baseline_closing_balance.toFixed(2)}` : 'N/A'}
                        </td>
                        <td style={{ padding: '0.65rem 0.85rem', fontFamily: 'JetBrains Mono, monospace', color: 'var(--rose-dark)' }}>
                          -${pt.proposed_outflow.toFixed(2)}
                        </td>
                        <td style={{ padding: '0.65rem 0.85rem', fontFamily: 'JetBrains Mono, monospace', fontWeight: 700, color: (pt.simulated_closing_balance !== null && pt.simulated_closing_balance < 0) ? 'var(--rose-dark)' : 'var(--navy-slate)' }}>
                          {pt.simulated_closing_balance !== null ? `$${pt.simulated_closing_balance.toFixed(2)}` : 'Hypothetical'}
                        </td>
                        <td style={{ padding: '0.65rem 0.85rem' }}>
                          {pt.is_cash_depleted ? (
                            <span style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--rose-dark)', background: 'var(--rose-bg)', padding: '0.2rem 0.5rem', borderRadius: '4px' }}>
                              Deficit
                            </span>
                          ) : (
                            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--emerald-dark)', background: 'var(--emerald-bg)', padding: '0.2rem 0.5rem', borderRadius: '4px' }}>
                              Solvent
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Action Advice Guidance */}
          {result.action_advice && result.action_advice.length > 0 && (
            <div style={{ padding: '1rem 1.25rem', background: '#f8fafc', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-light)' }}>
              <div style={{ fontWeight: 800, fontSize: '0.88rem', color: 'var(--navy-slate)', marginBottom: '0.45rem' }}>
                Recommended CFO Action Steps:
              </div>
              <ul style={{ margin: 0, paddingLeft: '1.25rem', fontSize: '0.85rem', color: 'var(--text-body)', lineHeight: 1.6 }}>
                {result.action_advice.map((adv, i) => (
                  <li key={i}>{adv}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const RecommendationsPage = () => {
  const { business, refreshBusiness } = useAuth();
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncStatus, setSyncStatus] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [typeFilter, setTypeFilter] = useState('ALL');

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await recommendationsAPI.getRecommendations();
      setRecommendations(res || []);
    } catch (err) {
      console.error('Failed to load recommendations:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [business?.id]);

  const handleSync = async () => {
    setSyncing(true);
    setSyncStatus(null);
    try {
      const res = await recommendationsAPI.generateRecommendations();
      setRecommendations(res || []);
      setSyncStatus({ type: 'success', text: `AI Recommendation Engine refreshed. ${res?.length || 0} optimization opportunities identified.` });
      await refreshBusiness();
    } catch (err) {
      setSyncStatus({ type: 'error', text: err.response?.data?.detail || 'Re-evaluating recommendations failed.' });
    } finally {
      setSyncing(false);
    }
  };

  const filtered = useMemo(() => {
    if (typeFilter === 'ALL') return recommendations;
    return recommendations.filter((r) => (r.action_type || r.type || '').toUpperCase() === typeFilter);
  }, [recommendations, typeFilter]);

  const totalMonthlySavings = recommendations.reduce((s, r) => s + Number(r.potential_monthly_saving || r.potentialMonthlySaving || 0), 0);
  const totalAnnualSavings = recommendations.reduce((s, r) => s + Number(r.potential_annual_saving || r.potentialAnnualSaving || 0), 0);
  const totalRunwayDays = recommendations.reduce((s, r) => s + Number(r.runway_impact_days || r.runwayImpactDays || 0), 0);

  const availableActionTypes = useMemo(() => {
    const types = new Set(recommendations.map(r => (r.action_type || '').toUpperCase()).filter(Boolean));
    return ['ALL', ...Array.from(types)];
  }, [recommendations]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: '1.25rem' }}>
        <div>
          <h1 style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--navy-slate)', letterSpacing: '-0.03em', marginBottom: '0.45rem', lineHeight: 1.25 }}>
            Calendar-Aware Recommendations & Purchase Intelligence
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '1rem' }}>
            Evidence-backed renewal risk, price creep alerts, functional redundancy, and forward purchase simulation for {(!business?.company_name || business.company_name.toLowerCase().includes('demo')) ? 'My Business' : business.company_name}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <button
            onClick={handleSync}
            disabled={syncing}
            className="btn-fintech btn-fintech-primary btn-sm"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.55rem', minHeight: '48px', padding: '0.65rem 1.35rem', fontSize: '1rem' }}
          >
            <RefreshCw size={17} className={syncing ? 'spin-icon' : ''} />
            <span>{syncing ? 'Evaluating Engine...' : 'Refresh AI Advisor'}</span>
          </button>
        </div>
      </div>

      {/* AI Transparency & Deterministic Grounding Banner */}
      <div style={{
        padding: '0.85rem 1.25rem',
        borderRadius: 'var(--radius-md)',
        background: '#f8fafc',
        border: '1.5px solid var(--border-medium)',
        display: 'flex',
        alignItems: 'center',
        gap: '0.75rem',
        fontSize: '0.86rem',
        color: 'var(--text-body)',
        lineHeight: 1.5
      }}>
        <Info size={18} color="var(--paypal-blue)" style={{ flexShrink: 0 }} />
        <div>
          <strong>AI Transparency Disclosure: </strong>
          SubWise AI recommendations are produced by a deterministic, rule-based fintech calculation engine grounded
          strictly in completed PayPal ledger transactions, confirmed subscription schedules, and forward cash-flow models.
          Financial calculations are never fabricated or guessed.
        </div>
      </div>

      {syncStatus && (
        <div style={{
          padding: '0.95rem 1.35rem',
          borderRadius: 'var(--radius-sm)',
          fontSize: '1rem',
          background: syncStatus.type === 'success' ? '#dcfce7' : '#fee2e2',
          color: syncStatus.type === 'success' ? 'var(--emerald-dark)' : 'var(--rose-dark)',
          border: `1.5px solid ${syncStatus.type === 'success' ? '#bbf7d0' : '#fecaca'}`
        }}>
          {syncStatus.text}
        </div>
      )}

      {/* KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.25rem' }}>
        {[
          { label: 'Total Potential Monthly Savings', value: `$${totalMonthlySavings.toFixed(0)}/mo`, sub: 'Across all active recommendations', color: 'var(--emerald-dark)', icon: TrendingUp },
          { label: 'Total Annual Value Unlocked', value: `$${totalAnnualSavings.toLocaleString()}/yr`, sub: 'Compounded 12-month impact', color: 'var(--navy-primary)', icon: DollarSign },
          { label: 'Estimated Runway Extended', value: `+${totalRunwayDays} days`, sub: 'Cash preservation effect', color: 'var(--paypal-blue)', icon: Clock },
          { label: 'Active Opportunities', value: `${recommendations.length}`, sub: 'Prioritized recommendations', color: 'var(--indigo-accent)', icon: Sparkles },
        ].map((kpi) => (
          <div key={kpi.label} className="fintech-card" style={{ padding: '1.5rem', display: 'flex', alignItems: 'center', gap: '1.15rem' }}>
            <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: 'var(--bg-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              <kpi.icon size={24} color={kpi.color} />
            </div>
            <div>
              <div style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--navy-slate)', fontFamily: 'JetBrains Mono, monospace' }}>{kpi.value}</div>
              <div style={{ fontSize: '0.88rem', color: 'var(--text-muted)', fontWeight: 600 }}>{kpi.label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Subscription Purchase Decision Simulator */}
      <PurchaseSimulator />

      {/* Section Divider */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginTop: '0.5rem' }}>
        <div>
          <h2 style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--navy-slate)', letterSpacing: '-0.02em', margin: 0 }}>
            Active Optimization & Risk Recommendations
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', margin: '0.2rem 0 0 0' }}>
            Prioritized by potential annual savings and liquidity preservation impact
          </p>
        </div>

        {/* Type filter tabs */}
        {availableActionTypes.length > 1 && (
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            {availableActionTypes.map((t) => (
              <button
                key={t}
                onClick={() => setTypeFilter(t)}
                style={{
                  padding: '0.45rem 1rem',
                  borderRadius: '9999px',
                  border: '1px solid',
                  borderColor: typeFilter === t ? 'var(--navy-primary)' : 'var(--border-medium)',
                  background: typeFilter === t ? 'var(--navy-primary)' : 'var(--bg-surface)',
                  color: typeFilter === t ? '#fff' : 'var(--text-body)',
                  fontWeight: 700,
                  fontSize: '0.84rem',
                  cursor: 'pointer',
                }}
              >
                {t === 'ALL' ? 'All Opportunities' : (ACTION_CONFIG[t]?.label || t)}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Recommendations List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        {filtered.length === 0 ? (
          <div className="fintech-card" style={{
            padding: '3rem 2rem',
            textAlign: 'center',
            background: 'var(--bg-subtle)',
            border: '1.5px dashed var(--border-medium)',
            borderRadius: 'var(--radius-lg)'
          }}>
            <Database size={44} color="var(--text-muted)" style={{ margin: '0 auto 1rem' }} />
            <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--navy-slate)', marginBottom: '0.5rem' }}>
              No Optimization Recommendations Available
            </h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', maxWidth: '540px', margin: '0 auto 1.5rem', lineHeight: 1.5 }}>
              The AI Advisor generates evidence-backed recommendations once recurring subscriptions and completed operating sales are detected in your connected PayPal Sandbox account. You can test hypothetical purchasing scenarios using the Purchase Decision Simulator above.
            </p>
            <button
              onClick={handleSync}
              disabled={syncing}
              className="btn-fintech btn-fintech-primary"
              style={{ minHeight: '46px', padding: '0.65rem 1.5rem' }}
            >
              Evaluate Opportunities
            </button>
          </div>
        ) : (
          filtered.map((rec) => (
            <RecommendationCard
              key={rec.id || rec.title}
              rec={rec}
              onApplied={() => loadData()}
            />
          ))
        )}
      </div>
    </div>
  );
};

export default RecommendationsPage;
