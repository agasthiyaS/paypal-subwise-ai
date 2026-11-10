import React, { useState, useEffect, useMemo } from 'react';
import { forecastAPI, paypalAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine, BarChart, Bar, LineChart, Line
} from 'recharts';
import {
  TrendingUp, TrendingDown, Wallet, Calendar, RefreshCw,
  Database, AlertTriangle, CheckCircle2, Info, AlertCircle,
  ArrowRight, Shield, Layers, Sliders, ChevronRight, Clock,
  CreditCard, Tag, Search, Filter, AlertOctagon, Sparkles
} from 'lucide-react';

const fmt = (n) =>
  `$${Number(n || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

const formatDate = (isoStr) => {
  if (!isoStr) return '—';
  try {
    const parts = isoStr.split('-');
    if (parts.length === 3) {
      const [y, m, d] = parts;
      const date = new Date(Number(y), Number(m) - 1, Number(d));
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    }
    return isoStr;
  } catch (e) {
    return isoStr;
  }
};

// ─── Status Badge ────────────────────────────────────────────────────────────
const StatusBadge = ({ status }) => {
  const configs = {
    sufficient_data: {
      label: 'Sufficient Data',
      icon: CheckCircle2,
      bg: 'var(--emerald-bg)',
      border: 'var(--emerald-border)',
      color: 'var(--emerald-dark)',
    },
    limited_data: {
      label: 'Limited Data',
      icon: AlertTriangle,
      bg: 'var(--amber-bg)',
      border: 'var(--amber-border)',
      color: 'var(--amber-dark)',
    },
    insufficient_data: {
      label: 'Insufficient Data',
      icon: AlertCircle,
      bg: 'var(--rose-bg)',
      border: 'var(--rose-border)',
      color: 'var(--rose-dark)',
    },
  };
  const cfg = configs[status] || configs.insufficient_data;
  const Icon = cfg.icon;
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: '0.4rem',
      padding: '0.3rem 0.85rem', borderRadius: '999px',
      background: cfg.bg, border: `1.5px solid ${cfg.border}`,
      color: cfg.color, fontSize: '0.82rem', fontWeight: 700,
      letterSpacing: '0.03em',
    }}>
      <Icon size={13} />
      {cfg.label}
    </span>
  );
};

// ─── Scenario Comparison Tooltip ─────────────────────────────────────────────
const ScenarioComparisonTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: '#fff', border: '1px solid var(--border-light)',
      borderRadius: 'var(--radius-md)', padding: '0.9rem 1.1rem',
      boxShadow: 'var(--shadow-hover)', fontSize: '0.84rem', minWidth: '220px',
    }}>
      <div style={{
        fontWeight: 700, color: 'var(--navy-slate)', marginBottom: '0.5rem',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <span>{label}</span>
        <span style={{
          background: 'var(--indigo-bg)', color: 'var(--indigo-accent)',
          padding: '0.1rem 0.45rem', borderRadius: '4px', fontSize: '0.68rem', fontWeight: 700,
        }}>6-MO PROJECTION</span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
        {payload.map((p) => (
          <div key={p.dataKey} style={{
            display: 'flex', justifyContent: 'space-between',
            alignItems: 'center', gap: '1rem',
          }}>
            <span style={{ color: p.color, fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: p.color, display: 'inline-block' }} />
              {p.name}
            </span>
            <span style={{ fontWeight: 700, color: 'var(--navy-slate)', fontFamily: 'JetBrains Mono, monospace' }}>
              {fmt(p.value)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

// ─── Insufficient-data empty state ───────────────────────────────────────────
const InsufficientDataPanel = ({ forecast, onSync, syncing }) => (
  <div style={{
    padding: '3.5rem 2rem', textAlign: 'center',
    background: 'var(--bg-subtle)', borderRadius: 'var(--radius-md)',
    border: '2px dashed var(--border-medium)',
  }}>
    <Database size={42} color="var(--text-muted)" style={{ margin: '0 auto 1.25rem' }} />
    <h3 style={{ fontSize: '1.3rem', fontWeight: 700, color: 'var(--navy-slate)', marginBottom: '0.5rem' }}>
      No Historical Operating Transactions Available
    </h3>
    <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', maxWidth: '560px', margin: '0 auto 1.25rem', lineHeight: 1.6 }}>
      The multi-scenario forecast engine requires verified completed PayPal operating transactions to establish revenue baseline and calculate scenario sensitivity cones (+15% / 0% / -20%).
      Capital funding transfers, balance adjustments, and internal sandbox test payments are strictly excluded.
    </p>

    {forecast?.missing_data_reasons?.length > 0 && (
      <div style={{
        background: '#fff', border: '1px solid var(--border-light)',
        borderRadius: 'var(--radius-md)', padding: '1rem 1.25rem',
        margin: '0 auto 1.75rem', textAlign: 'left', maxWidth: '520px',
      }}>
        <div style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem' }}>
          Data Verification Requirements:
        </div>
        <ul style={{
          display: 'flex', flexDirection: 'column', gap: '0.45rem',
          listStyle: 'none', padding: 0, margin: 0,
        }}>
          {forecast.missing_data_reasons.map((r, i) => (
            <li key={i} style={{
              display: 'flex', alignItems: 'flex-start', gap: '0.55rem',
              fontSize: '0.88rem', color: 'var(--rose-dark)',
            }}>
              <AlertCircle size={15} style={{ flexShrink: 0, marginTop: '0.2rem' }} />
              {r}
            </li>
          ))}
        </ul>
      </div>
    )}

    <button
      onClick={onSync}
      disabled={syncing}
      className="btn-fintech btn-fintech-primary"
      style={{ minHeight: '46px', padding: '0.65rem 1.65rem', fontSize: '0.95rem' }}
    >
      <RefreshCw size={16} className={syncing ? 'spin-icon' : ''} style={{ marginRight: '0.55rem' }} />
      {syncing ? 'Synchronizing Transactions…' : 'Sync PayPal Sandbox'}
    </button>
  </div>
);

// ─── Scenario Comparison Card Component ──────────────────────────────────────
const ScenarioCard = ({
  scenarioKey,
  title,
  assumptionLabel,
  assumptionPct,
  monthlyRev,
  monthlyExp,
  netCashflow,
  closingBalance,
  runwayMonths,
  runwayNote,
  isSelected,
  onSelect,
  color,
  bg,
  border,
  badgeBg,
  badgeColor,
  description
}) => {
  return (
    <div
      onClick={onSelect}
      className="fintech-card"
      style={{
        padding: '1.75rem',
        border: `2px solid ${isSelected ? color : border}`,
        background: isSelected ? bg : '#ffffff',
        cursor: 'pointer',
        transition: 'all 0.2s ease',
        boxShadow: isSelected ? `0 8px 20px -4px ${color}22` : 'var(--shadow-card)',
        display: 'flex',
        flexDirection: 'column',
        gap: '1rem',
      }}
    >
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <span style={{
            fontSize: '0.74rem', fontWeight: 800, textTransform: 'uppercase',
            letterSpacing: '0.08em', color,
          }}>
            {title}
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', marginTop: '0.25rem' }}>
            <span style={{
              fontSize: '0.82rem', fontWeight: 700, padding: '0.15rem 0.55rem',
              borderRadius: '999px', background: badgeBg, color: badgeColor,
            }}>
              Revenue: {assumptionLabel}
            </span>
          </div>
        </div>
        <div style={{
          width: '26px', height: '26px', borderRadius: '50%',
          border: `2px solid ${isSelected ? color : 'var(--border-medium)'}`,
          background: isSelected ? color : '#fff',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          transition: 'all 0.2s ease',
        }}>
          {isSelected && <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#fff' }} />}
        </div>
      </div>

      {/* Primary KPI: Closing Balance */}
      <div>
        <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
          Projected 6-Mo Closing Cash
        </div>
        <div style={{
          fontSize: '1.85rem', fontWeight: 800, color: 'var(--navy-slate)',
          fontFamily: 'JetBrains Mono, monospace', letterSpacing: '-0.02em',
          marginTop: '0.15rem',
        }}>
          {fmt(closingBalance)}
        </div>
      </div>

      {/* Financial Breakdown Grid */}
      <div style={{
        display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem',
        padding: '0.85rem', background: 'var(--bg-subtle)',
        borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-light)',
      }}>
        <div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 600 }}>Projected Revenue</div>
          <div style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--navy-slate)', fontFamily: 'JetBrains Mono, monospace' }}>
            {fmt(monthlyRev)}/mo
          </div>
        </div>
        <div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 600 }}>Monthly Expenses</div>
          <div style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--navy-slate)', fontFamily: 'JetBrains Mono, monospace' }}>
            {fmt(monthlyExp)}/mo
          </div>
        </div>
        <div style={{ gridColumn: 'span 2', borderTop: '1px dashed var(--border-medium)', paddingTop: '0.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>Net Cash Flow:</span>
          <span style={{
            fontSize: '0.92rem', fontWeight: 800, fontFamily: 'JetBrains Mono, monospace',
            color: netCashflow >= 0 ? 'var(--emerald-dark)' : 'var(--rose-dark)',
          }}>
            {netCashflow >= 0 ? '+' : ''}{fmt(netCashflow)}/mo
          </span>
        </div>
      </div>

      {/* Runway / Sustainability Footer */}
      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: 1.45, marginTop: 'auto' }}>
        {runwayMonths !== null ? (
          <span style={{ fontWeight: 600, color: runwayMonths < 3 ? 'var(--rose-dark)' : runwayMonths < 6 ? 'var(--amber-dark)' : 'var(--emerald-dark)' }}>
            Est. Runway: {runwayMonths} months
          </span>
        ) : (
          <span style={{ color: 'var(--emerald-dark)', fontWeight: 600 }}>
            Self-Sustaining (No Net Burn)
          </span>
        )}
        <div style={{ fontSize: '0.75rem', color: 'var(--text-caption)', marginTop: '0.2rem' }}>
          {description}
        </div>
      </div>
    </div>
  );
};

// ─── Main ForecastPage Component ─────────────────────────────────────────────
const ForecastPage = () => {
  const { business, refreshBusiness } = useAuth();
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncStatus, setSyncStatus] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [error, setError] = useState(null);

  // Scenario selection: 'all' | 'optimistic' | 'baseline' | 'conservative'
  const [selectedScenario, setSelectedScenario] = useState('all');

  // Calendar month filter: 'all' or month_index (1 to 6)
  const [calendarMonthFilter, setCalendarMonthFilter] = useState('all');
  const [selectedCalendarDate, setSelectedCalendarDate] = useState(null);

  const loadForecast = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await forecastAPI.getForecast(6);
      setForecast(data);
    } catch (err) {
      console.error('Failed to load forecast:', err);
      setError(err.response?.data?.detail || 'Failed to load forecast data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadForecast();
  }, [business?.id]);

  const handleSync = async () => {
    setSyncing(true);
    setSyncStatus(null);
    try {
      const res = await paypalAPI.sync();
      setSyncStatus({ type: 'success', text: res.message || 'Transactions synced.' });
      await refreshBusiness();
      await loadForecast();
    } catch (err) {
      setSyncStatus({ type: 'error', text: err.response?.data?.detail || 'Sync failed.' });
    } finally {
      setSyncing(false);
    }
  };

  // ── Derived display values from backend ──────────────────────────────────
  const status = forecast?.status;
  const scenariosAvailable = Boolean(forecast?.scenarios_available);
  const hasVerifiedCash = forecast?.has_verified_cash ?? false;
  const startingCash = forecast?.verified_starting_cash ?? null;
  const histRevenue = forecast?.historical_monthly_operating_revenue ?? 0;
  const histNonSub = forecast?.historical_monthly_non_sub_expenses ?? 0;
  const histSubExp = forecast?.historical_monthly_subscription_expenses ?? 0;
  const confirmedCommit = forecast?.confirmed_monthly_subscription_commitments ?? 0;
  const potentialCommit = forecast?.potential_monthly_subscription_commitments ?? 0;
  const warnings = forecast?.data_quality_warnings ?? [];
  const assumptions = forecast?.assumptions_explanation ?? '';
  const methodologyNote = forecast?.scenario_methodology_note ?? '';
  const isInsufficient = status === 'insufficient_data' || !forecast;

  // Stage 3 calendar & concentration fields directly from backend
  const paymentCalendar = useMemo(() => forecast?.payment_calendar || [], [forecast]);
  const upcomingPayments = useMemo(() => forecast?.upcoming_subscription_payments || [], [forecast]);
  const monthlyScheduledTotals = useMemo(() => forecast?.monthly_scheduled_subscription_totals || [], [forecast]);
  const concentrationWarnings = useMemo(() => forecast?.renewal_concentration_warnings || [], [forecast]);
  const unknownDateCount = forecast?.unknown_renewal_date_count || 0;
  const paymentSchedulingMethodology = forecast?.payment_scheduling_methodology || '';

  // Scenarios objects from backend response
  const opt = forecast?.optimistic;
  const base = forecast?.baseline;
  const cons = forecast?.conservative;

  // ── Multi-Scenario Timeline Data for Recharts ─────────────────────────────
  const scenarioChartData = useMemo(() => {
    if (!scenariosAvailable || !base?.months) return [];
    const optMonths = opt?.months || [];
    const baseMonths = base?.months || [];
    const consMonths = cons?.months || [];

    return baseMonths.map((bm, idx) => ({
      month: bm.month_name,
      optimisticBalance: optMonths[idx]?.projected_closing_cash_balance ?? 0,
      baselineBalance: bm.projected_closing_cash_balance,
      conservativeBalance: consMonths[idx]?.projected_closing_cash_balance ?? 0,
      optimisticRev: optMonths[idx]?.projected_operating_revenue ?? 0,
      baselineRev: bm.projected_operating_revenue,
      conservativeRev: consMonths[idx]?.projected_operating_revenue ?? 0,
      optimisticNet: optMonths[idx]?.projected_net_cashflow ?? 0,
      baselineNet: bm.projected_net_cashflow,
      conservativeNet: consMonths[idx]?.projected_net_cashflow ?? 0,
    }));
  }, [scenariosAvailable, opt, base, cons]);

  // Active scenario data for detailed breakdown table
  const activeScenarioObj = useMemo(() => {
    if (selectedScenario === 'optimistic') return opt;
    if (selectedScenario === 'conservative') return cons;
    return base; // default to baseline
  }, [selectedScenario, opt, base, cons]);

  // Group payments by date for visual calendar inspection
  const paymentsByDate = useMemo(() => {
    const map = {};
    paymentCalendar.forEach((p) => {
      const key = p.expected_payment_date;
      if (!map[key]) {
        map[key] = [];
      }
      map[key].push(p);
    });
    return map;
  }, [paymentCalendar]);

  // Filtered payments list based on month filter
  const filteredCalendarPayments = useMemo(() => {
    if (calendarMonthFilter === 'all') return paymentCalendar;
    return paymentCalendar.filter((p) => p.month_index === Number(calendarMonthFilter));
  }, [paymentCalendar, calendarMonthFilter]);

  const displayCompanyName = useMemo(() => {
    const name = business?.company_name;
    if (!name) return 'My Business';
    const lower = name.toLowerCase();
    if (lower === 'my business' || lower === 'business') return name;
    return name;
  }, [business?.company_name]);

  // ── Loading state ─────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
          <div>
            <h1 style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--navy-slate)', marginBottom: '0.45rem' }}>
              Cash Flow Forecast
            </h1>
            <p style={{ color: 'var(--text-muted)', fontSize: '1rem' }}>Loading calendar-aware forecast…</p>
          </div>
        </div>
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          height: '320px', background: 'var(--bg-subtle)',
          borderRadius: 'var(--radius-lg)', border: '1.5px dashed var(--border-medium)',
        }}>
          <div style={{ textAlign: 'center' }}>
            <RefreshCw size={32} color="var(--text-muted)" className="spin-icon" style={{ margin: '0 auto 1rem' }} />
            <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>Querying verified forecast calculations from backend…</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>

      {/* ── Header ──────────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: '1.25rem' }}>
        <div>
          <h1 style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--navy-slate)', letterSpacing: '-0.03em', marginBottom: '0.45rem', lineHeight: 1.25 }}>
            Cash Flow Forecast
          </h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
            <p style={{ color: 'var(--text-muted)', fontSize: '1rem' }}>
              Calendar-aware sensitivity projections &amp; subscription scheduling · {displayCompanyName}
            </p>
            {status && <StatusBadge status={status} />}
          </div>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <button
            onClick={loadForecast}
            disabled={loading}
            className="btn-fintech btn-fintech-outline btn-sm"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', minHeight: '44px' }}
          >
            <RefreshCw size={15} className={loading ? 'spin-icon' : ''} />
            Refresh
          </button>
          <button
            onClick={handleSync}
            disabled={syncing}
            className="btn-fintech btn-fintech-primary btn-sm"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.55rem', minHeight: '48px', padding: '0.65rem 1.35rem', fontSize: '1rem' }}
          >
            <RefreshCw size={17} className={syncing ? 'spin-icon' : ''} />
            {syncing ? 'Synchronizing…' : 'Sync Stream'}
          </button>
        </div>
      </div>

      {/* ── Sync feedback ────────────────────────────────────────────────── */}
      {syncStatus && (
        <div style={{
          padding: '0.95rem 1.35rem', borderRadius: 'var(--radius-sm)', fontSize: '1rem',
          background: syncStatus.type === 'success' ? '#dcfce7' : '#fee2e2',
          color: syncStatus.type === 'success' ? 'var(--emerald-dark)' : 'var(--rose-dark)',
          border: `1.5px solid ${syncStatus.type === 'success' ? '#bbf7d0' : '#fecaca'}`,
        }}>
          {syncStatus.text}
        </div>
      )}

      {/* ── API error ────────────────────────────────────────────────────── */}
      {error && (
        <div style={{
          padding: '0.95rem 1.35rem', borderRadius: 'var(--radius-sm)',
          background: 'var(--rose-bg)', border: '1.5px solid var(--rose-border)',
          color: 'var(--rose-dark)', fontSize: '0.95rem',
          display: 'flex', alignItems: 'center', gap: '0.65rem',
        }}>
          <AlertCircle size={18} />
          {error}
        </div>
      )}

      {/* ── Starting Cash Provenance Banner ───────────────────────────────── */}
      {forecast && (
        <div style={{
          display: 'flex', alignItems: 'flex-start', gap: '0.85rem',
          background: hasVerifiedCash ? 'var(--indigo-bg)' : 'var(--amber-bg)',
          border: `1.5px solid ${hasVerifiedCash ? '#c7d2fe' : 'var(--amber-border)'}`,
          borderRadius: 'var(--radius-lg)', padding: '1.1rem 1.5rem',
          fontSize: '0.92rem',
          color: hasVerifiedCash ? '#4338ca' : 'var(--amber-dark)',
          lineHeight: 1.6,
        }}>
          {hasVerifiedCash
            ? <Shield size={18} style={{ flexShrink: 0, marginTop: '0.15rem' }} />
            : <AlertTriangle size={18} style={{ flexShrink: 0, marginTop: '0.15rem' }} />
          }
          <span>
            {hasVerifiedCash ? (
              <>
                <strong>Verified starting cash</strong>: <span style={{ fontFamily: 'JetBrains Mono, monospace', fontWeight: 700 }}>{fmt(startingCash)}</span> — derived from settled PayPal ledger transactions.{' '}
                <em style={{ fontWeight: 400 }}>This is a ledger-computed estimate from completed records, not an independently queried PayPal balance.</em>
              </>
            ) : (
              <>
                <strong>Starting balance unavailable</strong> — no verified completed PayPal transactions found. Projections cannot establish opening liquidity.
              </>
            )}
          </span>
        </div>
      )}

      {/* ── Data Quality Warnings ─────────────────────────────────────────── */}
      {warnings.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
          {warnings.map((w, i) => (
            <div key={i} style={{
              display: 'flex', alignItems: 'flex-start', gap: '0.75rem',
              background: 'var(--amber-bg)', border: '1.5px solid var(--amber-border)',
              borderRadius: 'var(--radius-md)', padding: '0.9rem 1.25rem',
              fontSize: '0.9rem', color: 'var(--amber-dark)', lineHeight: 1.55,
            }}>
              <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: '0.15rem' }} />
              {w}
            </div>
          ))}
        </div>
      )}

      {/* ── Insufficient Data View OR Full Multi-Scenario Suite ─────────── */}
      {isInsufficient || !scenariosAvailable ? (
        <InsufficientDataPanel forecast={forecast} onSync={handleSync} syncing={syncing} />
      ) : (
        <>
          {/* ── Section: Scenario Comparison Cards ────────────────────────── */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
              <div>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--navy-slate)', letterSpacing: '-0.02em' }}>
                  Coordinated Scenario Projections
                </h2>
                <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)' }}>
                  Click a scenario card to highlight its projection trajectory in the comparison chart below
                </p>
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-caption)', fontWeight: 600 }}>
                Deterministic Assumptions · Contractual Subs Unchanged
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(310px, 1fr))', gap: '1.25rem' }}>
              {/* Card 1: OPTIMISTIC */}
              {opt && (
                <ScenarioCard
                  scenarioKey="optimistic"
                  title="Optimistic Scenario"
                  assumptionLabel="+15% Growth"
                  assumptionPct={15.0}
                  monthlyRev={opt.monthly_revenue}
                  monthlyExp={opt.monthly_non_sub_expenses + opt.monthly_confirmed_sub_expenses}
                  netCashflow={opt.monthly_net_cashflow}
                  closingBalance={opt.months[opt.months.length - 1]?.projected_closing_cash_balance}
                  runwayMonths={opt.runway_months}
                  runwayNote={opt.runway_note}
                  isSelected={selectedScenario === 'optimistic'}
                  onSelect={() => setSelectedScenario(selectedScenario === 'optimistic' ? 'all' : 'optimistic')}
                  color="var(--emerald-dark)"
                  bg="var(--emerald-bg)"
                  border="var(--emerald-border)"
                  badgeBg="#dcfce7"
                  badgeColor="var(--emerald-dark)"
                  description="Assumes +15% revenue expansion above historical average. Subscriptions locked at contractual commitment."
                />
              )}

              {/* Card 2: BASELINE */}
              {base && (
                <ScenarioCard
                  scenarioKey="baseline"
                  title="Baseline Scenario"
                  assumptionLabel="0% (Actual Avg)"
                  assumptionPct={0.0}
                  monthlyRev={base.monthly_revenue}
                  monthlyExp={base.monthly_non_sub_expenses + base.monthly_confirmed_sub_expenses}
                  netCashflow={base.monthly_net_cashflow}
                  closingBalance={base.months[base.months.length - 1]?.projected_closing_cash_balance}
                  runwayMonths={base.runway_months}
                  runwayNote={base.runway_note}
                  isSelected={selectedScenario === 'baseline'}
                  onSelect={() => setSelectedScenario(selectedScenario === 'baseline' ? 'all' : 'baseline')}
                  color="var(--navy-primary)"
                  bg="var(--paypal-blue-subtle)"
                  border="var(--border-medium)"
                  badgeBg="#e0f2fe"
                  badgeColor="var(--navy-primary)"
                  description="Maintains exact verified monthly operating run rate and confirmed subscription commitments."
                />
              )}

              {/* Card 3: CONSERVATIVE */}
              {cons && (
                <ScenarioCard
                  scenarioKey="conservative"
                  title="Conservative Scenario"
                  assumptionLabel="-20% Contraction"
                  assumptionPct={-20.0}
                  monthlyRev={cons.monthly_revenue}
                  monthlyExp={cons.monthly_non_sub_expenses + cons.monthly_confirmed_sub_expenses}
                  netCashflow={cons.monthly_net_cashflow}
                  closingBalance={cons.months[cons.months.length - 1]?.projected_closing_cash_balance}
                  runwayMonths={cons.runway_months}
                  runwayNote={cons.runway_note}
                  isSelected={selectedScenario === 'conservative'}
                  onSelect={() => setSelectedScenario(selectedScenario === 'conservative' ? 'all' : 'conservative')}
                  color="var(--amber-dark)"
                  bg="var(--amber-bg)"
                  border="var(--amber-border)"
                  badgeBg="#fef3c7"
                  badgeColor="var(--amber-dark)"
                  description="Stress-tests a 20% revenue contraction while servicing 100% of confirmed subscription commitments."
                />
              )}
            </div>
          </div>

          {/* ── Section: Multi-Scenario Comparison Chart ──────────────────── */}
          <div className="fintech-card" style={{ padding: '1.75rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem' }}>
              <div>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--navy-slate)', marginBottom: '0.25rem' }}>
                  6-Month Cash Balance Comparison
                </h2>
                <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                  Projected month-end closing balances across sensitivity scenarios from verified starting cash of <strong style={{ fontFamily: 'JetBrains Mono, monospace' }}>{fmt(startingCash)}</strong>
                </p>
              </div>

              {/* Scenario Selector Pills */}
              <div style={{
                display: 'inline-flex', background: 'var(--bg-subtle)',
                padding: '0.25rem', borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-light)', gap: '0.25rem',
              }}>
                {[
                  { key: 'all', label: 'All Scenarios' },
                  { key: 'optimistic', label: 'Optimistic (+15%)' },
                  { key: 'baseline', label: 'Baseline (0%)' },
                  { key: 'conservative', label: 'Conservative (-20%)' },
                ].map((tab) => (
                  <button
                    key={tab.key}
                    onClick={() => setSelectedScenario(tab.key)}
                    style={{
                      padding: '0.4rem 0.85rem',
                      borderRadius: '6px',
                      border: 'none',
                      fontSize: '0.82rem',
                      fontWeight: selectedScenario === tab.key ? 700 : 500,
                      color: selectedScenario === tab.key ? 'var(--navy-slate)' : 'var(--text-muted)',
                      background: selectedScenario === tab.key ? '#ffffff' : 'transparent',
                      boxShadow: selectedScenario === tab.key ? '0 1px 3px rgba(0,0,0,0.08)' : 'none',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Line / Area Multi-Scenario Chart */}
            <div style={{ width: '100%', height: '360px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={scenarioChartData} margin={{ top: 10, right: 25, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="optGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={selectedScenario === 'optimistic' ? 0.35 : 0.12} />
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                    </linearGradient>
                    <linearGradient id="baseGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#0070ba" stopOpacity={selectedScenario === 'baseline' ? 0.35 : 0.12} />
                      <stop offset="95%" stopColor="#0070ba" stopOpacity={0.0} />
                    </linearGradient>
                    <linearGradient id="consGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#f59e0b" stopOpacity={selectedScenario === 'conservative' ? 0.35 : 0.12} />
                      <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                  <XAxis dataKey="month" stroke="#64748b" fontSize={12} tickLine={false} axisLine={{ stroke: '#e2e8f0' }} />
                  <YAxis
                    stroke="#64748b" fontSize={12} tickLine={false}
                    axisLine={{ stroke: '#e2e8f0' }}
                    tickFormatter={(v) => `$${v >= 1000 ? (v / 1000).toFixed(1) + 'k' : v}`}
                  />
                  <Tooltip content={<ScenarioComparisonTooltip />} />
                  <Legend verticalAlign="top" align="right" wrapperStyle={{ fontSize: '0.82rem', paddingBottom: '14px' }} />

                  {/* Starting balance horizontal reference */}
                  {startingCash && (
                    <ReferenceLine
                      y={startingCash}
                      stroke="#94a3b8"
                      strokeDasharray="4 4"
                      label={{ value: `Start: ${fmt(startingCash)}`, fontSize: 11, fill: '#64748b', position: 'insideTopLeft' }}
                    />
                  )}

                  {/* Optimistic Area */}
                  {(selectedScenario === 'all' || selectedScenario === 'optimistic') && (
                    <Area
                      type="monotone"
                      dataKey="optimisticBalance"
                      name="Optimistic (+15%)"
                      stroke="#10b981"
                      strokeWidth={selectedScenario === 'optimistic' ? 3.5 : 2}
                      fillOpacity={1}
                      fill="url(#optGrad)"
                    />
                  )}

                  {/* Baseline Area */}
                  {(selectedScenario === 'all' || selectedScenario === 'baseline') && (
                    <Area
                      type="monotone"
                      dataKey="baselineBalance"
                      name="Baseline (0%)"
                      stroke="#003087"
                      strokeWidth={selectedScenario === 'baseline' ? 3.5 : 2.5}
                      fillOpacity={1}
                      fill="url(#baseGrad)"
                    />
                  )}

                  {/* Conservative Area */}
                  {(selectedScenario === 'all' || selectedScenario === 'conservative') && (
                    <Area
                      type="monotone"
                      dataKey="conservativeBalance"
                      name="Conservative (-20%)"
                      stroke="#f59e0b"
                      strokeWidth={selectedScenario === 'conservative' ? 3.5 : 2}
                      fillOpacity={1}
                      fill="url(#consGrad)"
                    />
                  )}
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* ── Section: Additional Financial Information ─────────────────── */}
          <div className="fintech-card" style={{ padding: '1.75rem' }}>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--navy-slate)', marginBottom: '0.35rem' }}>
              Underlying Financial Baseline &amp; Commitments
            </h2>
            <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '1.35rem' }}>
              Verified historical parameters from completed PayPal activity used to anchor all 3 scenarios.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: '1.1rem' }}>
              <div style={{ padding: '1.1rem', borderRadius: 'var(--radius-md)', background: 'var(--emerald-bg)', border: '1px solid var(--emerald-border)' }}>
                <div style={{ fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.07em', color: 'var(--emerald-dark)', marginBottom: '0.4rem' }}>
                  Historical Monthly Revenue
                </div>
                <div style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--navy-slate)', fontFamily: 'JetBrains Mono, monospace' }}>
                  {fmt(histRevenue)}
                </div>
                <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                  Baseline operating inflow run rate
                </div>
              </div>

              <div style={{ padding: '1.1rem', borderRadius: 'var(--radius-md)', background: 'var(--rose-bg)', border: '1px solid var(--rose-border)' }}>
                <div style={{ fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.07em', color: 'var(--rose-dark)', marginBottom: '0.4rem' }}>
                  Non-Subscription Expenses
                </div>
                <div style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--navy-slate)', fontFamily: 'JetBrains Mono, monospace' }}>
                  {fmt(histNonSub)}
                </div>
                <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                  Historical average operating outflows
                </div>
              </div>

              <div style={{ padding: '1.1rem', borderRadius: 'var(--radius-md)', background: 'var(--paypal-blue-subtle)', border: '1px solid var(--border-light)' }}>
                <div style={{ fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.07em', color: 'var(--navy-primary)', marginBottom: '0.4rem' }}>
                  Confirmed Sub Commitments
                </div>
                <div style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--navy-slate)', fontFamily: 'JetBrains Mono, monospace' }}>
                  {fmt(confirmedCommit)}
                </div>
                <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                  Contractual recurring obligations (held constant)
                </div>
              </div>

              <div style={{ padding: '1.1rem', borderRadius: 'var(--radius-md)', background: potentialCommit > 0 ? 'var(--amber-bg)' : 'var(--bg-subtle)', border: `1px solid ${potentialCommit > 0 ? 'var(--amber-border)' : 'var(--border-light)'}` }}>
                <div style={{ fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.07em', color: potentialCommit > 0 ? 'var(--amber-dark)' : 'var(--text-muted)', marginBottom: '0.4rem' }}>
                  Potential Sub Commitments
                </div>
                <div style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--navy-slate)', fontFamily: 'JetBrains Mono, monospace' }}>
                  {fmt(potentialCommit)}
                </div>
                <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                  {potentialCommit > 0 ? 'Awaiting 2nd cycle (excluded from baseline)' : 'No unconfirmed subscriptions'}
                </div>
              </div>
            </div>
          </div>

          {/* ── Section: Monthly Breakdown for Active Scenario ───────────── */}
          {activeScenarioObj && (
            <div className="fintech-card" style={{ padding: '1.75rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.75rem' }}>
                <div>
                  <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--navy-slate)' }}>
                    Monthly Detail: {activeScenarioObj.display_label}
                  </h3>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                    Individual month breakdown for the active scenario selection (calendar-accurate subscription expenses)
                  </p>
                </div>
                <span style={{ fontSize: '0.82rem', fontWeight: 700, padding: '0.2rem 0.65rem', borderRadius: '6px', background: 'var(--bg-subtle)', border: '1px solid var(--border-light)' }}>
                  Net: {activeScenarioObj.monthly_net_cashflow >= 0 ? '+' : ''}{fmt(activeScenarioObj.monthly_net_cashflow)}/mo avg
                </span>
              </div>

              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.88rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '2px solid var(--border-light)', textAlign: 'left' }}>
                      <th style={{ padding: '0.75rem 0.5rem', color: 'var(--text-muted)', fontWeight: 600 }}>Month</th>
                      <th style={{ padding: '0.75rem 0.5rem', color: 'var(--text-muted)', fontWeight: 600 }}>Projected Revenue</th>
                      <th style={{ padding: '0.75rem 0.5rem', color: 'var(--text-muted)', fontWeight: 600 }}>Non-Sub Expenses</th>
                      <th style={{ padding: '0.75rem 0.5rem', color: 'var(--text-muted)', fontWeight: 600 }}>Scheduled Subs</th>
                      <th style={{ padding: '0.75rem 0.5rem', color: 'var(--text-muted)', fontWeight: 600 }}>Net Cash Flow</th>
                      <th style={{ padding: '0.75rem 0.5rem', color: 'var(--text-muted)', fontWeight: 600, textAlign: 'right' }}>Closing Cash</th>
                    </tr>
                  </thead>
                  <tbody>
                    {activeScenarioObj.months.map((m) => (
                      <tr key={m.month} style={{ borderBottom: '1px solid var(--border-light)' }}>
                        <td style={{ padding: '0.85rem 0.5rem', fontWeight: 700, color: 'var(--navy-slate)' }}>{m.month_name}</td>
                        <td style={{ padding: '0.85rem 0.5rem', color: 'var(--emerald-dark)', fontFamily: 'JetBrains Mono, monospace', fontWeight: 600 }}>{fmt(m.projected_operating_revenue)}</td>
                        <td style={{ padding: '0.85rem 0.5rem', color: 'var(--text-body)', fontFamily: 'JetBrains Mono, monospace' }}>{fmt(m.projected_non_sub_expenses)}</td>
                        <td style={{ padding: '0.85rem 0.5rem', color: 'var(--navy-primary)', fontFamily: 'JetBrains Mono, monospace', fontWeight: 600 }}>
                          {fmt(m.projected_confirmed_subscription_expenses)}
                        </td>
                        <td style={{
                          padding: '0.85rem 0.5rem', fontFamily: 'JetBrains Mono, monospace', fontWeight: 700,
                          color: m.projected_net_cashflow >= 0 ? 'var(--emerald-dark)' : 'var(--rose-dark)',
                        }}>
                          {m.projected_net_cashflow >= 0 ? '+' : ''}{fmt(m.projected_net_cashflow)}
                        </td>
                        <td style={{ padding: '0.85rem 0.5rem', textAlign: 'right', fontWeight: 800, color: 'var(--navy-slate)', fontFamily: 'JetBrains Mono, monospace' }}>
                          {fmt(m.projected_closing_cash_balance)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ════════════════════════════════════════════════════════════════ */}
          {/* ── NEW SECTION: Subscription Payment Calendar & Intelligence ── */}
          {/* ════════════════════════════════════════════════════════════════ */}
          <div className="fintech-card" style={{ padding: '1.75rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                  <Calendar size={22} color="var(--navy-primary)" />
                  <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--navy-slate)', letterSpacing: '-0.02em' }}>
                    Subscription Payment Calendar
                  </h2>
                </div>
                <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                  Exact projected renewal dates across weekly, monthly, quarterly, and annual billing cadences
                </p>
              </div>

              {unknownDateCount > 0 && (
                <div style={{
                  display: 'inline-flex', alignItems: 'center', gap: '0.45rem',
                  padding: '0.35rem 0.75rem', borderRadius: '6px',
                  background: 'var(--amber-bg)', border: '1px solid var(--amber-border)',
                  fontSize: '0.8rem', color: 'var(--amber-dark)', fontWeight: 600,
                }}>
                  <AlertTriangle size={14} />
                  <span>{unknownDateCount} subscription(s) have unverified renewal dates</span>
                </div>
              )}
            </div>

            {/* ── Concentration Alerts ──────────────────────────────────── */}
            {concentrationWarnings.length > 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem', marginBottom: '1.5rem' }}>
                {concentrationWarnings.map((warn, idx) => (
                  <div key={idx} style={{
                    display: 'flex', alignItems: 'flex-start', gap: '0.75rem',
                    background: '#fffbeb', border: '1.5px solid #fde68a',
                    borderRadius: 'var(--radius-md)', padding: '0.95rem 1.25rem',
                    fontSize: '0.88rem', color: '#b45309', lineHeight: 1.55,
                  }}>
                    <AlertOctagon size={18} style={{ flexShrink: 0, marginTop: '0.15rem' }} />
                    <div>
                      <strong style={{ color: '#92400e' }}>Renewal Concentration Alert: </strong>
                      {warn}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Empty State when no subscriptions are scheduled */}
            {paymentCalendar.length === 0 ? (
              <div style={{
                padding: '3rem 2rem', textAlign: 'center',
                background: 'var(--bg-subtle)', borderRadius: 'var(--radius-md)',
                border: '1.5px dashed var(--border-medium)',
              }}>
                <CreditCard size={38} color="var(--text-muted)" style={{ margin: '0 auto 1rem' }} />
                <h4 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--navy-slate)', marginBottom: '0.4rem' }}>
                  No Scheduled Subscription Payments Detected
                </h4>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: '480px', margin: '0 auto 1.25rem', lineHeight: 1.55 }}>
                  No recurring software subscriptions with confirmed billing schedules were identified.
                  Synchronize your PayPal account to detect subscriptions and map out exact calendar renewals.
                </p>
                <button
                  onClick={handleSync}
                  disabled={syncing}
                  className="btn-fintech btn-fintech-primary btn-sm"
                  style={{ minHeight: '40px', padding: '0.5rem 1.25rem' }}
                >
                  <RefreshCw size={14} className={syncing ? 'spin-icon' : ''} style={{ marginRight: '0.45rem' }} />
                  {syncing ? 'Syncing…' : 'Sync PayPal Transactions'}
                </button>
              </div>
            ) : (
              <>
                {/* ── 6-Month Scheduled Totals Summary Grid ─────────────── */}
                <div style={{ marginBottom: '1.75rem' }}>
                  <div style={{ fontSize: '0.82rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                    Monthly Scheduled Obligations (Next 6 Months)
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(175px, 1fr))', gap: '0.85rem' }}>
                    {monthlyScheduledTotals.map((tot) => (
                      <div
                        key={tot.month_index}
                        onClick={() => setCalendarMonthFilter(calendarMonthFilter === String(tot.month_index) ? 'all' : String(tot.month_index))}
                        style={{
                          padding: '1rem',
                          borderRadius: 'var(--radius-md)',
                          background: tot.is_high_concentration ? 'var(--amber-bg)' : 'var(--bg-subtle)',
                          border: `1.5px solid ${calendarMonthFilter === String(tot.month_index) ? 'var(--navy-primary)' : (tot.is_high_concentration ? 'var(--amber-border)' : 'var(--border-light)')}`,
                          cursor: 'pointer',
                          transition: 'all 0.15s ease',
                          boxShadow: calendarMonthFilter === String(tot.month_index) ? '0 4px 12px rgba(0,48,135,0.1)' : 'none',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                          <span style={{ fontSize: '0.78rem', fontWeight: 800, color: 'var(--navy-slate)' }}>
                            {tot.month_name}
                          </span>
                          {tot.is_high_concentration && (
                            <span style={{
                              fontSize: '0.65rem', fontWeight: 800, padding: '0.1rem 0.35rem',
                              borderRadius: '4px', background: '#fef3c7', color: 'var(--amber-dark)',
                            }}>
                              SPIKE
                            </span>
                          )}
                        </div>

                        <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--navy-slate)', fontFamily: 'JetBrains Mono, monospace' }}>
                          {fmt(tot.total_confirmed_amount)}
                        </div>

                        <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', marginTop: '0.3rem', display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
                          <span>{tot.confirmed_renewals_count} renewal(s) scheduled</span>
                          {tot.largest_individual_payment > 0 && (
                            <span style={{ color: 'var(--text-body)', fontWeight: 600 }}>
                              Max: {fmt(tot.largest_individual_payment)} ({tot.largest_payment_vendor})
                            </span>
                          )}
                          {tot.total_potential_amount > 0 && (
                            <span style={{ color: 'var(--amber-dark)', fontSize: '0.7rem' }}>
                              +{fmt(tot.total_potential_amount)} potential
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* ── Month Filter & Search Bar ─────────────────────────── */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem', marginBottom: '1rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                    <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-muted)' }}>Filter by Month:</span>
                    <div style={{
                      display: 'inline-flex', background: 'var(--bg-subtle)',
                      padding: '0.2rem', borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--border-light)', gap: '0.2rem',
                    }}>
                      <button
                        onClick={() => setCalendarMonthFilter('all')}
                        style={{
                          padding: '0.3rem 0.7rem', borderRadius: '4px', border: 'none',
                          fontSize: '0.78rem', fontWeight: calendarMonthFilter === 'all' ? 700 : 500,
                          background: calendarMonthFilter === 'all' ? '#fff' : 'transparent',
                          color: calendarMonthFilter === 'all' ? 'var(--navy-slate)' : 'var(--text-muted)',
                          boxShadow: calendarMonthFilter === 'all' ? '0 1px 3px rgba(0,0,0,0.08)' : 'none',
                          cursor: 'pointer',
                        }}
                      >
                        All ({paymentCalendar.length})
                      </button>
                      {monthlyScheduledTotals.map((tot) => (
                        <button
                          key={tot.month_index}
                          onClick={() => setCalendarMonthFilter(String(tot.month_index))}
                          style={{
                            padding: '0.3rem 0.7rem', borderRadius: '4px', border: 'none',
                            fontSize: '0.78rem', fontWeight: calendarMonthFilter === String(tot.month_index) ? 700 : 500,
                            background: calendarMonthFilter === String(tot.month_index) ? '#fff' : 'transparent',
                            color: calendarMonthFilter === String(tot.month_index) ? 'var(--navy-slate)' : 'var(--text-muted)',
                            boxShadow: calendarMonthFilter === String(tot.month_index) ? '0 1px 3px rgba(0,0,0,0.08)' : 'none',
                            cursor: 'pointer',
                          }}
                        >
                          {tot.month_name.split(' ')[0]}
                        </button>
                      ))}
                    </div>
                  </div>

                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    Showing {filteredCalendarPayments.length} of {paymentCalendar.length} scheduled payments
                  </span>
                </div>

                {/* ── Scheduled Payments Table ──────────────────────────── */}
                <div style={{ overflowX: 'auto', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.88rem' }}>
                    <thead>
                      <tr style={{ background: 'var(--bg-subtle)', borderBottom: '2px solid var(--border-light)', textAlign: 'left' }}>
                        <th style={{ padding: '0.75rem 0.85rem', color: 'var(--text-muted)', fontWeight: 600 }}>Vendor</th>
                        <th style={{ padding: '0.75rem 0.85rem', color: 'var(--text-muted)', fontWeight: 600 }}>Expected Date</th>
                        <th style={{ padding: '0.75rem 0.85rem', color: 'var(--text-muted)', fontWeight: 600 }}>Frequency</th>
                        <th style={{ padding: '0.75rem 0.85rem', color: 'var(--text-muted)', fontWeight: 600 }}>Status</th>
                        <th style={{ padding: '0.75rem 0.85rem', color: 'var(--text-muted)', fontWeight: 600, textAlign: 'right' }}>Expected Amount</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredCalendarPayments.map((pmt, i) => (
                        <tr
                          key={i}
                          style={{
                            borderBottom: '1px solid var(--border-light)',
                            background: !pmt.is_contractual_commitment ? '#fffbeb22' : 'transparent',
                          }}
                        >
                          <td style={{ padding: '0.85rem', fontWeight: 700, color: 'var(--navy-slate)' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                              <span>{pmt.vendor_name}</span>
                              <span style={{ fontSize: '0.72rem', color: 'var(--text-caption)' }}>({pmt.month_name})</span>
                            </div>
                          </td>
                          <td style={{ padding: '0.85rem', color: 'var(--text-body)', fontFamily: 'JetBrains Mono, monospace', fontSize: '0.85rem' }}>
                            {formatDate(pmt.expected_payment_date)}
                          </td>
                          <td style={{ padding: '0.85rem' }}>
                            <span style={{
                              textTransform: 'capitalize',
                              padding: '0.2rem 0.55rem', borderRadius: '4px',
                              background: 'var(--bg-subtle)', border: '1px solid var(--border-light)',
                              fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-body)',
                            }}>
                              {pmt.billing_frequency}
                            </span>
                          </td>
                          <td style={{ padding: '0.85rem' }}>
                            {pmt.is_contractual_commitment ? (
                              <span style={{
                                display: 'inline-flex', alignItems: 'center', gap: '0.3rem',
                                padding: '0.15rem 0.55rem', borderRadius: '999px',
                                background: 'var(--emerald-bg)', color: 'var(--emerald-dark)',
                                border: '1px solid var(--emerald-border)', fontSize: '0.76rem', fontWeight: 700,
                              }}>
                                <CheckCircle2 size={11} />
                                Confirmed
                              </span>
                            ) : (
                              <span style={{
                                display: 'inline-flex', alignItems: 'center', gap: '0.3rem',
                                padding: '0.15rem 0.55rem', borderRadius: '999px',
                                background: 'var(--amber-bg)', color: 'var(--amber-dark)',
                                border: '1px solid var(--amber-border)', fontSize: '0.76rem', fontWeight: 700,
                              }}>
                                <Clock size={11} />
                                Potential
                              </span>
                            )}
                          </td>
                          <td style={{
                            padding: '0.85rem', textAlign: 'right', fontWeight: 800,
                            color: pmt.is_contractual_commitment ? 'var(--navy-slate)' : 'var(--amber-dark)',
                            fontFamily: 'JetBrains Mono, monospace',
                          }}>
                            {fmt(pmt.expected_payment_amount)} {pmt.currency}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Methodology note for calendar */}
                {paymentSchedulingMethodology && (
                  <div style={{
                    marginTop: '1.25rem', padding: '0.85rem 1.15rem',
                    background: 'var(--bg-subtle)', borderRadius: 'var(--radius-sm)',
                    fontSize: '0.82rem', color: 'var(--text-muted)', lineHeight: 1.55,
                    display: 'flex', alignItems: 'center', gap: '0.65rem',
                  }}>
                    <Info size={15} color="var(--text-caption)" style={{ flexShrink: 0 }} />
                    <span>
                      <strong style={{ color: 'var(--navy-slate)' }}>Payment Calendar Methodology: </strong>
                      {paymentSchedulingMethodology}
                    </span>
                  </div>
                )}
              </>
            )}
          </div>
        </>
      )}

      {/* ── Section: Methodology & Deterministic Modeling Disclosure ──────── */}
      {(methodologyNote || assumptions) && (
        <div style={{
          display: 'flex', alignItems: 'flex-start', gap: '0.85rem',
          background: 'var(--bg-subtle)', border: '1.5px solid var(--border-light)',
          borderRadius: 'var(--radius-lg)', padding: '1.15rem 1.5rem',
          fontSize: '0.88rem', color: 'var(--text-muted)', lineHeight: 1.65,
        }}>
          <Info size={18} style={{ flexShrink: 0, marginTop: '0.15rem', color: 'var(--text-caption)' }} />
          <div>
            <strong style={{ color: 'var(--navy-slate)' }}>Methodology &amp; Modeling Disclosure: </strong>
            {methodologyNote || assumptions}
          </div>
        </div>
      )}

    </div>
  );
};

export default ForecastPage;
